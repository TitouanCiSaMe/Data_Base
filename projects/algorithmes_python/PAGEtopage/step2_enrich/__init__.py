"""
Étape 2 : Enrichissement → Format Vertical

Ce module enrichit les pages extraites avec :
- Segmentation en phrases
- Tokenisation
- Lemmatisation via CLTK
- Annotation POS (Part-of-Speech)

Classes principales:
    - EnrichmentProcessor: Processeur principal
    - Tokenizer: Segmentation et tokenisation
    - CLTKLemmatizer: Interface avec CLTK

Usage:
    from PAGEtopage.step2_enrich import EnrichmentProcessor
    from PAGEtopage.config import Config

    config = Config.from_yaml("config.yaml")
    processor = EnrichmentProcessor(config)
    annotated_pages = processor.process_pages(extracted_pages)
"""

from .processor import EnrichmentProcessor
from .tokenizer import Tokenizer
from .lemmatizer import CLTKLemmatizer

__all__ = ["EnrichmentProcessor", "Tokenizer", "CLTKLemmatizer"]
