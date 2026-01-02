"""
Reference deduplication utilities.

Handles finding and merging duplicate references based on DOI, title, and authors.
"""

import hashlib
import re
from typing import Optional


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison.
    - Lowercase
    - Remove extra whitespace
    - Remove punctuation
    """
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text


def extract_first_author(authors: str) -> str:
    """
    Extract the first author's last name from authors string.

    Examples:
        "Smith, J., Doe, A." -> "smith"
        "Smith et al." -> "smith"
        "John Smith and Jane Doe" -> "smith"
    """
    authors = normalize_text(authors)

    # Handle "et al" format
    if 'et al' in authors:
        parts = authors.split('et al')[0].strip().split()
        return parts[0] if parts else ""

    # Handle comma-separated format: "LastName, FirstName"
    if ',' in authors:
        return authors.split(',')[0].strip()

    # Handle "and" separated: "FirstName LastName and ..."
    if ' and ' in authors:
        authors = authors.split(' and ')[0]

    # Take first word as last name
    parts = authors.strip().split()
    return parts[0] if parts else ""


def compute_dedup_hash(
    title: str,
    authors: str,
    doi: Optional[str] = None
) -> str:
    """
    Compute a deduplication hash for a reference.

    Priority:
    1. If DOI exists, use it (most reliable)
    2. Otherwise, use normalized title + first author

    Args:
        title: Reference title
        authors: Authors string
        doi: Optional DOI

    Returns:
        64-character hex hash string
    """
    if doi:
        # DOI is the most reliable identifier
        normalized_doi = normalize_text(doi)
        return hashlib.sha256(f"doi:{normalized_doi}".encode()).hexdigest()

    # Fallback to title + first author
    normalized_title = normalize_text(title)
    first_author = extract_first_author(authors)

    # Create hash from title + first author
    hash_input = f"{normalized_title}:{first_author}"
    return hashlib.sha256(hash_input.encode()).hexdigest()


def should_merge_references(
    ref1_title: str,
    ref1_authors: str,
    ref1_doi: Optional[str],
    ref2_title: str,
    ref2_authors: str,
    ref2_doi: Optional[str],
) -> bool:
    """
    Determine if two references should be merged.

    Returns:
        True if references are duplicates and should be merged
    """
    # If both have DOI and they match, definitely merge
    if ref1_doi and ref2_doi:
        return normalize_text(ref1_doi) == normalize_text(ref2_doi)

    # Compare normalized titles and first authors
    title1_norm = normalize_text(ref1_title)
    title2_norm = normalize_text(ref2_title)
    author1_first = extract_first_author(ref1_authors)
    author2_first = extract_first_author(ref2_authors)

    # Must have same first author and very similar title
    if author1_first != author2_first:
        return False

    # Simple string similarity: check if titles are very close
    # (In production, you might use Levenshtein distance or vector similarity)
    return title1_norm == title2_norm
