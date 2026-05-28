# PanCan-RE Annotation Guidelines

## Biomedical Entity and Relation Annotation for Pancreatic Cancer

**Version:** 1.0
**Date:** 2026-05-28
**Dataset:** PanCan-RE Corpus
**Target Journal:** Language Resources and Evaluation (Springer)

---

## 1. Overview

These guidelines describe how to annotate biomedical entities and their relations in pancreatic cancer abstracts. The annotation scheme follows the BioRED framework (Luo et al., 2022) extended with Pathway entities and directionality from BioREDirect (Lai et al., 2025).

Each abstract is annotated at two levels:
1. **Entity annotation**: Mark all biomedical entity mentions with their type and text span
2. **Relation annotation**: For each entity pair within the same abstract, annotate the relation type (if any), directionality, and novelty

---

## 2. Entity Types

### 2.1 GeneOrProtein (GENE)

**Definition:** A named gene, protein, enzyme, receptor, or transcription factor.

**Annotate:**
- Gene names: KRAS, TP53, BRCA1, CDKN2A
- Protein names: EGFR, VEGF, HER2, PD-L1, c-Myc
- Enzymes: PARP, ATR, CDK4/6
- Receptors: EGFR, GPR120, C5aR1
- Transcription factors: FOXM1, GATA6

**Do NOT annotate:**
- Generic descriptions: "protein", "enzyme", "kinase" (without a specific name)
- Gene families without a specific member: "oncogenes" (but "KRAS oncogene" → annotate KRAS)
- Functional descriptions: "tumor suppressor" (but "TP53 tumor suppressor" → annotate TP53)

**Boundary rules:**
- "KRAS protein" → annotate only "KRAS"
- "EGFR receptor" → annotate only "EGFR"
- "PI3K/AKT/mTOR" → annotate as THREE separate entities: "PI3K", "AKT", "mTOR"
- "PD-1/PD-L1" → annotate as TWO separate entities: "PD-1", "PD-L1"

### 2.2 Chemical (CHEM)

**Definition:** A drug, pharmaceutical compound, chemical substance, or therapeutic agent.

**Annotate:**
- Approved drugs: gemcitabine, olaparib, erlotinib, cisplatin
- Drug regimens: FOLFIRINOX (as a single entity)
- Experimental compounds: saikosaponin D, evofosfamide
- Natural products with therapeutic role: ursolic acid, digoxin
- Nanoplatforms with drug payload: "gemcitabine-loaded nanoparticle" → annotate "gemcitabine"

**Do NOT annotate:**
- General terms: "chemotherapy", "immunotherapy", "treatment" (without a drug name)
- Drug classes without specific members: "platinum-based agents" (but "cisplatin" within that phrase → annotate)
- Laboratory reagents not studied as therapeutics: "DMSO", "PBS"

**Boundary rules:**
- "gemcitabine (GEM)" → annotate "gemcitabine" as the primary mention; "GEM" as a separate mention if used later
- "nab-paclitaxel" → annotate as one entity (includes the nanoparticle albumin-bound formulation)
- "5-FU" and "fluorouracil" → each is a separate mention of the same entity

### 2.3 Disease (DIS)

**Definition:** A disease, disorder, pathological condition, syndrome, or clinically significant phenotype.

**Annotate:**
- Cancer types: pancreatic cancer, PDAC, pancreatic ductal adenocarcinoma, metastatic pancreatic cancer
- Cancer subtypes: pancreatic neuroendocrine tumor, pancreatic intraepithelial neoplasia (PanIN)
- Adverse effects (as diseases): neuropathy, neutropenia, thrombocytopenia
- Comorbidities: diabetes, pancreatitis, cachexia
- Clinically significant phenotypes: chemoresistance, drug resistance, metastasis

**Do NOT annotate:**
- Generic terms: "cancer", "tumor", "malignancy" (without specifying pancreatic)
- Experimental outcomes: "cell death", "growth inhibition" (these describe results, not diseases)
- Patient descriptions: "unresectable", "locally advanced" (these are modifiers, not diseases)

**Boundary rules:**
- "metastatic PDAC" → annotate as one Disease entity: "metastatic PDAC"
- "pancreatic ductal adenocarcinoma (PDAC)" → annotate "pancreatic ductal adenocarcinoma" as primary, "PDAC" as separate mention
- "gemcitabine resistance" → annotate "gemcitabine resistance" as one Disease entity

### 2.4 SequenceVariant (VAR)

**Definition:** A specific genetic mutation, polymorphism, variant, or genomic alteration.

**Annotate:**
- Point mutations: KRASG12D, KRASG12C, KRASQ61H
- Named variants: BRCA2 mutation, TP53 deletion
- Genomic events: loss of heterozygosity (LOH), microsatellite instability-high (MSI-H)
- Epigenetic alterations: CDKN2A hypermethylation

**Do NOT annotate:**
- Generic terms: "mutation", "variant", "polymorphism" (without a gene or specific variant)
- Chromosomal descriptions: "chromosome 18q" (unless describing a specific known alteration)

**Boundary rules:**
- "KRASG12D mutation" → annotate "KRASG12D" as SequenceVariant (the word "mutation" is implicit in the variant notation)
- "KRAS mutation" (no specific variant) → annotate "KRAS mutation" as SequenceVariant
- "BRCA2 with loss of heterozygosity" → annotate "BRCA2" as GeneOrProtein AND "loss of heterozygosity" as SequenceVariant

### 2.5 Pathway (PATH)

**Definition:** A named biological pathway, signaling cascade, or well-defined cellular process.

**Annotate:**
- Named pathways: MAPK pathway, Wnt signaling, Hedgehog pathway, NF-kB pathway
- Cellular processes: apoptosis, autophagy, ferroptosis, angiogenesis
- Biological mechanisms: epithelial-mesenchymal transition (EMT), DNA damage response (DDR)
- Immune processes: immunogenic cell death (ICD)

**Do NOT annotate:**
- Generic terms: "cell death" (not specific enough), "cell growth", "proliferation"
- Pathway components: "MAPK" alone is a GeneOrProtein; "MAPK pathway" or "MAPK signaling" is a Pathway
- Experimental procedures: "Western blot", "flow cytometry"

**Boundary rules:**
- "PI3K/AKT/mTOR pathway" → annotate as one Pathway entity: "PI3K/AKT/mTOR pathway"
- "MAPK" → GeneOrProtein; "MAPK pathway" → Pathway; "MAPK signaling cascade" → Pathway
- "apoptosis" → Pathway (it is a defined cellular process)
- "DDR1/PYK2/ERK signaling cascades" → annotate as one Pathway entity

### 2.6 CellLine (CELL)

**Definition:** An established cell line used in experimental studies.

**Annotate:**
- Named cell lines: PANC-1, MIA PaCa-2, AsPC-1, BxPC-3, Suit-2, SU.86.86

**Do NOT annotate:**
- Generic cell descriptions: "pancreatic cancer cells", "PDAC cells", "tumor cells"
- Primary cells: "patient-derived organoids" (unless given a specific identifier)
- Mouse models: "KPC mice", "xenograft models"

---

## 3. Relation Types

### 3.1 Annotation Scope

- Annotate relations between entity pairs **within the same abstract** (document-level RE)
- A relation can be supported by evidence anywhere in the abstract (not restricted to a single sentence)
- Each entity pair receives at most ONE relation type annotation
- If multiple relation types could apply, choose the most specific one

### 3.2 Relation Type Definitions

#### Positive_Correlation (Directed: Subject → Object)
**Use when:** Subject positively affects, increases, induces, activates, upregulates, promotes, or causes the object.

| Subject → Object | Example |
|------------------|---------|
| GENE → DIS | "KRAS mutations drive pancreatic cancer progression" |
| CHEM → DIS | "Gemcitabine caused peripheral neuropathy" (adverse effect) |
| GENE → PATH | "KRAS activates the MAPK signaling pathway" |
| VAR → DIS | "KRASG12D mutation increases risk of PDAC" |
| PATH → DIS | "Autophagy promotes chemoresistance" |
| CHEM → GENE | "Gemcitabine upregulates PD-L1 expression" |
| CHEM → PATH | "Cisplatin induces apoptosis" |
| GENE → GENE | "FOXM1 upregulates JUP expression" |

**Key distinction:** Drug side effects are Positive_Correlation (drug CAUSES adverse effect).

#### Negative_Correlation (Directed: Subject → Object)
**Use when:** Subject negatively affects, decreases, inhibits, suppresses, downregulates, treats, or blocks the object.

| Subject → Object | Example |
|------------------|---------|
| CHEM → DIS | "Gemcitabine is first-line treatment for PDAC" (treats) |
| CHEM → GENE | "Olaparib inhibits PARP activity" |
| CHEM → PATH | "SSD inhibits AKT/mTOR pathway" |
| GENE → DIS | "SMAD4 suppresses tumor growth" |
| GENE → PATH | "TP53 inhibits angiogenesis" |
| GENE → GENE | "C5aR1 knockdown impaired PI3K/mTOR activation" |
| VAR → DIS | "BRCA2 mutation associated with reduced disease risk" (protective) |

**Key distinction:** Drug TREATS disease = Negative_Correlation (drug REDUCES disease).

#### Association (Undirected)
**Use when:** Two entities are associated but the specific positive/negative direction is unclear or not stated.

| Entity Pair | Example |
|-------------|---------|
| GENE - DIS | "CA19-9 is a biomarker for pancreatic cancer" |
| GENE - DIS | "KRAS mutations are found in ~94% of PDAC" |
| CHEM - VAR | "Response to olaparib was associated with BRCA2 status" |
| GENE - GENE | "PD-L1 expression correlated with CD8+ T cell infiltration" |

**When to use Association vs. Positive/Negative Correlation:**
- "KRAS is associated with poor prognosis" → Association (the direction of effect on prognosis is implied but the relation between KRAS and the disease is associative)
- "KRAS activates MAPK pathway" → Positive_Correlation (clear causal direction)
- "Gemcitabine treats PDAC" → Negative_Correlation (clear therapeutic effect)
- "CA19-9 levels correlated with disease stage" → Association (correlation, not causation)

#### Binding (Undirected)
**Use when:** Physical molecular binding, direct contact, or complex formation between entities.

| Entity Pair | Example |
|-------------|---------|
| CHEM - GENE | "Erlotinib binds to EGFR tyrosine kinase domain" |
| GENE - GENE | "PD-1 binds PD-L1" |
| CHEM - PATH | Rare; use for pathway-component binding |

**Key distinction:** Binding describes PHYSICAL interaction. "Erlotinib inhibits EGFR" is Negative_Correlation (functional effect); "Erlotinib binds EGFR" is Binding (physical contact). If both are stated, annotate BOTH relations if they add information.

#### Drug_Interaction (Undirected)
**Use when:** Two drugs interact pharmacologically when co-administered; the combined effect differs from individual effects.

| Entity Pair | Example |
|-------------|---------|
| CHEM - CHEM | "Olaparib shows synergistic effects with gemcitabine" |
| CHEM - CHEM | "Evofosfamide and gemcitabine act synergistically" |

#### Cotreatment (Undirected)
**Use when:** Two drugs are co-administered as a treatment regimen, without specific pharmacological interaction described.

| Entity Pair | Example |
|-------------|---------|
| CHEM - CHEM | "Patients received gemcitabine plus nab-paclitaxel" |
| CHEM - CHEM | "First-line FOLFIRINOX followed by gemcitabine" |

**Key distinction Drug_Interaction vs. Cotreatment:**
- "Drug A and Drug B showed synergy" → Drug_Interaction (mechanism described)
- "Patients received Drug A and Drug B" → Cotreatment (clinical co-administration, no mechanism)

#### Comparison (Undirected)
**Use when:** Two entities are directly compared in a study.

| Entity Pair | Example |
|-------------|---------|
| CHEM - CHEM | "FOLFIRINOX demonstrated superior OS compared to gemcitabine" |
| GENE - GENE | "KRAS vs TP53 mutation status as predictors" |

#### Conversion (Directed: Subject → Object)
**Use when:** One chemical is metabolized or converted into another.

| Subject → Object | Example |
|------------------|---------|
| CHEM → CHEM | "Capecitabine is converted to 5-FU" |
| CHEM → CHEM | "Evofosfamide is a prodrug activated under hypoxia" |

---

## 4. Novelty Labels

For each annotated relation, assign a novelty label:

### Novel
The relation is a **finding of the current study**. Look for:
- "We found that...", "Our results show...", "We demonstrated..."
- Relations described in Results or Conclusions sections
- New experimental observations

### Known
The relation is **background knowledge** cited by the authors. Look for:
- "It is known that...", "Previous studies showed...", "X has been reported to..."
- Relations described in Background or Introduction sections
- Established medical knowledge

**When ambiguous:** Default to Novel if the abstract focuses on demonstrating the relation.

---

## 5. Annotation Procedure

### Step 1: Read the abstract completely
Understand the study's purpose, methods, and conclusions before annotating.

### Step 2: Annotate entities
- Read sentence by sentence
- Mark each entity mention with its type and exact text span (character offsets)
- Apply the boundary rules from Section 2

### Step 3: Annotate relations
- For each pair of annotated entities in the abstract, determine if a relation exists
- If yes, assign the relation type, directionality, and novelty label
- Use the decision tree below

### Decision Tree for Relation Type Selection

```
Is there a stated relationship between Entity A and Entity B?
├── NO → Do not annotate (implicit No_Relation)
└── YES → 
    ├── Is it physical binding/contact?
    │   └── YES → Binding
    ├── Are both entities Chemicals?
    │   ├── Is one converted/metabolized to the other?
    │   │   └── YES → Conversion
    │   ├── Do they interact pharmacologically?
    │   │   └── YES → Drug_Interaction
    │   ├── Are they co-administered as treatment?
    │   │   └── YES → Cotreatment
    │   └── Are they compared in a study?
    │       └── YES → Comparison
    ├── Does Entity A increase/activate/cause/induce Entity B?
    │   └── YES → Positive_Correlation (A → B)
    ├── Does Entity A decrease/inhibit/suppress/treat Entity B?
    │   └── YES → Negative_Correlation (A → B)
    └── Is the relationship associative/correlative without clear direction?
        └── YES → Association
```

---

## 6. Edge Cases and Special Rules

### 6.1 Multiple relations between the same entity pair
If an abstract states both "Drug A binds to Gene B" AND "Drug A inhibits Gene B", annotate the **most functionally meaningful** relation (Negative_Correlation in this case), unless both add unique information.

### 6.2 Negated relations
"Drug A did NOT inhibit Gene B" → Do NOT annotate this as a relation. Negated statements are not relations.

### 6.3 Hypothetical relations
"Drug A may inhibit Gene B" or "We hypothesize that..." → Annotate if the abstract provides supporting evidence. Do NOT annotate pure speculation without data.

### 6.4 Indirect relations
"Drug A inhibits Gene B, which activates Pathway C" describes TWO relations:
1. Drug A → Gene B: Negative_Correlation
2. Gene B → Pathway C: Positive_Correlation

Do NOT annotate Drug A → Pathway C (that's an inference, not a direct relation stated in the text).

### 6.5 Drug resistance
"Cancer cells developed resistance to gemcitabine" involves:
- Entity 1: "gemcitabine" (Chemical)
- Entity 2: "resistance" (annotate as part of Disease: "gemcitabine resistance" or "chemoresistance")
- Relation: Positive_Correlation (cancer process → resistance phenotype)

### 6.6 Biomarkers
"CA19-9 is a prognostic biomarker for PDAC":
- Entity 1: CA19-9 (GeneOrProtein)
- Entity 2: PDAC (Disease)
- Relation: Association (correlative, not causal)

---

## 7. Quality Control

### 7.1 Annotator qualification
All annotators must have graduate-level knowledge of biomedical sciences or bioinformatics.

### 7.2 Pilot annotation
Before full annotation, annotators independently annotate 20 abstracts. Disagreements are discussed and resolved to calibrate the guidelines.

### 7.3 Inter-annotator agreement
Cohen's Kappa (κ) is computed on a subset of double-annotated abstracts:
- **Entity annotation**: κ ≥ 0.80 required (BioRED achieved 97%)
- **Relation type**: κ ≥ 0.65 required (BioRED achieved 78%)
- **Novelty label**: κ ≥ 0.70 required (BioRED achieved 85%)

### 7.4 Expert validation
A subset of annotations is reviewed by clinical oncology experts for domain accuracy.

---

## 8. Output Format

Annotations are stored in JSON format following the PPI-RE structure with BioRED-style entity and relation definitions. See `annotation/schema/` for the complete format specification.

---

## 9. References

- Luo, L., Lai, P. T., Wei, C. H., Arighi, C. N., & Lu, Z. (2022). BioRED: A rich biomedical relation extraction dataset. Briefings in Bioinformatics, 23(5), bbac282.
- Lai, P. T., et al. (2025). BioREDirect: Adding directionality to biomedical relation extraction. arXiv:2501.14079.
- Page, M. J., et al. (2021). The PRISMA 2020 statement. BMJ, 372, n71.
- Park, C., et al. (2022). Extracting Protein-Protein Interactions using Attention-based Relational Context Information. IEEE BigData 2022.
