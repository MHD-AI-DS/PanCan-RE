#!/usr/bin/env python3
"""
Stage 01 — IDENTIFICATION
Search PubMed, PMC, and Scopus. Collect all matching record IDs.
Output: data/raw/pubmed_ids.json, data/raw/scopus_entries.json
"""

import json
import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pancan_corpus.io_utils import load_config, setup_logging, get_project_root
from src.pancan_corpus.pubmed_client import PubMedClient
from src.pancan_corpus.scopus_client import ScopusClient

logger = setup_logging("01_identify")


def main():
    config = load_config()
    root = get_project_root()
    raw_dir = root / config["output"]["data_dir"] / "raw"
    os.makedirs(raw_dir, exist_ok=True)

    search_cfg = config["search"]
    api_cfg = config["api"]
    retrieval_date = datetime.now().strftime("%Y-%m-%d")

    results_summary = {}

    # --- PubMed Search ---
    logger.info("=" * 60)
    logger.info("Searching PubMed...")
    logger.info("=" * 60)

    pm_client = PubMedClient(
        api_key=api_cfg["ncbi"].get("api_key", ""),
        email=api_cfg["ncbi"].get("email", ""),
        tool=api_cfg["ncbi"].get("tool_name", "pancan_re_corpus"),
        rate_limit=api_cfg["ncbi"].get("rate_limit_per_sec", 3),
    )

    pubmed_ids = pm_client.search(
        query=search_cfg["pubmed_query"],
        db="pubmed",
        retmax=search_cfg.get("pubmed_retmax", 10000),
        mindate=search_cfg.get("date_from", ""),
        maxdate=search_cfg.get("date_to", ""),
    )
    results_summary["pubmed_identified"] = len(pubmed_ids)
    logger.info(f"PubMed: {len(pubmed_ids)} records identified")

    # --- PMC Search ---
    logger.info("=" * 60)
    logger.info("Searching PMC...")
    logger.info("=" * 60)

    pmc_ids = pm_client.search(
        query=search_cfg["pubmed_query"],
        db="pmc",
        retmax=search_cfg.get("pubmed_retmax", 10000),
        mindate=search_cfg.get("date_from", ""),
        maxdate=search_cfg.get("date_to", ""),
    )
    results_summary["pmc_identified"] = len(pmc_ids)
    logger.info(f"PMC: {len(pmc_ids)} records identified")

    # Save PubMed + PMC IDs
    id_data = {
        "retrieval_date": retrieval_date,
        "pubmed_query": search_cfg["pubmed_query"],
        "pubmed_ids": pubmed_ids,
        "pmc_ids": pmc_ids,
    }
    id_path = raw_dir / "pubmed_ids.json"
    with open(id_path, "w", encoding="utf-8") as f:
        json.dump(id_data, f, indent=2)
    logger.info(f"Saved {len(pubmed_ids)} PubMed + {len(pmc_ids)} PMC IDs to {id_path}")

    # --- Scopus Search ---
    scopus_key = api_cfg["scopus"].get("api_key", "")
    if scopus_key:
        logger.info("=" * 60)
        logger.info("Searching Scopus...")
        logger.info("=" * 60)

        sc_client = ScopusClient(
            api_key=scopus_key,
            rate_limit=api_cfg["scopus"].get("rate_limit_per_sec", 5),
        )

        scopus_entries = sc_client.search(
            query=search_cfg["scopus_query"],
            max_results=search_cfg.get("scopus_max_results", 10000),
            date_from=int(search_cfg.get("date_from", "2015/01/01")[:4]),
        )
        results_summary["scopus_identified"] = len(scopus_entries)
        logger.info(f"Scopus: {len(scopus_entries)} records identified")

        scopus_data = {
            "retrieval_date": retrieval_date,
            "scopus_query": search_cfg["scopus_query"],
            "entries": scopus_entries,
        }
        scopus_path = raw_dir / "scopus_entries.json"
        with open(scopus_path, "w", encoding="utf-8") as f:
            json.dump(scopus_data, f, indent=2, default=str)
        logger.info(f"Saved {len(scopus_entries)} Scopus entries to {scopus_path}")
    else:
        logger.info("No Scopus API key configured, skipping Scopus search")
        results_summary["scopus_identified"] = 0

    # Save summary
    results_summary["total_identified"] = (
        results_summary["pubmed_identified"]
        + results_summary["pmc_identified"]
        + results_summary["scopus_identified"]
    )
    summary_path = raw_dir / "identification_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results_summary, f, indent=2)

    logger.info("=" * 60)
    logger.info("IDENTIFICATION COMPLETE")
    logger.info(f"  PubMed: {results_summary['pubmed_identified']:,}")
    logger.info(f"  PMC:    {results_summary['pmc_identified']:,}")
    logger.info(f"  Scopus: {results_summary['scopus_identified']:,}")
    logger.info(f"  TOTAL:  {results_summary['total_identified']:,}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
