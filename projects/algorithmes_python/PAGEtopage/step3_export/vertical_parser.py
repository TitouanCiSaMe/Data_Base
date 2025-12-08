"""
Parseur de fichiers au format vertical

Parse les fichiers corpus vertical pour extraire les pages et sentences.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Iterator
import logging

from ..models import (
    AnnotatedPage, AnnotatedCorpus,
    PageMetadata, Sentence, Token
)

logger = logging.getLogger(__name__)


class VerticalParser:
    """
    Parse les fichiers au format vertical

    Le format vertical est structuré comme suit:
        <doc folio="..." page_number="..." ...attributs...>
        <s>
        word1   POS1    lemma1
        word2   POS2    lemma2
        </s>
        </doc>

    Usage:
        parser = VerticalParser()
        corpus = parser.parse_file("corpus.vertical.txt")
        for page in corpus.pages:
            print(page.metadata.folio)
    """

    # Pattern pour la balise <doc ...>
    DOC_OPEN_PATTERN = re.compile(r'<doc\s+(.+?)>')
    DOC_CLOSE_PATTERN = re.compile(r'</doc>')

    # Pattern pour les balises <s> et </s>
    SENTENCE_OPEN = "<s>"
    SENTENCE_CLOSE = "</s>"

    # Pattern pour extraire les attributs
    ATTR_PATTERN = re.compile(r'(\w+)="([^"]*)"')

    def __init__(self):
        self._parsed_count = 0

    def parse_file(self, file_path: str | Path) -> AnnotatedCorpus:
        """
        Parse un fichier vertical complet

        Args:
            file_path: Chemin vers le fichier vertical

        Returns:
            AnnotatedCorpus contenant toutes les pages
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Fichier non trouvé: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        return self.parse_content(content)

    def parse_content(self, content: str) -> AnnotatedCorpus:
        """
        Parse le contenu d'un fichier vertical

        Args:
            content: Contenu textuel du fichier

        Returns:
            AnnotatedCorpus
        """
        pages = []
        self._parsed_count = 0

        # Split par </doc> pour obtenir chaque document
        doc_chunks = content.split("</doc>")

        for chunk in doc_chunks:
            chunk = chunk.strip()
            if not chunk:
                continue

            page = self._parse_doc_chunk(chunk)
            if page:
                pages.append(page)
                self._parsed_count += 1

        logger.info(f"Parsé {len(pages)} pages depuis le fichier vertical")
        return AnnotatedCorpus(pages=pages)

    def _parse_doc_chunk(self, chunk: str) -> Optional[AnnotatedPage]:
        """
        Parse un bloc <doc>...</doc>

        Args:
            chunk: Contenu du bloc (sans </doc>)

        Returns:
            AnnotatedPage ou None
        """
        # Trouve la balise d'ouverture <doc ...>
        match = self.DOC_OPEN_PATTERN.search(chunk)
        if not match:
            return None

        # Parse les attributs
        attrs_str = match.group(1)
        attrs = self._parse_attributes(attrs_str)

        # Extrait le contenu après <doc ...>
        content_start = match.end()
        content = chunk[content_start:]

        # Parse les sentences
        sentences = self._parse_sentences(content)

        # Crée les métadonnées
        metadata = self._create_metadata(attrs)

        return AnnotatedPage(
            metadata=metadata,
            sentences=sentences,
            is_empty=len(sentences) == 0
        )

    def _parse_attributes(self, attrs_str: str) -> Dict[str, str]:
        """
        Parse les attributs d'une balise

        Args:
            attrs_str: Chaîne d'attributs (ex: 'folio="test.xml" page_number="1"')

        Returns:
            Dictionnaire des attributs
        """
        attrs = {}
        for match in self.ATTR_PATTERN.finditer(attrs_str):
            key = match.group(1)
            value = match.group(2)
            # Décode les entités XML
            value = self._decode_xml_entities(value)
            attrs[key] = value
        return attrs

    def _decode_xml_entities(self, text: str) -> str:
        """Décode les entités XML"""
        return (
            text
            .replace("&quot;", '"')
            .replace("&apos;", "'")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
            .replace("&amp;", "&")
        )

    def _create_metadata(self, attrs: Dict[str, str]) -> PageMetadata:
        """
        Crée PageMetadata depuis les attributs

        Args:
            attrs: Dictionnaire des attributs

        Returns:
            PageMetadata
        """
        # Attributs de base
        folio = attrs.pop("folio", "unknown.xml")
        page_number = int(attrs.pop("page_number", "0"))
        running_title = attrs.pop("running_title", "No running title")

        # Le reste va dans corpus_metadata
        corpus_metadata = attrs

        return PageMetadata(
            folio=folio,
            page_number=page_number,
            running_title=running_title,
            corpus_metadata=corpus_metadata,
        )

    def _parse_sentences(self, content: str) -> List[Sentence]:
        """
        Parse les sentences depuis le contenu

        Args:
            content: Contenu entre <doc> et </doc>

        Returns:
            Liste de Sentence
        """
        sentences = []
        sentence_id = 0

        # Split par <s> et </s>
        parts = re.split(r'<s>|</s>', content)

        for i, part in enumerate(parts):
            # Les parties impaires sont le contenu des sentences
            if i % 2 == 1:
                sentence_id += 1
                tokens = self._parse_tokens(part)
                if tokens:
                    sentences.append(Sentence(tokens=tokens, id=sentence_id))

        return sentences

    def _parse_tokens(self, content: str) -> List[Token]:
        """
        Parse les tokens depuis le contenu d'une sentence

        Args:
            content: Contenu entre <s> et </s>

        Returns:
            Liste de Token
        """
        tokens = []

        for line in content.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            # Format: word\tPOS\tlemma
            parts = line.split("\t")

            if len(parts) >= 3:
                tokens.append(Token(
                    word=parts[0],
                    pos=parts[1],
                    lemma=parts[2],
                ))
            elif len(parts) == 2:
                tokens.append(Token(
                    word=parts[0],
                    pos=parts[1],
                    lemma=parts[0].lower(),
                ))
            elif len(parts) == 1 and parts[0]:
                tokens.append(Token(
                    word=parts[0],
                    pos="UNK",
                    lemma=parts[0].lower(),
                ))

        return tokens

    def iter_pages(self, file_path: str | Path) -> Iterator[AnnotatedPage]:
        """
        Itère sur les pages d'un fichier (économise la mémoire)

        Args:
            file_path: Chemin vers le fichier

        Yields:
            AnnotatedPage
        """
        corpus = self.parse_file(file_path)
        for page in corpus.pages:
            yield page

    @property
    def parsed_count(self) -> int:
        """Nombre de pages parsées"""
        return self._parsed_count


def parse_vertical_file(file_path: str | Path) -> AnnotatedCorpus:
    """
    Fonction utilitaire pour parser un fichier vertical

    Args:
        file_path: Chemin vers le fichier

    Returns:
        AnnotatedCorpus
    """
    parser = VerticalParser()
    return parser.parse_file(file_path)
