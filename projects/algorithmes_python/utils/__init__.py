"""
Utils module - Utilitaires réutilisables
"""

from .async_downloader import AsyncDownloader
from .fuzzy_matcher import FuzzyMatcher, normalize_reference, similarity_score
from .text_processing import extract_ids_recursive, split_references
from .error_handler import RetryHandler, ErrorLogger
from .progress import ProgressTracker

__all__ = [
    'AsyncDownloader',
    'FuzzyMatcher',
    'normalize_reference',
    'similarity_score',
    'extract_ids_recursive',
    'split_references',
    'RetryHandler',
    'ErrorLogger',
    'ProgressTracker',
]
