"""
Parser pour le format scholarly

Parse les fichiers au format scholarly pour extraire les métadonnées
et le texte, permettant le ré-enrichissement après correction manuelle.
"""

from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re
import logging

from ..models import ExtractedPage, PageMetadata

logger = logging.getLogger(__name__)


class ScholarlyParser:
    """
    Parser pour le format scholarly

    Extrait les métadonnées et le texte depuis les fichiers au format scholarly
    pour permettre le ré-enrichissement après correction manuelle.

    Format attendu:
        ================================================================================
        PAGE 79
        Source: manuscript.xml
        Image: manuscript.jpg
        Titre courant: DISTINCTIO OCTOGESIMA
        Œuvre: Summa 'Induent sancti'
        Auteur: Anonyme
        Date: 1194
        ================================================================================
        [texte de la page...]

    Usage:
        parser = ScholarlyParser()
        pages = parser.parse_folder("./pages_corrigees/")
    """

    # Pattern pour détecter le séparateur
    SEPARATOR_PATTERN = re.compile(r'^={40,}\s*$')

    # Patterns pour extraire les métadonnées
    METADATA_PATTERNS = {
        'page_number': re.compile(r'^PAGE\s+(\d+)\s*$', re.IGNORECASE),
        'folio': re.compile(r'^Source:\s*(.+?)\s*$', re.IGNORECASE),
        'image': re.compile(r'^Image:\s*(.+?)\s*$', re.IGNORECASE),
        'running_title': re.compile(r'^Titre courant:\s*(.+?)\s*$', re.IGNORECASE),
        'edition_id': re.compile(r'^Edition ID:\s*(.+?)\s*$', re.IGNORECASE),
        'title': re.compile(r'^Œuvre:\s*(.+?)\s*$', re.IGNORECASE),
        'author': re.compile(r'^Auteur:\s*(.+?)\s*$', re.IGNORECASE),
        'date': re.compile(r'^Date:\s*(.+?)\s*$', re.IGNORECASE),
        'language': re.compile(r'^Langue:\s*(.+?)\s*$', re.IGNORECASE),
        'source': re.compile(r'^Provenance:\s*(.+?)\s*$', re.IGNORECASE),
        'type': re.compile(r'^Type:\s*(.+?)\s*$', re.IGNORECASE),
        'lieu': re.compile(r'^Lieu:\s*(.+?)\s*$', re.IGNORECASE),
        'ville': re.compile(r'^Ville:\s*(.+?)\s*$', re.IGNORECASE),
    }

    def parse_file(self, file_path: str | Path) -> Optional[ExtractedPage]:
        """
        Parse un fichier scholarly

        Args:
            file_path: Chemin vers le fichier

        Returns:
            ExtractedPage ou None si le parsing échoue
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"Fichier non trouvé: {file_path}")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return self.parse_content(content)

        except Exception as e:
            logger.error(f"Erreur lors du parsing de {file_path}: {e}")
            return None

    def parse_content(self, content: str) -> Optional[ExtractedPage]:
        """
        Parse le contenu d'un fichier scholarly

        Args:
            content: Contenu du fichier

        Returns:
            ExtractedPage ou None si le parsing échoue
        """
        lines = content.split('\n')

        # Recherche l'en-tête
        metadata, text_start = self._parse_header(lines)

        if metadata is None:
            logger.warning("Impossible de parser l'en-tête")
            return None

        # Extrait le texte
        text_lines = self._extract_text(lines[text_start:])

        # Crée la PageMetadata
        # Construit le dictionnaire corpus_metadata avec TOUTES les métadonnées disponibles
        corpus_metadata = {}
        for key in ['edition_id', 'title', 'author', 'date', 'language', 'source', 'type', 'lieu', 'ville']:
            if key in metadata and metadata[key]:
                corpus_metadata[key] = metadata[key]

        # Ajoute toute autre métadonnée qui n'est pas dans la liste standard
        for key, value in metadata.items():
            if key not in ['page_number', 'folio', 'image', 'running_title'] and key not in corpus_metadata and value:
                corpus_metadata[key] = value

        page_metadata = PageMetadata(
            folio=metadata.get('folio', 'unknown.xml'),
            page_number=metadata.get('page_number', 0),
            running_title=metadata.get('running_title', 'No running title'),
            corpus_metadata=corpus_metadata
        )

        return ExtractedPage(
            metadata=page_metadata,
            lines=text_lines,
            is_empty=len(text_lines) == 0
        )

    def _parse_header(self, lines: List[str]) -> Tuple[Optional[Dict[str, any]], int]:
        """
        Parse l'en-tête scholarly

        Args:
            lines: Lignes du fichier

        Returns:
            Tuple (métadonnées dict, index de début du texte)
        """
        metadata = {}
        separator_count = 0
        text_start = 0

        for i, line in enumerate(lines):
            # Détecte les séparateurs
            if self.SEPARATOR_PATTERN.match(line):
                separator_count += 1
                if separator_count == 2:
                    # Fin de l'en-tête
                    text_start = i + 1
                    break
                continue

            # Parse les métadonnées
            if separator_count == 1:
                for key, pattern in self.METADATA_PATTERNS.items():
                    match = pattern.match(line)
                    if match:
                        value = match.group(1).strip()
                        if key == 'page_number':
                            metadata[key] = int(value)
                        else:
                            metadata[key] = value
                        break

        # Vérifie qu'on a au moins trouvé les séparateurs
        if separator_count < 2:
            return None, 0

        return metadata, text_start

    def _extract_text(self, lines: List[str]) -> List[str]:
        """
        Extrait le texte après l'en-tête

        Args:
            lines: Lignes après l'en-tête

        Returns:
            Liste de lignes de texte (avec sauts de ligne logiques préservés)
        """
        # Filtre les lignes vides au début et à la fin
        text_lines = [line.rstrip() for line in lines]

        # Retire les lignes vides au début
        while text_lines and not text_lines[0]:
            text_lines.pop(0)

        # Retire les lignes vides à la fin
        while text_lines and not text_lines[-1]:
            text_lines.pop()

        # Reconstruit le texte en une seule ligne (le format scholarly a des retours à la ligne artificiels)
        # On rejoint tout en un seul paragraphe
        text = ' '.join(line for line in text_lines if line)

        # Retourne comme une seule "ligne" pour le traitement
        return [text] if text else []

    def parse_folder(
        self,
        folder_path: str | Path,
        pattern: str = "*.txt"
    ) -> List[ExtractedPage]:
        """
        Parse tous les fichiers scholarly d'un dossier

        Args:
            folder_path: Dossier contenant les fichiers
            pattern: Pattern de fichiers à parser

        Returns:
            Liste de ExtractedPage
        """
        folder_path = Path(folder_path)

        if not folder_path.exists():
            logger.error(f"Dossier non trouvé: {folder_path}")
            return []

        pages = []
        files = sorted(folder_path.glob(pattern))

        logger.info(f"Parsing de {len(files)} fichiers depuis {folder_path}")

        for file_path in files:
            page = self.parse_file(file_path)
            if page:
                pages.append(page)
            else:
                logger.warning(f"Échec du parsing: {file_path}")

        logger.info(f"Parsé {len(pages)} pages avec succès")
        return pages

    def parse_combined_file(self, file_path: str | Path) -> List[ExtractedPage]:
        """
        Parse un fichier texte_complet.txt qui contient plusieurs pages

        Args:
            file_path: Chemin vers le fichier combiné

        Returns:
            Liste de ExtractedPage
        """
        file_path = Path(file_path)

        if not file_path.exists():
            logger.error(f"Fichier non trouvé: {file_path}")
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Sépare les pages (séparées par deux lignes vides minimum)
            page_contents = re.split(r'\n\s*\n(?==)', content)

            pages = []
            for page_content in page_contents:
                if not page_content.strip():
                    continue

                page = self.parse_content(page_content)
                if page:
                    pages.append(page)

            logger.info(f"Parsé {len(pages)} pages depuis {file_path}")
            return pages

        except Exception as e:
            logger.error(f"Erreur lors du parsing de {file_path}: {e}")
            return []


def parse_scholarly_pages(
    input_path: str | Path,
    pattern: str = "*.txt"
) -> List[ExtractedPage]:
    """
    Fonction utilitaire pour parser des pages scholarly

    Args:
        input_path: Dossier ou fichier à parser
        pattern: Pattern pour les fichiers (si input_path est un dossier)

    Returns:
        Liste de ExtractedPage
    """
    parser = ScholarlyParser()
    input_path = Path(input_path)

    if input_path.is_file():
        # Fichier unique (probablement texte_complet.txt)
        if "complet" in input_path.name.lower():
            return parser.parse_combined_file(input_path)
        else:
            page = parser.parse_file(input_path)
            return [page] if page else []
    else:
        # Dossier
        return parser.parse_folder(input_path, pattern)
