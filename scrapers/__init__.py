"""
Scrapers package for IG Reports Bot
"""

from .base import BaseScraper
from .oversight_gov import OversightGovScraper, INTERESTING_KEYWORDS

__all__ = [
    'BaseScraper',
    'OversightGovScraper',
    'INTERESTING_KEYWORDS'
]
