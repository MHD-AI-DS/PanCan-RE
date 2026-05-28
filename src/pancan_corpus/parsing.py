"""PubMed XML parser — converts PubmedArticle XML to CorpusRecord."""

import re
import xml.etree.ElementTree as ET
from typing import List, Optional

from .schema import CorpusRecord
from .io_utils import setup_logging

logger = setup_logging(__name__)


def parse_pubmed_xml(xml_text: str, source_query: str,
                     retrieval_date: str) -> List[CorpusRecord]:
    """Parse PubMed EFetch XML and return a list of CorpusRecord."""
    records = []
    parse_failures = 0

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        return records

    for article_elem in root.findall(".//PubmedArticle"):
        rec = _parse_single_article(article_elem, source_query, retrieval_date)
        if rec is not None:
            records.append(rec)
        else:
            parse_failures += 1

    if parse_failures:
        logger.warning(f"Failed to parse {parse_failures} article(s) in this batch")

    return records


def _parse_single_article(article_elem, source_query: str,
                           retrieval_date: str) -> Optional[CorpusRecord]:
    """Parse a single PubmedArticle element."""
    pmid = ""
    try:
        medline = article_elem.find("MedlineCitation")
        if medline is None:
            return None

        # PMID
        pmid_elem = medline.find("PMID")
        pmid = pmid_elem.text if pmid_elem is not None else ""

        article = medline.find("Article")
        if article is None:
            logger.warning(f"PMID {pmid}: No Article element found")
            return None

        # Title
        title_elem = article.find("ArticleTitle")
        title = _get_text(title_elem)

        # Abstract
        abstract_elem = article.find("Abstract")
        abstract = _extract_abstract(abstract_elem)

        # Journal
        journal_elem = article.find("Journal/Title")
        journal = journal_elem.text if journal_elem is not None else ""

        # Year
        year = _extract_year(article)

        # Authors
        authors = _extract_authors(article)

        # DOI
        doi = _extract_doi(article_elem)

        # Language
        lang_elem = article.find("Language")
        language = lang_elem.text if lang_elem is not None else ""

        # Publication types
        pub_types = []
        for pt in article.findall("PublicationTypeList/PublicationType"):
            if pt.text:
                pub_types.append(pt.text)

        # MeSH terms
        mesh_terms = []
        for mh in medline.findall("MeshHeadingList/MeshHeading/DescriptorName"):
            if mh.text:
                mesh_terms.append(mh.text)

        # Chemicals
        chemicals = []
        for chem in medline.findall("ChemicalList/Chemical/NameOfSubstance"):
            if chem.text:
                chemicals.append(chem.text)

        # Keywords
        keywords = []
        for kw in medline.findall("KeywordList/Keyword"):
            if kw.text:
                keywords.append(kw.text)

        return CorpusRecord(
            pmid=pmid,
            doi=doi,
            title=title,
            abstract=abstract,
            authors=authors,
            journal=journal,
            year=year,
            mesh_terms=mesh_terms,
            chemicals=chemicals,
            keywords=keywords,
            publication_type=pub_types,
            language=language,
            source_db="pubmed",
            source_query=source_query,
            retrieval_date=retrieval_date,
        )

    except (AttributeError, TypeError, ValueError) as e:
        logger.warning(f"Failed to parse article (PMID={pmid}): {type(e).__name__}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error parsing article (PMID={pmid}): {type(e).__name__}: {e}")
        return None


def _get_text(elem) -> str:
    """Extract all text from an element, including mixed content."""
    if elem is None:
        return ""
    return "".join(elem.itertext()).strip()


def _extract_abstract(abstract_elem) -> str:
    """Extract abstract text, handling structured abstracts."""
    if abstract_elem is None:
        return ""

    parts = []
    for text_elem in abstract_elem.findall("AbstractText"):
        label = text_elem.get("Label", "")
        text = _get_text(text_elem)
        if label and text:
            parts.append(f"{label}: {text}")
        elif text:
            parts.append(text)

    return " ".join(parts)


def _extract_year(article_elem) -> int:
    """Extract publication year from article. Prefers JournalPubDate for PubMed consistency."""
    # Prefer Journal PubDate (matches PubMed PDAT filter)
    year_elem = article_elem.find("Journal/JournalIssue/PubDate/Year")
    if year_elem is not None and year_elem.text:
        try:
            return int(year_elem.text)
        except ValueError:
            pass

    # Try MedlineDate
    medline_date = article_elem.find("Journal/JournalIssue/PubDate/MedlineDate")
    if medline_date is not None and medline_date.text:
        match = re.search(r"(\d{4})", medline_date.text)
        if match:
            return int(match.group(1))

    # Fall back to ArticleDate (electronic publication)
    for date_elem in article_elem.findall("ArticleDate"):
        year_elem = date_elem.find("Year")
        if year_elem is not None and year_elem.text:
            try:
                return int(year_elem.text)
            except ValueError:
                pass

    return 0


def _extract_authors(article_elem) -> List[str]:
    """Extract author names as 'LastName Initials' format."""
    authors = []
    for author in article_elem.findall("AuthorList/Author"):
        last = author.find("LastName")
        fore = author.find("ForeName")
        if last is not None and last.text:
            name = last.text
            if fore is not None and fore.text:
                initials = "".join(w[0] for w in fore.text.split() if w)
                name = f"{last.text} {initials}"
            authors.append(name)
    return authors


def _extract_doi(article_elem) -> str:
    """Extract DOI from ArticleIdList or ELocationID."""
    # Check ArticleIdList in PubmedData
    pubmed_data = article_elem.find("PubmedData")
    if pubmed_data is not None:
        for aid in pubmed_data.findall("ArticleIdList/ArticleId"):
            if aid.get("IdType") == "doi" and aid.text:
                return aid.text

    # Check ELocationID
    article = article_elem.find("MedlineCitation/Article")
    if article is not None:
        for eloc in article.findall("ELocationID"):
            if eloc.get("EIdType") == "doi" and eloc.text:
                return eloc.text

    return ""
