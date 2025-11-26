"""
Analyseur de textes latins médiévaux - Version 2

Package pour l'analyse automatique de textes latins médiévaux avec :
- PyCollatinus (latin classique)
- Dictionnaire Du Cange (latin médiéval)
- Système de scoring multi-critères
- Colorisation à 3 niveaux (rouge/orange/noir)
- Support XML Pages (extraction MainZone)

Auteur: Claude
Version: 2.0.0
"""

from .latin_analyzer_v2 import LatinAnalyzer
from .page_xml_parser import PageXMLParser

__version__ = "2.0.0"
__all__ = ["LatinAnalyzer", "PageXMLParser"]
