"""
Tokenisation et segmentation en phrases

Segmente le texte en phrases et tokens pour le traitement linguistique.
"""

import re
from typing import List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class RawToken:
    """Token brut avant lemmatisation"""
    text: str
    is_punctuation: bool = False


class Tokenizer:
    """
    Tokeniseur pour textes latins (et autres langues)

    Segmente le texte en phrases et tokens, en préservant la ponctuation
    comme tokens séparés.

    Exemple:
        tokenizer = Tokenizer()
        sentences = tokenizer.tokenize_text("Dominus dicit. Amen.")
        # [["Dominus", "dicit", "."], ["Amen", "."]]
    """

    # Ponctuation de fin de phrase
    DEFAULT_SENTENCE_DELIMITERS = [".", "?", "!", ";"]

    # Ponctuation à séparer comme tokens
    PUNCTUATION_PATTERN = re.compile(r'([.,;:!?\(\)\[\]«»""\'„‟⁊])')

    # Pattern pour nettoyer les espaces multiples
    MULTI_SPACE = re.compile(r'\s+')

    def __init__(
        self,
        sentence_delimiters: List[str] = None,
        preserve_case: bool = True
    ):
        """
        Args:
            sentence_delimiters: Caractères de fin de phrase
            preserve_case: Préserver la casse originale
        """
        self.sentence_delimiters = sentence_delimiters or self.DEFAULT_SENTENCE_DELIMITERS
        self.preserve_case = preserve_case

        # Crée le pattern de fin de phrase
        escaped = [re.escape(d) for d in self.sentence_delimiters]
        self._sentence_end_pattern = re.compile(f"[{''.join(escaped)}]")

    def tokenize_text(self, text: str) -> List[List[str]]:
        """
        Tokenise un texte en phrases et tokens

        Args:
            text: Texte à tokeniser

        Returns:
            Liste de phrases, chaque phrase étant une liste de tokens
        """
        if not text or not text.strip():
            return []

        # Normalise les espaces
        text = self.MULTI_SPACE.sub(" ", text.strip())

        # Segmente en phrases
        sentences = self._segment_sentences(text)

        # Tokenise chaque phrase
        result = []
        for sentence in sentences:
            tokens = self._tokenize_sentence(sentence)
            if tokens:
                result.append(tokens)

        return result

    def tokenize_lines(self, lines: List[str]) -> List[List[str]]:
        """
        Tokenise une liste de lignes

        Args:
            lines: Liste de lignes de texte

        Returns:
            Liste de phrases tokenisées
        """
        # Concatène les lignes en un seul texte
        text = " ".join(line.strip() for line in lines if line.strip())
        return self.tokenize_text(text)

    def _segment_sentences(self, text: str) -> List[str]:
        """
        Segmente le texte en phrases

        Args:
            text: Texte à segmenter

        Returns:
            Liste de phrases
        """
        sentences = []
        current = []

        # Sépare la ponctuation pour analyse
        tokens = self.PUNCTUATION_PATTERN.sub(r' \1 ', text).split()

        for token in tokens:
            current.append(token)

            # Vérifie si c'est une fin de phrase
            if token in self.sentence_delimiters:
                sentence = " ".join(current).strip()
                if sentence:
                    sentences.append(sentence)
                current = []

        # Ajoute la dernière phrase si non terminée
        if current:
            sentence = " ".join(current).strip()
            if sentence:
                sentences.append(sentence)

        return sentences

    def _tokenize_sentence(self, sentence: str) -> List[str]:
        """
        Tokenise une phrase en mots

        Args:
            sentence: Phrase à tokeniser

        Returns:
            Liste de tokens
        """
        # Sépare la ponctuation
        tokenized = self.PUNCTUATION_PATTERN.sub(r' \1 ', sentence)

        # Split et filtre les vides
        tokens = [t.strip() for t in tokenized.split() if t.strip()]

        if not self.preserve_case:
            tokens = [t.lower() for t in tokens]

        return tokens

    def get_raw_tokens(self, text: str) -> List[List[RawToken]]:
        """
        Retourne les tokens avec métadonnées

        Args:
            text: Texte à tokeniser

        Returns:
            Liste de phrases avec RawToken
        """
        sentences = self.tokenize_text(text)
        result = []

        for sentence in sentences:
            raw_tokens = []
            for token in sentence:
                is_punct = bool(self.PUNCTUATION_PATTERN.fullmatch(token))
                raw_tokens.append(RawToken(text=token, is_punctuation=is_punct))
            result.append(raw_tokens)

        return result

    def is_punctuation(self, token: str) -> bool:
        """Vérifie si le token est de la ponctuation"""
        return bool(self.PUNCTUATION_PATTERN.fullmatch(token))


def tokenize(text: str, sentence_delimiters: List[str] = None) -> List[List[str]]:
    """
    Fonction utilitaire pour tokeniser un texte

    Args:
        text: Texte à tokeniser
        sentence_delimiters: Délimiteurs de phrase optionnels

    Returns:
        Liste de phrases tokenisées
    """
    tokenizer = Tokenizer(sentence_delimiters=sentence_delimiters)
    return tokenizer.tokenize_text(text)
