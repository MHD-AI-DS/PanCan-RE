"""PRISMA 2020 flow diagram generator and count tracker."""

import json
import os
from typing import Dict

from .io_utils import setup_logging

logger = setup_logging(__name__)


class PRISMATracker:
    """Track and visualize PRISMA 2020 flow counts."""

    def __init__(self):
        self.counts: Dict[str, int] = {
            # Identification
            "pubmed_identified": 0,
            "pmc_identified": 0,
            "scopus_identified": 0,
            "total_identified": 0,
            # Screening
            "exact_duplicates_removed": 0,
            "near_duplicates_removed": 0,
            "total_duplicates_removed": 0,
            "after_deduplication": 0,
            "excluded_language": 0,
            "excluded_pub_type": 0,
            "excluded_no_abstract": 0,
            "excluded_abstract_too_short": 0,
            "excluded_abstract_too_long": 0,
            "total_screening_excluded": 0,
            "after_screening": 0,
            # Eligibility
            "assessed_eligibility": 0,
            "excluded_no_entity_pairs": 0,
            "after_eligibility": 0,
            # Included
            "final_included": 0,
        }

    def update(self, new_counts: dict):
        """Merge new counts into the tracker."""
        for key, value in new_counts.items():
            if key in self.counts and isinstance(value, (int, float)):
                self.counts[key] = int(value)

    def compute_totals(self):
        """Compute derived totals."""
        self.counts["total_identified"] = (
            self.counts["pubmed_identified"]
            + self.counts["pmc_identified"]
            + self.counts["scopus_identified"]
        )
        self.counts["total_duplicates_removed"] = (
            self.counts["exact_duplicates_removed"]
            + self.counts["near_duplicates_removed"]
        )
        self.counts["total_screening_excluded"] = (
            self.counts["excluded_language"]
            + self.counts["excluded_pub_type"]
            + self.counts["excluded_no_abstract"]
            + self.counts["excluded_abstract_too_short"]
            + self.counts["excluded_abstract_too_long"]
        )

    def validate(self) -> list:
        """Validate PRISMA count arithmetic consistency. Returns list of errors (empty = OK)."""
        c = self.counts
        errors = []

        # Check dedup arithmetic
        expected_after_dedup = c["total_identified"] - c["total_duplicates_removed"]
        if c["after_deduplication"] and expected_after_dedup != c["after_deduplication"]:
            errors.append(
                f"Dedup inconsistency: {c['total_identified']} - {c['total_duplicates_removed']} "
                f"= {expected_after_dedup}, but after_deduplication = {c['after_deduplication']}"
            )

        # Check screening arithmetic
        expected_after_screen = c["after_deduplication"] - c["total_screening_excluded"]
        if c["after_screening"] and expected_after_screen != c["after_screening"]:
            errors.append(
                f"Screening inconsistency: {c['after_deduplication']} - {c['total_screening_excluded']} "
                f"= {expected_after_screen}, but after_screening = {c['after_screening']}"
            )

        # Check eligibility arithmetic
        expected_after_elig = c["assessed_eligibility"] - c["excluded_no_entity_pairs"]
        if c["after_eligibility"] and expected_after_elig != c["after_eligibility"]:
            errors.append(
                f"Eligibility inconsistency: {c['assessed_eligibility']} - {c['excluded_no_entity_pairs']} "
                f"= {expected_after_elig}, but after_eligibility = {c['after_eligibility']}"
            )

        for err in errors:
            logger.error(f"PRISMA VALIDATION: {err}")

        if not errors:
            logger.info("PRISMA count validation passed: all arithmetic consistent")

        return errors

    def save(self, path: str):
        """Save counts to JSON."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.counts, f, indent=2)
        logger.info(f"PRISMA counts saved to {path}")

    def load(self, path: str):
        """Load counts from JSON."""
        with open(path, "r", encoding="utf-8") as f:
            self.counts = json.load(f)

    def generate_diagram(self, output_path: str):
        """Generate a PRISMA 2020 flow diagram as PNG."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches

        fig, ax = plt.subplots(1, 1, figsize=(12, 16))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 20)
        ax.axis("off")
        fig.patch.set_facecolor("white")

        c = self.counts

        # Title
        ax.text(5, 19.5, "PRISMA 2020 Flow Diagram",
                ha="center", va="center", fontsize=16, fontweight="bold",
                fontfamily="serif")
        ax.text(5, 19.0,
                "PanCan-RE: Pancreatic Cancer Biomedical Corpus",
                ha="center", va="center", fontsize=11, fontstyle="italic",
                fontfamily="serif")

        # Color scheme
        id_color = "#E3F2FD"     # Light blue
        screen_color = "#FFF3E0"  # Light orange
        elig_color = "#F3E5F5"    # Light purple
        incl_color = "#E8F5E9"    # Light green
        excl_color = "#FFEBEE"    # Light red
        border_color = "#455A64"

        def draw_box(x, y, w, h, text, bg_color, fontsize=9, bold_first=True):
            rect = mpatches.FancyBboxPatch(
                (x - w / 2, y - h / 2), w, h,
                boxstyle="round,pad=0.15",
                facecolor=bg_color, edgecolor=border_color, linewidth=1.5
            )
            ax.add_patch(rect)
            lines = text.split("\n")
            line_height = fontsize * 0.018
            start_y = y + (len(lines) - 1) * line_height / 2
            for i, line in enumerate(lines):
                weight = "bold" if (i == 0 and bold_first) else "normal"
                ax.text(x, start_y - i * line_height, line,
                        ha="center", va="center", fontsize=fontsize,
                        fontweight=weight, fontfamily="serif")

        def draw_arrow(x1, y1, x2, y2):
            ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                        arrowprops=dict(arrowstyle="-|>", color=border_color,
                                        lw=1.5))

        # === IDENTIFICATION ===
        draw_box(2.5, 17.0, 4.0, 1.8,
                 f"IDENTIFICATION\n\n"
                 f"PubMed:  n = {c['pubmed_identified']:,}\n"
                 f"PMC:     n = {c['pmc_identified']:,}\n"
                 f"Scopus:  n = {c['scopus_identified']:,}\n"
                 f"Total:   n = {c['total_identified']:,}",
                 id_color)

        draw_arrow(2.5, 16.1, 2.5, 15.0)

        # === SCREENING: Deduplication ===
        draw_box(2.5, 14.2, 4.0, 1.2,
                 f"DUPLICATE REMOVAL\n\n"
                 f"Duplicates removed: n = {c['total_duplicates_removed']:,}\n"
                 f"Records remaining:  n = {c['after_deduplication']:,}",
                 screen_color)

        # Exclusion box for duplicates
        draw_box(7.5, 14.2, 3.5, 1.0,
                 f"Duplicates removed\n"
                 f"Exact: {c['exact_duplicates_removed']:,}\n"
                 f"Near-dup: {c['near_duplicates_removed']:,}",
                 excl_color, fontsize=8)
        draw_arrow(4.5, 14.2, 5.75, 14.2)

        draw_arrow(2.5, 13.6, 2.5, 12.5)

        # === SCREENING: Criteria ===
        draw_box(2.5, 11.5, 4.0, 1.5,
                 f"SCREENING\n\n"
                 f"Records screened: n = {c['after_deduplication']:,}\n"
                 f"Records after screening: n = {c['after_screening']:,}",
                 screen_color)

        # Exclusion reasons
        draw_box(7.5, 11.5, 3.5, 1.5,
                 f"Excluded (n = {c['total_screening_excluded']:,})\n"
                 f"Language: {c['excluded_language']:,}\n"
                 f"Pub type: {c['excluded_pub_type']:,}\n"
                 f"No abstract: {c['excluded_no_abstract']:,}\n"
                 f"Too short: {c['excluded_abstract_too_short']:,}",
                 excl_color, fontsize=8)
        draw_arrow(4.5, 11.5, 5.75, 11.5)

        draw_arrow(2.5, 10.75, 2.5, 9.5)

        # === ELIGIBILITY ===
        draw_box(2.5, 8.7, 4.0, 1.2,
                 f"ELIGIBILITY\n\n"
                 f"Assessed: n = {c['assessed_eligibility']:,}\n"
                 f"Eligible: n = {c['after_eligibility']:,}",
                 elig_color)

        draw_box(7.5, 8.7, 3.5, 0.8,
                 f"Excluded (no entity pairs)\n"
                 f"n = {c['excluded_no_entity_pairs']:,}",
                 excl_color, fontsize=8)
        draw_arrow(4.5, 8.7, 5.75, 8.7)

        draw_arrow(2.5, 8.1, 2.5, 7.0)

        # === INCLUDED ===
        draw_box(2.5, 6.3, 4.0, 1.0,
                 f"INCLUDED\n\n"
                 f"Final corpus: n = {c['final_included']:,}",
                 incl_color)

        # Save
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        plt.savefig(output_path, dpi=200, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        plt.close()
        logger.info(f"PRISMA flow diagram saved to {output_path}")
