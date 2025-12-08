"""
Processeur d'enrichissement principal

Orchestre la tokenisation, lemmatisation et génération du format vertical.
"""

from pathlib import Path
from typing import List, Iterator, Optional
import logging
import json

from ..config import Config
from ..models import (
    ExtractedPage, ExtractedCorpus,
    AnnotatedPage, AnnotatedCorpus,
    Token, Sentence, PageMetadata
)
from .tokenizer import Tokenizer
from .lemmatizer import CLTKLemmatizer, SimpleLemmatizer, create_lemmatizer

logger = logging.getLogger(__name__)


class EnrichmentProcessor:
    """
    Processeur d'enrichissement linguistique

    Transforme les pages extraites (étape 1) en pages annotées
    avec lemmatisation et POS tagging.

    Entrée:
        - ExtractedPage ou fichier JSON (sortie étape 1)

    Sortie:
        - AnnotatedPage avec sentences et tokens
        - Fichier au format vertical

    Usage:
        config = Config.from_yaml("config.yaml")
        processor = EnrichmentProcessor(config)

        # Depuis des pages extraites
        annotated = processor.process_pages(extracted_pages)

        # Depuis un fichier JSON
        annotated = processor.process_json("extracted.json")

        # Sauvegarde en format vertical
        processor.save_vertical(annotated, "corpus.vertical.txt")
    """

    def __init__(self, config: Config):
        """
        Args:
            config: Configuration du pipeline
        """
        self.config = config

        # Initialise le tokenizer
        self.tokenizer = Tokenizer(
            sentence_delimiters=config.enrichment.sentence_delimiters
        )

        # Initialise le lemmatiseur
        self.lemmatizer = create_lemmatizer(
            backend=config.enrichment.lemmatizer,
            language=config.enrichment.language
        )

        self._processed_count = 0
        self._error_count = 0

    def process_pages(
        self,
        pages: List[ExtractedPage]
    ) -> List[AnnotatedPage]:
        """
        Enrichit une liste de pages extraites

        Args:
            pages: Liste de ExtractedPage

        Returns:
            Liste de AnnotatedPage
        """
        logger.info(f"Enrichissement de {len(pages)} pages...")

        annotated_pages = []
        for page in pages:
            try:
                annotated = self.process_page(page)
                annotated_pages.append(annotated)
            except Exception as e:
                logger.error(f"Erreur sur la page {page.metadata.folio}: {e}")
                self._error_count += 1

        logger.info(
            f"Enrichissement terminé: {len(annotated_pages)} pages, "
            f"{self._error_count} erreurs"
        )

        return annotated_pages

    def process_page(self, page: ExtractedPage) -> AnnotatedPage:
        """
        Enrichit une page extraite

        Args:
            page: ExtractedPage

        Returns:
            AnnotatedPage
        """
        logger.debug(f"Enrichissement de {page.metadata.folio}")

        if page.is_empty:
            return AnnotatedPage(
                metadata=page.metadata,
                sentences=[],
                is_empty=True
            )

        # Concatène les lignes
        text = " ".join(page.lines)

        # Tokenise en phrases
        sentence_tokens = self.tokenizer.tokenize_text(text)

        # Lemmatise et crée les sentences
        sentences = []
        for i, tokens in enumerate(sentence_tokens):
            sentence = self._create_sentence(tokens, sentence_id=i + 1)
            sentences.append(sentence)

        self._processed_count += 1

        return AnnotatedPage(
            metadata=page.metadata,
            sentences=sentences,
        )

    def _create_sentence(
        self,
        tokens: List[str],
        sentence_id: int
    ) -> Sentence:
        """
        Crée une Sentence annotée

        Args:
            tokens: Liste de tokens bruts
            sentence_id: ID de la phrase

        Returns:
            Sentence avec tokens lemmatisés
        """
        # Lemmatise les tokens
        lemmatized = self.lemmatizer.lemmatize_tokens(tokens)

        # Convertit en Token
        result_tokens = []
        for lt in lemmatized:
            result_tokens.append(Token(
                word=lt.word,
                pos=lt.pos,
                lemma=lt.lemma,
            ))

        return Sentence(tokens=result_tokens, id=sentence_id)

    def process_json(self, json_path: str | Path) -> List[AnnotatedPage]:
        """
        Enrichit depuis un fichier JSON (sortie étape 1)

        Args:
            json_path: Chemin vers le fichier JSON

        Returns:
            Liste de AnnotatedPage
        """
        json_path = Path(json_path)

        if not json_path.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {json_path}")

        # Charge le corpus extrait
        corpus = ExtractedCorpus.load(json_path)

        return self.process_pages(corpus.pages)

    def process_json_folder(self, folder_path: str | Path) -> List[AnnotatedPage]:
        """
        Enrichit depuis un dossier de fichiers JSON

        Args:
            folder_path: Dossier contenant les JSON

        Returns:
            Liste de AnnotatedPage
        """
        folder_path = Path(folder_path)

        if not folder_path.exists():
            raise FileNotFoundError(f"Dossier non trouvé: {folder_path}")

        # Charge les fichiers JSON individuels
        json_files = sorted(folder_path.glob("*.json"))
        pages = []

        for json_file in json_files:
            page = ExtractedPage.load(json_file)
            pages.append(page)

        return self.process_pages(pages)

    def save_vertical(
        self,
        pages: List[AnnotatedPage],
        output_path: str | Path
    ) -> None:
        """
        Sauvegarde en format vertical

        Args:
            pages: Liste de pages annotées
            output_path: Chemin de sortie
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        corpus = AnnotatedCorpus(pages=pages)
        corpus.save_vertical(output_path)

        logger.info(f"Sauvegardé {len(pages)} pages en format vertical dans {output_path}")

    def process_and_save(
        self,
        input_path: str | Path,
        output_path: str | Path,
        input_type: str = "json"
    ) -> List[AnnotatedPage]:
        """
        Enrichit et sauvegarde en une seule opération

        Args:
            input_path: Chemin d'entrée (JSON ou dossier)
            output_path: Chemin de sortie vertical
            input_type: "json" pour fichier unique, "folder" pour dossier

        Returns:
            Liste de pages annotées
        """
        if input_type == "json":
            pages = self.process_json(input_path)
        else:
            pages = self.process_json_folder(input_path)

        self.save_vertical(pages, output_path)
        return pages

    @property
    def processed_count(self) -> int:
        """Nombre de pages traitées"""
        return self._processed_count

    @property
    def error_count(self) -> int:
        """Nombre d'erreurs"""
        return self._error_count

    def reset_stats(self) -> None:
        """Réinitialise les statistiques"""
        self._processed_count = 0
        self._error_count = 0


def enrich_corpus(
    input_path: str | Path,
    output_path: str | Path,
    config: Optional[Config] = None
) -> List[AnnotatedPage]:
    """
    Fonction utilitaire pour enrichir un corpus

    Args:
        input_path: Chemin vers le JSON ou dossier d'entrée
        output_path: Chemin de sortie vertical
        config: Configuration optionnelle

    Returns:
        Liste de pages annotées
    """
    if config is None:
        config = Config()

    processor = EnrichmentProcessor(config)

    input_path = Path(input_path)
    if input_path.is_file():
        pages = processor.process_json(input_path)
    else:
        pages = processor.process_json_folder(input_path)

    processor.save_vertical(pages, output_path)
    return pages
