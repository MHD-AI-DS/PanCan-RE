"""Shared I/O helpers — JSONL read/write, config loading, logging."""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Iterator, List

import yaml

from .schema import CorpusRecord


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent.parent


def load_config(config_path: str = None) -> dict:
    """Load config.yaml and return as dict. API keys can be overridden by env vars."""
    if config_path is None:
        config_path = get_project_root() / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Override API keys from environment variables (avoids hardcoding secrets)
    scopus_key = os.environ.get("SCOPUS_API_KEY", "")
    if scopus_key:
        config.setdefault("api", {}).setdefault("scopus", {})["api_key"] = scopus_key

    ncbi_key = os.environ.get("NCBI_API_KEY", "")
    if ncbi_key:
        config.setdefault("api", {}).setdefault("ncbi", {})["api_key"] = ncbi_key

    return config


def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)
    return logger


def write_jsonl(records: List[CorpusRecord], path: str) -> int:
    """Write a list of CorpusRecord to a JSONL file. Returns count written."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    count = 0
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(rec.to_json() + "\n")
            count += 1
    return count


def read_jsonl(path: str) -> List[CorpusRecord]:
    """Read all records from a JSONL file."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(CorpusRecord.from_json(line))
    return records


def iter_jsonl(path: str) -> Iterator[CorpusRecord]:
    """Iterate over records in a JSONL file (memory-efficient)."""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield CorpusRecord.from_json(line)


def save_prisma_counts(counts: dict, path: str):
    """Save PRISMA stage counts to JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(counts, f, indent=2)


def load_prisma_counts(path: str) -> dict:
    """Load PRISMA stage counts from JSON."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
