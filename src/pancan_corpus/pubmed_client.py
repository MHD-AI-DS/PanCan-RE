"""PubMed / PMC client using NCBI E-utilities API."""

import json
import os
import time
from typing import List

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .io_utils import setup_logging

logger = setup_logging(__name__)

EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Maximum retmax enforced by NCBI E-utilities
NCBI_MAX_RETMAX = 10000

# Maximum pagination pages to prevent infinite loops
MAX_PAGINATION_PAGES = 50


def _create_session(verify_ssl: bool = True) -> requests.Session:
    """Create a requests session with retry logic."""
    session = requests.Session()

    # SSL: prefer proper verification; allow override for institutional proxies
    ca_bundle = os.environ.get("REQUESTS_CA_BUNDLE", "")
    if ca_bundle and os.path.exists(ca_bundle):
        session.verify = ca_bundle
        logger.info(f"Using custom CA bundle: {ca_bundle}")
    elif not verify_ssl:
        # Fallback for environments with proxy issues (document in paper)
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        session.verify = False
        logger.warning("SSL verification disabled. Set REQUESTS_CA_BUNDLE for proper cert handling.")
    else:
        session.verify = True

    # Retry with exponential backoff
    retry_strategy = Retry(
        total=5,
        backoff_factor=1.0,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


class PubMedClient:
    """Client for NCBI E-utilities (ESearch + EFetch)."""

    def __init__(self, api_key: str = "", email: str = "", tool: str = "pancan_re_corpus",
                 rate_limit: float = 3.0, verify_ssl: bool = True):
        self.api_key = api_key
        self.email = email
        self.tool = tool
        self.delay = 1.0 / rate_limit
        self.session = _create_session(verify_ssl=verify_ssl)
        self.session.headers.update({"User-Agent": f"{tool}/1.0"})

    def _base_params(self) -> dict:
        params = {"tool": self.tool}
        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key
        return params

    def search(self, query: str, db: str = "pubmed", retmax: int = 10000,
               mindate: str = "", maxdate: str = "") -> List[str]:
        """
        Run ESearch and return a list of PMIDs.
        Handles pagination for large result sets.
        """
        # Clean query: collapse whitespace/newlines into single spaces
        query = " ".join(query.split())

        # Enforce NCBI retmax cap
        if retmax > NCBI_MAX_RETMAX:
            logger.warning(f"retmax={retmax} exceeds NCBI limit of {NCBI_MAX_RETMAX}; capping.")
            retmax = NCBI_MAX_RETMAX

        all_ids = []
        retstart = 0

        # First call to get total count
        params = {
            **self._base_params(),
            "db": db,
            "term": query,
            "retmax": retmax,
            "retstart": retstart,
            "rettype": "uilist",
            "retmode": "json",
            "usehistory": "y",
        }
        if mindate:
            params["mindate"] = mindate
            params["datetype"] = "pdat"
        if maxdate:
            params["maxdate"] = maxdate

        logger.info(f"Searching {db} with query (first {len(query)} chars): {query[:120]}...")
        resp = self.session.get(f"{EUTILS_BASE}/esearch.fcgi", params=params, timeout=60)
        resp.raise_for_status()
        data = json.loads(resp.text, strict=False)

        result = data.get("esearchresult", {})
        total = int(result.get("count", 0))
        ids = result.get("idlist", [])
        webenv = result.get("webenv", "")
        query_key = result.get("querykey", "")
        all_ids.extend(ids)

        logger.info(f"  Total results: {total}, fetched: {len(ids)}")

        # Rate limit after initial request
        time.sleep(self.delay)

        # Paginate with guard against infinite loops
        page = 0
        while len(all_ids) < total and page < MAX_PAGINATION_PAGES:
            page += 1
            retstart += retmax
            params["retstart"] = retstart
            params["WebEnv"] = webenv
            params["query_key"] = query_key

            resp = self.session.get(f"{EUTILS_BASE}/esearch.fcgi", params=params, timeout=60)
            resp.raise_for_status()
            data = json.loads(resp.text, strict=False)
            ids = data.get("esearchresult", {}).get("idlist", [])
            if not ids:
                break
            all_ids.extend(ids)
            logger.info(f"  Fetched {len(all_ids)}/{total} IDs (page {page})")
            time.sleep(self.delay)

        if page >= MAX_PAGINATION_PAGES:
            logger.warning(f"Pagination stopped at {MAX_PAGINATION_PAGES} pages ({len(all_ids)} IDs of {total})")

        return all_ids

    def fetch_records_xml(self, pmids: List[str], db: str = "pubmed",
                          batch_size: int = 200) -> List[str]:
        """
        Fetch PubMed XML records for a list of PMIDs in batches.
        Returns list of XML strings (one per batch).
        """
        xml_chunks = []
        failed_batches = 0

        for i in range(0, len(pmids), batch_size):
            batch = pmids[i:i + batch_size]
            params = {
                **self._base_params(),
                "db": db,
                "id": ",".join(batch),
                "rettype": "xml",
                "retmode": "xml",
            }
            logger.info(f"  Fetching batch {i // batch_size + 1} "
                        f"({len(batch)} records, {i + len(batch)}/{len(pmids)} total)")

            try:
                resp = self.session.get(f"{EUTILS_BASE}/efetch.fcgi", params=params, timeout=120)
                resp.raise_for_status()
                xml_chunks.append(resp.text)
            except requests.exceptions.RequestException as e:
                failed_batches += 1
                logger.error(f"  Batch {i // batch_size + 1} failed: {e}")

            time.sleep(self.delay)

        if failed_batches:
            logger.warning(f"  {failed_batches} batch(es) failed during fetch")

        return xml_chunks
