#!/usr/bin/env python3
"""
Pre-annotation pipeline using Groq LLM API.

Sends abstracts to Groq (LLaMA-based model) to generate draft entity
and relation annotations. These drafts are then loaded into the
annotation GUI for human review and correction.

Usage:
    python preannotate.py --input ../../data/final/corpus.jsonl \
                          --output ../data/preannotated.jsonl \
                          --n 50 --start 0
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

# Groq API endpoint
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

# Entity and relation type definitions (for the prompt)
ENTITY_TYPES = [
    "GeneOrProtein — A SPECIFIC named gene, protein, enzyme, receptor, or transcription factor. Must be a real molecular entity with a known database ID. Examples: KRAS, EGFR, PARP, PD-L1, c-Myc, TP53, BRCA2. Do NOT tag generic terms like 'oncogene', 'kinase', 'protein' without a specific name.",
    "Chemical — A SPECIFIC named drug, pharmaceutical compound, or therapeutic agent. Must be a real substance. Examples: gemcitabine, olaparib, cisplatin, FOLFIRINOX, 5-FU, erlotinib. Do NOT tag generic terms like 'chemotherapy', 'drug', 'treatment', 'blood tests', 'contrast agent'.",
    "Disease — A disease, disorder, pathological condition, or clinically significant phenotype. Examples: pancreatic cancer, PDAC, pancreatic ductal adenocarcinoma, chemoresistance, neuropathy, metastasis. Do NOT tag general terms like 'malignancy' or 'cancer' alone without the organ.",
    "SequenceVariant — A SPECIFIC genetic mutation, variant, or genomic alteration. Must reference a real variant. Examples: KRASG12D, KRASG12C, BRCA2 mutation, TP53 deletion, MSI-H. Do NOT tag vague terms like 'genetic alteration' or 'somatic changes'.",
    "Pathway — A SPECIFIC named biological pathway or well-defined cellular process with a known pathway database entry (KEGG/Reactome/GO). Examples: MAPK pathway, Wnt signaling, apoptosis, autophagy, ferroptosis, EMT, DNA damage response. Do NOT tag clinical procedures (endoscopy, ultrasonography), diagnostic methods (cytology, biopsy), clinical workflows, or screening protocols.",
    "CellLine — An established laboratory cell line with a known Cellosaurus ID. Examples: PANC-1, MIA PaCa-2, AsPC-1, BxPC-3. Do NOT tag animal models (KPC mice), patient-derived organoids, or generic cell descriptions ('cancer cells')."
]

RELATION_TYPES = [
    "Positive_Correlation — Subject increases/activates/causes/induces/upregulates object (directed: subject→object)",
    "Negative_Correlation — Subject decreases/inhibits/suppresses/treats/blocks object (directed: subject→object)",
    "Association — General association without clear positive/negative direction (undirected)",
    "Binding — Physical molecular binding or direct interaction (undirected)",
    "Drug_Interaction — Pharmacological interaction between two drugs (undirected)",
    "Cotreatment — Two drugs co-administered as treatment (undirected)",
    "Comparison — Two entities compared in a study (undirected)",
    "Conversion — One chemical converted/metabolized into another (directed: substrate→product)"
]

SYSTEM_PROMPT = """You are a biomedical annotation expert specializing in pancreatic cancer literature.
Your task is to extract biomedical entities and their relations from scientific abstracts.

ENTITY TYPES:
{entity_types}

RELATION TYPES:
{relation_types}

NOVELTY LABELS:
- Novel: The relation is a NEW finding/result of the current study
- Known: The relation is BACKGROUND knowledge cited by the authors

CRITICAL RULES:
1. ONLY extract entities that are SPECIFIC named biomedical entities (genes, drugs, diseases, variants, pathways, cell lines). Be STRICT — quality over quantity. If unsure, do NOT annotate.
2. Do NOT tag clinical procedures (endoscopy, ultrasonography, biopsy), laboratory methods (Western blot, PCR, sequencing), clinical workflows (diagnostic pathway, screening protocol), or generic medical terms (blood tests, imaging).
3. For each entity, provide the exact text span and character offsets (start, end) from the abstract text.
4. Only annotate relations that are EXPLICITLY stated or strongly supported by evidence in the text.
5. Do NOT annotate negated relations ("did NOT inhibit"), speculation ("may potentially"), or trivial co-occurrences.
6. For directed relations (Positive_Correlation, Negative_Correlation, Conversion), clearly specify subject and object.
7. Be precise with character offsets — count from position 0 of the abstract field.
8. If an abstract is primarily clinical/epidemiological with no molecular entities, return fewer entities rather than forcing incorrect annotations.

OUTPUT FORMAT: Return a valid JSON object with this structure:
{{
  "entities": [
    {{"entity_id": "T1", "type": "Chemical", "text": "gemcitabine", "start": 0, "end": 11}},
    ...
  ],
  "relations": [
    {{"relation_id": "R1", "type": "Negative_Correlation", "subject_id": "T1", "object_id": "T2", "directed": true, "novelty": "Known", "evidence": "sentence supporting this relation"}},
    ...
  ]
}}

Return ONLY the JSON object. No explanations, no markdown code blocks.""".format(
    entity_types="\n".join(f"- {t}" for t in ENTITY_TYPES),
    relation_types="\n".join(f"- {t}" for t in RELATION_TYPES)
)


def call_groq(api_key: str, abstract: str, title: str, max_retries: int = 3) -> dict:
    """Call Groq API to pre-annotate an abstract."""
    import requests

    user_prompt = f"TITLE: {title}\n\nABSTRACT: {abstract}\n\nExtract all biomedical entities and relations from this pancreatic cancer abstract. Return valid JSON only."

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.1,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"}
    }

    for attempt in range(max_retries):
        try:
            resp = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=60)

            if resp.status_code == 429:
                wait = min(2 ** attempt * 5, 60)
                print(f"    Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                continue

            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]

            # Parse JSON response
            result = json.loads(content)
            return result

        except json.JSONDecodeError as e:
            print(f"    JSON parse error (attempt {attempt + 1}): {e}")
            # Try to extract JSON from response
            try:
                match = re.search(r'\{[\s\S]*\}', content)
                if match:
                    return json.loads(match.group())
            except Exception:
                pass

        except requests.exceptions.RequestException as e:
            print(f"    API error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    return {"entities": [], "relations": [], "error": "Failed after retries"}


def validate_offsets(entities: list, abstract: str) -> list:
    """Validate and fix entity character offsets against the actual abstract text."""
    validated = []
    for ent in entities:
        text = ent.get("text", "")
        start = ent.get("start", -1)
        end = ent.get("end", -1)

        # Check if offsets are correct
        if 0 <= start < end <= len(abstract) and abstract[start:end] == text:
            validated.append(ent)
            continue

        # Try to find the text in the abstract and fix offsets
        idx = abstract.find(text)
        if idx >= 0:
            ent["start"] = idx
            ent["end"] = idx + len(text)
            ent["offset_corrected"] = True
            validated.append(ent)
        else:
            # Try case-insensitive search
            idx = abstract.lower().find(text.lower())
            if idx >= 0:
                ent["text"] = abstract[idx:idx + len(text)]
                ent["start"] = idx
                ent["end"] = idx + len(text)
                ent["offset_corrected"] = True
                validated.append(ent)
            else:
                ent["offset_valid"] = False
                ent["start"] = -1
                ent["end"] = -1
                validated.append(ent)

    return validated


def preannotate_record(api_key: str, record: dict) -> dict:
    """Pre-annotate a single corpus record."""
    abstract = record.get("abstract", "")
    title = record.get("title", "")

    if not abstract:
        return {
            "record_id": record.get("record_id", ""),
            "entities": [],
            "relations": [],
            "preannotation_status": "skipped_no_abstract"
        }

    # Call Groq API
    result = call_groq(api_key, abstract, title)

    # Validate entity offsets
    entities = result.get("entities", [])
    entities = validate_offsets(entities, abstract)

    # Validate relation entity references
    valid_entity_ids = {e["entity_id"] for e in entities if e.get("entity_id")}
    relations = []
    for rel in result.get("relations", []):
        subj = rel.get("subject_id", "")
        obj = rel.get("object_id", "")
        if subj in valid_entity_ids and obj in valid_entity_ids:
            relations.append(rel)

    return {
        "record_id": record.get("record_id", ""),
        "pmid": record.get("pmid", ""),
        "doi": record.get("doi", ""),
        "title": title,
        "abstract": abstract,
        "sentences": record.get("sentences", []),
        "year": record.get("year", 0),
        "journal": record.get("journal", ""),
        "source_db": record.get("source_db", ""),
        "entities": entities,
        "relations": relations,
        "metadata": {
            "annotator": "groq_preannotation",
            "annotation_date": "",
            "annotation_time_seconds": 0,
            "confidence": "low",
            "notes": "Auto-generated by Groq LLM. Requires human validation.",
            "model": GROQ_MODEL
        },
        "preannotation_status": "error" if result.get("error") else "complete"
    }


def main():
    parser = argparse.ArgumentParser(description="Pre-annotate corpus using Groq LLM API")
    parser.add_argument("--input", default="../../data/final/corpus.jsonl",
                        help="Input corpus JSONL file")
    parser.add_argument("--output", default="../data/preannotated.jsonl",
                        help="Output pre-annotated JSONL file")
    parser.add_argument("--api-key", default="",
                        help="Groq API key (or set GROQ_API_KEY env var)")
    parser.add_argument("--n", type=int, default=50,
                        help="Number of records to pre-annotate")
    parser.add_argument("--start", type=int, default=0,
                        help="Starting record index")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Delay between API calls in seconds")
    args = parser.parse_args()

    # Get API key
    api_key = args.api_key or os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        print("ERROR: Groq API key required. Use --api-key or set GROQ_API_KEY env var.")
        sys.exit(1)

    # Resolve paths
    script_dir = Path(__file__).resolve().parent
    input_path = (script_dir / args.input).resolve()
    output_path = (script_dir / args.output).resolve()

    # Load corpus
    print(f"Loading corpus from {input_path}...")
    records = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    print(f"Loaded {len(records)} records")

    # Select records to annotate
    end_idx = min(args.start + args.n, len(records))
    subset = records[args.start:end_idx]
    print(f"Pre-annotating records {args.start} to {end_idx - 1} ({len(subset)} records)")

    # Pre-annotate
    os.makedirs(output_path.parent, exist_ok=True)
    results = []
    errors = 0

    for i, record in enumerate(subset):
        rid = record.get("record_id", f"record_{i}")
        print(f"  [{i + 1}/{len(subset)}] Pre-annotating {rid}...", end=" ", flush=True)

        result = preannotate_record(api_key, record)
        results.append(result)

        n_ent = len(result.get("entities", []))
        n_rel = len(result.get("relations", []))
        status = result.get("preannotation_status", "unknown")

        if status == "error":
            errors += 1
            print(f"ERROR")
        else:
            print(f"{n_ent} entities, {n_rel} relations")

        if i < len(subset) - 1:
            time.sleep(args.delay)

    # Save results
    with open(output_path, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\nPre-annotation complete:")
    print(f"  Records processed: {len(results)}")
    print(f"  Errors: {errors}")
    print(f"  Output: {output_path}")

    # Summary statistics
    total_entities = sum(len(r.get("entities", [])) for r in results)
    total_relations = sum(len(r.get("relations", [])) for r in results)
    print(f"  Total entities extracted: {total_entities}")
    print(f"  Total relations extracted: {total_relations}")
    if results:
        print(f"  Avg entities per abstract: {total_entities / len(results):.1f}")
        print(f"  Avg relations per abstract: {total_relations / len(results):.1f}")


if __name__ == "__main__":
    main()
