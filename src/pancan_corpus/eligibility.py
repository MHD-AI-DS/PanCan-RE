"""Eligibility filter — entity-based pre-filter for relation extraction."""

import re
from typing import Dict, List, Set, Tuple

from .schema import CorpusRecord
from .io_utils import setup_logging

logger = setup_logging(__name__)


class EligibilityFilter:
    """Filter records that contain at least N biomedical entity types."""

    def __init__(self, config: dict):
        elig = config.get("eligibility", {})
        self.min_entity_types = elig.get("min_entity_types", 1)
        self.method = elig.get("entity_method", "dictionary")

        # Build keyword lookup from config
        self.entity_keywords: Dict[str, List[str]] = {}
        if self.method == "dictionary":
            kw_config = elig.get("entity_keywords", {})
            for entity_type, keywords in kw_config.items():
                self.entity_keywords[entity_type] = [kw.lower() for kw in keywords]

    def filter(self, records: List[CorpusRecord]) -> Tuple[List[CorpusRecord], Dict[str, int]]:
        """
        Filter records that have at least min_entity_types distinct entity types.
        Returns (eligible_records, counts).
        """
        eligible = []
        excluded = 0
        entity_type_dist: Dict[str, int] = {}  # Track distribution

        for rec in records:
            detected_types = self._detect_entity_types(rec)
            if len(detected_types) >= self.min_entity_types:
                eligible.append(rec)
                for et in detected_types:
                    entity_type_dist[et] = entity_type_dist.get(et, 0) + 1
            else:
                excluded += 1

        logger.info(f"Eligibility: {len(records)} → {len(eligible)} "
                    f"({excluded} excluded, < {self.min_entity_types} entity types)")
        logger.info(f"  Entity type distribution: {entity_type_dist}")

        counts = {
            "excluded_no_entity_pairs": excluded,
            "entity_type_distribution": entity_type_dist,
        }
        return eligible, counts

    def _detect_entity_types(self, rec: CorpusRecord) -> Set[str]:
        """Detect which entity types appear in a record's abstract using word-boundary matching."""
        text_lower = (rec.abstract + " " + rec.title).lower()
        detected = set()

        for entity_type, keywords in self.entity_keywords.items():
            for kw in keywords:
                # Word boundary matching to avoid false positives (e.g., "akt" in "reaktion")
                if re.search(r'\b' + re.escape(kw) + r'\b', text_lower):
                    detected.add(entity_type)
                    break  # One match per type is enough

        return detected
