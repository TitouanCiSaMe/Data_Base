"""
Processeurs de données pour le pipeline

Ce module fournit des processeurs communs (filtrage, transformation, etc.)
"""

from typing import Any, Callable, Optional, Iterator
from pathlib import Path
import xml.etree.ElementTree as ET

from .base import Processor, PipelineContext


class FilterProcessor(Processor):
    """Filtre les éléments selon une condition"""

    def __init__(self,
                 filter_func: Callable[[Any], bool],
                 name: Optional[str] = None):
        """
        Args:
            filter_func: Fonction de filtrage (retourne True pour garder l'élément)
            name: Nom du processeur
        """
        super().__init__(name)
        self.filter_func = filter_func

    def process(self, item: Any, context: PipelineContext) -> Optional[Any]:
        """Applique le filtre"""
        if self.filter_func(item):
            return item
        return None


class TransformProcessor(Processor):
    """Transforme les éléments via une fonction"""

    def __init__(self,
                 transform_func: Callable[[Any], Any],
                 name: Optional[str] = None):
        """
        Args:
            transform_func: Fonction de transformation
            name: Nom du processeur
        """
        super().__init__(name)
        self.transform_func = transform_func

    def process(self, item: Any, context: PipelineContext) -> Any:
        """Applique la transformation"""
        return self.transform_func(item)


class MapProcessor(Processor):
    """Map une fonction sur chaque élément"""

    def __init__(self,
                 map_func: Callable[[Any], Any],
                 skip_none: bool = True,
                 name: Optional[str] = None):
        """
        Args:
            map_func: Fonction à appliquer
            skip_none: Si True, skip les résultats None
            name: Nom du processeur
        """
        super().__init__(name)
        self.map_func = map_func
        self.skip_none = skip_none

    def process(self, item: Any, context: PipelineContext) -> Optional[Any]:
        """Applique la fonction"""
        result = self.map_func(item)
        if self.skip_none and result is None:
            return None
        return result


class DeduplicateProcessor(Processor):
    """Supprime les doublons"""

    def __init__(self,
                 key_func: Optional[Callable[[Any], Any]] = None,
                 name: Optional[str] = None):
        """
        Args:
            key_func: Fonction pour extraire la clé de déduplication (optionnel)
            name: Nom du processeur
        """
        super().__init__(name)
        self.key_func = key_func or (lambda x: x)
        self.seen = set()

    def process(self, item: Any, context: PipelineContext) -> Optional[Any]:
        """Vérifie si l'élément a déjà été vu"""
        key = self.key_func(item)
        if key in self.seen:
            return None
        self.seen.add(key)
        return item


class BatchCollector(Processor):
    """Collecte les éléments par lots"""

    def __init__(self,
                 batch_size: int = 100,
                 name: Optional[str] = None):
        """
        Args:
            batch_size: Taille des lots
            name: Nom du processeur
        """
        super().__init__(name)
        self.batch_size = batch_size
        self.current_batch = []

    def process(self, item: Any, context: PipelineContext) -> Optional[list]:
        """Collecte les éléments en lots"""
        self.current_batch.append(item)

        if len(self.current_batch) >= self.batch_size:
            batch = self.current_batch
            self.current_batch = []
            return batch

        return None

    def flush(self) -> Optional[list]:
        """Retourne le dernier lot incomplet"""
        if self.current_batch:
            batch = self.current_batch
            self.current_batch = []
            return batch
        return None


class XMLAnnotationProcessor(Processor):
    """
    Processeur spécialisé pour annoter des éléments XML avec des données

    Utilisé pour le script Gratien: ajoute les IDs trouvés comme attributs XML
    """

    def __init__(self,
                 matcher_func: Callable[[ET.Element], list],
                 attribute_name: str = "gratien_refs",
                 name: Optional[str] = None):
        """
        Args:
            matcher_func: Fonction qui prend un Element XML et retourne une liste d'IDs
            attribute_name: Nom de l'attribut XML à ajouter
            name: Nom du processeur
        """
        super().__init__(name)
        self.matcher_func = matcher_func
        self.attribute_name = attribute_name

    def process(self, item: ET.Element, context: PipelineContext) -> ET.Element:
        """Annote l'élément XML"""
        ids = self.matcher_func(item)

        if ids:
            # Ajoute les IDs comme attribut (séparés par des virgules)
            item.set(self.attribute_name, ",".join(str(id) for id in ids))

        return item


class DownloadProcessor(Processor):
    """
    Processeur pour télécharger des fichiers

    Prend des URLs en entrée et retourne les chemins des fichiers téléchargés
    """

    def __init__(self,
                 output_dir: Path,
                 downloader: Any,
                 filename_template: str = "{index}.dat",
                 name: Optional[str] = None):
        """
        Args:
            output_dir: Dossier de sortie
            downloader: Instance d'AsyncDownloader
            filename_template: Template pour les noms de fichiers
            name: Nom du processeur
        """
        super().__init__(name)
        self.output_dir = Path(output_dir)
        self.downloader = downloader
        self.filename_template = filename_template
        self.index = 0

    def process(self, url: str, context: PipelineContext) -> Optional[Path]:
        """Télécharge une URL"""
        self.index += 1

        # Génère le nom de fichier
        url_parts = url.split('/')
        url_filename = url_parts[-1] if url_parts else f"file_{self.index}"

        filename = self.filename_template.format(
            index=self.index,
            url=url_filename
        )
        file_path = self.output_dir / filename

        # Téléchargement
        downloads = [(url, file_path)]
        results = self.downloader.download_sync(downloads, show_progress=False)

        if results and results[0].success:
            return file_path
        return None


class StatisticsCollector(Processor):
    """Collecte des statistiques sur les éléments traités"""

    def __init__(self,
                 stat_func: Callable[[Any], dict],
                 name: Optional[str] = None):
        """
        Args:
            stat_func: Fonction qui extrait des statistiques d'un élément
            name: Nom du processeur
        """
        super().__init__(name)
        self.stat_func = stat_func
        self.stats = []

    def process(self, item: Any, context: PipelineContext) -> Any:
        """Collecte les statistiques et passe l'élément"""
        stats = self.stat_func(item)
        self.stats.append(stats)
        return item

    def get_aggregated_stats(self) -> dict:
        """Retourne les statistiques agrégées"""
        if not self.stats:
            return {}

        # Agrégation simple (peut être étendue)
        aggregated = {
            'count': len(self.stats),
            'stats': self.stats
        }
        return aggregated


class ChainProcessor(Processor):
    """Chaîne plusieurs processeurs ensemble"""

    def __init__(self,
                 processors: list,
                 name: Optional[str] = None):
        """
        Args:
            processors: Liste de processeurs à chaîner
            name: Nom du processeur
        """
        super().__init__(name)
        self.processors = processors

    def process(self, item: Any, context: PipelineContext) -> Optional[Any]:
        """Applique tous les processeurs séquentiellement"""
        current = item

        for processor in self.processors:
            if current is None:
                return None
            current = processor.process(current, context)

        return current
