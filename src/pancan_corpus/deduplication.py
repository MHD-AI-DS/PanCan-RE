"""Deduplication — exact + near-duplicate removal via MinHash LSH."""

import random
from typing import Dict, List, Set, Tuple

import numpy as np

from .schema import CorpusRecord
from .io_utils import setup_logging

logger = setup_logging(__name__)

# Fixed seed for reproducibility
RANDOM_SEED = 42


class Deduplicator:
    """Remove exact and near-duplicate records."""

    def __init__(self, config: dict):
        dedup_cfg = config.get("deduplication", {})
        self.minhash_threshold = dedup_cfg.get("minhash_threshold", 0.85)
        self.num_perm = dedup_cfg.get("minhash_num_perm", 128)
        self.shingle_size = dedup_cfg.get("shingle_size", 3)

    def deduplicate(self, records: List[CorpusRecord]) -> Tuple[List[CorpusRecord], Dict[str, int]]:
        """
        Two-stage deduplication:
        1. Exact: same PMID/DOI across sources
        2. Near-duplicate: MinHash Jaccard similarity on abstract text
        Returns (unique_records, counts).
        """
        # Stage 1: Exact deduplication
        unique, exact_dupes = self._exact_dedup(records)
        logger.info(f"Exact dedup: {len(records)} → {len(unique)} ({exact_dupes} duplicates)")

        # Stage 2: Near-duplicate via MinHash
        final, near_dupes = self._minhash_dedup(unique)
        logger.info(f"Near-dup dedup: {len(unique)} → {len(final)} ({near_dupes} near-duplicates)")

        counts = {
            "exact_duplicates_removed": exact_dupes,
            "near_duplicates_removed": near_dupes,
            "total_duplicates_removed": exact_dupes + near_dupes,
        }
        return final, counts

    def _exact_dedup(self, records: List[CorpusRecord]) -> Tuple[List[CorpusRecord], int]:
        """Remove records with identical PMID or DOI."""
        seen_keys: Set[str] = set()
        unique = []
        dupes = 0

        for rec in records:
            key = rec.unique_key()
            if key in seen_keys:
                dupes += 1
                continue
            seen_keys.add(key)
            unique.append(rec)

        return unique, dupes

    def _minhash_dedup(self, records: List[CorpusRecord]) -> Tuple[List[CorpusRecord], int]:
        """Remove near-duplicates using MinHash with LSH."""
        try:
            from datasketch import MinHash, MinHashLSH
        except ImportError:
            logger.warning("datasketch not installed, skipping near-duplicate detection")
            return records, 0

        if not records:
            return records, 0

        # Set seeds for reproducibility
        random.seed(RANDOM_SEED)
        np.random.seed(RANDOM_SEED)

        lsh = MinHashLSH(threshold=self.minhash_threshold, num_perm=self.num_perm)
        minhashes = {}

        # Build MinHash for each record (skip empty abstracts)
        for i, rec in enumerate(records):
            if not rec.abstract or not rec.abstract.strip():
                continue
            mh = MinHash(num_perm=self.num_perm, seed=RANDOM_SEED)
            shingles = self._get_shingles(rec.abstract)
            for s in shingles:
                mh.update(s.encode("utf-8"))
            minhashes[i] = mh

        # Insert into LSH and identify duplicates
        duplicate_indices: Set[int] = set()
        for i, mh in minhashes.items():
            if i in duplicate_indices:
                continue
            try:
                lsh.insert(str(i), mh)
            except ValueError:
                # Already inserted (shouldn't happen but be safe)
                continue

            # Query for similar items
            results = lsh.query(mh)
            for r in results:
                r_idx = int(r)
                if r_idx != i and r_idx not in duplicate_indices:
                    duplicate_indices.add(r_idx)

        unique = [rec for i, rec in enumerate(records) if i not in duplicate_indices]
        return unique, len(duplicate_indices)

    def _get_shingles(self, text: str) -> List[str]:
        """Generate word n-gram shingles from text."""
        words = text.lower().split()
        if len(words) < self.shingle_size:
            return [" ".join(words)]
        return [
            " ".join(words[i:i + self.shingle_size])
            for i in range(len(words) - self.shingle_size + 1)
        ]
