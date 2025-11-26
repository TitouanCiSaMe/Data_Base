"""
Gestionnaires d'erreurs et système de retry

Utilitaires pour gérer les erreurs, les retries et le logging.
"""

import time
import logging
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps
from pathlib import Path
import json


class RetryHandler:
    """Gestionnaire de retry avec backoff exponentiel"""

    def __init__(self,
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential_base: float = 2.0,
                 exceptions: Tuple[Type[Exception], ...] = (Exception,)):
        """
        Args:
            max_retries: Nombre maximum de tentatives
            base_delay: Délai initial en secondes
            max_delay: Délai maximum en secondes
            exponential_base: Base pour le backoff exponentiel
            exceptions: Types d'exceptions à gérer
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.exceptions = exceptions
        self.logger = logging.getLogger(self.__class__.__name__)

    def calculate_delay(self, attempt: int) -> float:
        """
        Calcule le délai pour une tentative donnée (backoff exponentiel)

        Args:
            attempt: Numéro de la tentative (0-indexed)

        Returns:
            Délai en secondes
        """
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute une fonction avec retry automatique

        Args:
            func: Fonction à exécuter
            *args, **kwargs: Arguments de la fonction

        Returns:
            Résultat de la fonction

        Raises:
            Exception: Si toutes les tentatives échouent
        """
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)

            except self.exceptions as e:
                last_exception = e
                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt)
                    self.logger.warning(
                        f"Tentative {attempt + 1}/{self.max_retries + 1} échouée: {e}. "
                        f"Nouvelle tentative dans {delay:.1f}s..."
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(
                        f"Échec après {self.max_retries + 1} tentatives: {e}"
                    )

        raise last_exception

    def __call__(self, func: Callable) -> Callable:
        """Décorateur pour ajouter le retry automatique à une fonction"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.execute(func, *args, **kwargs)

        return wrapper


def retry(max_retries: int = 3,
          base_delay: float = 1.0,
          exceptions: Tuple[Type[Exception], ...] = (Exception,)):
    """
    Décorateur de retry simplifié

    Args:
        max_retries: Nombre maximum de tentatives
        base_delay: Délai initial en secondes
        exceptions: Types d'exceptions à gérer

    Example:
        @retry(max_retries=3, base_delay=2.0)
        def download_file(url):
            # code qui peut échouer
            pass
    """
    handler = RetryHandler(
        max_retries=max_retries,
        base_delay=base_delay,
        exceptions=exceptions
    )
    return handler


class ErrorLogger:
    """Logger d'erreurs avec sauvegarde dans un fichier"""

    def __init__(self,
                 log_file: Optional[Path] = None,
                 log_to_console: bool = True,
                 log_level: int = logging.INFO):
        """
        Args:
            log_file: Chemin vers le fichier de log (optionnel)
            log_to_console: Si True, log aussi sur la console
            log_level: Niveau de logging
        """
        self.log_file = Path(log_file) if log_file else None
        self.log_to_console = log_to_console
        self.log_level = log_level
        self.errors = []

        # Configuration du logger
        self.logger = logging.getLogger('ErrorLogger')
        self.logger.setLevel(log_level)

        # Handler pour fichier
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

        # Handler pour console
        if self.log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            formatter = logging.Formatter('%(levelname)s: %(message)s')
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

    def log_error(self,
                  error: Exception,
                  context: Optional[dict] = None,
                  severity: str = 'ERROR'):
        """
        Log une erreur avec contexte

        Args:
            error: Exception à logger
            context: Contexte additionnel (dict)
            severity: Niveau de sévérité
        """
        error_info = {
            'type': type(error).__name__,
            'message': str(error),
            'severity': severity,
            'context': context or {}
        }

        self.errors.append(error_info)

        # Log selon la sévérité
        log_msg = f"{error_info['type']}: {error_info['message']}"
        if context:
            log_msg += f" | Context: {context}"

        if severity == 'CRITICAL':
            self.logger.critical(log_msg)
        elif severity == 'ERROR':
            self.logger.error(log_msg)
        elif severity == 'WARNING':
            self.logger.warning(log_msg)
        else:
            self.logger.info(log_msg)

    def save_errors_to_file(self, file_path: Path):
        """
        Sauvegarde toutes les erreurs dans un fichier JSON

        Args:
            file_path: Chemin vers le fichier de sauvegarde
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.errors, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Erreurs sauvegardées dans {file_path}")

    def get_errors_by_type(self, error_type: str) -> list:
        """
        Récupère les erreurs d'un type spécifique

        Args:
            error_type: Type d'erreur à filtrer

        Returns:
            Liste des erreurs du type spécifié
        """
        return [e for e in self.errors if e['type'] == error_type]

    def get_error_summary(self) -> dict:
        """
        Génère un résumé des erreurs

        Returns:
            Dict avec statistiques d'erreurs
        """
        summary = {
            'total': len(self.errors),
            'by_type': {},
            'by_severity': {}
        }

        for error in self.errors:
            # Par type
            error_type = error['type']
            summary['by_type'][error_type] = summary['by_type'].get(error_type, 0) + 1

            # Par sévérité
            severity = error['severity']
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1

        return summary

    def clear_errors(self):
        """Efface toutes les erreurs enregistrées"""
        self.errors = []


class ProgressCheckpoint:
    """Gestionnaire de checkpoints pour reprendre après un crash"""

    def __init__(self, checkpoint_file: Path):
        """
        Args:
            checkpoint_file: Fichier pour sauvegarder les checkpoints
        """
        self.checkpoint_file = Path(checkpoint_file)
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        self.data = self._load()

    def _load(self) -> dict:
        """Charge le checkpoint existant"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save(self, key: str, value: Any):
        """
        Sauvegarde une valeur de checkpoint

        Args:
            key: Clé du checkpoint
            value: Valeur à sauvegarder
        """
        self.data[key] = value
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Récupère une valeur de checkpoint

        Args:
            key: Clé du checkpoint
            default: Valeur par défaut si la clé n'existe pas

        Returns:
            Valeur du checkpoint
        """
        return self.data.get(key, default)

    def clear(self):
        """Efface tous les checkpoints"""
        self.data = {}
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()


def safe_execute(func: Callable,
                 *args,
                 default: Any = None,
                 logger: Optional[logging.Logger] = None,
                 **kwargs) -> Any:
    """
    Execute une fonction de manière sécurisée

    Args:
        func: Fonction à exécuter
        default: Valeur à retourner en cas d'erreur
        logger: Logger optionnel
        *args, **kwargs: Arguments de la fonction

    Returns:
        Résultat de la fonction ou valeur par défaut

    Example:
        result = safe_execute(risky_function, arg1, arg2, default=[])
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if logger:
            logger.error(f"Erreur lors de l'exécution de {func.__name__}: {e}")
        return default
