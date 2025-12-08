"""
Extracteur XML PAGE principal

Extrait le texte et les métadonnées depuis des fichiers XML PAGE
et produit des données structurées.
"""

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Iterator, Optional, Dict, Any
import logging
import json

from ..config import Config, CorpusMetadata
from ..models import PageMetadata, ExtractedPage, ExtractedCorpus
from .zone_parser import ZoneParser
from .hyphen_merger import HyphenMerger

logger = logging.getLogger(__name__)


class XMLPageExtractor:
    """
    Extracteur de fichiers XML PAGE

    Extrait le texte et les métadonnées depuis des fichiers XML au format PAGE
    (utilisé par Transkribus, eScriptorium, etc.)

    Entrée:
        - Fichiers XML PAGE (.xml)

    Sortie:
        - ExtractedPage avec métadonnées et lignes de texte
        - Ou fichiers JSON intermédiaires

    Usage:
        config = Config.from_yaml("config.yaml")
        extractor = XMLPageExtractor(config)

        # Extraction d'un dossier
        pages = extractor.extract_folder("./xml_pages/")

        # Sauvegarde en JSON
        extractor.save_to_json(pages, "./output/extracted.json")
    """

    def __init__(self, config: Config):
        """
        Args:
            config: Configuration du pipeline
        """
        self.config = config
        self.zone_parser = ZoneParser(
            main_zone_type=config.extraction.main_zone_type,
            running_title_zone_type=config.extraction.running_title_zone_type,
            numbering_zone_type=config.extraction.numbering_zone_type,
        )
        self.hyphen_merger = HyphenMerger()

        self._processed_count = 0
        self._error_count = 0

    def extract_folder(
        self,
        input_folder: str | Path,
        sort_files: bool = True
    ) -> List[ExtractedPage]:
        """
        Extrait tous les fichiers XML d'un dossier

        Args:
            input_folder: Dossier contenant les fichiers XML
            sort_files: Trier les fichiers par nom

        Returns:
            Liste de ExtractedPage
        """
        input_folder = Path(input_folder)

        if not input_folder.exists():
            raise FileNotFoundError(f"Dossier non trouvé: {input_folder}")

        # Liste les fichiers XML
        xml_files = list(input_folder.glob("*.xml"))

        if sort_files:
            xml_files = sorted(xml_files, key=lambda f: f.name)

        if not xml_files:
            logger.warning(f"Aucun fichier XML trouvé dans {input_folder}")
            return []

        logger.info(f"Extraction de {len(xml_files)} fichiers XML depuis {input_folder}")

        pages = []
        for i, xml_file in enumerate(xml_files):
            try:
                page = self.extract_file(xml_file, page_index=i)
                pages.append(page)
            except Exception as e:
                logger.error(f"Erreur lors de l'extraction de {xml_file}: {e}")
                self._error_count += 1

        logger.info(f"Extraction terminée: {len(pages)} pages extraites, {self._error_count} erreurs")
        return pages

    def extract_file(
        self,
        xml_path: str | Path,
        page_index: int = 0
    ) -> ExtractedPage:
        """
        Extrait un fichier XML PAGE

        Args:
            xml_path: Chemin vers le fichier XML
            page_index: Index de la page (pour calculer le numéro)

        Returns:
            ExtractedPage avec métadonnées et lignes
        """
        xml_path = Path(xml_path)
        logger.debug(f"Extraction de {xml_path.name}")

        # Parse le XML
        tree = ET.parse(xml_path)
        root = tree.getroot()

        # Extrait les métadonnées
        metadata = self._extract_metadata(root, xml_path, page_index)

        # Extrait les lignes de la zone principale
        lines = self.zone_parser.extract_main_zone_lines(
            root,
            column_mode=self.config.extraction.column_mode
        )

        # Fusionne les mots coupés si configuré
        if self.config.extraction.merge_hyphenated:
            lines = self.hyphen_merger.merge_lines(lines)

        self._processed_count += 1

        return ExtractedPage(
            metadata=metadata,
            lines=lines,
        )

    def _extract_metadata(
        self,
        root: ET.Element,
        xml_path: Path,
        page_index: int
    ) -> PageMetadata:
        """
        Extrait les métadonnées d'une page

        Args:
            root: Élément racine XML
            xml_path: Chemin du fichier
            page_index: Index de la page

        Returns:
            PageMetadata
        """
        folio = xml_path.name

        # Numéro de page
        if self.config.pagination.page_number_source == "zone":
            page_number = self.zone_parser.extract_page_number_from_zone(root)
            if page_number is None:
                page_number = self._extract_page_number_from_filename(xml_path.name, page_index)
        else:
            page_number = self._extract_page_number_from_filename(xml_path.name, page_index)

        # Titre courant
        running_title = self.zone_parser.extract_running_title(
            root,
            default=self.config.extraction.default_running_title
        )

        # Métadonnées du corpus
        corpus_metadata = self.config.corpus.to_dict()

        return PageMetadata(
            folio=folio,
            page_number=page_number,
            running_title=running_title,
            corpus_metadata=corpus_metadata,
        )

    def _extract_page_number_from_filename(
        self,
        filename: str,
        page_index: int
    ) -> int:
        """
        Extrait le numéro de page depuis le nom de fichier

        Args:
            filename: Nom du fichier
            page_index: Index de la page (fallback)

        Returns:
            Numéro de page
        """
        # Essaie d'extraire un numéro du nom de fichier
        # Patterns courants: 0042.xml, page_0042.xml, folio_42.xml, 0042_1.xml
        patterns = [
            r"(\d+)\.xml$",           # 0042.xml
            r"(\d+)_\d+\.xml$",       # 0042_1.xml (premier groupe)
            r"page[_-]?(\d+)",        # page_0042, page-42
            r"folio[_-]?(\d+)",       # folio_42
            r"f[_-]?(\d+)",           # f42, f_42
        ]

        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                return int(match.group(1))

        # Fallback: utilise l'index + starting_page_number
        return self.config.pagination.starting_page_number + page_index

    def extract_iter(
        self,
        input_folder: str | Path,
        sort_files: bool = True
    ) -> Iterator[ExtractedPage]:
        """
        Itérateur sur les pages extraites (économise la mémoire)

        Args:
            input_folder: Dossier contenant les fichiers XML
            sort_files: Trier les fichiers par nom

        Yields:
            ExtractedPage
        """
        input_folder = Path(input_folder)
        xml_files = list(input_folder.glob("*.xml"))

        if sort_files:
            xml_files = sorted(xml_files, key=lambda f: f.name)

        for i, xml_file in enumerate(xml_files):
            try:
                yield self.extract_file(xml_file, page_index=i)
            except Exception as e:
                logger.error(f"Erreur lors de l'extraction de {xml_file}: {e}")

    def save_to_json(
        self,
        pages: List[ExtractedPage],
        output_path: str | Path
    ) -> None:
        """
        Sauvegarde les pages extraites en JSON

        Args:
            pages: Liste de pages extraites
            output_path: Chemin de sortie
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        corpus = ExtractedCorpus(pages=pages)
        corpus.save(output_path)

        logger.info(f"Sauvegardé {len(pages)} pages dans {output_path}")

    def save_individual_json(
        self,
        pages: List[ExtractedPage],
        output_folder: str | Path
    ) -> None:
        """
        Sauvegarde chaque page dans un fichier JSON séparé

        Args:
            pages: Liste de pages extraites
            output_folder: Dossier de sortie
        """
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        for page in pages:
            # Génère le nom de fichier
            folio_base = Path(page.metadata.folio).stem
            json_path = output_folder / f"{folio_base}.json"
            page.save(json_path)

        logger.info(f"Sauvegardé {len(pages)} fichiers JSON dans {output_folder}")

    @property
    def processed_count(self) -> int:
        """Nombre de fichiers traités"""
        return self._processed_count

    @property
    def error_count(self) -> int:
        """Nombre d'erreurs rencontrées"""
        return self._error_count

    def reset_stats(self) -> None:
        """Réinitialise les statistiques"""
        self._processed_count = 0
        self._error_count = 0


def extract_xml_folder(
    input_folder: str | Path,
    output_path: str | Path,
    config: Optional[Config] = None,
    individual_files: bool = False
) -> List[ExtractedPage]:
    """
    Fonction utilitaire pour extraire un dossier XML

    Args:
        input_folder: Dossier d'entrée
        output_path: Chemin de sortie (fichier JSON ou dossier)
        config: Configuration (optionnel)
        individual_files: Si True, crée un JSON par page

    Returns:
        Liste des pages extraites
    """
    if config is None:
        config = Config()

    extractor = XMLPageExtractor(config)
    pages = extractor.extract_folder(input_folder)

    if individual_files:
        extractor.save_individual_json(pages, output_path)
    else:
        extractor.save_to_json(pages, output_path)

    return pages
