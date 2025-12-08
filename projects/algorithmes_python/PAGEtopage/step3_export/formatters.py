"""
Formateurs de texte pour l'export

Fournit différents formats de sortie pour les pages annotées.
"""

from abc import ABC, abstractmethod
from typing import List
from ..models import AnnotatedPage, Sentence, Token


class TextFormatter(ABC):
    """
    Classe abstraite pour les formateurs de texte

    Chaque formateur implémente une façon différente de
    représenter le texte annoté.
    """

    @abstractmethod
    def format_page(self, page: AnnotatedPage) -> str:
        """
        Formate une page annotée

        Args:
            page: Page annotée

        Returns:
            Texte formaté
        """
        pass

    @abstractmethod
    def format_sentence(self, sentence: Sentence) -> str:
        """
        Formate une sentence

        Args:
            sentence: Sentence annotée

        Returns:
            Texte formaté
        """
        pass

    def get_extension(self) -> str:
        """Retourne l'extension de fichier recommandée"""
        return ".txt"


class CleanFormatter(TextFormatter):
    """
    Format clean : texte brut sans annotations

    Produit un texte lisible avec uniquement les mots,
    la ponctuation attachée aux mots.

    Exemple:
        "Dominus enim dicit in evangelio."
    """

    def __init__(self, include_punctuation: bool = True):
        """
        Args:
            include_punctuation: Inclure la ponctuation
        """
        self.include_punctuation = include_punctuation

    def format_page(self, page: AnnotatedPage) -> str:
        """Formate une page en texte clean"""
        if page.is_empty:
            return ""

        sentences = []
        for sentence in page.sentences:
            formatted = self.format_sentence(sentence)
            if formatted:
                sentences.append(formatted)

        return " ".join(sentences)

    def format_sentence(self, sentence: Sentence) -> str:
        """Formate une sentence en texte clean"""
        words = []

        for i, token in enumerate(sentence.tokens):
            if token.pos == "PUNCT":
                if self.include_punctuation:
                    # Attache la ponctuation au mot précédent
                    if words:
                        words[-1] += token.word
                    else:
                        words.append(token.word)
            else:
                words.append(token.word)

        return " ".join(words)


class DiplomaticFormatter(TextFormatter):
    """
    Format diplomatic : texte avec annotations POS inline

    Produit un texte avec chaque mot suivi de son POS et lemme
    entre parenthèses.

    Exemple:
        "Dominus(NOM→dominus) enim(ADV→enim) dicit(VER→dico)."
    """

    def __init__(
        self,
        show_lemma: bool = True,
        separator: str = "→"
    ):
        """
        Args:
            show_lemma: Inclure le lemme
            separator: Séparateur entre POS et lemme
        """
        self.show_lemma = show_lemma
        self.separator = separator

    def format_page(self, page: AnnotatedPage) -> str:
        """Formate une page en format diplomatic"""
        if page.is_empty:
            return ""

        sentences = []
        for sentence in page.sentences:
            formatted = self.format_sentence(sentence)
            if formatted:
                sentences.append(formatted)

        return " ".join(sentences)

    def format_sentence(self, sentence: Sentence) -> str:
        """Formate une sentence en format diplomatic"""
        parts = []

        for token in sentence.tokens:
            if token.pos == "PUNCT":
                # Ponctuation sans annotation
                if parts:
                    parts[-1] += token.word
                else:
                    parts.append(token.word)
            else:
                if self.show_lemma:
                    annotation = f"({token.pos}{self.separator}{token.lemma})"
                else:
                    annotation = f"({token.pos})"
                parts.append(f"{token.word}{annotation}")

        return " ".join(parts)


class AnnotatedFormatter(TextFormatter):
    """
    Format annotated : format tabulaire

    Produit un format tabulaire avec une ligne par token :
        word\\tPOS\\tlemma

    Exemple:
        Dominus	NOM	dominus
        enim	ADV	enim
        dicit	VER	dico
    """

    def __init__(
        self,
        include_sentence_markers: bool = True,
        separator: str = "\t"
    ):
        """
        Args:
            include_sentence_markers: Inclure <s> et </s>
            separator: Séparateur de colonnes
        """
        self.include_sentence_markers = include_sentence_markers
        self.separator = separator

    def format_page(self, page: AnnotatedPage) -> str:
        """Formate une page en format tabulaire"""
        if page.is_empty:
            return ""

        lines = []
        for sentence in page.sentences:
            formatted = self.format_sentence(sentence)
            if formatted:
                lines.append(formatted)

        return "\n".join(lines)

    def format_sentence(self, sentence: Sentence) -> str:
        """Formate une sentence en format tabulaire"""
        lines = []

        if self.include_sentence_markers:
            lines.append("<s>")

        for token in sentence.tokens:
            line = self.separator.join([token.word, token.pos, token.lemma])
            lines.append(line)

        if self.include_sentence_markers:
            lines.append("</s>")

        return "\n".join(lines)

    def get_extension(self) -> str:
        return ".tsv"


class VerticalFormatter(TextFormatter):
    """
    Format vertical : format complet avec balises <doc>

    Reproduit le format vertical standard avec toutes les métadonnées.

    Exemple:
        <doc folio="0042.xml" page_number="1" ...>
        <s>
        Dominus	NOM	dominus
        </s>
        </doc>
    """

    def format_page(self, page: AnnotatedPage) -> str:
        """Formate une page en format vertical complet"""
        return page.to_vertical()

    def format_sentence(self, sentence: Sentence) -> str:
        """Formate une sentence en format vertical"""
        return sentence.to_vertical()

    def get_extension(self) -> str:
        return ".vertical.txt"


def create_formatter(format_type: str) -> TextFormatter:
    """
    Factory pour créer un formateur

    Args:
        format_type: "clean", "diplomatic", "annotated", ou "vertical"

    Returns:
        Instance de TextFormatter
    """
    formatters = {
        "clean": CleanFormatter,
        "diplomatic": DiplomaticFormatter,
        "annotated": AnnotatedFormatter,
        "vertical": VerticalFormatter,
    }

    if format_type not in formatters:
        raise ValueError(
            f"Format inconnu: {format_type}. "
            f"Formats disponibles: {list(formatters.keys())}"
        )

    return formatters[format_type]()
