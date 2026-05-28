"""Scopus client using Elsevier Scopus Search API."""

import os
import time
from typing import Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .io_utils import setup_logging
from .schema import CorpusRecord

logger = setup_logging(__name__)

SCOPUS_SEARCH_URL = "https://api.elsevier.com/content/search/scopus"
SCOPUS_ABSTRACT_URL = "https://api.elsevier.com/content/abstract/scopus_id"

# Scopus API pagination hard limit
SCOPUS_MAX_RESULTS = 5000
MAX_429_RETRIES = 5


def _create_session(api_key: str, verify_ssl: bool = True) -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()
    session.headers.update({
        "X-ELS-APIKey": api_key,
        "Accept": "application/json",
    })

    ca_bundle = os.environ.get("REQUESTS_CA_BUNDLE", "")
    if ca_bundle and os.path.exists(ca_bundle):
        session.verify = ca_bundle
    elif not verify_ssl:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        session.verify = False
        logger.warning("SSL verification disabled for Scopus. Set REQUESTS_CA_BUNDLE for proper cert handling.")
    else:
        session.verify = True

    retry_strategy = Retry(
        total=5,
        backoff_factor=1.0,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


class ScopusClient:
    """Client for the Elsevier Scopus Search API."""

    def __init__(self, api_key: str, rate_limit: float = 5.0, verify_ssl: bool = True):
        self.api_key = api_key
        self.delay = 1.0 / rate_limit
        self.session = _create_session(api_key, verify_ssl=verify_ssl)

    def search(self, query: str, max_results: int = 10000,
               date_from: int = 2015) -> List[Dict]:
        """
        Search Scopus and return a list of result entries.
        Handles pagination automatically.
        """
        all_entries = []
        start = 0
        count = 25  # Scopus max per page

        # Clean query and add date filter
        query = " ".join(query.split())
        full_query = f"{query} AND PUBYEAR > {date_from - 1}"

        # Scopus API limits pagination to 5000 results
        if max_results > SCOPUS_MAX_RESULTS:
            logger.warning(
                f"Scopus API limits pagination to {SCOPUS_MAX_RESULTS} results; "
                f"requested {max_results} will be capped."
            )
            max_results = SCOPUS_MAX_RESULTS

        logger.info(f"Searching Scopus: {full_query[:120]}...")

        rate_limit_retries = 0

        while True:
            params = {
                "query": full_query,
                "start": start,
                "count": count,
                "sort": "pubyear",
                "field": "dc:identifier,dc:title,dc:creator,prism:publicationName,"
                         "prism:coverDate,prism:doi,citedby-count,subtypeDescription,"
                         "authkeywords,eid",
            }

            resp = self.session.get(SCOPUS_SEARCH_URL, params=params, timeout=60)

            if resp.status_code == 429:
                rate_limit_retries += 1
                if rate_limit_retries > MAX_429_RETRIES:
                    logger.error(f"Scopus rate limit exceeded after {MAX_429_RETRIES} retries. Stopping.")
                    break
                wait = min(10 * rate_limit_retries, 60)
                logger.warning(f"Rate limited by Scopus. Waiting {wait}s (retry {rate_limit_retries}/{MAX_429_RETRIES})...")
                time.sleep(wait)
                continue

            resp.raise_for_status()
            data = resp.json()
            rate_limit_retries = 0  # Reset on success

            results = data.get("search-results", {})
            total = int(results.get("opensearch:totalResults", 0))
            entries = results.get("entry", [])

            # Check for error entries
            if entries and "error" in entries[0]:
                logger.warning(f"Scopus returned error: {entries[0]['error']}")
                break

            all_entries.extend(entries)
            logger.info(f"  Fetched {len(all_entries)}/{min(total, max_results)} entries")

            start += count
            if start >= total or len(all_entries) >= max_results:
                break

            time.sleep(self.delay)

        return all_entries[:max_results]

    def fetch_abstract(self, scopus_id: str) -> Optional[str]:
        """Fetch the full abstract text for a Scopus ID."""
        url = f"{SCOPUS_ABSTRACT_URL}/{scopus_id}"
        params = {"field": "dc:description"}

        try:
            resp = self.session.get(url, params=params, timeout=30)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()
            # Navigate the nested response
            core = data.get("abstracts-retrieval-response", {}).get("coredata", {})
            return core.get("dc:description", "") or ""
        except Exception as e:
            logger.warning(f"Failed to fetch abstract for {scopus_id}: {e}")
            return None

    def fetch_abstracts_batch(self, scopus_ids: List[str]) -> Dict[str, str]:
        """Fetch abstracts for multiple Scopus IDs. Returns {scopus_id: abstract_text}."""
        results = {}
        for i, sid in enumerate(scopus_ids):
            abstract = self.fetch_abstract(sid)
            if abstract:
                results[sid] = abstract
            if (i + 1) % 50 == 0:
                logger.info(f"  Fetched {i + 1}/{len(scopus_ids)} Scopus abstracts")
            time.sleep(self.delay)
        return results

    @staticmethod
    def entry_to_record(entry: dict, query: str, retrieval_date: str,
                        abstract: str = "") -> CorpusRecord:
        """Convert a Scopus search entry to a CorpusRecord."""
        # Extract Scopus ID from EID
        eid = entry.get("eid") or ""
        scopus_id = eid.replace("2-s2.0-", "") if eid.startswith("2-s2.0-") else eid

        # Extract year from cover date
        cover_date = entry.get("prism:coverDate") or ""
        year = int(cover_date[:4]) if cover_date and len(cover_date) >= 4 else 0

        # Extract authors
        creator = entry.get("dc:creator") or ""
        authors = [creator] if creator else []

        # Extract keywords
        kw_str = entry.get("authkeywords") or ""
        keywords = [k.strip() for k in kw_str.split("|")] if kw_str else []

        return CorpusRecord(
            scopus_id=scopus_id,
            doi=entry.get("prism:doi") or "",
            title=entry.get("dc:title") or "",
            abstract=abstract,
            authors=authors,
            journal=entry.get("prism:publicationName") or "",
            year=year,
            keywords=keywords,
            publication_type=[entry.get("subtypeDescription") or ""],
            source_db="scopus",
            source_query=query,
            retrieval_date=retrieval_date,
            language="",  # Unknown from search API; screening will handle
        )
