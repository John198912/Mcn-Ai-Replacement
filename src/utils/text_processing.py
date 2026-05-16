"""Text processing utilities."""

import re
from typing import List, Set


def clean_text(text: str) -> str:
    """Clean and normalize text.

    Args:
        text: Input text

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove special characters (keep Chinese, English, numbers, basic punctuation)
    text = re.sub(r"[^\w\s一-鿿.,!?;:，。！？；：]", "", text)

    return text.strip()


def extract_keywords(text: str, min_length: int = 2) -> List[str]:
    """Extract keywords from text.

    Args:
        text: Input text
        min_length: Minimum keyword length

    Returns:
        List of keywords
    """
    if not text:
        return []

    # Simple keyword extraction (split by whitespace and punctuation)
    words = re.findall(r"[\w一-鿿]+", text)

    # Filter by length
    keywords = [w for w in words if len(w) >= min_length]

    return keywords


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate simple keyword-based similarity between two texts.

    Args:
        text1: First text
        text2: Second text

    Returns:
        Similarity score (0-1)
    """
    if not text1 or not text2:
        return 0.0

    # Extract keywords
    keywords1 = set(extract_keywords(text1.lower()))
    keywords2 = set(extract_keywords(text2.lower()))

    if not keywords1 or not keywords2:
        return 0.0

    # Calculate Jaccard similarity
    intersection = len(keywords1 & keywords2)
    union = len(keywords1 | keywords2)

    return intersection / union if union > 0 else 0.0


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length.

    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def count_chinese_chars(text: str) -> int:
    """Count Chinese characters in text.

    Args:
        text: Input text

    Returns:
        Number of Chinese characters
    """
    if not text:
        return 0

    return len(re.findall(r"[一-鿿]", text))
