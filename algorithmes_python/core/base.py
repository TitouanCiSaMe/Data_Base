"""
Classes abstraites de base pour l'architecture Pipeline

Ce module définit les interfaces de base que tous les composants
du pipeline doivent implémenter.
"""

from abc import ABC, abstractmethod
from typing import Any, Iterator, Optional
from dataclasses import dataclass
import logging


@dataclass
class PipelineContext:
    """Contexte partagé entre les étapes du pipeline"""
    metadata: dict
    errors: list
    stats: dict

    def __init__(self):
        self.metadata = {}
        self.errors = []
        self.stats = {
            'processed': 0,
            'succeeded': 0,
            'failed': 0,
        }


class PipelineStep(ABC):
    """
    Classe abstraite de base pour toutes les étapes du pipeline

    Chaque étape doit implémenter la méthode execute() qui prend
    des données en entrée et retourne des données transformées.
    """

    def __init__(self, name: Optional[str] = None):
        """
        Args:
            name: Nom de l'étape (utilisé pour le logging)
        """
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(f"pipeline.{self.name}")

    @abstractmethod
    def execute(self, data: Any, context: PipelineContext) -> Any:
        """
        Execute cette étape du pipeline

        Args:
            data: Données en entrée
            context: Contexte partagé du pipeline

        Returns:
            Données transformées

        Raises:
            Exception: Si l'étape échoue
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"


class Extractor(PipelineStep):
    """
    Classe abstraite pour les extracteurs de données

    Un extracteur lit des données depuis une source (fichier, API, DB, etc.)
    et les retourne sous forme itérable.
    """

    @abstractmethod
    def extract(self) -> Iterator[Any]:
        """
        Extrait les données de la source

        Yields:
            Éléments de données extraits
        """
        pass

    def execute(self, data: Any, context: PipelineContext) -> Iterator[Any]:
        """
        Execute l'extraction (ignore les données d'entrée)

        Args:
            data: Ignoré pour les extracteurs
            context: Contexte du pipeline

        Returns:
            Iterator sur les données extraites
        """
        return self.extract()


class Processor(PipelineStep):
    """
    Classe abstraite pour les processeurs de données

    Un processeur transforme des données (filtrage, mapping, enrichissement, etc.)
    """

    @abstractmethod
    def process(self, item: Any, context: PipelineContext) -> Any:
        """
        Traite un élément de données

        Args:
            item: Élément à traiter
            context: Contexte du pipeline

        Returns:
            Élément transformé (ou None pour filtrer)
        """
        pass

    def execute(self, data: Iterator[Any], context: PipelineContext) -> Iterator[Any]:
        """
        Execute le traitement sur un flux de données

        Args:
            data: Iterator sur les données d'entrée
            context: Contexte du pipeline

        Yields:
            Éléments traités
        """
        for item in data:
            try:
                result = self.process(item, context)
                if result is not None:
                    yield result
                    context.stats['succeeded'] += 1
            except Exception as e:
                self.logger.error(f"Erreur lors du traitement de {item}: {e}")
                context.errors.append({'item': item, 'error': str(e)})
                context.stats['failed'] += 1
            finally:
                context.stats['processed'] += 1


class Writer(PipelineStep):
    """
    Classe abstraite pour les writers

    Un writer écrit des données vers une destination (fichier, DB, API, etc.)
    """

    @abstractmethod
    def write(self, data: Iterator[Any], context: PipelineContext) -> dict:
        """
        Écrit les données vers la destination

        Args:
            data: Iterator sur les données à écrire
            context: Contexte du pipeline

        Returns:
            Statistiques d'écriture
        """
        pass

    def execute(self, data: Iterator[Any], context: PipelineContext) -> dict:
        """
        Execute l'écriture

        Args:
            data: Iterator sur les données à écrire
            context: Contexte du pipeline

        Returns:
            Statistiques d'écriture
        """
        return self.write(data, context)


class BatchProcessor(Processor):
    """
    Processeur qui traite les données par lots (batch)

    Utile pour les opérations qui bénéficient du traitement groupé
    (requêtes DB, appels API, etc.)
    """

    def __init__(self, name: Optional[str] = None, batch_size: int = 100):
        """
        Args:
            name: Nom du processeur
            batch_size: Taille des lots
        """
        super().__init__(name)
        self.batch_size = batch_size

    @abstractmethod
    def process_batch(self, batch: list, context: PipelineContext) -> list:
        """
        Traite un lot d'éléments

        Args:
            batch: Liste d'éléments à traiter
            context: Contexte du pipeline

        Returns:
            Liste d'éléments traités
        """
        pass

    def process(self, item: Any, context: PipelineContext) -> Any:
        """Non utilisé pour BatchProcessor"""
        raise NotImplementedError("BatchProcessor utilise process_batch()")

    def execute(self, data: Iterator[Any], context: PipelineContext) -> Iterator[Any]:
        """
        Execute le traitement par lots

        Args:
            data: Iterator sur les données
            context: Contexte du pipeline

        Yields:
            Éléments traités
        """
        batch = []
        for item in data:
            batch.append(item)
            if len(batch) >= self.batch_size:
                try:
                    results = self.process_batch(batch, context)
                    for result in results:
                        yield result
                    context.stats['succeeded'] += len(batch)
                except Exception as e:
                    self.logger.error(f"Erreur lors du traitement du lot: {e}")
                    context.errors.append({'batch_size': len(batch), 'error': str(e)})
                    context.stats['failed'] += len(batch)
                finally:
                    context.stats['processed'] += len(batch)
                    batch = []

        # Traite le dernier lot incomplet
        if batch:
            try:
                results = self.process_batch(batch, context)
                for result in results:
                    yield result
                context.stats['succeeded'] += len(batch)
            except Exception as e:
                self.logger.error(f"Erreur lors du traitement du dernier lot: {e}")
                context.errors.append({'batch_size': len(batch), 'error': str(e)})
                context.stats['failed'] += len(batch)
            finally:
                context.stats['processed'] += len(batch)
