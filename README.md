# PanCan-RE

### A PRISMA-Compliant Multi-Relation Annotated Corpus for Pancreatic Cancer Biomedical Relation Extraction

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![GitHub Pages](https://img.shields.io/badge/Expert%20Review-Live-brightgreen)](https://mr-slyfox.github.io/PanCan-RE/)
[![PRISMA](https://img.shields.io/badge/PRISMA-2020%20Compliant-blue)]()

---

## Overview

**PanCan-RE** is a domain-specific biomedical corpus for relation extraction, focusing on pancreatic cancer. The corpus was systematically constructed following PRISMA 2020 guidelines from three scholarly databases (PubMed, PubMed Central, Scopus) and annotated with biomedical entities and typed relations.

### Key Features

- **7,749 abstracts** from 2015–2026, systematically retrieved and screened
- **6 entity types**: Gene/Protein, Chemical/Drug, Disease, Sequence Variant, Pathway, Cell Line
- **8 relation types** based on [BioRED](https://academic.oup.com/bib/article/23/5/bbac282/6645993): Positive Correlation, Negative Correlation, Association, Binding, Drug Interaction, Cotreatment, Comparison, Conversion
- **Novel/Known labels** distinguishing new findings from background knowledge
- **Directed relations** with subject–object roles following [BioREDirect](https://arxiv.org/abs/2501.14079)
- **PRISMA 2020 compliant** with full documentation of the selection process
- **LLM-assisted annotation** with expert oncologist validation

---

## Corpus Statistics

### PRISMA Selection Flow

| Stage | Records |
|-------|---------|
| Identified (PubMed + PMC + Scopus) | 24,998 |
| After deduplication (exact + MinHash) | 9,860 |
| After screening (language, pub type, abstract) | 8,018 |
| After eligibility (entity-based filter) | 7,749 |
| **Final corpus** | **7,749** |

### Annotation Schema

| Entity Types | Relation Types |
|-------------|----------------|
| `GeneOrProtein` — KRAS, EGFR, PD-L1 | `Positive_Correlation` — activates, causes, induces |
| `Chemical` — gemcitabine, olaparib | `Negative_Correlation` — inhibits, treats, suppresses |
| `Disease` — PDAC, chemoresistance | `Association` — correlated with, biomarker for |
| `SequenceVariant` — KRASG12D, BRCA2 mutation | `Binding` — physically binds to |
| `Pathway` — MAPK, apoptosis, EMT | `Drug_Interaction` — synergistic/antagonistic |
| `CellLine` — PANC-1, MIA PaCa-2 | `Cotreatment` · `Comparison` · `Conversion` |

---

## Repository Structure

```
PanCan-RE/
├── src/pancan_corpus/          # Corpus construction pipeline
│   ├── pubmed_client.py        # PubMed/PMC API client
│   ├── scopus_client.py        # Scopus API client
│   ├── parsing.py              # PubMed XML parser
│   ├── screening.py            # Inclusion/exclusion filters
│   ├── deduplication.py        # Exact + MinHash near-duplicate removal
│   ├── preprocessing.py        # NLP preprocessing (NLTK)
│   ├── eligibility.py          # Entity-based filtering
│   ├── prisma.py               # PRISMA flow diagram generator
│   └── schema.py               # Record dataclass
├── scripts/                    # Pipeline entry points (stages 01–05)
├── annotation/
│   ├── schema/                 # Entity & relation type definitions
│   ├── guidelines/             # Annotation guidelines
│   └── tools/                  # Pre-annotation, GUI, export, IAA
├── data/
│   ├── final/                  # Final corpus (JSONL) + manifest
│   └── prisma/                 # PRISMA flow diagram + counts
├── docs/                       # GitHub Pages expert review app
├── PROTOCOL.md                 # PRISMA protocol document
├── config.yaml                 # Pipeline configuration
└── requirements.txt            # Python dependencies
```

---

## Getting Started

### Requirements

```bash
pip install -r requirements.txt
```

### Running the Pipeline

```bash
python scripts/01_identify.py    # Search PubMed, PMC, Scopus
python scripts/02_fetch.py       # Download abstract records
python scripts/03_screen.py      # Deduplicate + screen
python scripts/04_preprocess.py  # NLP preprocessing
python scripts/05_finalize.py    # Eligibility filter + PRISMA diagram
```

---

## Expert Review

An interactive web-based validation interface is available for domain experts:

**https://mhd-ai-ds.github.io/PanCan-RE/**

Experts can validate entity and relation annotations directly in the browser — no installation or account required.

---

## License

This dataset is released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The source code is released under the MIT License.

---

## Acknowledgements

This work is part of a doctoral thesis at the Universidad de Alcalá, Doctoral Programme in Information and Knowledge Engineering (D442).
