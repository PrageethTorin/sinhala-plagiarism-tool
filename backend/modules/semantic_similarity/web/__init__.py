"""
Web Search Module for Sinhala Plagiarism Detection
Provides live web search and content extraction capabilities
"""

from .web_search_service import (
    WebPlagiarismChecker,
    GoogleSearchService,
    WebContentExtractor,
    WebSearchCache,
    WebSearchResult,
    PlagiarismMatch,
    check_web_plagiarism
)

__all__ = [
    "WebPlagiarismChecker",
    "GoogleSearchService",
    "WebContentExtractor",
    "WebSearchCache",
    "WebSearchResult",
    "PlagiarismMatch",
    "check_web_plagiarism"
]
