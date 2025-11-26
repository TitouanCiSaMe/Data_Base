"""
Système de Pipeline pour orchestrer le traitement de données

Le Pipeline permet de chaîner plusieurs étapes de traitement de manière fluide.
"""

import logging
from typing import List, Optional, Any
from .base import PipelineStep, PipelineContext, Extractor, Processor, Writer


class Pipeline:
    """
    Orchestrateur de pipeline de traitement de données

    Le Pipeline exécute séquentiellement une série d'étapes (extracteurs,
    processeurs, writers) et gère le contexte partagé entre les étapes.

    Example:
        pipeline = Pipeline("My Pipeline")
        pipeline.add_step(JSONExtractor("data.json"))
        pipeline.add_step(FilterProcessor(lambda x: x > 0))
        pipeline.add_step(FileWriter("output.txt"))
        results = pipeline.run()
    """

    def __init__(self, name: str = "Pipeline"):
        """
        Args:
            name: Nom du pipeline
        """
        self.name = name
        self.steps: List[PipelineStep] = []
        self.context = PipelineContext()
        self.logger = logging.getLogger(f"pipeline.{name}")

    def add_step(self, step: PipelineStep) -> 'Pipeline':
        """
        Ajoute une étape au pipeline

        Args:
            step: Étape à ajouter

        Returns:
            Self pour chaînage
        """
        self.steps.append(step)
        self.logger.debug(f"Étape ajoutée: {step}")
        return self

    def add_extractor(self, extractor: Extractor) -> 'Pipeline':
        """Alias pour add_step spécifique aux extracteurs"""
        return self.add_step(extractor)

    def add_processor(self, processor: Processor) -> 'Pipeline':
        """Alias pour add_step spécifique aux processeurs"""
        return self.add_step(processor)

    def add_writer(self, writer: Writer) -> 'Pipeline':
        """Alias pour add_step spécifique aux writers"""
        return self.add_step(writer)

    def run(self, initial_data: Any = None) -> Any:
        """
        Execute le pipeline

        Args:
            initial_data: Données initiales (optionnel)

        Returns:
            Résultat final du pipeline

        Raises:
            Exception: Si une étape échoue
        """
        if not self.steps:
            self.logger.warning("Pipeline vide, aucune étape à exécuter")
            return None

        self.logger.info(f"Démarrage du pipeline '{self.name}' avec {len(self.steps)} étape(s)")

        data = initial_data

        for i, step in enumerate(self.steps, 1):
            try:
                self.logger.info(f"Étape {i}/{len(self.steps)}: {step.name}")
                data = step.execute(data, self.context)

            except Exception as e:
                self.logger.error(f"Erreur à l'étape {i} ({step.name}): {e}")
                self.context.errors.append({
                    'step': step.name,
                    'step_index': i,
                    'error': str(e)
                })
                raise

        self.logger.info(f"Pipeline '{self.name}' terminé avec succès")
        self._print_summary()

        return data

    def _print_summary(self):
        """Affiche un résumé de l'exécution"""
        stats = self.context.stats

        print("\n" + "=" * 60)
        print(f"📊 RÉSUMÉ DU PIPELINE: {self.name}")
        print("=" * 60)
        print(f"Éléments traités  : {stats['processed']}")
        print(f"✓ Réussis         : {stats['succeeded']}")
        print(f"✗ Échoués         : {stats['failed']}")

        if stats['processed'] > 0:
            success_rate = (stats['succeeded'] / stats['processed']) * 100
            print(f"Taux de réussite  : {success_rate:.1f}%")

        if self.context.errors:
            print(f"\n⚠ Erreurs         : {len(self.context.errors)}")

        print("=" * 60)

    def get_stats(self) -> dict:
        """
        Retourne les statistiques du pipeline

        Returns:
            Dict avec statistiques
        """
        return self.context.stats.copy()

    def get_errors(self) -> list:
        """
        Retourne la liste des erreurs

        Returns:
            Liste des erreurs
        """
        return self.context.errors.copy()

    def clear(self):
        """Réinitialise le pipeline (garde les étapes)"""
        self.context = PipelineContext()

    def reset(self):
        """Réinitialise complètement le pipeline (supprime les étapes)"""
        self.steps = []
        self.context = PipelineContext()


class PipelineBuilder:
    """
    Builder pour créer des pipelines de manière fluide

    Example:
        pipeline = (PipelineBuilder("MyPipeline")
            .extract_from_json("data.json", key_path="items")
            .filter(lambda x: x['status'] == 'active')
            .transform(lambda x: x['name'])
            .write_to_file("output.txt")
            .build())

        results = pipeline.run()
    """

    def __init__(self, name: str = "Pipeline"):
        """
        Args:
            name: Nom du pipeline
        """
        self.pipeline = Pipeline(name)

    def extract_from_json(self, file_path: str, **kwargs) -> 'PipelineBuilder':
        """Ajoute un extracteur JSON"""
        from .extractors import JSONExtractor
        self.pipeline.add_extractor(JSONExtractor(file_path, **kwargs))
        return self

    def extract_from_csv(self, file_path: str, **kwargs) -> 'PipelineBuilder':
        """Ajoute un extracteur CSV"""
        from .extractors import CSVExtractor
        self.pipeline.add_extractor(CSVExtractor(file_path, **kwargs))
        return self

    def extract_from_xml(self, file_pattern: str, **kwargs) -> 'PipelineBuilder':
        """Ajoute un extracteur XML"""
        from .extractors import XMLExtractor
        self.pipeline.add_extractor(XMLExtractor(file_pattern, **kwargs))
        return self

    def filter(self, filter_func: callable) -> 'PipelineBuilder':
        """Ajoute un filtre"""
        from .processors import FilterProcessor
        self.pipeline.add_processor(FilterProcessor(filter_func))
        return self

    def transform(self, transform_func: callable) -> 'PipelineBuilder':
        """Ajoute une transformation"""
        from .processors import TransformProcessor
        self.pipeline.add_processor(TransformProcessor(transform_func))
        return self

    def add_step(self, step: PipelineStep) -> 'PipelineBuilder':
        """Ajoute une étape personnalisée"""
        self.pipeline.add_step(step)
        return self

    def build(self) -> Pipeline:
        """
        Construit et retourne le pipeline

        Returns:
            Pipeline configuré
        """
        return self.pipeline