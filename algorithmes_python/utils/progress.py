"""
Utilitaires pour le suivi de progression

Gestion des barres de progression et du reporting de statut.
"""

from tqdm import tqdm
from typing import Optional, Iterator, Any
from contextlib import contextmanager
import time


class ProgressTracker:
    """Tracker de progression avec barres tqdm améliorées"""

    def __init__(self,
                 total: Optional[int] = None,
                 desc: str = "Processing",
                 unit: str = "item",
                 disable: bool = False):
        """
        Args:
            total: Nombre total d'items (None pour indéterminé)
            desc: Description de la progression
            unit: Unité des items
            disable: Si True, désactive la barre de progression
        """
        self.total = total
        self.desc = desc
        self.unit = unit
        self.disable = disable
        self.pbar: Optional[tqdm] = None
        self.start_time = None
        self.completed = 0

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def start(self):
        """Démarre la barre de progression"""
        self.start_time = time.time()
        self.pbar = tqdm(
            total=self.total,
            desc=self.desc,
            unit=self.unit,
            disable=self.disable,
            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
        )

    def update(self, n: int = 1):
        """
        Met à jour la progression

        Args:
            n: Nombre d'items à ajouter
        """
        if self.pbar:
            self.pbar.update(n)
            self.completed += n

    def set_description(self, desc: str):
        """
        Change la description de la barre

        Args:
            desc: Nouvelle description
        """
        if self.pbar:
            self.pbar.set_description(desc)

    def set_postfix(self, **kwargs):
        """
        Ajoute des informations après la barre

        Args:
            **kwargs: Paires clé-valeur à afficher
        """
        if self.pbar:
            self.pbar.set_postfix(**kwargs)

    def close(self):
        """Ferme la barre de progression"""
        if self.pbar:
            self.pbar.close()

    def get_elapsed_time(self) -> float:
        """
        Retourne le temps écoulé en secondes

        Returns:
            Temps écoulé
        """
        if self.start_time:
            return time.time() - self.start_time
        return 0

    def get_rate(self) -> float:
        """
        Calcule le taux de traitement (items/seconde)

        Returns:
            Taux de traitement
        """
        elapsed = self.get_elapsed_time()
        if elapsed > 0:
            return self.completed / elapsed
        return 0


def track_progress(iterable: Iterator[Any],
                   total: Optional[int] = None,
                   desc: str = "Processing",
                   unit: str = "item") -> Iterator[Any]:
    """
    Wraps un iterable avec une barre de progression

    Args:
        iterable: Iterable à traiter
        total: Nombre total d'éléments (optionnel)
        desc: Description
        unit: Unité

    Yields:
        Éléments de l'iterable

    Example:
        for item in track_progress(my_list, desc="Processing items"):
            process(item)
    """
    with tqdm(iterable, total=total, desc=desc, unit=unit) as pbar:
        for item in pbar:
            yield item


@contextmanager
def progress_context(total: Optional[int] = None,
                     desc: str = "Processing",
                     unit: str = "item"):
    """
    Context manager pour une barre de progression

    Args:
        total: Nombre total d'items
        desc: Description
        unit: Unité

    Example:
        with progress_context(total=100, desc="Downloading") as progress:
            for i in range(100):
                # do work
                progress.update(1)
    """
    tracker = ProgressTracker(total=total, desc=desc, unit=unit)
    try:
        tracker.start()
        yield tracker
    finally:
        tracker.close()


class MultiProgressTracker:
    """Gestionnaire de multiples barres de progression"""

    def __init__(self):
        """Initialize le multi-tracker"""
        self.trackers = {}

    def add_tracker(self,
                    name: str,
                    total: Optional[int] = None,
                    desc: Optional[str] = None,
                    unit: str = "item"):
        """
        Ajoute un nouveau tracker

        Args:
            name: Nom unique du tracker
            total: Nombre total d'items
            desc: Description (par défaut = name)
            unit: Unité
        """
        if name in self.trackers:
            raise ValueError(f"Tracker '{name}' existe déjà")

        desc = desc or name
        tracker = ProgressTracker(total=total, desc=desc, unit=unit)
        tracker.start()
        self.trackers[name] = tracker

    def update(self, name: str, n: int = 1):
        """
        Met à jour un tracker spécifique

        Args:
            name: Nom du tracker
            n: Nombre d'items à ajouter
        """
        if name in self.trackers:
            self.trackers[name].update(n)

    def set_description(self, name: str, desc: str):
        """
        Change la description d'un tracker

        Args:
            name: Nom du tracker
            desc: Nouvelle description
        """
        if name in self.trackers:
            self.trackers[name].set_description(desc)

    def close_all(self):
        """Ferme tous les trackers"""
        for tracker in self.trackers.values():
            tracker.close()
        self.trackers.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_all()


class ProgressReporter:
    """Reporter de progression avec callbacks personnalisables"""

    def __init__(self,
                 total: int,
                 report_interval: int = 10,
                 callback: Optional[callable] = None):
        """
        Args:
            total: Nombre total d'items
            report_interval: Intervalle de reporting (pourcentage)
            callback: Fonction à appeler à chaque report
        """
        self.total = total
        self.report_interval = report_interval
        self.callback = callback
        self.current = 0
        self.last_reported = 0

    def update(self, n: int = 1):
        """
        Met à jour la progression

        Args:
            n: Nombre d'items à ajouter
        """
        self.current += n
        current_percent = (self.current / self.total) * 100

        # Report si l'intervalle est dépassé
        if current_percent >= self.last_reported + self.report_interval:
            self.last_reported = int(current_percent / self.report_interval) * self.report_interval
            if self.callback:
                self.callback(self.current, self.total, current_percent)

    def is_complete(self) -> bool:
        """
        Vérifie si la progression est complète

        Returns:
            True si complète
        """
        return self.current >= self.total


def format_time(seconds: float) -> str:
    """
    Formate un temps en secondes en format lisible

    Args:
        seconds: Temps en secondes

    Returns:
        Temps formaté (ex: "1h 23m 45s")

    Example:
        >>> format_time(3665)
        '1h 1m 5s'
    """
    if seconds < 60:
        return f"{seconds:.1f}s"

    minutes = int(seconds // 60)
    seconds = int(seconds % 60)

    if minutes < 60:
        return f"{minutes}m {seconds}s"

    hours = minutes // 60
    minutes = minutes % 60

    return f"{hours}h {minutes}m {seconds}s"


def format_size(bytes_size: int) -> str:
    """
    Formate une taille en octets en format lisible

    Args:
        bytes_size: Taille en octets

    Returns:
        Taille formatée (ex: "1.5 MB")

    Example:
        >>> format_size(1536000)
        '1.46 MB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"
