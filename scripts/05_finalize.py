#!/usr/bin/env python3
"""
Stage 05 — FINALIZE
Apply eligibility filter, assign record IDs, generate PRISMA diagram,
create final corpus and reproducibility manifest.
Input:  data/processed/processed_records.jsonl
Output: data/final/corpus.jsonl
        data/prisma/prisma_flow.png
        data/prisma/prisma_counts.json
"""

import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pancan_corpus.io_utils import (
    load_config, setup_logging, read_jsonl, write_jsonl, get_project_root
)
from src.pancan_corpus.eligibility import EligibilityFilter
from src.pancan_corpus.prisma import PRISMATracker

logger = setup_logging("05_finalize")


def main():
    config = load_config()
    root = get_project_root()
    data_dir = root / config["output"]["data_dir"]

    # Load processed records
    input_path = str(data_dir / "processed" / "processed_records.jsonl")
    logger.info(f"Loading processed records from {input_path}...")
    records = read_jsonl(input_path)
    logger.info(f"Loaded {len(records)} records")

    # --- Eligibility filtering ---
    logger.info("=" * 60)
    logger.info("ELIGIBILITY FILTERING")
    logger.info("=" * 60)

    elig_filter = EligibilityFilter(config)
    eligible, elig_counts = elig_filter.filter(records)

    # --- Assign record IDs ---
    for i, rec in enumerate(eligible, start=1):
        rec.record_id = f"PANCAN-{i:05d}"

    # --- Save final corpus ---
    final_path = str(root / config["output"]["final_corpus"])
    count = write_jsonl(eligible, final_path)
    logger.info(f"Final corpus: {count} records saved to {final_path}")

    # --- Build PRISMA counts ---
    prisma = PRISMATracker()

    # Load identification summary
    id_summary_path = data_dir / "raw" / "identification_summary.json"
    if id_summary_path.exists():
        with open(id_summary_path, "r", encoding="utf-8") as f:
            id_summary = json.load(f)
        prisma.update(id_summary)

    # Load screening counts
    screen_counts_path = data_dir / "screened" / "screening_counts.json"
    if screen_counts_path.exists():
        with open(screen_counts_path, "r", encoding="utf-8") as f:
            screen_counts = json.load(f)
        prisma.update(screen_counts)

    # Add eligibility counts
    prisma.update({
        "assessed_eligibility": len(records),
        "excluded_no_entity_pairs": elig_counts.get("excluded_no_entity_pairs", 0),
        "after_eligibility": len(eligible),
        "final_included": len(eligible),
    })

    prisma.compute_totals()

    # Save PRISMA counts
    prisma_counts_path = str(root / config["output"]["prisma_counts"])
    prisma.save(prisma_counts_path)

    # Generate PRISMA flow diagram
    prisma_diagram_path = str(root / config["output"]["prisma_diagram"])
    prisma.generate_diagram(prisma_diagram_path)

    # --- Create reproducibility manifest ---
    manifest = {
        "project": config["project"]["name"],
        "version": config["project"]["version"],
        "generated_at": datetime.now().isoformat(),
        "corpus_size": len(eligible),
        "prisma_counts": prisma.counts,
        "config_snapshot": {
            "search": config["search"],
            "screening": config["screening"],
            "deduplication": config["deduplication"],
            "preprocessing": config["preprocessing"],
            "eligibility": config["eligibility"],
        },
    }
    manifest_path = str(data_dir / "final" / "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Manifest saved to {manifest_path}")

    # --- Summary ---
    logger.info("=" * 60)
    logger.info("PIPELINE COMPLETE")
    logger.info("=" * 60)
    logger.info(f"  Identified:   {prisma.counts['total_identified']:,}")
    logger.info(f"  After dedup:  {prisma.counts['after_deduplication']:,}")
    logger.info(f"  After screen: {prisma.counts['after_screening']:,}")
    logger.info(f"  Eligible:     {prisma.counts['after_eligibility']:,}")
    logger.info(f"  FINAL CORPUS: {prisma.counts['final_included']:,}")
    logger.info("=" * 60)
    logger.info(f"  Corpus:  {final_path}")
    logger.info(f"  PRISMA:  {prisma_diagram_path}")
    logger.info(f"  Counts:  {prisma_counts_path}")
    logger.info(f"  Manifest: {manifest_path}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
