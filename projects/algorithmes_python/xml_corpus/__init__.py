"""
Module XMLCorpusProcessor pour traitement de corpus XML.

Ce module fournit des outils pour extraire, nettoyer et lemmatiser
des corpus XML (format PAGE) avec TreeTagger.
"""

from .xml_corpus_processor import (
    XMLCorpusProcessor,
    ProcessingConfig,
    PageMetadata,
    PATTERNS,
    DEFAULT_LANGUAGE
)

__version__ = "2.0.0"
__author__ = "TitouanCiSaMe"

__all__ = [
    "XMLCorpusProcessor",
    "ProcessingConfig",
    "PageMetadata",
    "PATTERNS",
    "DEFAULT_LANGUAGE"
]
