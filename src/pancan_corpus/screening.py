"""Screening — apply inclusion/exclusion criteria per PRISMA protocol."""

from typing import Dict, List, Tuple

from .schema import CorpusRecord
from .io_utils import setup_logging

logger = setup_logging(__name__)


class Screener:
    """Applies inclusion/exclusion filters to corpus records."""

    def __init__(self, config: dict):
        sc = config.get("screening", {})
        self.allowed_languages = set(sc.get("allowed_languages", ["eng"]))
        self.excluded_pub_types = set(sc.get("excluded_pub_types", []))
        self.min_abstract_length = sc.get("min_abstract_length", 200)
        self.max_abstract_length = sc.get("max_abstract_length", 0)

    def screen(self, records: List[CorpusRecord]) -> Tuple[List[CorpusRecord], Dict[str, int]]:
        """
        Apply all screening filters.
        Returns (passed_records, exclusion_counts).
        """
        exclusion_counts = {
            "excluded_language": 0,
            "excluded_pub_type": 0,
            "excluded_no_abstract": 0,
            "excluded_abstract_too_short": 0,
            "excluded_abstract_too_long": 0,
        }
        passed = []

        for rec in records:
            # 1. Language filter
            if rec.language and rec.language.lower() not in {
                lang.lower() for lang in self.allowed_languages
            }:
                exclusion_counts["excluded_language"] += 1
                continue

            # 2. Publication type filter
            if any(pt in self.excluded_pub_types for pt in rec.publication_type):
                exclusion_counts["excluded_pub_type"] += 1
                continue

            # 3. Must have an abstract
            if not rec.abstract or not rec.abstract.strip():
                exclusion_counts["excluded_no_abstract"] += 1
                continue

            # 4. Minimum abstract length
            if len(rec.abstract.strip()) < self.min_abstract_length:
                exclusion_counts["excluded_abstract_too_short"] += 1
                continue

            # 5. Maximum abstract length (0 = no limit)
            if self.max_abstract_length > 0 and len(rec.abstract.strip()) > self.max_abstract_length:
                exclusion_counts["excluded_abstract_too_long"] += 1
                continue

            passed.append(rec)

        logger.info(f"Screening: {len(records)} input → {len(passed)} passed")
        for reason, count in exclusion_counts.items():
            if count > 0:
                logger.info(f"  {reason}: {count}")

        return passed, exclusion_counts
