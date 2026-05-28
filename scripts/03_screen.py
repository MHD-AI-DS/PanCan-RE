#!/usr/bin/env python3
"""
Stage 03 — SCREENING & DEDUPLICATION
Apply inclusion/exclusion criteria, then remove duplicates.
Input:  data/raw/all_records.jsonl
Output: data/screened/screened_records.jsonl
        data/deduplicated/deduped_records.jsonl
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pancan_corpus.io_utils import (
    load_config, setup_logging, read_jsonl, write_jsonl, get_project_root
)
from src.pancan_corpus.screening import Screener
from src.pancan_corpus.deduplication import Deduplicator

logger = setup_logging("03_screen")


def main():
    config = load_config()
    root = get_project_root()
    data_dir = root / config["output"]["data_dir"]

    # Load raw records
    raw_path = str(data_dir / "raw" / "all_records.jsonl")
    logger.info(f"Loading raw records from {raw_path}...")
    records = read_jsonl(raw_path)
    logger.info(f"Loaded {len(records)} raw records")

    # --- Deduplication first (before screening) ---
    logger.info("=" * 60)
    logger.info("DEDUPLICATION")
    logger.info("=" * 60)

    deduplicator = Deduplicator(config)
    deduped, dedup_counts = deduplicator.deduplicate(records)

    dedup_path = str(data_dir / "deduplicated" / "deduped_records.jsonl")
    write_jsonl(deduped, dedup_path)
    logger.info(f"Saved {len(deduped)} deduplicated records to {dedup_path}")

    # --- Screening ---
    logger.info("=" * 60)
    logger.info("SCREENING")
    logger.info("=" * 60)

    screener = Screener(config)
    screened, screen_counts = screener.screen(deduped)

    screened_path = str(data_dir / "screened" / "screened_records.jsonl")
    write_jsonl(screened, screened_path)
    logger.info(f"Saved {len(screened)} screened records to {screened_path}")

    # --- Save stage counts ---
    stage_counts = {
        **dedup_counts,
        **screen_counts,
        "after_deduplication": len(deduped),
        "after_screening": len(screened),
    }
    counts_path = str(data_dir / "screened" / "screening_counts.json")
    os.makedirs(os.path.dirname(counts_path), exist_ok=True)
    with open(counts_path, "w", encoding="utf-8") as f:
        json.dump(stage_counts, f, indent=2)

    logger.info("=" * 60)
    logger.info("SCREENING COMPLETE")
    logger.info(f"  Raw records:        {len(records):,}")
    logger.info(f"  After dedup:        {len(deduped):,}")
    logger.info(f"  After screening:    {len(screened):,}")
    logger.info(f"  Duplicates removed: {dedup_counts['total_duplicates_removed']:,}")
    logger.info(f"  Screening excluded: {sum(screen_counts.values()):,}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
