"""
Core module - Architecture de base pour le traitement de données
"""

from .base import Extractor, Processor, Writer, PipelineStep, PipelineContext
from .extractors import (
    JSONExtractor,
    XMLExtractor,
    CSVExtractor,
    JSONRecursiveExtractor,
    FileListExtractor,
    MultiFileExtractor
)
from .processors import (
    FilterProcessor,
    TransformProcessor,
    MapProcessor,
    DeduplicateProcessor
)
from .writers import (
    FileWriter,
    JSONWriter,
    CSVWriter,
    XMLWriter
)
from .pipeline import Pipeline, PipelineBuilder

__all__ = [
    # Base
    'Extractor',
    'Processor',
    'Writer',
    'PipelineStep',
    'PipelineContext',
    # Extractors
    'JSONExtractor',
    'XMLExtractor',
    'CSVExtractor',
    'JSONRecursiveExtractor',
    'FileListExtractor',
    'MultiFileExtractor',
    # Processors
    'FilterProcessor',
    'TransformProcessor',
    'MapProcessor',
    'DeduplicateProcessor',
    # Writers
    'FileWriter',
    'JSONWriter',
    'CSVWriter',
    'XMLWriter',
    # Pipeline
    'Pipeline',
    'PipelineBuilder',
]
