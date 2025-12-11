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


class ScholarlyFormatter(TextFormatter):
    """
    Format scholarly : format avec en-tête détaillé et texte continu

    Produit des pages avec un en-tête complet contenant toutes les métadonnées
    et le texte en lignes continues (comme dans un livre imprimé).

    Exemple:
        ================================================================================
        PAGE 79
        Source: manuscript_page_109.xml
        Image: manuscript_page_109.jpg
        Titre courant: DISTINCTIO OCTOGESIMA
        Œuvre: Summa 'Induent sancti'
        Auteur: Anonyme
        Date: 1194
        ================================================================================
        catum susceperit biennio in lectoratu erit, et sequenti quinquennio...
    """

    def __init__(
        self,
        header_width: int = 80,
        include_punctuation: bool = True,
        line_width: int = 80
    ):
        """
        Args:
            header_width: Largeur de la ligne de séparation
            include_punctuation: Inclure la ponctuation
            line_width: Largeur maximale des lignes de texte (0 = pas de limite)
        """
        self.header_width = header_width
        self.include_punctuation = include_punctuation
        self.line_width = line_width

    def format_page(self, page: AnnotatedPage) -> str:
        """Formate une page avec en-tête scholarly"""
        if page.is_empty:
            return ""

        # Génère l'en-tête
        header = self._format_header(page)

        # Génère le texte
        text = self._format_text(page)

        # Combine
        return f"{header}\n{text}"

    def _format_header(self, page: AnnotatedPage) -> str:
        """Génère l'en-tête de la page"""
        separator = "=" * self.header_width
        lines = [separator]

        # Numéro de page
        lines.append(f"PAGE {page.metadata.page_number}")

        # Source (nom du fichier XML)
        lines.append(f"Source: {page.metadata.folio}")

        # Image (déduit du nom du fichier XML)
        from pathlib import Path
        image_name = Path(page.metadata.folio).stem + ".jpg"
        lines.append(f"Image: {image_name}")

        # Titre courant
        if page.metadata.running_title and page.metadata.running_title != "No running title":
            lines.append(f"Titre courant: {page.metadata.running_title}")

        # Métadonnées du corpus (TOUTES les métadonnées, dans un ordre cohérent)
        corpus_meta = page.metadata.corpus_metadata

        # Ordre préféré des métadonnées
        metadata_labels = {
            "edition_id": "Edition ID",
            "title": "Œuvre",
            "author": "Auteur",
            "date": "Date",
            "language": "Langue",
            "source": "Provenance",
            "type": "Type",
            "lieu": "Lieu",
            "ville": "Ville",
        }

        # Affiche les métadonnées dans l'ordre préféré
        for key, label in metadata_labels.items():
            if corpus_meta.get(key):
                lines.append(f"{label}: {corpus_meta[key]}")

        # Ajoute toute métadonnée supplémentaire non listée
        for key, value in corpus_meta.items():
            if key not in metadata_labels and value:
                # Capitalise la première lettre de la clé pour le label
                label = key.replace("_", " ").title()
                lines.append(f"{label}: {value}")

        # Ligne de séparation finale
        lines.append(separator)

        return "\n".join(lines)

    def _format_text(self, page: AnnotatedPage) -> str:
        """Formate le texte de la page en lignes continues"""
        # Collecte tous les mots
        all_words = []

        for sentence in page.sentences:
            for token in sentence.tokens:
                if token.pos == "PUNCT":
                    if self.include_punctuation:
                        # Attache la ponctuation au mot précédent
                        if all_words:
                            all_words[-1] += token.word
                        else:
                            all_words.append(token.word)
                else:
                    all_words.append(token.word)

        # Crée le texte continu
        text = " ".join(all_words)

        # Si line_width est défini, découpe en lignes
        if self.line_width > 0:
            return self._wrap_text(text, self.line_width)
        else:
            return text

    def _wrap_text(self, text: str, width: int) -> str:
        """Découpe le texte en lignes de largeur maximale"""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            word_length = len(word)

            # Si ajouter ce mot dépasse la largeur
            if current_length + word_length + len(current_line) > width:
                if current_line:  # Finit la ligne actuelle
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = word_length
                else:  # Le mot seul est trop long, on le met quand même
                    lines.append(word)
                    current_length = 0
            else:
                current_line.append(word)
                current_length += word_length

        # Ajoute la dernière ligne
        if current_line:
            lines.append(" ".join(current_line))

        return "\n".join(lines)

    def format_sentence(self, sentence: Sentence) -> str:
        """Formate une sentence en texte clean"""
        words = []

        for token in sentence.tokens:
            if token.pos == "PUNCT":
                if self.include_punctuation:
                    if words:
                        words[-1] += token.word
                    else:
                        words.append(token.word)
            else:
                words.append(token.word)

        return " ".join(words)


def create_formatter(format_type: str) -> TextFormatter:
    """
    Factory pour créer un formateur

    Args:
        format_type: "clean", "diplomatic", "annotated", "vertical", ou "scholarly"

    Returns:
        Instance de TextFormatter
    """
    formatters = {
        "clean": CleanFormatter,
        "diplomatic": DiplomaticFormatter,
        "annotated": AnnotatedFormatter,
        "vertical": VerticalFormatter,
        "scholarly": ScholarlyFormatter,
    }

    if format_type not in formatters:
        raise ValueError(
            f"Format inconnu: {format_type}. "
            f"Formats disponibles: {list(formatters.keys())}"
        )

    return formatters[format_type]()
