"""
Configuration du pipeline PAGEtopage

Gère la configuration via fichier YAML ou programmatiquement.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml


@dataclass
class CorpusMetadata:
    """Métadonnées du corpus à inclure dans chaque <doc>"""
    edition_id: str = ""
    title: str = ""
    language: str = "Latin"
    author: str = ""
    source: str = ""
    type: str = ""
    date: str = ""
    lieu: str = ""
    ville: str = ""

    def to_dict(self) -> Dict[str, str]:
        """Convertit en dictionnaire pour les attributs XML"""
        return {
            "edition_id": self.edition_id,
            "title": self.title,
            "language": self.language,
            "author": self.author,
            "source": self.source,
            "type": self.type,
            "date": self.date,
            "lieu": self.lieu,
            "ville": self.ville,
        }

    def to_xml_attributes(self) -> str:
        """Génère la chaîne d'attributs XML"""
        attrs = []
        for key, value in self.to_dict().items():
            if value:  # N'inclut que les valeurs non vides
                # Échappe les guillemets dans les valeurs
                escaped_value = value.replace('"', '&quot;')
                attrs.append(f'{key}="{escaped_value}"')
        return " ".join(attrs)


@dataclass
class PaginationConfig:
    """Configuration de la pagination"""
    starting_page_number: int = 1
    page_number_source: str = "filename"  # "filename" ou "zone"


@dataclass
class ExtractionConfig:
    """Configuration de l'étape 1 : Extraction XML"""
    column_mode: str = "single"  # "single" ou "dual"
    merge_hyphenated: bool = True
    main_zone_type: str = "MainZone"
    running_title_zone_type: str = "RunningTitleZone"
    numbering_zone_type: str = "NumberingZone"
    default_running_title: str = "No running title"


@dataclass
class EnrichmentConfig:
    """Configuration de l'étape 2 : Enrichissement"""
    lemmatizer: str = "cltk"  # "cltk", "stanza", ou "treetagger"
    language: str = "lat"  # Code langue pour CLTK
    sentence_delimiters: List[str] = field(default_factory=lambda: [".", "?", "!"])
    treetagger_path: Optional[str] = None  # Si lemmatizer == "treetagger"


@dataclass
class ExportConfig:
    """Configuration de l'étape 3 : Export"""
    format: str = "clean"  # "clean", "diplomatic", "annotated"
    generate_index: bool = True
    generate_combined: bool = True
    page_filename_pattern: str = "page_{number:04d}_{folio}.txt"


@dataclass
class Config:
    """Configuration complète du pipeline"""
    corpus: CorpusMetadata = field(default_factory=CorpusMetadata)
    pagination: PaginationConfig = field(default_factory=PaginationConfig)
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    enrichment: EnrichmentConfig = field(default_factory=EnrichmentConfig)
    export: ExportConfig = field(default_factory=ExportConfig)

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "Config":
        """
        Charge la configuration depuis un fichier YAML

        Args:
            yaml_path: Chemin vers le fichier YAML

        Returns:
            Instance Config configurée
        """
        yaml_path = Path(yaml_path)

        if not yaml_path.exists():
            raise FileNotFoundError(f"Fichier de configuration non trouvé: {yaml_path}")

        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """
        Crée une configuration depuis un dictionnaire

        Args:
            data: Dictionnaire de configuration

        Returns:
            Instance Config configurée
        """
        config = cls()

        # Corpus metadata
        if "corpus" in data:
            corpus_data = data["corpus"]
            config.corpus = CorpusMetadata(
                edition_id=corpus_data.get("edition_id", ""),
                title=corpus_data.get("title", ""),
                language=corpus_data.get("language", "Latin"),
                author=corpus_data.get("author", ""),
                source=corpus_data.get("source", ""),
                type=corpus_data.get("type", ""),
                date=corpus_data.get("date", ""),
                lieu=corpus_data.get("lieu", ""),
                ville=corpus_data.get("ville", ""),
            )

        # Pagination
        if "pagination" in data:
            pag_data = data["pagination"]
            config.pagination = PaginationConfig(
                starting_page_number=pag_data.get("starting_page_number", 1),
                page_number_source=pag_data.get("page_number_source", "filename"),
            )

        # Extraction
        if "extraction" in data:
            ext_data = data["extraction"]
            config.extraction = ExtractionConfig(
                column_mode=ext_data.get("column_mode", "single"),
                merge_hyphenated=ext_data.get("merge_hyphenated", True),
                main_zone_type=ext_data.get("main_zone_type", "MainZone"),
                running_title_zone_type=ext_data.get("running_title_zone_type", "RunningTitleZone"),
                numbering_zone_type=ext_data.get("numbering_zone_type", "NumberingZone"),
                default_running_title=ext_data.get("default_running_title", "No running title"),
            )

        # Enrichment
        if "enrichment" in data:
            enr_data = data["enrichment"]
            config.enrichment = EnrichmentConfig(
                lemmatizer=enr_data.get("lemmatizer", "cltk"),
                language=enr_data.get("language", "lat"),
                sentence_delimiters=enr_data.get("sentence_delimiters", [".", "?", "!"]),
                treetagger_path=enr_data.get("treetagger_path"),
            )

        # Export
        if "export" in data:
            exp_data = data["export"]
            config.export = ExportConfig(
                format=exp_data.get("format", "clean"),
                generate_index=exp_data.get("generate_index", True),
                generate_combined=exp_data.get("generate_combined", True),
                page_filename_pattern=exp_data.get("page_filename_pattern", "page_{number:04d}_{folio}.txt"),
            )

        return config

    def to_yaml(self, yaml_path: str | Path) -> None:
        """
        Sauvegarde la configuration dans un fichier YAML

        Args:
            yaml_path: Chemin de destination
        """
        yaml_path = Path(yaml_path)

        data = {
            "corpus": self.corpus.to_dict(),
            "pagination": {
                "starting_page_number": self.pagination.starting_page_number,
                "page_number_source": self.pagination.page_number_source,
            },
            "extraction": {
                "column_mode": self.extraction.column_mode,
                "merge_hyphenated": self.extraction.merge_hyphenated,
                "main_zone_type": self.extraction.main_zone_type,
                "running_title_zone_type": self.extraction.running_title_zone_type,
                "numbering_zone_type": self.extraction.numbering_zone_type,
                "default_running_title": self.extraction.default_running_title,
            },
            "enrichment": {
                "lemmatizer": self.enrichment.lemmatizer,
                "language": self.enrichment.language,
                "sentence_delimiters": self.enrichment.sentence_delimiters,
                "treetagger_path": self.enrichment.treetagger_path,
            },
            "export": {
                "format": self.export.format,
                "generate_index": self.export.generate_index,
                "generate_combined": self.export.generate_combined,
                "page_filename_pattern": self.export.page_filename_pattern,
            },
        }

        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def validate(self) -> List[str]:
        """
        Valide la configuration

        Returns:
            Liste des erreurs de validation (vide si OK)
        """
        errors = []

        # Validation extraction
        if self.extraction.column_mode not in ("single", "dual"):
            errors.append(f"column_mode invalide: {self.extraction.column_mode} (attendu: single ou dual)")

        # Validation enrichment
        if self.enrichment.lemmatizer not in ("cltk", "stanza", "treetagger"):
            errors.append(f"lemmatizer invalide: {self.enrichment.lemmatizer} (attendu: cltk, stanza, ou treetagger)")

        if self.enrichment.lemmatizer == "treetagger" and not self.enrichment.treetagger_path:
            errors.append("treetagger_path requis si lemmatizer == 'treetagger'")

        # Validation export
        if self.export.format not in ("clean", "diplomatic", "annotated"):
            errors.append(f"format invalide: {self.export.format} (attendu: clean, diplomatic, ou annotated)")

        # Validation pagination
        if self.pagination.starting_page_number < 0:
            errors.append(f"starting_page_number doit être >= 0")

        if self.pagination.page_number_source not in ("filename", "zone"):
            errors.append(f"page_number_source invalide: {self.pagination.page_number_source}")

        return errors
