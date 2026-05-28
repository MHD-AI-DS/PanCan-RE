#!/usr/bin/env python3
"""
Stage 02 — FETCH
Download full abstract records from PubMed and Scopus.
Input:  data/raw/pubmed_ids.json, data/raw/scopus_entries.json
Output: data/raw/all_records.jsonl
"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pancan_corpus.io_utils import load_config, setup_logging, write_jsonl, get_project_root
from src.pancan_corpus.pubmed_client import PubMedClient
from src.pancan_corpus.parsing import parse_pubmed_xml
from src.pancan_corpus.scopus_client import ScopusClient
from src.pancan_corpus.schema import CorpusRecord

logger = setup_logging("02_fetch")


def main():
    config = load_config()
    root = get_project_root()
    raw_dir = root / config["output"]["data_dir"] / "raw"
    api_cfg = config["api"]
    retrieval_date = datetime.now().strftime("%Y-%m-%d")
    all_records = []

    # --- Fetch PubMed records ---
    id_path = raw_dir / "pubmed_ids.json"
    if id_path.exists():
        with open(id_path, "r", encoding="utf-8") as f:
            id_data = json.load(f)

        pubmed_ids = id_data.get("pubmed_ids", [])
        pmc_ids = id_data.get("pmc_ids", [])
        query = id_data.get("pubmed_query", "")

        if pubmed_ids:
            logger.info(f"Fetching {len(pubmed_ids)} PubMed records...")
            pm_client = PubMedClient(
                api_key=api_cfg["ncbi"].get("api_key", ""),
                email=api_cfg["ncbi"].get("email", ""),
                rate_limit=api_cfg["ncbi"].get("rate_limit_per_sec", 3),
            )
            xml_chunks = pm_client.fetch_records_xml(pubmed_ids, db="pubmed")
            for xml_text in xml_chunks:
                records = parse_pubmed_xml(xml_text, query, retrieval_date)
                all_records.extend(records)
            logger.info(f"  Parsed {len(all_records)} PubMed records")

        if pmc_ids:
            logger.info(f"Fetching {len(pmc_ids)} PMC records...")
            pm_client = PubMedClient(
                api_key=api_cfg["ncbi"].get("api_key", ""),
                email=api_cfg["ncbi"].get("email", ""),
                rate_limit=api_cfg["ncbi"].get("rate_limit_per_sec", 3),
            )
            pmc_before = len(all_records)
            xml_chunks = pm_client.fetch_records_xml(pmc_ids, db="pmc")
            for xml_text in xml_chunks:
                records = parse_pubmed_xml(xml_text, query, retrieval_date)
                for r in records:
                    r.source_db = "pmc"
                all_records.extend(records)
            logger.info(f"  Parsed {len(all_records) - pmc_before} PMC records")
    else:
        logger.warning(f"No PubMed ID file found at {id_path}")

    # --- Fetch Scopus records ---
    scopus_path = raw_dir / "scopus_entries.json"
    scopus_key = api_cfg["scopus"].get("api_key", "")

    if scopus_path.exists() and scopus_key:
        with open(scopus_path, "r", encoding="utf-8") as f:
            scopus_data = json.load(f)

        entries = scopus_data.get("entries", [])
        query = scopus_data.get("scopus_query", "")
        logger.info(f"Processing {len(entries)} Scopus entries...")

        # Collect Scopus IDs that need abstract fetching
        sc_client = ScopusClient(
            api_key=scopus_key,
            rate_limit=api_cfg["scopus"].get("rate_limit_per_sec", 5),
        )

        scopus_records = []
        scopus_ids_need_abstract = []

        for entry in entries:
            rec = ScopusClient.entry_to_record(entry, query, retrieval_date)
            scopus_records.append(rec)
            if not rec.abstract:
                eid = entry.get("eid", "")
                sid = eid.replace("2-s2.0-", "") if eid.startswith("2-s2.0-") else eid
                if sid:
                    scopus_ids_need_abstract.append((len(scopus_records) - 1, sid))

        # Fetch missing abstracts
        if scopus_ids_need_abstract:
            logger.info(f"  Fetching {len(scopus_ids_need_abstract)} Scopus abstracts...")
            for idx, sid in scopus_ids_need_abstract:
                abstract = sc_client.fetch_abstract(sid)
                if abstract:
                    scopus_records[idx].abstract = abstract

        all_records.extend(scopus_records)
        logger.info(f"  Added {len(scopus_records)} Scopus records")
    else:
        if not scopus_path.exists():
            logger.info("No Scopus entries file found, skipping")

    # --- Save all raw records ---
    output_path = str(raw_dir / "all_records.jsonl")
    count = write_jsonl(all_records, output_path)
    logger.info("=" * 60)
    logger.info(f"FETCH COMPLETE: {count} total records saved to {output_path}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
