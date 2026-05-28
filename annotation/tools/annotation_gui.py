#!/usr/bin/env python3
"""
Streamlit-based Annotation GUI for PanCan-RE corpus.

Loads pre-annotated records and allows human annotators to:
- Review, accept, reject, or modify entity annotations
- Review, accept, reject, or modify relation annotations
- Add new entities and relations
- Assign novelty labels (Novel/Known)
- Track annotation progress and time

Usage:
    streamlit run annotation_gui.py -- --input ../data/preannotated.jsonl --output ../data/validated.jsonl
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

# --- Configuration ---
ENTITY_TYPES = ["GeneOrProtein", "Chemical", "Disease", "SequenceVariant", "Pathway", "CellLine"]
ENTITY_COLORS = {
    "GeneOrProtein": "#4CAF50",
    "Chemical": "#2196F3",
    "Disease": "#F44336",
    "SequenceVariant": "#9C27B0",
    "Pathway": "#FF9800",
    "CellLine": "#607D8B"
}
ENTITY_SHORT = {
    "GeneOrProtein": "GENE",
    "Chemical": "CHEM",
    "Disease": "DIS",
    "SequenceVariant": "VAR",
    "Pathway": "PATH",
    "CellLine": "CELL"
}

RELATION_TYPES = [
    "Positive_Correlation", "Negative_Correlation", "Association",
    "Binding", "Drug_Interaction", "Cotreatment", "Comparison", "Conversion"
]
DIRECTED_RELATIONS = {"Positive_Correlation", "Negative_Correlation", "Conversion"}
NOVELTY_LABELS = ["Novel", "Known"]
CONFIDENCE_LEVELS = ["high", "medium", "low"]


# --- Data I/O ---
def load_records(path: str) -> list:
    records = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    return records


def save_records(records: list, path: str):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def get_validated_path(input_path: str) -> str:
    p = Path(input_path)
    return str(p.parent / f"validated_{p.stem}.jsonl")


# --- Rendering helpers ---
def render_annotated_text(abstract: str, entities: list) -> str:
    """Render abstract with highlighted entity spans as HTML."""
    if not entities:
        return f"<p style='font-family: Georgia, serif; font-size: 14px; line-height: 1.8;'>{abstract}</p>"

    # Sort entities by start position (reverse for insertion)
    sorted_ents = sorted(
        [e for e in entities if e.get("start", -1) >= 0 and e.get("end", -1) > 0],
        key=lambda e: e["start"]
    )

    # Build HTML with highlights (handle overlaps by processing left to right)
    html_parts = []
    last_end = 0
    for ent in sorted_ents:
        start = ent["start"]
        end = ent["end"]
        if start < last_end:
            continue  # Skip overlapping entities
        etype = ent.get("type", "Unknown")
        color = ENTITY_COLORS.get(etype, "#999")
        short = ENTITY_SHORT.get(etype, "?")
        eid = ent.get("entity_id", "?")

        html_parts.append(abstract[last_end:start])
        html_parts.append(
            f'<mark style="background-color: {color}22; border: 1px solid {color}; '
            f'border-radius: 3px; padding: 1px 3px; cursor: help;" '
            f'title="{etype} ({eid})">'
            f'{abstract[start:end]}'
            f'<sup style="color: {color}; font-size: 10px; font-weight: bold;"> {short}</sup>'
            f'</mark>'
        )
        last_end = end

    html_parts.append(abstract[last_end:])

    return (
        f"<div style='font-family: Georgia, serif; font-size: 14px; line-height: 2.0; "
        f"padding: 15px; background: #fafafa; border-radius: 8px; border: 1px solid #e0e0e0;'>"
        f"{''.join(html_parts)}</div>"
    )


def render_entity_legend():
    """Render entity type color legend."""
    items = []
    for etype, color in ENTITY_COLORS.items():
        short = ENTITY_SHORT[etype]
        items.append(
            f'<span style="background-color: {color}22; border: 1px solid {color}; '
            f'border-radius: 3px; padding: 2px 8px; margin: 2px; display: inline-block; '
            f'font-size: 12px;">{short} = {etype}</span>'
        )
    return " ".join(items)


# --- Main App ---
def main():
    st.set_page_config(
        page_title="PanCan-RE Annotation Tool",
        page_icon="🔬",
        layout="wide"
    )

    st.title("PanCan-RE Annotation Tool")
    st.caption("Biomedical Entity & Relation Annotation for Pancreatic Cancer")

    # --- Sidebar: File management ---
    with st.sidebar:
        st.header("Data Management")

        input_file = st.text_input(
            "Input file (pre-annotated)",
            value=str(Path(__file__).resolve().parent.parent / "data" / "preannotated.jsonl")
        )
        output_file = st.text_input(
            "Output file (validated)",
            value=str(Path(__file__).resolve().parent.parent / "data" / "validated.jsonl")
        )

        if st.button("Load Data", type="primary"):
            records = load_records(input_file)
            if records:
                st.session_state["records"] = records
                st.session_state["current_idx"] = 0
                st.session_state["start_time"] = time.time()
                st.success(f"Loaded {len(records)} records")
            else:
                st.error(f"No records found in {input_file}")

        # Load existing validated data
        if st.button("Load Validated (resume)"):
            records = load_records(output_file)
            if records:
                st.session_state["records"] = records
                # Find first unvalidated
                for i, r in enumerate(records):
                    if r.get("metadata", {}).get("annotator") in ("groq_preannotation", ""):
                        st.session_state["current_idx"] = i
                        break
                else:
                    st.session_state["current_idx"] = len(records) - 1
                st.success(f"Resumed with {len(records)} records")
            else:
                st.error("No validated records found")

        st.divider()

        # Progress
        if "records" in st.session_state:
            records = st.session_state["records"]
            validated = sum(
                1 for r in records
                if r.get("metadata", {}).get("annotator", "") not in ("groq_preannotation", "")
            )
            st.metric("Progress", f"{validated}/{len(records)}")
            st.progress(validated / len(records) if records else 0)

            st.divider()
            st.header("Navigation")
            idx = st.number_input(
                "Go to record #",
                min_value=0,
                max_value=len(records) - 1,
                value=st.session_state.get("current_idx", 0),
                key="nav_idx"
            )
            if idx != st.session_state.get("current_idx", 0):
                st.session_state["current_idx"] = idx
                st.rerun()

        st.divider()
        st.header("Annotator")
        annotator_id = st.text_input("Your ID", value="annotator_01")
        st.session_state["annotator_id"] = annotator_id

    # --- Main area ---
    if "records" not in st.session_state:
        st.info("Load a pre-annotated file from the sidebar to begin.")
        st.markdown("""
        ### Quick Start
        1. Run the pre-annotation pipeline: `python preannotate.py --api-key YOUR_KEY`
        2. Enter the output file path in the sidebar
        3. Click **Load Data**
        4. Review and correct each annotation
        5. Click **Save & Next** to progress
        """)
        return

    records = st.session_state["records"]
    idx = st.session_state.get("current_idx", 0)
    record = records[idx]

    # --- Header bar ---
    col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
    with col1:
        st.subheader(f"Record: {record.get('record_id', '?')}")
    with col2:
        st.caption(f"{record.get('journal', '')} ({record.get('year', '')})")
    with col3:
        if st.button("← Previous") and idx > 0:
            st.session_state["current_idx"] = idx - 1
            st.rerun()
    with col4:
        if st.button("Next →") and idx < len(records) - 1:
            st.session_state["current_idx"] = idx + 1
            st.rerun()

    # --- Title ---
    st.markdown(f"**Title:** {record.get('title', '')}")

    # --- Annotated abstract ---
    st.markdown("### Abstract with Entities")
    st.markdown(render_entity_legend(), unsafe_allow_html=True)
    entities = record.get("entities", [])
    st.markdown(render_annotated_text(record.get("abstract", ""), entities), unsafe_allow_html=True)

    # --- Entity editing ---
    st.markdown("### Entities")

    # Display entities in a table
    if entities:
        for i, ent in enumerate(entities):
            col1, col2, col3, col4, col5 = st.columns([1, 2, 3, 1, 1])
            with col1:
                st.text(ent.get("entity_id", f"T{i+1}"))
            with col2:
                new_type = st.selectbox(
                    "Type", ENTITY_TYPES,
                    index=ENTITY_TYPES.index(ent["type"]) if ent.get("type") in ENTITY_TYPES else 0,
                    key=f"ent_type_{idx}_{i}",
                    label_visibility="collapsed"
                )
                entities[i]["type"] = new_type
            with col3:
                st.text(f'"{ent.get("text", "")}" [{ent.get("start", "?")}-{ent.get("end", "?")}]')
            with col4:
                if ent.get("offset_corrected"):
                    st.warning("Fixed", icon="⚠️")
                elif ent.get("offset_valid") is False:
                    st.error("Bad", icon="❌")
            with col5:
                if st.button("🗑️", key=f"del_ent_{idx}_{i}"):
                    entities.pop(i)
                    # Remove relations referencing this entity
                    eid = ent.get("entity_id", "")
                    record["relations"] = [
                        r for r in record.get("relations", [])
                        if r.get("subject_id") != eid and r.get("object_id") != eid
                    ]
                    st.rerun()

    # Add new entity
    with st.expander("➕ Add Entity"):
        new_text = st.text_input("Entity text (select from abstract)", key=f"new_ent_text_{idx}")
        new_type = st.selectbox("Entity type", ENTITY_TYPES, key=f"new_ent_type_{idx}")
        if st.button("Add Entity", key=f"add_ent_{idx}") and new_text:
            abstract = record.get("abstract", "")
            start = abstract.find(new_text)
            new_id = f"T{len(entities) + 1}"
            new_ent = {
                "entity_id": new_id,
                "type": new_type,
                "text": new_text,
                "start": start if start >= 0 else -1,
                "end": start + len(new_text) if start >= 0 else -1,
                "normalized_id": ""
            }
            entities.append(new_ent)
            st.success(f"Added {new_id}: {new_text} ({new_type})")
            st.rerun()

    # --- Relation editing ---
    st.markdown("### Relations")
    relations = record.get("relations", [])

    if relations:
        # Build entity lookup
        ent_lookup = {e["entity_id"]: e for e in entities}

        for i, rel in enumerate(relations):
            subj = ent_lookup.get(rel.get("subject_id", ""), {})
            obj = ent_lookup.get(rel.get("object_id", ""), {})

            col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 1, 2, 1, 1])
            with col1:
                st.text(rel.get("relation_id", f"R{i+1}"))
            with col2:
                subj_label = f'{subj.get("text", "?")} ({ENTITY_SHORT.get(subj.get("type", ""), "?")})'
                st.text(subj_label)
            with col3:
                new_rtype = st.selectbox(
                    "→", RELATION_TYPES,
                    index=RELATION_TYPES.index(rel["type"]) if rel.get("type") in RELATION_TYPES else 0,
                    key=f"rel_type_{idx}_{i}",
                    label_visibility="collapsed"
                )
                relations[i]["type"] = new_rtype
                relations[i]["directed"] = new_rtype in DIRECTED_RELATIONS
            with col4:
                obj_label = f'{obj.get("text", "?")} ({ENTITY_SHORT.get(obj.get("type", ""), "?")})'
                st.text(obj_label)
            with col5:
                new_novelty = st.selectbox(
                    "Novelty", NOVELTY_LABELS,
                    index=NOVELTY_LABELS.index(rel["novelty"]) if rel.get("novelty") in NOVELTY_LABELS else 0,
                    key=f"rel_nov_{idx}_{i}",
                    label_visibility="collapsed"
                )
                relations[i]["novelty"] = new_novelty
            with col6:
                if st.button("🗑️", key=f"del_rel_{idx}_{i}"):
                    relations.pop(i)
                    st.rerun()

            # Show evidence
            evidence = rel.get("evidence", rel.get("evidence_sentence", ""))
            if evidence:
                st.caption(f"  Evidence: \"{evidence[:150]}...\"" if len(evidence) > 150 else f"  Evidence: \"{evidence}\"")
    else:
        st.info("No relations annotated. Add relations below.")

    # Add new relation
    with st.expander("➕ Add Relation"):
        ent_options = [f'{e["entity_id"]}: {e["text"]} ({ENTITY_SHORT.get(e["type"], "?")})' for e in entities]
        if len(ent_options) >= 2:
            subj_sel = st.selectbox("Subject entity", ent_options, key=f"new_rel_subj_{idx}")
            obj_sel = st.selectbox("Object entity", ent_options, key=f"new_rel_obj_{idx}")
            rel_type = st.selectbox("Relation type", RELATION_TYPES, key=f"new_rel_type_{idx}")
            novelty = st.selectbox("Novelty", NOVELTY_LABELS, key=f"new_rel_nov_{idx}")
            evidence = st.text_input("Evidence sentence", key=f"new_rel_ev_{idx}")

            if st.button("Add Relation", key=f"add_rel_{idx}"):
                subj_id = subj_sel.split(":")[0]
                obj_id = obj_sel.split(":")[0]
                new_rel = {
                    "relation_id": f"R{len(relations) + 1}",
                    "type": rel_type,
                    "subject_id": subj_id,
                    "object_id": obj_id,
                    "directed": rel_type in DIRECTED_RELATIONS,
                    "novelty": novelty,
                    "evidence_sentence": evidence
                }
                relations.append(new_rel)
                st.success(f"Added relation: {subj_id} → {obj_id} ({rel_type})")
                st.rerun()
        else:
            st.warning("Need at least 2 entities to add a relation")

    # --- Metadata ---
    st.markdown("### Annotation Metadata")
    col1, col2 = st.columns(2)
    with col1:
        confidence = st.selectbox(
            "Confidence",
            CONFIDENCE_LEVELS,
            index=0,
            key=f"confidence_{idx}"
        )
    with col2:
        notes = st.text_input("Notes", value=record.get("metadata", {}).get("notes", ""), key=f"notes_{idx}")

    # --- Save ---
    st.divider()
    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        if st.button("💾 Save & Next", type="primary", use_container_width=True):
            # Update record
            record["entities"] = entities
            record["relations"] = relations
            record["metadata"] = {
                "annotator": st.session_state.get("annotator_id", "unknown"),
                "annotation_date": datetime.now().strftime("%Y-%m-%d"),
                "annotation_time_seconds": int(time.time() - st.session_state.get("start_time", time.time())),
                "confidence": confidence,
                "notes": notes,
                "model": record.get("metadata", {}).get("model", "")
            }
            records[idx] = record
            st.session_state["records"] = records
            st.session_state["start_time"] = time.time()

            # Save to file
            save_records(records, output_file)

            # Move to next
            if idx < len(records) - 1:
                st.session_state["current_idx"] = idx + 1
            st.success(f"Saved {record.get('record_id', '')}!")
            st.rerun()

    with col2:
        if st.button("💾 Save (stay)", use_container_width=True):
            record["entities"] = entities
            record["relations"] = relations
            record["metadata"] = {
                "annotator": st.session_state.get("annotator_id", "unknown"),
                "annotation_date": datetime.now().strftime("%Y-%m-%d"),
                "annotation_time_seconds": int(time.time() - st.session_state.get("start_time", time.time())),
                "confidence": confidence,
                "notes": notes,
                "model": record.get("metadata", {}).get("model", "")
            }
            records[idx] = record
            save_records(records, output_file)
            st.success("Saved!")

    with col3:
        if st.button("⏭️ Skip", use_container_width=True):
            if idx < len(records) - 1:
                st.session_state["current_idx"] = idx + 1
                st.session_state["start_time"] = time.time()
                st.rerun()


if __name__ == "__main__":
    main()
