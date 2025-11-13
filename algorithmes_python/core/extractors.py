"""
Extracteurs de données pour différentes sources

Ce module fournit des extracteurs pour JSON, XML, CSV et d'autres formats.
"""

import json
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterator, Any, Optional, Union, Callable
import glob

from .base import Extractor, PipelineContext


class JSONExtractor(Extractor):
    """Extrait des données depuis un fichier JSON"""

    def __init__(self,
                 file_path: Union[str, Path],
                 key_path: Optional[str] = None,
                 filter_func: Optional[Callable] = None,
                 name: Optional[str] = None):
        """
        Args:
            file_path: Chemin vers le fichier JSON
            key_path: Chemin optionnel vers une clé spécifique (ex: "data.items")
            filter_func: Fonction de filtrage optionnelle
            name: Nom de l'extracteur
        """
        super().__init__(name)
        self.file_path = Path(file_path)
        self.key_path = key_path
        self.filter_func = filter_func

    def _navigate_to_key(self, data: dict, key_path: str) -> Any:
        """Navigate vers une clé imbriquée (ex: "data.items")"""
        keys = key_path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            else:
                return None
        return current

    def extract(self) -> Iterator[Any]:
        """Extrait les données du fichier JSON"""
        self.logger.info(f"Extraction depuis {self.file_path}")

        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Navigation vers la clé spécifique si fournie
        if self.key_path:
            data = self._navigate_to_key(data, self.key_path)

        # Si data est une liste, yield chaque élément
        if isinstance(data, list):
            for item in data:
                if self.filter_func is None or self.filter_func(item):
                    yield item
        else:
            # Sinon yield l'objet entier
            if self.filter_func is None or self.filter_func(data):
                yield data


class JSONRecursiveExtractor(Extractor):
    """Extrait récursivement toutes les valeurs d'une clé spécifique dans un JSON"""

    def __init__(self,
                 file_path: Union[str, Path],
                 target_key: str,
                 filter_func: Optional[Callable] = None,
                 name: Optional[str] = None):
        """
        Args:
            file_path: Chemin vers le fichier JSON
            target_key: Clé à extraire récursivement (ex: "@id")
            filter_func: Fonction de filtrage optionnelle
            name: Nom de l'extracteur
        """
        super().__init__(name)
        self.file_path = Path(file_path)
        self.target_key = target_key
        self.filter_func = filter_func

    def _extract_recursive(self, obj: Any, key: str) -> Iterator[Any]:
        """Extrait récursivement toutes les valeurs d'une clé"""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == key:
                    yield v
                else:
                    yield from self._extract_recursive(v, key)
        elif isinstance(obj, list):
            for item in obj:
                yield from self._extract_recursive(item, key)

    def extract(self) -> Iterator[Any]:
        """Extrait récursivement les valeurs de la clé cible"""
        self.logger.info(f"Extraction récursive de '{self.target_key}' depuis {self.file_path}")

        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for value in self._extract_recursive(data, self.target_key):
            if self.filter_func is None or self.filter_func(value):
                yield value


class CSVExtractor(Extractor):
    """Extrait des données depuis un fichier CSV"""

    def __init__(self,
                 file_path: Union[str, Path],
                 encoding: str = 'utf-8',
                 delimiter: str = ',',
                 skip_header: bool = False,
                 as_dict: bool = True,
                 name: Optional[str] = None):
        """
        Args:
            file_path: Chemin vers le fichier CSV
            encoding: Encodage du fichier
            delimiter: Délimiteur CSV
            skip_header: Si True, ignore la première ligne
            as_dict: Si True, retourne des dicts, sinon des listes
            name: Nom de l'extracteur
        """
        super().__init__(name)
        self.file_path = Path(file_path)
        self.encoding = encoding
        self.delimiter = delimiter
        self.skip_header = skip_header
        self.as_dict = as_dict

    def extract(self) -> Iterator[Union[dict, list]]:
        """Extrait les lignes du fichier CSV"""
        self.logger.info(f"Extraction depuis {self.file_path}")

        with open(self.file_path, 'r', encoding=self.encoding) as f:
            if self.as_dict:
                reader = csv.DictReader(f, delimiter=self.delimiter)
                if self.skip_header:
                    next(reader, None)
                for row in reader:
                    yield row
            else:
                reader = csv.reader(f, delimiter=self.delimiter)
                if self.skip_header:
                    next(reader, None)
                for row in reader:
                    yield row


class XMLExtractor(Extractor):
    """Extrait des données depuis des fichiers XML"""

    def __init__(self,
                 file_pattern: Union[str, Path],
                 xpath: Optional[str] = None,
                 name: Optional[str] = None):
        """
        Args:
            file_pattern: Chemin ou pattern glob vers le(s) fichier(s) XML
            xpath: Expression XPath optionnelle pour filtrer les éléments
            name: Nom de l'extracteur
        """
        super().__init__(name)
        self.file_pattern = str(file_pattern)
        self.xpath = xpath

    def extract(self) -> Iterator[ET.Element]:
        """Extrait les éléments des fichiers XML"""
        # Résolution du pattern glob
        files = glob.glob(self.file_pattern)

        if not files:
            self.logger.warning(f"Aucun fichier trouvé pour le pattern: {self.file_pattern}")
            return

        self.logger.info(f"Extraction depuis {len(files)} fichier(s) XML")

        for file_path in files:
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()

                if self.xpath:
                    # Utilise XPath si fourni
                    elements = root.findall(self.xpath)
                    for elem in elements:
                        yield elem
                else:
                    # Sinon yield la racine
                    yield root

            except Exception as e:
                self.logger.error(f"Erreur lors de la lecture de {file_path}: {e}")


class FileListExtractor(Extractor):
    """Extrait une liste de chemins de fichiers basée sur un pattern"""

    def __init__(self,
                 pattern: str,
                 recursive: bool = False,
                 filter_func: Optional[Callable] = None,
                 name: Optional[str] = None):
        """
        Args:
            pattern: Pattern glob (ex: "*.txt", "data/**/*.json")
            recursive: Si True, recherche récursive
            filter_func: Fonction de filtrage optionnelle sur les chemins
            name: Nom de l'extracteur
        """
        super().__init__(name)
        self.pattern = pattern
        self.recursive = recursive
        self.filter_func = filter_func

    def extract(self) -> Iterator[Path]:
        """Extrait les chemins de fichiers correspondants"""
        self.logger.info(f"Recherche de fichiers: {self.pattern}")

        files = glob.glob(self.pattern, recursive=self.recursive)

        for file_path in files:
            path = Path(file_path)
            if self.filter_func is None or self.filter_func(path):
                yield path


class MultiFileExtractor(Extractor):
    """Extrait des données depuis plusieurs fichiers d'un dossier"""

    def __init__(self,
                 directory: Union[str, Path],
                 file_pattern: str = "*.*",
                 extractor_factory: Callable[[Path], Extractor] = None,
                 name: Optional[str] = None):
        """
        Args:
            directory: Dossier contenant les fichiers
            file_pattern: Pattern pour filtrer les fichiers
            extractor_factory: Factory pour créer un extracteur par fichier
            name: Nom de l'extracteur
        """
        super().__init__(name)
        self.directory = Path(directory)
        self.file_pattern = file_pattern
        self.extractor_factory = extractor_factory

    def extract(self) -> Iterator[Any]:
        """Extrait les données de tous les fichiers"""
        files = self.directory.glob(self.file_pattern)

        for file_path in files:
            if self.extractor_factory:
                extractor = self.extractor_factory(file_path)
                yield from extractor.extract()
            else:
                yield file_path
