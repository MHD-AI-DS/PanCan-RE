#!/usr/bin/env python3
"""
Stage 04 — PREPROCESSING
Apply normalization, tokenization, and sentence splitting.
Input:  data/screened/screened_records.jsonl
Output: data/processed/processed_records.jsonl
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pancan_corpus.io_utils import (
    load_config, setup_logging, read_jsonl, write_jsonl, get_project_root
)
from src.pancan_corpus.preprocessing import Preprocessor

logger = setup_logging("04_preprocess")


def main():
    config = load_config()
    root = get_project_root()
    data_dir = root / config["output"]["data_dir"]

    # Load screened records
    input_path = str(data_dir / "screened" / "screened_records.jsonl")
    logger.info(f"Loading screened records from {input_path}...")
    records = read_jsonl(input_path)
    logger.info(f"Loaded {len(records)} records")

    # Preprocess
    logger.info("=" * 60)
    logger.info("PREPROCESSING")
    logger.info("=" * 60)

    preprocessor = Preprocessor(config)
    processed = preprocessor.process(records)

    # Save
    output_path = str(data_dir / "processed" / "processed_records.jsonl")
    count = write_jsonl(processed, output_path)

    logger.info("=" * 60)
    logger.info(f"PREPROCESSING COMPLETE: {count} records saved to {output_path}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
