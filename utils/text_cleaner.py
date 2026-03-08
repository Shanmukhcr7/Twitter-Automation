import re
import html
from bs4 import BeautifulSoup

def clean_html(text: str) -> str:
    """Removes HTML tags from a string."""
    if not text:
        return ""
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(separator=" ", strip=True)

def unescape_html(text: str) -> str:
    """Unescapes HTML entities (e.g. &amp; to &)."""
    return html.unescape(text) if text else ""

def normalize_whitespace(text: str) -> str:
    """Replaces multiple spaces/newlines with a single space."""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', text).strip()

def clean_text(text: str) -> str:
    """Applies all standard cleaning operations on a piece of text."""
    if not text:
        return ""
    text = clean_html(text)
    text = unescape_html(text)
    text = normalize_whitespace(text)
    # Remove URL links to clean up pure text
    text = re.sub(r'http\S+|www\.\S+', '', text)
    return text.strip()

def truncate_text(text: str, max_length: int = 280) -> str:
    """Truncates text to a maximum length, appending '...' if truncated."""
    if len(text) <= max_length:
        return text
    # 280 minus 3 for the ellipsis
    return text[:max_length-3] + "..."
