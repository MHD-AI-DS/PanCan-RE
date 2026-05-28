"""Preprocessing — normalization, tokenization, sentence splitting."""

import re
import unicodedata
from typing import List

from .schema import CorpusRecord
from .io_utils import setup_logging

logger = setup_logging(__name__)

# Lazy-loaded NLTK resources
_nltk_ready = False


def _ensure_nltk():
    """Download required NLTK data if not already present."""
    global _nltk_ready
    if _nltk_ready:
        return
    import ssl
    import nltk

    # Temporarily bypass SSL for NLTK downloads only (university proxy workaround)
    original_context = getattr(ssl, "_create_default_https_context", None)
    try:
        ssl._create_default_https_context = ssl._create_unverified_context
    except Exception:
        pass

    for resource in ["punkt", "punkt_tab"]:
        try:
            nltk.download(resource, quiet=True)
        except Exception:
            pass

    # Restore original SSL context
    if original_context is not None:
        ssl._create_default_https_context = original_context

    _nltk_ready = True


class Preprocessor:
    """Text normalization, tokenization, and sentence splitting."""

    def __init__(self, config: dict):
        prep = config.get("preprocessing", {})
        norm = prep.get("normalize", {})
        self.do_lowercase = norm.get("lowercase", True)
        self.strip_accents = norm.get("strip_accents", True)
        self.normalize_unicode = norm.get("normalize_unicode", True)
        self.normalize_whitespace = norm.get("normalize_whitespace", True)
        self.remove_urls = norm.get("remove_urls", True)
        self.remove_emails = norm.get("remove_emails", True)
        self.tokenizer = prep.get("tokenizer", "nltk")
        self.sentence_splitter = prep.get("sentence_splitter", "nltk")

    def process(self, records: List[CorpusRecord]) -> List[CorpusRecord]:
        """Apply full preprocessing to all records."""
        _ensure_nltk()
        logger.info(f"Preprocessing {len(records)} records...")

        for i, rec in enumerate(records):
            rec.normalized_text = self.normalize(rec.abstract)
            rec.tokens = self.tokenize(rec.normalized_text)
            rec.sentences = self.sentence_split(rec.abstract)  # Sentences from original case

            if (i + 1) % 500 == 0:
                logger.info(f"  Processed {i + 1}/{len(records)}")

        logger.info(f"Preprocessing complete: {len(records)} records")
        return records

    def normalize(self, text: str) -> str:
        """Apply all normalization steps."""
        if not text:
            return ""

        # Unicode normalization (NFC)
        if self.normalize_unicode:
            text = unicodedata.normalize("NFC", text)

        # Strip accents
        if self.strip_accents:
            text = self._strip_accents(text)

        # Remove URLs
        if self.remove_urls:
            text = re.sub(r"https?://\S+|www\.\S+", "", text)

        # Remove emails
        if self.remove_emails:
            text = re.sub(r"\S+@\S+\.\S+", "", text)

        # Lowercase
        if self.do_lowercase:
            text = text.lower()

        # Whitespace normalization
        if self.normalize_whitespace:
            text = re.sub(r"\s+", " ", text).strip()

        return text

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        if not text:
            return []
        from nltk.tokenize import word_tokenize
        return word_tokenize(text)

    def sentence_split(self, text: str) -> List[str]:
        """Split text into sentences."""
        if not text:
            return []
        from nltk.tokenize import sent_tokenize
        return sent_tokenize(text)

    @staticmethod
    def _strip_accents(text: str) -> str:
        """Remove diacritical marks while preserving base characters."""
        nfkd = unicodedata.normalize("NFKD", text)
        return "".join(c for c in nfkd if not unicodedata.combining(c))
