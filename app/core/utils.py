"""Utility functions for domain parsing and validation."""

from urllib.parse import urlparse, parse_qs
import re


def normalize_domain(url: str) -> str:
    """
    Extract clean domain from various input formats.

    Examples:
        https://www.example.com/path -> example.com
        example.com -> example.com
        http://subdomain.example.com -> subdomain.example.com
    """
    url = url.lower().strip()

    # Remove protocol if present
    if "://" in url:
        url = url.split("://", 1)[1]

    # Remove www prefix
    if url.startswith("www."):
        url = url[4:]

    # Extract just the domain (remove path, query, fragment)
    url = url.split("/")[0]
    url = url.split("?")[0]
    url = url.split("#")[0]

    return url


def get_base_domain(domain: str) -> str:
    """
    Extract base domain from subdomain.

    Examples:
        metrics.example.com -> example.com
        example.com -> example.com
    """
    parts = domain.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return domain


def is_third_party(request_url: str, publisher_domain: str) -> bool:
    """
    Determine if a request URL is to a third-party domain.

    Args:
        request_url: Full URL of the request
        publisher_domain: Publisher's base domain

    Returns:
        True if request is to a different domain
    """
    try:
        parsed = urlparse(request_url)
        request_domain = parsed.netloc.lower()

        # Remove www prefix
        if request_domain.startswith("www."):
            request_domain = request_domain[4:]

        # Get base domains for comparison
        request_base = get_base_domain(request_domain)
        publisher_base = get_base_domain(publisher_domain)

        return request_base != publisher_base
    except Exception:
        return True  # Assume third-party on error


def extract_url_params(url: str) -> dict[str, str]:
    """
    Extract query parameters from URL.

    Returns:
        Dictionary of parameter names to values
    """
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        # Flatten list values to single strings
        return {k: v[0] if isinstance(v, list) and len(v) > 0 else v for k, v in params.items()}
    except Exception:
        return {}


def extract_domain_from_url(url: str) -> str:
    """Extract domain from a full URL."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        if domain.startswith("www."):
            domain = domain[4:]
        return domain
    except Exception:
        return ""


def is_pii_value(value: str) -> tuple[bool, str]:
    """
    Check if a value contains PII (email or phone number).

    Returns:
        (is_pii, pii_type) tuple
    """
    if not value or not isinstance(value, str):
        return False, ""

    value = str(value).lower()

    # Email regex
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.search(email_pattern, value, re.IGNORECASE):
        return True, "email"

    # Phone number patterns (various formats)
    phone_patterns = [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # US: 123-456-7890
        r'\b\(\d{3}\)\s*\d{3}[-.]?\d{4}\b',  # US: (123) 456-7890
        r'\b\+\d{1,3}\s?\d{8,14}\b',  # International: +1 1234567890
    ]

    for pattern in phone_patterns:
        if re.search(pattern, value):
            return True, "phone"

    return False, ""


def generate_publisher_id(domain: str) -> str:
    """
    Generate a normalized publisher ID from domain.

    Example:
        example.com -> example-com
        news.example.co.in -> news-example-co-in
    """
    return domain.replace(".", "-")
