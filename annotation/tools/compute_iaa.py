#!/usr/bin/env python3
"""
Compute Inter-Annotator Agreement (IAA) using Cohen's Kappa.

Compares two annotation files (from different annotators) and computes:
- Entity-level agreement (type match)
- Relation-level agreement (type match given entity pair)
- Novelty-level agreement

Usage:
    python compute_iaa.py --annotator1 ../data/validated_ann1.jsonl \
                          --annotator2 ../data/validated_ann2.jsonl
"""

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def load_annotations(path: str) -> dict:
    """Load annotations indexed by record_id."""
    records = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rec = json.loads(line)
                rid = rec.get("record_id", "")
                if rid:
                    records[rid] = rec
    return records


def cohens_kappa(labels1: list, labels2: list) -> float:
    """Compute Cohen's Kappa between two lists of labels."""
    assert len(labels1) == len(labels2), "Label lists must have equal length"
    n = len(labels1)
    if n == 0:
        return 0.0

    all_labels = sorted(set(labels1) | set(labels2))
    label_to_idx = {l: i for i, l in enumerate(all_labels)}
    k = len(all_labels)

    # Confusion matrix
    matrix = [[0] * k for _ in range(k)]
    for l1, l2 in zip(labels1, labels2):
        matrix[label_to_idx[l1]][label_to_idx[l2]] += 1

    # Observed agreement
    p_o = sum(matrix[i][i] for i in range(k)) / n

    # Expected agreement
    p_e = 0.0
    for i in range(k):
        row_sum = sum(matrix[i])
        col_sum = sum(matrix[j][i] for j in range(k))
        p_e += (row_sum * col_sum) / (n * n)

    if p_e == 1.0:
        return 1.0

    kappa = (p_o - p_e) / (1.0 - p_e)
    return round(kappa, 4)


def interpret_kappa(k: float) -> str:
    """Interpret kappa value."""
    if k < 0:
        return "Poor (less than chance)"
    elif k < 0.20:
        return "Slight"
    elif k < 0.40:
        return "Fair"
    elif k < 0.60:
        return "Moderate"
    elif k < 0.80:
        return "Substantial"
    else:
        return "Almost perfect"


def entity_span_key(ent: dict) -> str:
    """Create a unique key for an entity based on span."""
    return f"{ent.get('start', -1)}_{ent.get('end', -1)}"


def compute_entity_agreement(records1: dict, records2: dict, common_ids: list):
    """Compute entity annotation agreement."""
    type_labels1 = []
    type_labels2 = []
    matches = 0
    total = 0

    for rid in common_ids:
        ents1 = {entity_span_key(e): e for e in records1[rid].get("entities", [])}
        ents2 = {entity_span_key(e): e for e in records2[rid].get("entities", [])}

        # Only compare entities with matching spans
        common_spans = set(ents1.keys()) & set(ents2.keys())
        for span in common_spans:
            t1 = ents1[span].get("type", "Unknown")
            t2 = ents2[span].get("type", "Unknown")
            type_labels1.append(t1)
            type_labels2.append(t2)
            if t1 == t2:
                matches += 1
            total += 1

    kappa = cohens_kappa(type_labels1, type_labels2) if type_labels1 else 0.0
    agreement = matches / total * 100 if total > 0 else 0.0

    return {
        "total_common_spans": total,
        "type_matches": matches,
        "raw_agreement_pct": round(agreement, 1),
        "cohens_kappa": kappa,
        "interpretation": interpret_kappa(kappa)
    }


def relation_pair_key(rel: dict) -> str:
    """Create a key for a relation based on entity pair."""
    subj = rel.get("subject_id", "")
    obj = rel.get("object_id", "")
    return f"{subj}_{obj}"


def compute_relation_agreement(records1: dict, records2: dict, common_ids: list):
    """Compute relation annotation agreement."""
    type_labels1 = []
    type_labels2 = []
    novelty_labels1 = []
    novelty_labels2 = []

    for rid in common_ids:
        rels1 = {relation_pair_key(r): r for r in records1[rid].get("relations", [])}
        rels2 = {relation_pair_key(r): r for r in records2[rid].get("relations", [])}

        common_pairs = set(rels1.keys()) & set(rels2.keys())
        for pair in common_pairs:
            # Relation type agreement
            t1 = rels1[pair].get("type", "None")
            t2 = rels2[pair].get("type", "None")
            type_labels1.append(t1)
            type_labels2.append(t2)

            # Novelty agreement
            n1 = rels1[pair].get("novelty", "Unknown")
            n2 = rels2[pair].get("novelty", "Unknown")
            novelty_labels1.append(n1)
            novelty_labels2.append(n2)

    type_kappa = cohens_kappa(type_labels1, type_labels2) if type_labels1 else 0.0
    novelty_kappa = cohens_kappa(novelty_labels1, novelty_labels2) if novelty_labels1 else 0.0

    type_matches = sum(1 for a, b in zip(type_labels1, type_labels2) if a == b)
    novelty_matches = sum(1 for a, b in zip(novelty_labels1, novelty_labels2) if a == b)

    return {
        "total_common_pairs": len(type_labels1),
        "relation_type": {
            "matches": type_matches,
            "raw_agreement_pct": round(type_matches / len(type_labels1) * 100, 1) if type_labels1 else 0.0,
            "cohens_kappa": type_kappa,
            "interpretation": interpret_kappa(type_kappa)
        },
        "novelty": {
            "matches": novelty_matches,
            "raw_agreement_pct": round(novelty_matches / len(novelty_labels1) * 100, 1) if novelty_labels1 else 0.0,
            "cohens_kappa": novelty_kappa,
            "interpretation": interpret_kappa(novelty_kappa)
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Compute Inter-Annotator Agreement")
    parser.add_argument("--annotator1", required=True, help="First annotator's JSONL file")
    parser.add_argument("--annotator2", required=True, help="Second annotator's JSONL file")
    parser.add_argument("--output", default="", help="Save report to JSON file")
    args = parser.parse_args()

    print("Loading annotations...")
    records1 = load_annotations(args.annotator1)
    records2 = load_annotations(args.annotator2)
    print(f"  Annotator 1: {len(records1)} records")
    print(f"  Annotator 2: {len(records2)} records")

    common_ids = sorted(set(records1.keys()) & set(records2.keys()))
    print(f"  Common records: {len(common_ids)}")

    if not common_ids:
        print("ERROR: No common records found between annotators.")
        sys.exit(1)

    print("\n" + "=" * 50)
    print("INTER-ANNOTATOR AGREEMENT REPORT")
    print("=" * 50)

    # Entity agreement
    ent_result = compute_entity_agreement(records1, records2, common_ids)
    print(f"\n--- Entity Type Agreement ---")
    print(f"  Common entity spans: {ent_result['total_common_spans']}")
    print(f"  Type matches: {ent_result['type_matches']}")
    print(f"  Raw agreement: {ent_result['raw_agreement_pct']}%")
    print(f"  Cohen's Kappa: {ent_result['cohens_kappa']}")
    print(f"  Interpretation: {ent_result['interpretation']}")

    # Relation agreement
    rel_result = compute_relation_agreement(records1, records2, common_ids)
    print(f"\n--- Relation Type Agreement ---")
    print(f"  Common relation pairs: {rel_result['total_common_pairs']}")
    rt = rel_result['relation_type']
    print(f"  Type matches: {rt['matches']}")
    print(f"  Raw agreement: {rt['raw_agreement_pct']}%")
    print(f"  Cohen's Kappa: {rt['cohens_kappa']}")
    print(f"  Interpretation: {rt['interpretation']}")

    nv = rel_result['novelty']
    print(f"\n--- Novelty Agreement ---")
    print(f"  Matches: {nv['matches']}")
    print(f"  Raw agreement: {nv['raw_agreement_pct']}%")
    print(f"  Cohen's Kappa: {nv['cohens_kappa']}")
    print(f"  Interpretation: {nv['interpretation']}")

    # Thresholds
    print(f"\n--- Quality Thresholds ---")
    print(f"  Entity κ ≥ 0.80: {'PASS' if ent_result['cohens_kappa'] >= 0.80 else 'FAIL'}")
    print(f"  Relation κ ≥ 0.65: {'PASS' if rt['cohens_kappa'] >= 0.65 else 'FAIL'}")
    print(f"  Novelty κ ≥ 0.70: {'PASS' if nv['cohens_kappa'] >= 0.70 else 'FAIL'}")

    # Save report
    if args.output:
        report = {
            "common_records": len(common_ids),
            "entity_agreement": ent_result,
            "relation_agreement": rel_result,
            "generated_at": __import__("datetime").datetime.now().isoformat()
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved to {args.output}")


if __name__ == "__main__":
    main()
