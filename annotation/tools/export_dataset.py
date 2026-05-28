#!/usr/bin/env python3
"""
Export validated annotations to final PanCan-RE dataset format.

Reads the validated JSONL from the annotation GUI and produces:
1. Final dataset JSONL (PanCan-RE format)
2. Dataset statistics summary
3. Train/dev/test splits

Usage:
    python export_dataset.py --input ../data/validated.jsonl --output ../data/dataset/
"""

import argparse
import json
import os
import random
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path


def load_validated(path: str) -> list:
    """Load validated annotation records."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rec = json.loads(line)
                # Only include human-validated records
                annotator = rec.get("metadata", {}).get("annotator", "")
                if annotator and annotator != "groq_preannotation":
                    records.append(rec)
    return records


def export_pancan_format(records: list, output_dir: str):
    """Export to PanCan-RE JSONL format."""
    os.makedirs(output_dir, exist_ok=True)

    # Full dataset
    full_path = os.path.join(output_dir, "pancan_re_annotated.jsonl")
    with open(full_path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"  Full dataset: {full_path} ({len(records)} records)")

    # Train/dev/test split (70/15/15)
    random.seed(42)
    indices = list(range(len(records)))
    random.shuffle(indices)

    n = len(records)
    n_train = int(n * 0.70)
    n_dev = int(n * 0.15)

    splits = {
        "train": [records[i] for i in indices[:n_train]],
        "dev": [records[i] for i in indices[n_train:n_train + n_dev]],
        "test": [records[i] for i in indices[n_train + n_dev:]],
    }

    for split_name, split_records in splits.items():
        split_path = os.path.join(output_dir, f"{split_name}.jsonl")
        with open(split_path, "w", encoding="utf-8") as f:
            for rec in split_records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"  {split_name}: {split_path} ({len(split_records)} records)")

    return splits


def compute_statistics(records: list) -> dict:
    """Compute dataset statistics."""
    entity_type_counts = Counter()
    relation_type_counts = Counter()
    novelty_counts = Counter()
    entity_pair_counts = Counter()
    entities_per_record = []
    relations_per_record = []
    confidence_counts = Counter()

    for rec in records:
        entities = rec.get("entities", [])
        relations = rec.get("relations", [])
        entities_per_record.append(len(entities))
        relations_per_record.append(len(relations))

        ent_lookup = {e["entity_id"]: e for e in entities}

        for ent in entities:
            entity_type_counts[ent.get("type", "Unknown")] += 1

        for rel in relations:
            relation_type_counts[rel.get("type", "Unknown")] += 1
            novelty_counts[rel.get("novelty", "Unknown")] += 1

            subj = ent_lookup.get(rel.get("subject_id", ""), {})
            obj = ent_lookup.get(rel.get("object_id", ""), {})
            pair = f'{subj.get("type", "?")}-{obj.get("type", "?")}'
            entity_pair_counts[pair] += 1

        confidence_counts[rec.get("metadata", {}).get("confidence", "unknown")] += 1

    stats = {
        "total_records": len(records),
        "total_entities": sum(entities_per_record),
        "total_relations": sum(relations_per_record),
        "avg_entities_per_record": round(sum(entities_per_record) / len(records), 1) if records else 0,
        "avg_relations_per_record": round(sum(relations_per_record) / len(records), 1) if records else 0,
        "entity_type_distribution": dict(entity_type_counts.most_common()),
        "relation_type_distribution": dict(relation_type_counts.most_common()),
        "novelty_distribution": dict(novelty_counts.most_common()),
        "entity_pair_distribution": dict(entity_pair_counts.most_common()),
        "annotator_confidence": dict(confidence_counts.most_common()),
        "generated_at": datetime.now().isoformat()
    }
    return stats


def main():
    parser = argparse.ArgumentParser(description="Export PanCan-RE annotated dataset")
    parser.add_argument("--input", default="../data/validated.jsonl")
    parser.add_argument("--output", default="../data/dataset/")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    input_path = str((script_dir / args.input).resolve())
    output_dir = str((script_dir / args.output).resolve())

    print(f"Loading validated annotations from {input_path}...")
    records = load_validated(input_path)
    print(f"Loaded {len(records)} validated records")

    if not records:
        print("ERROR: No validated records found. Run annotation GUI first.")
        sys.exit(1)

    print(f"\nExporting to {output_dir}...")
    splits = export_pancan_format(records, output_dir)

    print("\nComputing statistics...")
    stats = compute_statistics(records)
    stats_path = os.path.join(output_dir, "dataset_statistics.json")
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"  Statistics: {stats_path}")

    # Print summary
    print("\n" + "=" * 50)
    print("DATASET SUMMARY")
    print("=" * 50)
    print(f"  Records:   {stats['total_records']}")
    print(f"  Entities:  {stats['total_entities']} (avg {stats['avg_entities_per_record']}/record)")
    print(f"  Relations: {stats['total_relations']} (avg {stats['avg_relations_per_record']}/record)")
    print(f"\n  Entity types:")
    for t, c in stats["entity_type_distribution"].items():
        print(f"    {t}: {c}")
    print(f"\n  Relation types:")
    for t, c in stats["relation_type_distribution"].items():
        print(f"    {t}: {c}")
    print(f"\n  Novelty:")
    for t, c in stats["novelty_distribution"].items():
        print(f"    {t}: {c}")


if __name__ == "__main__":
    main()
