"""
Étape 1 : Extraction XML PAGE → Données structurées

Ce module extrait le texte et les métadonnées depuis des fichiers XML PAGE
(format HTR/OCR) et produit des données structurées en JSON.

Classes principales:
    - XMLPageExtractor: Extracteur principal
    - ZoneParser: Parse les différentes zones du XML
    - HyphenMerger: Fusionne les mots coupés en fin de ligne

Usage:
    from PAGEtopage.step1_extract import XMLPageExtractor
    from PAGEtopage.config import Config

    config = Config.from_yaml("config.yaml")
    extractor = XMLPageExtractor(config)
    pages = extractor.extract_folder("./xml_pages/")
"""

from .extractor import XMLPageExtractor
from .zone_parser import ZoneParser
from .hyphen_merger import HyphenMerger

__all__ = ["XMLPageExtractor", "ZoneParser", "HyphenMerger"]
