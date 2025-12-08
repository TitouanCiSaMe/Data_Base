"""
Parseur de zones XML PAGE

Parse les différentes zones (MainZone, RunningTitleZone, NumberingZone)
d'un fichier XML au format PAGE.
"""

import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Namespace PAGE XML
PAGE_NS = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"
NS = {"page": PAGE_NS}


@dataclass
class ZoneContent:
    """Contenu extrait d'une zone"""
    zone_type: str
    lines: List[str]
    raw_text: str
    column_id: Optional[str] = None


class ZoneParser:
    """
    Parse les zones d'un fichier XML PAGE

    Supporte les zones :
    - MainZone : Texte principal (avec support colonnes)
    - RunningTitleZone : Titre courant
    - NumberingZone : Numéro de page
    - MarginTextZone : Notes marginales (optionnel)
    """

    def __init__(
        self,
        main_zone_type: str = "MainZone",
        running_title_zone_type: str = "RunningTitleZone",
        numbering_zone_type: str = "NumberingZone",
    ):
        """
        Args:
            main_zone_type: Type de zone pour le texte principal
            running_title_zone_type: Type de zone pour le titre courant
            numbering_zone_type: Type de zone pour la numérotation
        """
        self.main_zone_type = main_zone_type
        self.running_title_zone_type = running_title_zone_type
        self.numbering_zone_type = numbering_zone_type

    def parse_file(self, xml_path: str) -> Dict[str, List[ZoneContent]]:
        """
        Parse un fichier XML PAGE

        Args:
            xml_path: Chemin vers le fichier XML

        Returns:
            Dictionnaire {zone_type: [ZoneContent, ...]}
        """
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            return self.parse_root(root)
        except ET.ParseError as e:
            logger.error(f"Erreur de parsing XML pour {xml_path}: {e}")
            raise

    def parse_root(self, root: ET.Element) -> Dict[str, List[ZoneContent]]:
        """
        Parse un élément racine XML

        Args:
            root: Élément racine du XML

        Returns:
            Dictionnaire {zone_type: [ZoneContent, ...]}
        """
        zones: Dict[str, List[ZoneContent]] = {
            "main": [],
            "running_title": [],
            "numbering": [],
            "other": [],
        }

        # Trouve tous les TextRegion
        text_regions = root.findall(".//page:TextRegion", NS)

        # Fallback sans namespace
        if not text_regions:
            text_regions = root.findall(".//TextRegion")

        for region in text_regions:
            zone_type, column_id = self._get_zone_type(region)
            content = self._extract_region_content(region, zone_type, column_id)

            if content:
                if zone_type == self.main_zone_type:
                    zones["main"].append(content)
                elif zone_type == self.running_title_zone_type:
                    zones["running_title"].append(content)
                elif zone_type == self.numbering_zone_type:
                    zones["numbering"].append(content)
                else:
                    zones["other"].append(content)

        return zones

    def _get_zone_type(self, region: ET.Element) -> Tuple[str, Optional[str]]:
        """
        Extrait le type de zone et l'ID de colonne

        Args:
            region: Élément TextRegion

        Returns:
            Tuple (zone_type, column_id ou None)
        """
        custom = region.get("custom", "")

        # Pattern pour extraire le type : structure {type:MainZone;}
        type_match = re.search(r"type:([^;}\s]+)", custom)
        zone_type = type_match.group(1) if type_match else "Unknown"

        # Pattern pour extraire la colonne : structure {type:MainZone:column#1;}
        column_match = re.search(r"column#(\d+)", custom)
        column_id = column_match.group(1) if column_match else None

        return zone_type, column_id

    def _extract_region_content(
        self,
        region: ET.Element,
        zone_type: str,
        column_id: Optional[str]
    ) -> Optional[ZoneContent]:
        """
        Extrait le contenu d'un TextRegion

        Args:
            region: Élément TextRegion
            zone_type: Type de zone
            column_id: ID de colonne (ou None)

        Returns:
            ZoneContent ou None si vide
        """
        lines = []

        # Cherche les TextLine
        text_lines = region.findall(".//page:TextLine", NS)
        if not text_lines:
            text_lines = region.findall(".//TextLine")

        for text_line in text_lines:
            text = self._get_unicode_content(text_line)
            if text:
                lines.append(text)

        # Si pas de TextLine, cherche directement TextEquiv
        if not lines:
            text = self._get_unicode_content(region)
            if text:
                lines = [text]

        if not lines:
            return None

        return ZoneContent(
            zone_type=zone_type,
            lines=lines,
            raw_text="\n".join(lines),
            column_id=column_id,
        )

    def _get_unicode_content(self, element: ET.Element) -> str:
        """
        Extrait le contenu Unicode d'un élément

        Args:
            element: Élément XML

        Returns:
            Texte Unicode ou chaîne vide
        """
        # Cherche TextEquiv/Unicode
        unicode_elem = element.find(".//page:TextEquiv/page:Unicode", NS)
        if unicode_elem is None:
            unicode_elem = element.find(".//TextEquiv/Unicode")
        if unicode_elem is None:
            unicode_elem = element.find(".//page:Unicode", NS)
        if unicode_elem is None:
            unicode_elem = element.find(".//Unicode")

        if unicode_elem is not None and unicode_elem.text:
            return unicode_elem.text.strip()

        return ""

    def extract_main_zone_lines(
        self,
        root: ET.Element,
        column_mode: str = "single"
    ) -> List[str]:
        """
        Extrait les lignes de la zone principale

        Args:
            root: Élément racine XML
            column_mode: "single" ou "dual"

        Returns:
            Liste des lignes de texte
        """
        zones = self.parse_root(root)
        main_zones = zones["main"]

        if not main_zones:
            return []

        if column_mode == "single":
            # Concatène toutes les zones main
            all_lines = []
            for zone in main_zones:
                all_lines.extend(zone.lines)
            return all_lines

        elif column_mode == "dual":
            # Trie par column_id et traite séparément
            column1_lines = []
            column2_lines = []

            for zone in main_zones:
                if zone.column_id == "1":
                    column1_lines.extend(zone.lines)
                elif zone.column_id == "2":
                    column2_lines.extend(zone.lines)
                else:
                    # Pas d'ID de colonne, ajoute à la première
                    column1_lines.extend(zone.lines)

            # Retourne les deux colonnes concaténées
            return column1_lines + column2_lines

        return []

    def extract_running_title(
        self,
        root: ET.Element,
        default: str = "No running title"
    ) -> str:
        """
        Extrait le titre courant

        Args:
            root: Élément racine XML
            default: Valeur par défaut si non trouvé

        Returns:
            Titre courant
        """
        zones = self.parse_root(root)
        running_title_zones = zones["running_title"]

        if running_title_zones:
            return running_title_zones[0].raw_text

        return default

    def extract_page_number_from_zone(
        self,
        root: ET.Element,
        default: Optional[int] = None
    ) -> Optional[int]:
        """
        Extrait le numéro de page depuis la zone NumberingZone

        Args:
            root: Élément racine XML
            default: Valeur par défaut si non trouvé

        Returns:
            Numéro de page ou default
        """
        zones = self.parse_root(root)
        numbering_zones = zones["numbering"]

        if numbering_zones:
            text = numbering_zones[0].raw_text
            # Extrait les chiffres
            numbers = re.findall(r"\d+", text)
            if numbers:
                try:
                    return int(numbers[0])
                except ValueError:
                    pass

        return default
