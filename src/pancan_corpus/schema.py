"""Corpus record schema — defines the structure of each JSONL record."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional
import json


@dataclass
class CorpusRecord:
    """A single abstract record in the corpus."""

    record_id: str = ""
    pmid: str = ""
    doi: str = ""
    scopus_id: str = ""
    title: str = ""
    abstract: str = ""
    authors: List[str] = field(default_factory=list)
    journal: str = ""
    year: int = 0
    mesh_terms: List[str] = field(default_factory=list)
    chemicals: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    publication_type: List[str] = field(default_factory=list)
    language: str = ""
    source_db: str = ""          # "pubmed", "pmc", "scopus"
    source_query: str = ""
    retrieval_date: str = ""
    # Preprocessing outputs (populated in stage 04)
    normalized_text: str = ""
    tokens: List[str] = field(default_factory=list)
    sentences: List[str] = field(default_factory=list)

    def to_json(self) -> str:
        """Serialize to a single JSON line."""
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, line: str) -> "CorpusRecord":
        """Deserialize from a JSON line."""
        data = json.loads(line)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def unique_key(self) -> str:
        """Return a dedup key: prefer PMID, fall back to DOI, then scopus_id."""
        if self.pmid:
            return f"pmid:{self.pmid}"
        if self.doi:
            return f"doi:{self.doi.lower()}"
        if self.scopus_id:
            return f"scopus:{self.scopus_id}"
        return f"title:{self.title.lower().strip()}"
