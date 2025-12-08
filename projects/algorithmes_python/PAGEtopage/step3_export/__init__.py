"""
Étape 3 : Export Format Vertical → Texte

Ce module exporte le format vertical vers différents formats texte :
- clean : Texte brut (mots uniquement)
- diplomatic : Texte avec annotations POS
- annotated : Format tabulaire (word\\tPOS\\tlemma)

Classes principales:
    - TextExporter: Exporteur principal
    - VerticalParser: Parse les fichiers vertical
    - TextFormatter: Formate le texte de sortie

Usage:
    from PAGEtopage.step3_export import TextExporter
    from PAGEtopage.config import Config

    config = Config.from_yaml("config.yaml")
    exporter = TextExporter(config)
    exporter.export("corpus.vertical.txt", "./output/")
"""

from .exporter import TextExporter
from .vertical_parser import VerticalParser
from .formatters import TextFormatter, CleanFormatter, DiplomaticFormatter, AnnotatedFormatter

__all__ = [
    "TextExporter",
    "VerticalParser",
    "TextFormatter",
    "CleanFormatter",
    "DiplomaticFormatter",
    "AnnotatedFormatter",
]
