# PanCan-RE Annotation Phase

Annotation tools for adding biomedical entity and relation annotations to the PanCan-RE corpus.

## Schema

Based on BioRED (Luo et al., 2022) with Pathway entity extension and directionality.

- **6 entity types:** GeneOrProtein, Chemical, Disease, SequenceVariant, Pathway, CellLine
- **8 relation types:** Positive_Correlation, Negative_Correlation, Association, Binding, Drug_Interaction, Cotreatment, Comparison, Conversion
- **2 novelty labels:** Novel, Known
- **Directed relations:** Positive_Correlation, Negative_Correlation, Conversion

See `schema/` for full definitions and `guidelines/` for annotation instructions.

## Workflow

```
Step 1: Pre-annotate with Groq LLM
    python tools/preannotate.py --api-key YOUR_KEY --n 50

Step 2: Review in annotation GUI
    pip install streamlit
    streamlit run tools/annotation_gui.py

Step 3: Export for expert review
    python tools/expert_review_export.py --n 50

Step 4: Compute inter-annotator agreement
    python tools/compute_iaa.py --annotator1 data/validated_ann1.jsonl \
                                --annotator2 data/validated_ann2.jsonl

Step 5: Export final dataset
    python tools/export_dataset.py
```

## Directory Structure

```
annotation/
├── schema/
│   ├── entity_types.json        # Entity type definitions
│   ├── relation_types.json      # Relation type definitions
│   └── annotation_format.json   # Output record format + example
├── guidelines/
│   └── ANNOTATION_GUIDELINES.md # Full annotation guidelines
├── tools/
│   ├── preannotate.py           # Groq LLM pre-annotation
│   ├── annotation_gui.py        # Streamlit annotation GUI
│   ├── expert_review_export.py  # Excel export for oncologists
│   ├── compute_iaa.py           # Cohen's Kappa IAA
│   └── export_dataset.py        # Final dataset export
├── data/                        # Annotation outputs (created by tools)
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```
