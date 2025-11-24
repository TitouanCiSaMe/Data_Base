#!/usr/bin/env python3
"""
Extracteur de texte depuis XML Pages (compatible avec xml_corpus_processor.py).

Utilise EXACTEMENT la même logique d'extraction que le processeur NoSketch
pour garantir la cohérence entre les deux pipelines.

Structure supportée :
- TextRegion[@custom='structure {type:MainZone;}'] (mode single)
- TextRegion[@custom='structure {type:MainZone:column#1;}'] (mode dual)
- TextRegion[@custom='structure {type:MainZone:column#2;}'] (mode dual)

Auteur: Claude
Date: 2025-11-24
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Optional
import xml.etree.ElementTree as ET


class PageXMLParser:
    """
    Parser de fichiers XML Pages pour extraction de texte MainZone.

    Compatible avec la structure utilisée par xml_corpus_processor.py
    """

    def __init__(self, column_mode='single'):
        """
        Initialise le parser.

        Args:
            column_mode (str): 'single' ou 'dual' selon la structure des pages
        """
        self.column_mode = column_mode

    def parse_file(self, xml_file: str) -> Tuple[List[str], Optional[dict]]:
        """
        Parse un fichier XML Page et extrait le texte des MainZone.

        Args:
            xml_file (str): Chemin vers le fichier XML

        Returns:
            Tuple[List[str], dict]:
                - Liste des lignes de texte extraites
                - Métadonnées (page_number, running_title, etc.)
        """
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            # Nettoyer les namespaces (comme dans xml_corpus_processor)
            self._remove_namespaces(root)

            # Extraire les métadonnées
            metadata = self._extract_metadata(root, xml_file)

            # Extraire le texte selon le mode
            lines = self._extract_text(root)

            return lines, metadata

        except ET.ParseError as e:
            print(f"❌ Erreur de parsing XML dans {xml_file}: {e}")
            return [], None
        except Exception as e:
            print(f"❌ Erreur inattendue dans {xml_file}: {e}")
            return [], None

    def parse_folder(self, folder_path: str, file_pattern='*.xml') -> Tuple[str, List[dict]]:
        """
        Parse tous les fichiers XML d'un dossier.

        Args:
            folder_path (str): Chemin vers le dossier
            file_pattern (str): Pattern de fichiers à traiter

        Returns:
            Tuple[str, List[dict]]:
                - Texte complet concaténé
                - Liste des métadonnées par fichier
        """
        folder = Path(folder_path)

        if not folder.exists():
            raise FileNotFoundError(f"Dossier introuvable : {folder_path}")

        # Lister et trier les fichiers XML
        xml_files = sorted(folder.glob(file_pattern))

        if not xml_files:
            print(f"⚠️  Aucun fichier {file_pattern} trouvé dans {folder_path}")
            return "", []

        print(f"📂 Traitement de {len(xml_files)} fichiers XML...")

        all_lines = []
        all_metadata = []

        for xml_file in xml_files:
            lines, metadata = self.parse_file(str(xml_file))

            if lines:
                all_lines.extend(lines)
                if metadata:
                    all_metadata.append(metadata)

        # Concaténer tout le texte
        full_text = '\n'.join(all_lines)

        print(f"✅ {len(all_lines)} lignes extraites de {len(all_metadata)} fichiers")

        return full_text, all_metadata

    def _remove_namespaces(self, root: ET.Element) -> None:
        """
        Supprime les namespaces XML pour simplifier les requêtes XPath.
        (Copie de la méthode de xml_corpus_processor)

        Args:
            root: Élément racine de l'arbre XML
        """
        for elem in root.iter():
            # Supprimer le namespace du tag
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]

            # Supprimer les namespaces des attributs
            attribs = {}
            for key, value in elem.attrib.items():
                if '}' in key:
                    key = key.split('}', 1)[1]
                attribs[key] = value
            elem.attrib = attribs

    def _extract_metadata(self, root: ET.Element, filename: str) -> dict:
        """
        Extrait les métadonnées de la page.

        Args:
            root: Élément racine XML
            filename: Nom du fichier

        Returns:
            dict: Métadonnées extraites
        """
        metadata = {
            'filename': os.path.basename(filename),
            'page_number': self._extract_page_number(root, filename),
            'running_title': self._extract_running_title(root)
        }

        return metadata

    def _extract_page_number(self, root: ET.Element, filename: str) -> Optional[int]:
        """
        Extrait le numéro de page (depuis NumberingZone ou filename).

        Args:
            root: Élément racine XML
            filename: Nom du fichier

        Returns:
            int: Numéro de page ou None
        """
        # Essayer d'extraire depuis NumberingZone
        numbering_zone = root.find(
            ".//TextRegion[@custom='structure {type:NumberingZone;}']"
            "//TextEquiv/Unicode"
        )

        if numbering_zone is not None and numbering_zone.text:
            # Extraire le premier nombre trouvé
            match = re.search(r'\d+', numbering_zone.text)
            if match:
                return int(match.group())

        # Sinon extraire depuis le nom de fichier (ex: page_042.xml → 42)
        match = re.search(r'_(\d+)(?:\.xml)?$', filename)
        if match:
            return int(match.group(1))

        return None

    def _extract_running_title(self, root: ET.Element) -> str:
        """
        Extrait le titre courant de la page.

        Args:
            root: Élément racine XML

        Returns:
            str: Titre courant ou "No running title"
        """
        running_title_elem = root.find(
            ".//TextRegion[@custom='structure {type:RunningTitleZone;}']"
            "//TextEquiv/Unicode"
        )

        if running_title_elem is not None and running_title_elem.text:
            return running_title_elem.text.strip()

        return "No running title"

    def _extract_text(self, root: ET.Element) -> List[str]:
        """
        Extrait le texte des MainZone selon le mode (single/dual).

        LOGIQUE IDENTIQUE à xml_corpus_processor._extract_columns()

        Args:
            root: Élément racine XML

        Returns:
            List[str]: Liste des lignes de texte
        """
        all_lines = []

        if self.column_mode == 'single':
            # Mode classique : une seule MainZone
            main_zone = root.find(
                ".//TextRegion[@custom='structure {type:MainZone;}']"
            )

            if main_zone is not None:
                for text_line in main_zone.findall(".//TextLine"):
                    text_equiv = text_line.find(".//TextEquiv/Unicode")
                    if text_equiv is not None and text_equiv.text:
                        all_lines.append(text_equiv.text.strip())

        elif self.column_mode == 'dual':
            # Mode dual : deux colonnes séparées

            # Colonne 1
            col1 = root.find(
                ".//TextRegion[@custom='structure {type:MainZone:column#1;}']"
            )
            if col1 is not None:
                for text_line in col1.findall(".//TextLine"):
                    text_equiv = text_line.find(".//TextEquiv/Unicode")
                    if text_equiv is not None and text_equiv.text:
                        all_lines.append(text_equiv.text.strip())

            # Colonne 2
            col2 = root.find(
                ".//TextRegion[@custom='structure {type:MainZone:column#2;}']"
            )
            if col2 is not None:
                for text_line in col2.findall(".//TextLine"):
                    text_equiv = text_line.find(".//TextEquiv/Unicode")
                    if text_equiv is not None and text_equiv.text:
                        all_lines.append(text_equiv.text.strip())

        return all_lines


# Fonctions utilitaires pour usage direct

def extract_text_from_xml(xml_file: str, column_mode='single') -> str:
    """
    Fonction simple pour extraire le texte d'un fichier XML Page.

    Args:
        xml_file (str): Chemin vers le fichier XML
        column_mode (str): 'single' ou 'dual'

    Returns:
        str: Texte extrait
    """
    parser = PageXMLParser(column_mode=column_mode)
    lines, _ = parser.parse_file(xml_file)
    return '\n'.join(lines)


def extract_text_from_folder(folder_path: str, column_mode='single') -> str:
    """
    Fonction simple pour extraire le texte d'un dossier de fichiers XML Pages.

    Args:
        folder_path (str): Chemin vers le dossier
        column_mode (str): 'single' ou 'dual'

    Returns:
        str: Texte complet extrait
    """
    parser = PageXMLParser(column_mode=column_mode)
    text, _ = parser.parse_folder(folder_path)
    return text


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 page_xml_parser.py <fichier.xml|dossier> [single|dual]")
        sys.exit(1)

    input_path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else 'single'

    parser = PageXMLParser(column_mode=mode)

    if os.path.isfile(input_path):
        # Un seul fichier
        lines, metadata = parser.parse_file(input_path)
        print(f"\n📄 Fichier : {metadata['filename']}")
        print(f"📄 Page : {metadata['page_number']}")
        print(f"📄 Titre courant : {metadata['running_title']}")
        print(f"📄 Lignes extraites : {len(lines)}")
        print("\n" + "="*60)
        print('\n'.join(lines))

    elif os.path.isdir(input_path):
        # Dossier complet
        text, metadata_list = parser.parse_folder(input_path)
        print(f"\n📊 Pages traitées : {len(metadata_list)}")
        print(f"📊 Lignes totales : {len(text.splitlines())}")
        print("\n" + "="*60)
        print(text)

    else:
        print(f"❌ Chemin invalide : {input_path}")
        sys.exit(1)
