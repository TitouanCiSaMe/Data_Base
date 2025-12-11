"""
Ré-enrichissement de fichiers texte corrigés

Permet de prendre des fichiers texte corrigés manuellement
et de régénérer le format vertical avec TreeTagger.
"""

from pathlib import Path
from typing import List, Optional
import logging

from ..config import Config
from ..models import ExtractedPage, AnnotatedPage
from ..step2_enrich.processor import EnrichmentProcessor
from ..step3_export.scholarly_parser import ScholarlyParser, parse_scholarly_pages

logger = logging.getLogger(__name__)


class ReEnricher:
    """
    Ré-enrichisseur de fichiers texte corrigés

    Workflow:
        1. Parse les fichiers texte au format scholarly (ou clean)
        2. Extrait le texte et les métadonnées
        3. Re-tokenise et re-lemmatise avec TreeTagger
        4. Génère un nouveau fichier vertical

    Usage:
        config = Config.from_yaml("config.yaml")
        reenricher = ReEnricher(config)

        # Depuis un dossier de pages corrigées
        pages = reenricher.reenrich_folder("./pages_corrigees/")
        reenricher.save_vertical(pages, "corpus_corrige.vertical.txt")

        # Depuis le fichier texte_complet.txt corrigé
        pages = reenricher.reenrich_combined("./texte_complet_corrige.txt")
        reenricher.save_vertical(pages, "corpus_corrige.vertical.txt")
    """

    def __init__(self, config: Config):
        """
        Args:
            config: Configuration du pipeline
        """
        self.config = config
        self.parser = ScholarlyParser()
        self.processor = EnrichmentProcessor(config)

        self._reenriched_count = 0
        self._error_count = 0

    def reenrich_folder(
        self,
        folder_path: str | Path,
        pattern: str = "*.txt"
    ) -> List[AnnotatedPage]:
        """
        Ré-enrichit un dossier de fichiers texte corrigés

        Args:
            folder_path: Dossier contenant les fichiers texte
            pattern: Pattern de fichiers à traiter

        Returns:
            Liste de AnnotatedPage
        """
        logger.info(f"Ré-enrichissement depuis {folder_path}")

        # Parse les fichiers
        extracted_pages = self.parser.parse_folder(folder_path, pattern)

        if not extracted_pages:
            logger.warning("Aucune page trouvée à ré-enrichir")
            return []

        # Ré-enrichit les pages
        return self._reenrich_pages(extracted_pages)

    def reenrich_combined(self, file_path: str | Path) -> List[AnnotatedPage]:
        """
        Ré-enrichit depuis un fichier texte_complet.txt corrigé

        Args:
            file_path: Chemin vers le fichier combiné

        Returns:
            Liste de AnnotatedPage
        """
        logger.info(f"Ré-enrichissement depuis {file_path}")

        # Parse le fichier combiné
        extracted_pages = self.parser.parse_combined_file(file_path)

        if not extracted_pages:
            logger.warning("Aucune page trouvée à ré-enrichir")
            return []

        # Ré-enrichit les pages
        return self._reenrich_pages(extracted_pages)

    def reenrich_from_pages(
        self,
        pages: List[ExtractedPage]
    ) -> List[AnnotatedPage]:
        """
        Ré-enrichit depuis une liste de ExtractedPage

        Args:
            pages: Liste de pages extraites

        Returns:
            Liste de AnnotatedPage
        """
        return self._reenrich_pages(pages)

    def _reenrich_pages(
        self,
        pages: List[ExtractedPage]
    ) -> List[AnnotatedPage]:
        """
        Ré-enrichit une liste de pages

        Args:
            pages: Liste de ExtractedPage

        Returns:
            Liste de AnnotatedPage
        """
        logger.info(f"Ré-enrichissement de {len(pages)} pages...")

        annotated_pages = []

        for page in pages:
            try:
                # Utilise le processeur d'enrichissement standard
                annotated = self.processor.process_page(page)
                annotated_pages.append(annotated)
                self._reenriched_count += 1

            except Exception as e:
                logger.error(f"Erreur sur la page {page.metadata.folio}: {e}")
                self._error_count += 1

        logger.info(
            f"Ré-enrichissement terminé: {len(annotated_pages)} pages, "
            f"{self._error_count} erreurs"
        )

        return annotated_pages

    def save_vertical(
        self,
        pages: List[AnnotatedPage],
        output_path: str | Path
    ) -> None:
        """
        Sauvegarde les pages ré-enrichies en format vertical

        Args:
            pages: Liste de pages annotées
            output_path: Chemin de sortie
        """
        self.processor.save_vertical(pages, output_path)

    def reenrich_and_save(
        self,
        input_path: str | Path,
        output_path: str | Path,
        pattern: str = "*.txt"
    ) -> List[AnnotatedPage]:
        """
        Ré-enrichit et sauvegarde en une seule opération

        Args:
            input_path: Dossier ou fichier d'entrée
            output_path: Chemin de sortie vertical
            pattern: Pattern pour les fichiers (si dossier)

        Returns:
            Liste de pages annotées
        """
        input_path = Path(input_path)

        if input_path.is_file():
            pages = self.reenrich_combined(input_path)
        else:
            pages = self.reenrich_folder(input_path, pattern)

        self.save_vertical(pages, output_path)
        return pages

    @property
    def reenriched_count(self) -> int:
        """Nombre de pages ré-enrichies"""
        return self._reenriched_count

    @property
    def error_count(self) -> int:
        """Nombre d'erreurs"""
        return self._error_count

    def reset_stats(self) -> None:
        """Réinitialise les statistiques"""
        self._reenriched_count = 0
        self._error_count = 0


def reenrich_from_text(
    input_path: str | Path,
    output_path: str | Path,
    config: Optional[Config] = None,
    pattern: str = "*.txt"
) -> List[AnnotatedPage]:
    """
    Fonction utilitaire pour ré-enrichir depuis des fichiers texte

    Args:
        input_path: Dossier ou fichier d'entrée
        output_path: Chemin de sortie vertical
        config: Configuration optionnelle
        pattern: Pattern pour les fichiers (si dossier)

    Returns:
        Liste de pages annotées

    Example:
        >>> from PAGEtopage.step4_reenrich import reenrich_from_text
        >>> from PAGEtopage.config import Config
        >>>
        >>> config = Config.from_yaml("config.yaml")
        >>> pages = reenrich_from_text(
        ...     "./pages_corrigees/",
        ...     "./corpus_corrige.vertical.txt",
        ...     config
        ... )
    """
    if config is None:
        config = Config()

    reenricher = ReEnricher(config)
    return reenricher.reenrich_and_save(input_path, output_path, pattern)
