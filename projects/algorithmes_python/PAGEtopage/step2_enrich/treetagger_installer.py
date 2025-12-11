"""
Installation automatique de TreeTagger pour PAGEtopage

Ce module gère le téléchargement et l'installation automatique de TreeTagger
dans le répertoire vendor du projet pour une expérience clé en main.
"""

import logging
import os
import platform
import tarfile
import zipfile
from pathlib import Path
from typing import Optional
import urllib.request
import shutil

logger = logging.getLogger(__name__)


class TreeTaggerInstaller:
    """
    Installateur automatique de TreeTagger

    Télécharge et installe TreeTagger localement dans le projet
    pour une utilisation sans configuration manuelle.
    """

    # URLs de téléchargement TreeTagger
    BASE_URL = "https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data"

    DOWNLOADS = {
        "Linux": {
            "binary": f"{BASE_URL}/tree-tagger-linux-3.2.5.tar.gz",
            "tagger_scripts": f"{BASE_URL}/tagger-scripts.tar.gz",
            "install_script": f"{BASE_URL}/install-tagger.sh",
        },
        "Darwin": {  # macOS
            "binary": f"{BASE_URL}/tree-tagger-MacOSX-3.2.5.tar.gz",
            "tagger_scripts": f"{BASE_URL}/tagger-scripts.tar.gz",
            "install_script": f"{BASE_URL}/install-tagger.sh",
        },
        "Windows": {
            "binary": f"{BASE_URL}/tree-tagger-windows-3.2.5.zip",
            "tagger_scripts": f"{BASE_URL}/tagger-scripts.tar.gz",
            "install_script": None,
        }
    }

    # Paramètres de langue pour le latin
    LATIN_PARAMS = f"{BASE_URL}/latin.par.gz"

    def __init__(self, install_dir: Optional[Path] = None):
        """
        Args:
            install_dir: Répertoire d'installation (par défaut: vendor/treetagger dans le projet)
        """
        if install_dir is None:
            # Utilise vendor/treetagger dans le répertoire du module
            module_dir = Path(__file__).parent.parent
            install_dir = module_dir / "vendor" / "treetagger"

        self.install_dir = Path(install_dir)
        self.system = platform.system()

        if self.system not in self.DOWNLOADS:
            raise OSError(f"Système non supporté: {self.system}")

    def is_installed(self) -> bool:
        """Vérifie si TreeTagger est déjà installé"""
        if not self.install_dir.exists():
            return False

        # Vérifie la présence des fichiers essentiels
        binary_name = "tree-tagger.exe" if self.system == "Windows" else "tree-tagger"
        binary_path = self.install_dir / "bin" / binary_name

        latin_params = self.install_dir / "lib" / "latin.par"

        return binary_path.exists() and latin_params.exists()

    def install(self, force: bool = False) -> Path:
        """
        Installe TreeTagger automatiquement

        Args:
            force: Force la réinstallation même si déjà présent

        Returns:
            Chemin vers l'installation TreeTagger

        Raises:
            Exception: Si l'installation échoue
        """
        if self.is_installed() and not force:
            logger.info(f"TreeTagger déjà installé dans {self.install_dir}")
            return self.install_dir

        logger.info("Installation automatique de TreeTagger...")
        logger.info(f"Répertoire: {self.install_dir}")

        try:
            # Crée le répertoire d'installation
            self.install_dir.mkdir(parents=True, exist_ok=True)

            # Télécharge et installe les composants
            self._download_and_extract_binary()
            self._download_and_extract_scripts()
            self._download_latin_params()

            # Rend les binaires exécutables sur Unix
            if self.system != "Windows":
                self._make_executable()

            logger.info("✓ TreeTagger installé avec succès")
            return self.install_dir

        except Exception as e:
            logger.error(f"Erreur lors de l'installation de TreeTagger: {e}")
            # Nettoie en cas d'erreur
            if self.install_dir.exists():
                shutil.rmtree(self.install_dir)
            raise

    def _download_file(self, url: str, dest: Path) -> None:
        """Télécharge un fichier avec barre de progression"""
        logger.info(f"Téléchargement: {url}")

        dest.parent.mkdir(parents=True, exist_ok=True)

        def progress_hook(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, block_num * block_size * 100 / total_size)
                logger.debug(f"Progression: {percent:.1f}%")

        urllib.request.urlretrieve(url, dest, reporthook=progress_hook)
        logger.info(f"✓ Téléchargé: {dest.name}")

    def _download_and_extract_binary(self) -> None:
        """Télécharge et extrait le binaire TreeTagger"""
        url = self.DOWNLOADS[self.system]["binary"]
        filename = url.split("/")[-1]
        archive_path = self.install_dir / filename

        self._download_file(url, archive_path)

        logger.info("Extraction du binaire TreeTagger...")

        if filename.endswith(".tar.gz"):
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(self.install_dir)
        elif filename.endswith(".zip"):
            with zipfile.ZipFile(archive_path, "r") as zip_ref:
                zip_ref.extractall(self.install_dir)

        archive_path.unlink()  # Supprime l'archive
        logger.info("✓ Binaire extrait")

    def _download_and_extract_scripts(self) -> None:
        """Télécharge et extrait les scripts tagger"""
        url = self.DOWNLOADS[self.system]["tagger_scripts"]
        filename = "tagger-scripts.tar.gz"
        archive_path = self.install_dir / filename

        self._download_file(url, archive_path)

        logger.info("Extraction des scripts...")
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(self.install_dir)

        archive_path.unlink()
        logger.info("✓ Scripts extraits")

    def _download_latin_params(self) -> None:
        """Télécharge les paramètres pour le latin"""
        lib_dir = self.install_dir / "lib"
        lib_dir.mkdir(exist_ok=True)

        # Télécharge latin.par.gz
        gz_path = lib_dir / "latin.par.gz"
        self._download_file(self.LATIN_PARAMS, gz_path)

        # Décompresse
        logger.info("Décompression des paramètres latin...")
        import gzip
        par_path = lib_dir / "latin.par"

        with gzip.open(gz_path, "rb") as f_in:
            with open(par_path, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        gz_path.unlink()
        logger.info("✓ Paramètres latin installés")

    def _make_executable(self) -> None:
        """Rend les binaires exécutables (Unix)"""
        bin_dir = self.install_dir / "bin"
        if not bin_dir.exists():
            return

        for binary in bin_dir.glob("*"):
            if binary.is_file():
                os.chmod(binary, 0o755)

        # Scripts aussi
        for script in self.install_dir.glob("cmd/*.sh"):
            os.chmod(script, 0o755)

        logger.info("✓ Permissions exécutables définies")

    def get_install_path(self) -> Path:
        """Retourne le chemin d'installation"""
        return self.install_dir


def get_treetagger_path(auto_install: bool = True) -> Optional[Path]:
    """
    Obtient le chemin vers TreeTagger, avec installation automatique optionnelle

    Args:
        auto_install: Si True, installe automatiquement TreeTagger s'il n'est pas trouvé

    Returns:
        Chemin vers l'installation TreeTagger, ou None si non trouvé/installé
    """
    installer = TreeTaggerInstaller()

    # Vérifie si déjà installé localement
    if installer.is_installed():
        return installer.get_install_path()

    # Cherche dans les emplacements standards
    if platform.system() == "Linux":
        standard_paths = [
            Path("/opt/treetagger"),
            Path("/usr/local/treetagger"),
            Path("/usr/share/treetagger"),
            Path.home() / "treetagger",
        ]
    elif platform.system() == "Darwin":
        standard_paths = [
            Path("/usr/local/treetagger"),
            Path("/opt/treetagger"),
            Path.home() / "treetagger",
        ]
    else:  # Windows
        standard_paths = [
            Path("C:/TreeTagger"),
            Path("C:/Program Files/TreeTagger"),
        ]

    for path in standard_paths:
        if path.exists():
            logger.info(f"TreeTagger trouvé dans {path}")
            return path

    # Installation automatique si demandé
    if auto_install:
        try:
            logger.info("TreeTagger non trouvé, installation automatique...")
            return installer.install()
        except Exception as e:
            logger.error(f"Échec de l'installation automatique: {e}")
            return None

    return None


def ensure_treetagger() -> Path:
    """
    Garantit que TreeTagger est disponible, l'installe si nécessaire

    Returns:
        Chemin vers TreeTagger

    Raises:
        RuntimeError: Si TreeTagger ne peut pas être installé
    """
    path = get_treetagger_path(auto_install=True)

    if path is None:
        raise RuntimeError(
            "Impossible d'installer TreeTagger automatiquement. "
            "Veuillez l'installer manuellement depuis: "
            "https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/"
        )

    return path
