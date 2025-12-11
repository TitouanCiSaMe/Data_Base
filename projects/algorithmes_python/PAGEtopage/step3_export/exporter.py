"""
Exporteur principal

Exporte le format vertical vers différents formats texte.
"""

from pathlib import Path
from typing import List, Dict, Optional
import logging

from ..config import Config
from ..models import AnnotatedPage, AnnotatedCorpus
from .vertical_parser import VerticalParser
from .formatters import create_formatter, TextFormatter, ScholarlyFormatter
from .index_generator import IndexGenerator

logger = logging.getLogger(__name__)


class TextExporter:
    """
    Exporteur de format vertical vers texte

    Transforme un corpus vertical en fichiers texte individuels
    avec différents formats possibles.

    Entrée:
        - Fichier vertical (.vertical.txt)
        - Ou liste de AnnotatedPage

    Sortie:
        - Fichiers texte individuels par page
        - texte_complet.txt (optionnel)
        - pages_index.json (optionnel)
        - images_mapping.txt (optionnel)

    Usage:
        config = Config.from_yaml("config.yaml")
        exporter = TextExporter(config)

        # Depuis un fichier vertical
        exporter.export("corpus.vertical.txt", "./output/")

        # Depuis des pages
        exporter.export_pages(annotated_pages, "./output/")
    """

    def __init__(self, config: Config):
        """
        Args:
            config: Configuration du pipeline
        """
        self.config = config
        self.parser = VerticalParser()
        self.formatter = create_formatter(config.export.format)

        self._exported_count = 0
        self._error_count = 0

    def export(
        self,
        input_path: str | Path,
        output_folder: str | Path
    ) -> Dict[str, str]:
        """
        Exporte un fichier vertical

        Args:
            input_path: Chemin vers le fichier vertical
            output_folder: Dossier de sortie

        Returns:
            Mapping {folio: chemin_fichier_sortie}
        """
        input_path = Path(input_path)
        output_folder = Path(output_folder)

        # Parse le fichier vertical
        corpus = self.parser.parse_file(input_path)

        return self.export_pages(corpus.pages, output_folder)

    def export_pages(
        self,
        pages: List[AnnotatedPage],
        output_folder: str | Path
    ) -> Dict[str, str]:
        """
        Exporte une liste de pages

        Args:
            pages: Liste de AnnotatedPage
            output_folder: Dossier de sortie

        Returns:
            Mapping {folio: chemin_fichier_sortie}
        """
        output_folder = Path(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

        logger.info(f"Export de {len(pages)} pages vers {output_folder}")

        page_files: Dict[str, str] = {}
        all_text_parts: List[str] = []

        for page in pages:
            try:
                # Génère le nom de fichier
                filename = self._generate_filename(page)
                output_path = output_folder / filename

                # Formate et écrit la page
                text = self.formatter.format_page(page)
                self._write_page(output_path, text)

                page_files[page.metadata.folio] = filename
                all_text_parts.append(text)
                self._exported_count += 1

            except Exception as e:
                logger.error(f"Erreur export {page.metadata.folio}: {e}")
                self._error_count += 1

        # Génère le texte complet
        if self.config.export.generate_combined:
            self._write_combined_text(output_folder, all_text_parts)

        # Génère les index
        if self.config.export.generate_index:
            index_gen = IndexGenerator(output_folder)
            index_gen.generate_all(pages, page_files)

        logger.info(
            f"Export terminé: {self._exported_count} pages, "
            f"{self._error_count} erreurs"
        )

        return page_files

    def _generate_filename(self, page: AnnotatedPage) -> str:
        """
        Génère le nom de fichier pour une page

        Args:
            page: Page annotée

        Returns:
            Nom de fichier
        """
        pattern = self.config.export.page_filename_pattern

        # Retire l'extension .xml du folio
        folio_base = Path(page.metadata.folio).stem

        # Remplace les placeholders
        filename = pattern.format(
            number=page.metadata.page_number,
            folio=folio_base,
            page_number=page.metadata.page_number,
        )

        return filename

    def _write_page(self, path: Path, content: str) -> None:
        """
        Écrit une page dans un fichier

        Args:
            path: Chemin de sortie
            content: Contenu à écrire
        """
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        logger.debug(f"Écrit: {path}")

    def _write_combined_text(
        self,
        output_folder: Path,
        text_parts: List[str]
    ) -> Path:
        """
        Écrit le texte complet combiné

        Args:
            output_folder: Dossier de sortie
            text_parts: Liste des textes par page

        Returns:
            Chemin du fichier créé
        """
        output_path = output_folder / "texte_complet.txt"

        # Pour le format scholarly, les pages ont déjà leur en-tête
        # Pour les autres formats, on les sépare simplement par deux lignes vides
        if isinstance(self.formatter, ScholarlyFormatter):
            # Les pages incluent déjà l'en-tête, on les sépare par une ligne vide
            combined = "\n\n".join(part for part in text_parts if part.strip())
        else:
            # Pour les autres formats, sépare simplement les pages
            combined = "\n\n".join(part for part in text_parts if part.strip())

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(combined)

        logger.info(f"Texte complet écrit: {output_path}")
        return output_path

    def set_format(self, format_type: str) -> None:
        """
        Change le format de sortie

        Args:
            format_type: "clean", "diplomatic", "annotated"
        """
        self.formatter = create_formatter(format_type)
        self.config.export.format = format_type

    @property
    def exported_count(self) -> int:
        """Nombre de pages exportées"""
        return self._exported_count

    @property
    def error_count(self) -> int:
        """Nombre d'erreurs"""
        return self._error_count

    def reset_stats(self) -> None:
        """Réinitialise les statistiques"""
        self._exported_count = 0
        self._error_count = 0


def export_vertical_to_text(
    input_path: str | Path,
    output_folder: str | Path,
    format_type: str = "clean",
    config: Optional[Config] = None
) -> Dict[str, str]:
    """
    Fonction utilitaire pour exporter un fichier vertical

    Args:
        input_path: Chemin vers le fichier vertical
        output_folder: Dossier de sortie
        format_type: Format de sortie
        config: Configuration optionnelle

    Returns:
        Mapping {folio: chemin_fichier}
    """
    if config is None:
        config = Config()
        config.export.format = format_type

    exporter = TextExporter(config)
    return exporter.export(input_path, output_folder)
