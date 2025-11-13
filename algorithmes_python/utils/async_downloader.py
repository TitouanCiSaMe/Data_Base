"""
Téléchargeur asynchrone haute performance

Téléchargement parallèle avec retry, gestion d'erreurs et progression.
"""

import aiohttp
import aiofiles
import asyncio
from pathlib import Path
from typing import List, Optional, Callable, Dict, Any
from dataclasses import dataclass
import logging
from .error_handler import RetryHandler
from .progress import ProgressTracker


@dataclass
class DownloadResult:
    """Résultat d'un téléchargement"""
    url: str
    file_path: Path
    success: bool
    error: Optional[str] = None
    size: int = 0
    duration: float = 0.0


class AsyncDownloader:
    """
    Téléchargeur asynchrone haute performance

    Features:
    - Téléchargement parallèle (50-100x plus rapide)
    - Retry automatique avec backoff
    - Vérification d'existence (skip si déjà téléchargé)
    - Progress bar détaillée
    - Streaming pour grandes fichiers
    - Gestion robuste des erreurs
    """

    def __init__(self,
                 max_concurrent: int = 10,
                 max_retries: int = 3,
                 timeout: int = 30,
                 chunk_size: int = 8192,
                 skip_existing: bool = True,
                 rate_limit_delay: float = 0.0,
                 headers: Optional[Dict[str, str]] = None):
        """
        Args:
            max_concurrent: Nombre de téléchargements simultanés
            max_retries: Nombre de tentatives par fichier
            timeout: Timeout en secondes
            chunk_size: Taille des chunks pour streaming
            skip_existing: Si True, skip les fichiers déjà téléchargés
            rate_limit_delay: Délai minimum entre chaque téléchargement (rate limiting)
            headers: Headers HTTP personnalisés
        """
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.timeout = timeout
        self.chunk_size = chunk_size
        self.skip_existing = skip_existing
        self.rate_limit_delay = rate_limit_delay
        self.headers = headers or {}
        self.logger = logging.getLogger(self.__class__.__name__)

        # Statistiques
        self.stats = {
            'total': 0,
            'succeeded': 0,
            'failed': 0,
            'skipped': 0,
            'total_size': 0,
        }

    async def download_file(self,
                            session: aiohttp.ClientSession,
                            url: str,
                            file_path: Path,
                            semaphore: asyncio.Semaphore) -> DownloadResult:
        """
        Télécharge un fichier unique

        Args:
            session: Session aiohttp
            url: URL à télécharger
            file_path: Chemin de destination
            semaphore: Semaphore pour limiter la concurrence

        Returns:
            Résultat du téléchargement
        """
        import time
        start_time = time.time()

        async with semaphore:
            # Vérification d'existence
            if self.skip_existing and file_path.exists():
                self.logger.debug(f"Skip (déjà existant): {file_path.name}")
                self.stats['skipped'] += 1
                return DownloadResult(
                    url=url,
                    file_path=file_path,
                    success=True,
                    size=file_path.stat().st_size
                )

            # Rate limiting
            if self.rate_limit_delay > 0:
                await asyncio.sleep(self.rate_limit_delay)

            # Retry handler
            retry_handler = RetryHandler(
                max_retries=self.max_retries,
                base_delay=1.0,
                exceptions=(aiohttp.ClientError, asyncio.TimeoutError)
            )

            async def _download():
                # Crée le dossier parent si nécessaire
                file_path.parent.mkdir(parents=True, exist_ok=True)

                timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
                async with session.get(url, timeout=timeout_obj, headers=self.headers) as response:
                    response.raise_for_status()

                    # Téléchargement par streaming
                    total_size = 0
                    async with aiofiles.open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(self.chunk_size):
                            await f.write(chunk)
                            total_size += len(chunk)

                    return total_size

            try:
                size = await retry_handler.execute(_download)
                duration = time.time() - start_time

                self.stats['succeeded'] += 1
                self.stats['total_size'] += size

                return DownloadResult(
                    url=url,
                    file_path=file_path,
                    success=True,
                    size=size,
                    duration=duration
                )

            except Exception as e:
                duration = time.time() - start_time
                self.logger.error(f"Échec téléchargement {url}: {e}")
                self.stats['failed'] += 1

                return DownloadResult(
                    url=url,
                    file_path=file_path,
                    success=False,
                    error=str(e),
                    duration=duration
                )

    async def download_batch(self,
                             downloads: List[tuple],
                             progress_callback: Optional[Callable] = None) -> List[DownloadResult]:
        """
        Télécharge un lot de fichiers en parallèle

        Args:
            downloads: Liste de tuples (url, file_path)
            progress_callback: Callback appelé après chaque téléchargement

        Returns:
            Liste des résultats
        """
        self.stats['total'] = len(downloads)

        # Semaphore pour limiter la concurrence
        semaphore = asyncio.Semaphore(self.max_concurrent)

        # Session HTTP partagée
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Créer toutes les tâches
            tasks = [
                self.download_file(session, url, Path(file_path), semaphore)
                for url, file_path in downloads
            ]

            # Exécuter avec progression
            results = []
            for coro in asyncio.as_completed(tasks):
                result = await coro
                results.append(result)

                if progress_callback:
                    progress_callback(result)

            return results

    def download_sync(self,
                      downloads: List[tuple],
                      show_progress: bool = True) -> List[DownloadResult]:
        """
        Version synchrone pour appel depuis du code non-async

        Args:
            downloads: Liste de tuples (url, file_path)
            show_progress: Si True, affiche une barre de progression

        Returns:
            Liste des résultats

        Example:
            downloader = AsyncDownloader(max_concurrent=50)
            downloads = [
                ("http://example.com/img1.jpg", "output/img1.jpg"),
                ("http://example.com/img2.jpg", "output/img2.jpg"),
            ]
            results = downloader.download_sync(downloads)
        """
        # Barre de progression
        progress = None
        if show_progress:
            progress = ProgressTracker(
                total=len(downloads),
                desc="Downloading",
                unit="file"
            )
            progress.start()

        def progress_callback(result: DownloadResult):
            if progress:
                status = "✓" if result.success else "✗"
                progress.update(1)
                progress.set_postfix(
                    succeeded=self.stats['succeeded'],
                    failed=self.stats['failed'],
                    skipped=self.stats['skipped']
                )

        # Exécution async
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        results = loop.run_until_complete(
            self.download_batch(downloads, progress_callback if show_progress else None)
        )

        if progress:
            progress.close()

        return results

    def get_stats(self) -> dict:
        """
        Retourne les statistiques de téléchargement

        Returns:
            Dict avec statistiques
        """
        stats = self.stats.copy()
        if stats['total'] > 0:
            stats['success_rate'] = (stats['succeeded'] / stats['total']) * 100
        else:
            stats['success_rate'] = 0
        return stats

    def print_summary(self):
        """Affiche un résumé des téléchargements"""
        from .progress import format_size

        stats = self.get_stats()

        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TÉLÉCHARGEMENTS")
        print("=" * 60)
        print(f"Total de fichiers    : {stats['total']}")
        print(f"✓ Réussis            : {stats['succeeded']}")
        print(f"✗ Échoués            : {stats['failed']}")
        print(f"⊘ Ignorés (existants): {stats['skipped']}")
        print(f"Taille totale        : {format_size(stats['total_size'])}")
        print(f"Taux de réussite     : {stats['success_rate']:.1f}%")
        print("=" * 60)


async def download_urls_async(urls: List[str],
                               output_dir: Path,
                               filename_template: str = "{index}.dat",
                               **kwargs) -> List[DownloadResult]:
    """
    Fonction helper pour télécharger une liste d'URLs

    Args:
        urls: Liste des URLs
        output_dir: Dossier de sortie
        filename_template: Template pour les noms de fichiers (peut contenir {index}, {url})
        **kwargs: Arguments pour AsyncDownloader

    Returns:
        Liste des résultats

    Example:
        urls = ["http://example.com/img1.jpg", "http://example.com/img2.jpg"]
        results = await download_urls_async(urls, Path("output"))
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Prépare les tuples (url, file_path)
    downloads = []
    for index, url in enumerate(urls, start=1):
        # Extraction du nom de fichier depuis l'URL si possible
        url_parts = url.split('/')
        url_filename = url_parts[-1] if url_parts else f"file_{index}"

        filename = filename_template.format(
            index=index,
            url=url_filename
        )
        file_path = output_dir / filename
        downloads.append((url, file_path))

    # Téléchargement
    downloader = AsyncDownloader(**kwargs)
    results = await downloader.download_batch(downloads)

    return results


def download_urls(urls: List[str],
                  output_dir: Path,
                  filename_template: str = "{index}.dat",
                  **kwargs) -> List[DownloadResult]:
    """
    Version synchrone de download_urls_async

    Args:
        urls: Liste des URLs
        output_dir: Dossier de sortie
        filename_template: Template pour les noms de fichiers
        **kwargs: Arguments pour AsyncDownloader

    Returns:
        Liste des résultats

    Example:
        urls = ["http://example.com/img1.jpg", "http://example.com/img2.jpg"]
        results = download_urls(urls, Path("output"), max_concurrent=50)
    """
    downloader = AsyncDownloader(**kwargs)

    output_dir = Path(output_dir)
    downloads = []
    for index, url in enumerate(urls, start=1):
        url_parts = url.split('/')
        url_filename = url_parts[-1] if url_parts else f"file_{index}"

        filename = filename_template.format(
            index=index,
            url=url_filename
        )
        file_path = output_dir / filename
        downloads.append((url, file_path))

    return downloader.download_sync(downloads)
