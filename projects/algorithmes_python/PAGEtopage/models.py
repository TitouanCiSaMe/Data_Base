"""
Modèles de données pour le pipeline PAGEtopage

Définit les structures de données utilisées entre les étapes du pipeline.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json
from pathlib import Path


@dataclass
class PageMetadata:
    """
    Métadonnées d'une page

    Attributs:
        folio: Nom du fichier XML source (ex: "0042_1.xml")
        page_number: Numéro de page dans le document
        running_title: Titre courant extrait de la zone RunningTitle
        corpus_metadata: Métadonnées du corpus (edition_id, author, etc.)
    """
    folio: str
    page_number: int
    running_title: str = "No running title"
    corpus_metadata: Dict[str, str] = field(default_factory=dict)

    def to_xml_attributes(self) -> str:
        """
        Génère la chaîne d'attributs pour la balise <doc>

        Returns:
            Chaîne d'attributs XML formatée
        """
        # Attributs de base de la page
        attrs = [
            f'folio="{self.folio}"',
            f'page_number="{self.page_number}"',
            f'running_title="{self._escape_xml(self.running_title)}"',
        ]

        # Ajoute les métadonnées du corpus
        for key, value in self.corpus_metadata.items():
            if value:  # N'inclut que les valeurs non vides
                attrs.append(f'{key}="{self._escape_xml(str(value))}"')

        return " ".join(attrs)

    @staticmethod
    def _escape_xml(value: str) -> str:
        """Échappe les caractères spéciaux XML"""
        return (
            value
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour sérialisation JSON"""
        return {
            "folio": self.folio,
            "page_number": self.page_number,
            "running_title": self.running_title,
            "corpus_metadata": self.corpus_metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PageMetadata":
        """Crée une instance depuis un dictionnaire"""
        return cls(
            folio=data["folio"],
            page_number=data["page_number"],
            running_title=data.get("running_title", "No running title"),
            corpus_metadata=data.get("corpus_metadata", {}),
        )


@dataclass
class ExtractedPage:
    """
    Page extraite du XML (sortie de l'étape 1)

    Attributs:
        metadata: Métadonnées de la page
        lines: Lignes de texte brut extraites
        is_empty: True si la page ne contient pas de texte
    """
    metadata: PageMetadata
    lines: List[str]
    is_empty: bool = False

    def __post_init__(self):
        """Calcule is_empty automatiquement"""
        if not self.lines or all(not line.strip() for line in self.lines):
            self.is_empty = True

    def get_full_text(self) -> str:
        """Retourne le texte complet de la page"""
        return "\n".join(self.lines)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour sérialisation JSON"""
        return {
            "metadata": self.metadata.to_dict(),
            "lines": self.lines,
            "is_empty": self.is_empty,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractedPage":
        """Crée une instance depuis un dictionnaire"""
        return cls(
            metadata=PageMetadata.from_dict(data["metadata"]),
            lines=data["lines"],
            is_empty=data.get("is_empty", False),
        )

    def to_json(self) -> str:
        """Sérialise en JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ExtractedPage":
        """Désérialise depuis JSON"""
        return cls.from_dict(json.loads(json_str))

    def save(self, path: Path) -> None:
        """Sauvegarde dans un fichier JSON"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: Path) -> "ExtractedPage":
        """Charge depuis un fichier JSON"""
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_json(f.read())


@dataclass
class Token:
    """
    Un token annoté (mot avec POS et lemme)

    Attributs:
        word: Forme de surface du mot
        pos: Part-of-speech tag
        lemma: Forme lemmatisée
    """
    word: str
    pos: str
    lemma: str

    def to_vertical_line(self) -> str:
        """Formate en ligne verticale (tab-separated)"""
        return f"{self.word}\t{self.pos}\t{self.lemma}"

    def to_dict(self) -> Dict[str, str]:
        """Convertit en dictionnaire"""
        return {
            "word": self.word,
            "pos": self.pos,
            "lemma": self.lemma,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "Token":
        """Crée une instance depuis un dictionnaire"""
        return cls(
            word=data["word"],
            pos=data["pos"],
            lemma=data["lemma"],
        )

    @classmethod
    def from_vertical_line(cls, line: str) -> "Token":
        """Parse une ligne verticale"""
        parts = line.strip().split("\t")
        if len(parts) >= 3:
            return cls(word=parts[0], pos=parts[1], lemma=parts[2])
        elif len(parts) == 2:
            return cls(word=parts[0], pos=parts[1], lemma=parts[0])
        else:
            return cls(word=parts[0], pos="UNK", lemma=parts[0])


@dataclass
class Sentence:
    """
    Une phrase avec ses tokens

    Attributs:
        tokens: Liste des tokens de la phrase
        id: Identifiant de la phrase dans la page
    """
    tokens: List[Token]
    id: int = 0

    def to_vertical(self) -> str:
        """Formate la phrase en format vertical"""
        lines = ["<s>"]
        for token in self.tokens:
            lines.append(token.to_vertical_line())
        lines.append("</s>")
        return "\n".join(lines)

    def get_text(self, include_punctuation: bool = True) -> str:
        """
        Retourne le texte de la phrase

        Args:
            include_punctuation: Inclure la ponctuation

        Returns:
            Texte de la phrase
        """
        words = []
        for token in self.tokens:
            if include_punctuation or token.pos != "PUNCT":
                words.append(token.word)
        return " ".join(words)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "id": self.id,
            "tokens": [t.to_dict() for t in self.tokens],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Sentence":
        """Crée une instance depuis un dictionnaire"""
        return cls(
            id=data.get("id", 0),
            tokens=[Token.from_dict(t) for t in data["tokens"]],
        )


@dataclass
class AnnotatedPage:
    """
    Page annotée en format vertical (sortie de l'étape 2)

    Attributs:
        metadata: Métadonnées de la page
        sentences: Liste des phrases annotées
        is_empty: True si la page ne contient pas de texte
    """
    metadata: PageMetadata
    sentences: List[Sentence]
    is_empty: bool = False

    def __post_init__(self):
        """Calcule is_empty automatiquement"""
        if not self.sentences or all(not s.tokens for s in self.sentences):
            self.is_empty = True

    def to_vertical(self) -> str:
        """
        Formate la page en format vertical complet

        Returns:
            Format vertical avec balise <doc> et attributs
        """
        lines = [f"<doc {self.metadata.to_xml_attributes()}>"]

        if self.is_empty:
            lines.append("")
        else:
            for sentence in self.sentences:
                lines.append(sentence.to_vertical())

        lines.append("</doc>")
        return "\n".join(lines)

    def get_text(self, include_punctuation: bool = True) -> str:
        """Retourne le texte complet de la page"""
        return " ".join(s.get_text(include_punctuation) for s in self.sentences)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            "metadata": self.metadata.to_dict(),
            "sentences": [s.to_dict() for s in self.sentences],
            "is_empty": self.is_empty,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnnotatedPage":
        """Crée une instance depuis un dictionnaire"""
        return cls(
            metadata=PageMetadata.from_dict(data["metadata"]),
            sentences=[Sentence.from_dict(s) for s in data.get("sentences", [])],
            is_empty=data.get("is_empty", False),
        )


@dataclass
class ExtractedCorpus:
    """Collection de pages extraites (pour sérialisation groupée)"""
    pages: List[ExtractedPage]

    def to_json(self) -> str:
        """Sérialise en JSON"""
        return json.dumps(
            {"pages": [p.to_dict() for p in self.pages]},
            ensure_ascii=False,
            indent=2
        )

    @classmethod
    def from_json(cls, json_str: str) -> "ExtractedCorpus":
        """Désérialise depuis JSON"""
        data = json.loads(json_str)
        return cls(pages=[ExtractedPage.from_dict(p) for p in data["pages"]])

    def save(self, path: Path) -> None:
        """Sauvegarde dans un fichier JSON"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_json())

    @classmethod
    def load(cls, path: Path) -> "ExtractedCorpus":
        """Charge depuis un fichier JSON"""
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_json(f.read())


@dataclass
class AnnotatedCorpus:
    """Collection de pages annotées"""
    pages: List[AnnotatedPage]

    def to_vertical(self) -> str:
        """Génère le corpus vertical complet"""
        return "\n\n".join(page.to_vertical() for page in self.pages)

    def save_vertical(self, path: Path) -> None:
        """Sauvegarde le corpus vertical"""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_vertical())

    @classmethod
    def from_vertical_file(cls, path: Path) -> "AnnotatedCorpus":
        """
        Parse un fichier vertical existant

        Args:
            path: Chemin vers le fichier vertical

        Returns:
            AnnotatedCorpus avec les pages parsées
        """
        from .step3_export.vertical_parser import VerticalParser
        parser = VerticalParser()
        return parser.parse_file(path)
