#!/usr/bin/env python3
"""
Export annotated data to GitHub Pages review format.

Reads validated/pre-annotated JSONL and generates review_data.json
for the expert review web app.

Usage:
    python export_for_review.py --input ../data/preannotated.jsonl \
                                --output ../../docs/expert-review/review_data.json \
                                --n 50
"""

import argparse
import json
import os
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Export data for GitHub Pages expert review")
    parser.add_argument("--input", required=True, help="Input JSONL file")
    parser.add_argument("--output", required=True, help="Output JSON file for web app")
    parser.add_argument("--n", type=int, default=50, help="Number of records to export")
    args = parser.parse_args()

    print(f"Loading annotations from {args.input}...")
    records = []
    with open(args.input, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rec = json.loads(line)
                # Only export records with relations
                if rec.get("relations"):
                    records.append(rec)

    records = records[:args.n]
    print(f"Exporting {len(records)} records with relations")

    # Slim down for web — only include fields needed for review
    export = []
    for rec in records:
        export.append({
            "record_id": rec.get("record_id", ""),
            "title": rec.get("title", ""),
            "abstract": rec.get("abstract", ""),
            "year": rec.get("year", 0),
            "journal": rec.get("journal", ""),
            "entities": [
                {
                    "entity_id": e.get("entity_id", ""),
                    "type": e.get("type", ""),
                    "text": e.get("text", ""),
                    "start": e.get("start", -1),
                    "end": e.get("end", -1)
                }
                for e in rec.get("entities", [])
            ],
            "relations": [
                {
                    "relation_id": r.get("relation_id", ""),
                    "type": r.get("type", ""),
                    "subject_id": r.get("subject_id", ""),
                    "object_id": r.get("object_id", ""),
                    "directed": r.get("directed", False),
                    "novelty": r.get("novelty", ""),
                    "evidence": r.get("evidence", r.get("evidence_sentence", ""))
                }
                for r in rec.get("relations", [])
            ]
        })

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(export, f, ensure_ascii=False, indent=2)

    total_rels = sum(len(r["relations"]) for r in export)
    print(f"\nExported to {args.output}")
    print(f"  Records: {len(export)}")
    print(f"  Relations: {total_rels}")
    print(f"\nDeploy docs/expert-review/ to GitHub Pages and share the link with experts.")


if __name__ == "__main__":
    main()
