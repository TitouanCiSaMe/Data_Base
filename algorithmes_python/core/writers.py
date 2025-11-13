"""
Writers pour sauvegarder les résultats du pipeline

Ce module fournit des writers pour différents formats de sortie.
"""

import json
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterator, Any, Optional
from collections import Counter

from .base import Writer, PipelineContext


class FileWriter(Writer):
    """Écrit les éléments dans un fichier texte (un par ligne)"""

    def __init__(self,
                 file_path: Path,
                 encoding: str = 'utf-8',
                 mode: str = 'w',
                 name: Optional[str] = None):
        """
        Args:
            file_path: Chemin du fichier de sortie
            encoding: Encodage du fichier
            mode: Mode d'écriture ('w' ou 'a')
            name: Nom du writer
        """
        super().__init__(name)
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.mode = mode

    def write(self, data: Iterator[Any], context: PipelineContext) -> dict:
        """Écrit les données dans le fichier"""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        count = 0
        with open(self.file_path, self.mode, encoding=self.encoding) as f:
            for item in data:
                f.write(str(item) + '\n')
                count += 1

        self.logger.info(f"{count} lignes écrites dans {self.file_path}")

        return {'written': count, 'file': str(self.file_path)}


class JSONWriter(Writer):
    """Écrit les éléments dans un fichier JSON"""

    def __init__(self,
                 file_path: Path,
                 mode: str = 'array',
                 indent: int = 2,
                 encoding: str = 'utf-8',
                 name: Optional[str] = None):
        """
        Args:
            file_path: Chemin du fichier de sortie
            mode: 'array' (liste JSON) ou 'lines' (JSON Lines)
            indent: Indentation (pour mode array)
            encoding: Encodage du fichier
            name: Nom du writer
        """
        super().__init__(name)
        self.file_path = Path(file_path)
        self.mode = mode
        self.indent = indent
        self.encoding = encoding

    def write(self, data: Iterator[Any], context: PipelineContext) -> dict:
        """Écrit les données en JSON"""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        items = list(data)
        count = len(items)

        if self.mode == 'array':
            with open(self.file_path, 'w', encoding=self.encoding) as f:
                json.dump(items, f, indent=self.indent, ensure_ascii=False)

        elif self.mode == 'lines':
            with open(self.file_path, 'w', encoding=self.encoding) as f:
                for item in items:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')

        self.logger.info(f"{count} éléments écrits dans {self.file_path}")

        return {'written': count, 'file': str(self.file_path)}


class CSVWriter(Writer):
    """Écrit les éléments dans un fichier CSV"""

    def __init__(self,
                 file_path: Path,
                 fieldnames: Optional[list] = None,
                 delimiter: str = ',',
                 encoding: str = 'utf-8',
                 name: Optional[str] = None):
        """
        Args:
            file_path: Chemin du fichier de sortie
            fieldnames: Noms des colonnes (auto-détecté si None)
            delimiter: Délimiteur CSV
            encoding: Encodage du fichier
            name: Nom du writer
        """
        super().__init__(name)
        self.file_path = Path(file_path)
        self.fieldnames = fieldnames
        self.delimiter = delimiter
        self.encoding = encoding

    def write(self, data: Iterator[Any], context: PipelineContext) -> dict:
        """Écrit les données en CSV"""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        items = list(data)
        if not items:
            self.logger.warning("Aucune donnée à écrire")
            return {'written': 0}

        # Auto-détection des fieldnames si nécessaire
        fieldnames = self.fieldnames
        if fieldnames is None and isinstance(items[0], dict):
            fieldnames = list(items[0].keys())

        count = 0
        with open(self.file_path, 'w', newline='', encoding=self.encoding) as f:
            if fieldnames:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=self.delimiter)
                writer.writeheader()
                writer.writerows(items)
                count = len(items)
            else:
                writer = csv.writer(f, delimiter=self.delimiter)
                writer.writerows(items)
                count = len(items)

        self.logger.info(f"{count} lignes écrites dans {self.file_path}")

        return {'written': count, 'file': str(self.file_path)}


class XMLWriter(Writer):
    """Écrit des éléments XML dans un fichier"""

    def __init__(self,
                 output_dir: Path,
                 preserve_structure: bool = True,
                 encoding: str = 'utf-8',
                 name: Optional[str] = None):
        """
        Args:
            output_dir: Dossier de sortie
            preserve_structure: Si True, préserve la structure d'origine
            encoding: Encodage XML
            name: Nom du writer
        """
        super().__init__(name)
        self.output_dir = Path(output_dir)
        self.preserve_structure = preserve_structure
        self.encoding = encoding

    def write(self, data: Iterator[ET.Element], context: PipelineContext) -> dict:
        """Écrit les éléments XML"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Si les données sont des arbres XML complets
        count = 0
        for item in data:
            if isinstance(item, ET.ElementTree):
                # Arbre complet
                tree = item
                root = tree.getroot()
            elif isinstance(item, ET.Element):
                # Élément seul -> crée un arbre
                tree = ET.ElementTree(item)
                root = item
            else:
                self.logger.warning(f"Type non supporté: {type(item)}")
                continue

            # Génère un nom de fichier (basé sur un attribut ou index)
            filename = root.get('id', f'output_{count}.xml')
            if not filename.endswith('.xml'):
                filename += '.xml'

            output_path = self.output_dir / filename

            tree.write(
                output_path,
                encoding=self.encoding,
                xml_declaration=True
            )
            count += 1

        self.logger.info(f"{count} fichiers XML écrits dans {self.output_dir}")

        return {'written': count, 'directory': str(self.output_dir)}


class MultiFileXMLWriter(Writer):
    """
    Écrit des fichiers XML avec la même structure que les fichiers d'entrée

    Utilisé pour le script Gratien: traite plusieurs fichiers XML,
    les modifie et les sauvegarde.
    """

    def __init__(self,
                 input_dir: Path,
                 output_dir: Path,
                 encoding: str = 'utf-8',
                 name: Optional[str] = None):
        """
        Args:
            input_dir: Dossier des fichiers d'origine
            output_dir: Dossier de sortie
            encoding: Encodage XML
            name: Nom du writer
        """
        super().__init__(name)
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.encoding = encoding

    def write(self, data: Iterator[tuple], context: PipelineContext) -> dict:
        """
        Écrit les fichiers XML modifiés

        Attend des tuples (filename, tree)
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        count = 0
        for filename, tree in data:
            output_path = self.output_dir / filename

            tree.write(
                output_path,
                encoding=self.encoding,
                xml_declaration=True
            )
            count += 1

        self.logger.info(f"{count} fichiers XML écrits dans {self.output_dir}")

        return {'written': count, 'directory': str(self.output_dir)}


class StatsWriter(Writer):
    """Génère un rapport de statistiques"""

    def __init__(self,
                 file_path: Path,
                 format: str = 'text',
                 name: Optional[str] = None):
        """
        Args:
            file_path: Chemin du fichier de rapport
            format: Format ('text' ou 'json')
            name: Nom du writer
        """
        super().__init__(name)
        self.file_path = Path(file_path)
        self.format = format

    def write(self, data: Iterator[Any], context: PipelineContext) -> dict:
        """Génère le rapport de statistiques"""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        items = list(data)
        count = len(items)

        stats = {
            'total_items': count,
            'pipeline_stats': context.stats,
            'errors': len(context.errors),
        }

        # Analyse basique
        if items:
            type_counter = Counter(type(item).__name__ for item in items)
            stats['types'] = dict(type_counter)

        if self.format == 'json':
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2)
        else:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("RAPPORT DE STATISTIQUES\n")
                f.write("=" * 60 + "\n\n")

                for key, value in stats.items():
                    f.write(f"{key}: {value}\n")

        self.logger.info(f"Rapport écrit dans {self.file_path}")

        return {'written': 1, 'file': str(self.file_path)}


class NullWriter(Writer):
    """Writer qui ne fait rien (utile pour les tests ou le debugging)"""

    def write(self, data: Iterator[Any], context: PipelineContext) -> dict:
        """Consume les données sans les écrire"""
        count = sum(1 for _ in data)
        self.logger.debug(f"{count} éléments consommés (NullWriter)")
        return {'consumed': count}
