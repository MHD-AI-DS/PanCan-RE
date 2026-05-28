# PRISMA-Compliant Corpus Construction Protocol

## PanCan-RE: A Domain-Specific Biomedical Corpus for Pancreatic Cancer Relation Extraction

**Version:** 1.0  
**Date:** 2026-04-19  
**Status:** Active  

---

## 1. Objective

To construct a rigorously curated, PRISMA-compliant corpus of biomedical abstracts focused on pancreatic cancer, covering all major biomedical relation types (drug–drug, drug–gene, gene–disease, protein–protein, chemical–disease, drug–pathway, and gene–pathway interactions). This corpus will serve as the primary evaluation benchmark for generative AI-based biomedical relation extraction methods developed in this thesis.

## 2. Rationale

Existing biomedical relation extraction benchmarks (e.g., BioRED, ChemProt, DDI Corpus, BC5CDR) suffer from several limitations when applied to generative AI research:

1. **Domain mismatch** — General biomedical corpora lack pancreatic cancer-specific context, including domain-specific drug regimens (FOLFIRINOX, gemcitabine + nab-paclitaxel), gene panels (KRAS, TP53, BRCA1/2), and pathway biology (Hedgehog, Wnt, NF-κB).
2. **Training data contamination** — Large language models may have been exposed to widely-used public benchmarks during pre-training, compromising evaluation integrity.
3. **Relation type coverage** — Most existing corpora focus on a single relation type; a unified multi-relation corpus enables comprehensive evaluation.
4. **Reproducibility** — A fully documented, PRISMA-compliant construction process ensures transparent and reproducible research.

## 3. Registration

This protocol has not been registered with PROSPERO, as it describes corpus construction for computational research rather than a clinical systematic review. The protocol follows PRISMA 2020 guidelines adapted for NLP corpus construction (Page et al., 2021).

## 4. Eligibility Criteria

### 4.1 Inclusion Criteria

| Criterion | Specification |
|-----------|---------------|
| **Topic** | Abstracts must pertain to pancreatic cancer (pancreatic neoplasms, PDAC, pancreatic ductal adenocarcinoma, pancreatic carcinoma) |
| **Content** | Must contain at least one biomedical entity pair relevant to relation extraction (e.g., drug + gene, gene + disease, protein + protein) |
| **Language** | English only |
| **Publication type** | Original research articles, clinical trials, observational studies |
| **Date range** | January 1, 2015 – April 19, 2026 |
| **Abstract** | Must have a structured or unstructured abstract of ≥ 200 characters |

### 4.2 Exclusion Criteria

| Criterion | Rationale |
|-----------|-----------|
| Reviews, editorials, letters, comments | Secondary literature; does not report original relational findings |
| Errata and retracted publications | Unreliable data |
| Case reports | Typically describe individual patient narratives rather than generalizable relations |
| Non-English publications | Ensures consistency in NLP processing |
| Abstracts < 200 characters | Insufficient content for meaningful relation extraction |
| Duplicate records | Identified via exact PMID/DOI match and near-duplicate MinHash similarity (Jaccard > 0.85) |

## 5. Information Sources

| Database | Access Method | Coverage |
|----------|--------------|----------|
| **PubMed** | NCBI E-utilities API (ESearch + EFetch) | ~36 million biomedical citations |
| **PubMed Central (PMC)** | NCBI E-utilities API | ~9 million full-text articles |
| **Scopus** | Elsevier Scopus Search API | ~90 million records across sciences |

Searches will be conducted programmatically via RESTful APIs with structured Boolean queries. All search dates and result counts will be logged automatically.

## 6. Search Strategy

### 6.1 PubMed / PMC Query

```
("pancreatic neoplasms"[MeSH Terms] OR "pancreatic cancer"[Title/Abstract]
 OR "pancreatic ductal adenocarcinoma"[Title/Abstract] OR "PDAC"[Title/Abstract]
 OR "pancreatic tumor"[Title/Abstract] OR "pancreatic carcinoma"[Title/Abstract])
AND
("drug interactions"[MeSH Terms] OR "drug-drug interaction"[Title/Abstract]
 OR "gene expression"[MeSH Terms] OR "gene-disease"[Title/Abstract]
 OR "protein interaction"[Title/Abstract] OR "protein-protein interaction"[Title/Abstract]
 OR "signal transduction"[MeSH Terms] OR "drug response"[Title/Abstract]
 OR "biomarker"[Title/Abstract] OR "therapeutic target"[Title/Abstract]
 OR "mutation"[Title/Abstract] OR "polymorphism"[Title/Abstract]
 OR "adverse effect"[Title/Abstract] OR "side effect"[Title/Abstract]
 OR "chemical"[Title/Abstract] OR "compound"[Title/Abstract]
 OR "pathway"[Title/Abstract] OR "receptor"[Title/Abstract]
 OR "resistance"[Title/Abstract] OR "sensitivity"[Title/Abstract])
```

### 6.2 Scopus Query

```
TITLE-ABS-KEY("pancreatic cancer" OR "pancreatic neoplasm" OR "PDAC"
 OR "pancreatic ductal adenocarcinoma" OR "pancreatic carcinoma")
AND TITLE-ABS-KEY("drug interaction" OR "gene expression" OR "protein interaction"
 OR "biomarker" OR "therapeutic target" OR "mutation" OR "drug response"
 OR "signal transduction" OR "adverse effect" OR "pathway" OR "resistance"
 OR "receptor" OR "sensitivity")
```

### 6.3 Date Filters

- PubMed: `mindate=2015/01/01&maxdate=2026/04/19`
- Scopus: `PUBYEAR > 2014`

## 7. Selection Process (PRISMA Flow)

The selection process follows a four-stage PRISMA 2020 flow:

```
┌─────────────────────────────────────────────┐
│          IDENTIFICATION                      │
│  Records from PubMed: n = ?                  │
│  Records from PMC:    n = ?                  │
│  Records from Scopus: n = ?                  │
│  Total identified:    n = ?                  │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│          SCREENING                           │
│  Duplicates removed:           n = ?         │
│  Records after deduplication:  n = ?         │
│  Excluded (language):          n = ?         │
│  Excluded (pub type):          n = ?         │
│  Excluded (no abstract):       n = ?         │
│  Excluded (abstract too short): n = ?        │
│  Records after screening:      n = ?         │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│          ELIGIBILITY                         │
│  Assessed for eligibility:     n = ?         │
│  Excluded (no entity pairs):   n = ?         │
│  Records meeting eligibility:  n = ?         │
└──────────────────┬──────────────────────────┘
                   ▼
┌─────────────────────────────────────────────┐
│          INCLUDED                            │
│  Final corpus size:            n = ?         │
└─────────────────────────────────────────────┘
```

Counts will be populated automatically by the pipeline and recorded in `data/prisma/prisma_counts.json`.

## 8. Data Items

Each corpus record contains the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `record_id` | string | Unique identifier (format: `PANCAN-XXXXX`) |
| `pmid` | string | PubMed identifier (if available) |
| `doi` | string | Digital Object Identifier (if available) |
| `scopus_id` | string | Scopus EID (if available) |
| `title` | string | Article title |
| `abstract` | string | Raw abstract text |
| `authors` | list[string] | Author names |
| `journal` | string | Journal name |
| `year` | integer | Publication year |
| `mesh_terms` | list[string] | MeSH descriptors (PubMed only) |
| `chemicals` | list[string] | Chemical substances (PubMed only) |
| `keywords` | list[string] | Author keywords |
| `publication_type` | list[string] | PubMed publication types |
| `source_db` | string | Source database (pubmed / pmc / scopus) |
| `source_query` | string | Boolean query used for retrieval |
| `retrieval_date` | string | ISO 8601 date of retrieval |
| `normalized_text` | string | Preprocessed abstract text |
| `tokens` | list[string] | Tokenized abstract |
| `sentences` | list[string] | Sentence-split abstract |

## 9. Preprocessing Pipeline

### 9.1 Text Normalization
- Unicode normalization (NFC form)
- Accent stripping (e.g., résumé → resume)
- Whitespace normalization (collapse multiple spaces, strip leading/trailing)
- URL and email removal
- Lowercase conversion for normalized_text field (original case preserved in abstract field)

### 9.2 Tokenization
- Word-level tokenization using NLTK's `word_tokenize` (TreebankWordTokenizer)
- Optional: SciSpacy `en_core_sci_lg` for biomedical-aware tokenization

### 9.3 Sentence Splitting
- NLTK's `sent_tokenize` (Punkt sentence tokenizer)
- Optional: SciSpacy sentence boundary detection

### 9.4 Deduplication
- **Stage 1: Exact deduplication** — Remove records sharing the same PMID or DOI across databases
- **Stage 2: Near-duplicate detection** — MinHash with Locality-Sensitive Hashing (LSH). Parameters: 128 permutations, 3-word shingles, Jaccard similarity threshold 0.85

## 10. Storage Format

All data is stored in JSON Lines (JSONL) format — one JSON object per line. This format is chosen for:
- Streamability (no need to load entire file into memory)
- Line-level reproducibility (each record is self-contained)
- Compatibility with standard NLP tooling (Hugging Face datasets, spaCy, etc.)

## 11. Quality Control

- All counts are logged at each pipeline stage for PRISMA compliance
- Random sample of 100 records will be manually inspected for correctness
- Preprocessing outputs are spot-checked against raw text
- Pipeline is deterministic: fixed random seeds, logged dependency versions

## 12. Reproducibility

The following artifacts are archived alongside the corpus:
- This protocol document
- All source code (version-controlled)
- `config.yaml` with exact parameter values
- `requirements.txt` with pinned dependency versions
- `data/prisma/prisma_counts.json` with exact counts at each stage
- `data/prisma/prisma_flow.png` — auto-generated PRISMA 2020 flow diagram

## 13. Limitations

- **Abstract-level only:** Full-text articles are not included in this pilot; relations spanning multiple sections may be missed.
- **Automated screening:** Inclusion/exclusion is performed programmatically, not by dual human reviewers. This is appropriate for NLP corpus construction but would not meet clinical systematic review standards.
- **Entity detection:** Dictionary-based entity filtering may miss entities not in the keyword list. This is mitigated by using a broad, inclusive dictionary.
- **Temporal scope:** Restricting to 2015–present may exclude foundational work; this is intentional to capture contemporary therapeutic and genomic landscape.

## 14. References

- Page, M. J., et al. (2021). The PRISMA 2020 statement: an updated guideline for reporting systematic reviews. *BMJ*, 372, n71.
- NCBI E-utilities documentation: https://www.ncbi.nlm.nih.gov/books/NBK25501/
- Elsevier Scopus API: https://dev.elsevier.com/documentation/ScopusSearchAPI.wadl
