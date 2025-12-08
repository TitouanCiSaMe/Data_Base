"""
PAGEtopage - Pipeline de traitement XML PAGE vers texte

Ce module fournit une chaîne de traitement modulaire pour :
1. Extraire du texte depuis des fichiers XML PAGE (format HTR/OCR)
2. Enrichir avec lemmatisation et annotation POS via CLTK
3. Exporter vers différents formats texte

Usage CLI:
    python -m PAGEtopage extract --input ./xml/ --output ./extracted/
    python -m PAGEtopage enrich --input ./extracted/ --output ./vertical/
    python -m PAGEtopage export --input ./vertical/ --output ./pages/

Usage Python:
    from PAGEtopage import Pipeline, Config
    config = Config.from_yaml("config.yaml")
    pipeline = Pipeline(config)
    pipeline.run(input_dir="./xml/", output_dir="./output/")
"""

__version__ = "1.0.0"
__author__ = "Data_Base Project"

from .config import Config, ExtractionConfig, EnrichmentConfig, ExportConfig
from .models import PageMetadata, ExtractedPage, Token, Sentence, AnnotatedPage

__all__ = [
    "Config",
    "ExtractionConfig",
    "EnrichmentConfig",
    "ExportConfig",
    "PageMetadata",
    "ExtractedPage",
    "Token",
    "Sentence",
    "AnnotatedPage",
]
