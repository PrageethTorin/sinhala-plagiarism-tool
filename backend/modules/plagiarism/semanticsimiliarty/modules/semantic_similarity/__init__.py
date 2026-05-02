# Empty file to make this a Python package
"""
Semantic Similarity Module
"""
from .routes import router
from .services import SimilarityDetector, SinhalaTextProcessor, FileHandler
from .schemas import TextPair, SimilarityRequest, SimilarityResult

__all__ = [
    "router",
    "SimilarityDetector",
    "SinhalaTextProcessor",
    "FileHandler",
    "TextPair",
    "SimilarityRequest",
    "SimilarityResult"
]