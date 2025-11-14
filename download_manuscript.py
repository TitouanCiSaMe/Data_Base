#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de téléchargement de manuscrits depuis un manifest JSON IIIF

✨ Fonctionnalités :
- ✅ Télécharge uniquement les pages manquantes
- ✅ Gestion d'erreurs robuste avec retry automatique
- ✅ Progress bar détaillée
- ✅ Validation des URLs et codes HTTP
- ✅ Chemins configurables
- ✅ Logging complet
- ✅ Reprise automatique après interruption

Auteur: Script amélioré pour téléchargement de manuscrits
Date: 2025-01-14
"""

import json
import requests
from pathlib import Path
from tqdm import tqdm
import time
import logging
from typing import List, Tuple, Optional
import sys


class ManuscriptDownloader:
    """
    Téléchargeur de manuscrits depuis manifest JSON IIIF
    """

    def __init__(self,
                 manifest_path: str,
                 output_dir: str,
                 filename_template: str = "{manuscript}_{index:04d}.jpg",
                 delay: float = 2.0,
                 max_retries: int = 3,
                 timeout: int = 30):
        """
        Args:
            manifest_path: Chemin vers le fichier manifest.json
            output_dir: Dossier de sortie pour les images
            filename_template: Template pour les noms de fichiers (ex: "page_{index:04d}.jpg")
            delay: Délai entre chaque téléchargement en secondes
            max_retries: Nombre de tentatives en cas d'échec
            timeout: Timeout des requêtes HTTP en secondes
        """
        self.manifest_path = Path(manifest_path)
        self.output_dir = Path(output_dir)
        self.filename_template = filename_template
        self.delay = delay
        self.max_retries = max_retries
        self.timeout = timeout

        # Création du dossier de sortie
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Configuration du logging
        self._setup_logging()

        # Statistiques
        self.stats = {
            'total': 0,
            'downloaded': 0,
            'skipped': 0,
            'failed': 0,
            'total_size': 0
        }

    def _setup_logging(self):
        """Configure le système de logging"""
        log_file = self.output_dir / "download.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def extract_ids(self, json_obj, key: str):
        """
        Extrait récursivement toutes les valeurs d'une clé dans un JSON

        Args:
            json_obj: Objet JSON (dict ou list)
            key: Clé à rechercher

        Yields:
            Valeurs correspondant à la clé
        """
        if isinstance(json_obj, dict):
            for k, v in json_obj.items():
                if k == key:
                    yield v
                else:
                    yield from self.extract_ids(v, key)
        elif isinstance(json_obj, list):
            for item in json_obj:
                yield from self.extract_ids(item, key)

    def load_manifest(self) -> List[str]:
        """
        Charge le manifest et extrait les URLs d'images

        Returns:
            Liste des URLs d'images .jpg
        """
        self.logger.info(f"📖 Lecture du manifest : {self.manifest_path}")

        if not self.manifest_path.exists():
            raise FileNotFoundError(f"❌ Manifest non trouvé : {self.manifest_path}")

        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extraction de tous les IDs
        all_ids = list(self.extract_ids(data, '@id'))
        self.logger.info(f"   → {len(all_ids)} IDs trouvés")

        # Filtrer uniquement les .jpg
        jpg_urls = [url for url in all_ids if url.endswith('.jpg')]
        self.logger.info(f"   → {len(jpg_urls)} URLs d'images .jpg")

        return jpg_urls

    def download_image(self, url: str, file_path: Path) -> Tuple[bool, int]:
        """
        Télécharge une image avec retry automatique

        Args:
            url: URL de l'image
            file_path: Chemin de destination

        Returns:
            (success, size) - Tuple avec succès et taille en octets
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.get(
                    url,
                    timeout=self.timeout,
                    stream=True
                )
                response.raise_for_status()  # Lève une exception si code 4xx ou 5xx

                # Téléchargement par chunks pour grandes images
                total_size = 0
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            total_size += len(chunk)

                return True, total_size

            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Backoff exponentiel : 2, 4, 8 secondes
                    self.logger.warning(
                        f"   ⚠️  Échec tentative {attempt}/{self.max_retries} pour {file_path.name}: {e}"
                    )
                    self.logger.warning(f"   ⏳ Nouvelle tentative dans {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    self.logger.error(f"   ❌ Échec définitif pour {file_path.name}: {e}")
                    return False, 0

        return False, 0

    def get_manuscript_name(self) -> str:
        """
        Extrait le nom du manuscrit depuis le chemin de sortie

        Returns:
            Nom du manuscrit
        """
        return self.output_dir.name

    def download_all(self, save_urls: bool = True):
        """
        Télécharge toutes les images du manifest

        Args:
            save_urls: Si True, sauvegarde la liste des URLs dans un fichier texte
        """
        print("\n" + "=" * 70)
        print("📥 TÉLÉCHARGEMENT DE MANUSCRIT DEPUIS MANIFEST IIIF")
        print("=" * 70)
        print(f"Manifest       : {self.manifest_path}")
        print(f"Dossier sortie : {self.output_dir}")
        print(f"Délai/image    : {self.delay}s")
        print(f"Max retries    : {self.max_retries}")
        print("=" * 70 + "\n")

        # Chargement du manifest
        try:
            urls = self.load_manifest()
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du chargement du manifest: {e}")
            sys.exit(1)

        if not urls:
            self.logger.error("❌ Aucune URL d'image trouvée dans le manifest")
            sys.exit(1)

        self.stats['total'] = len(urls)

        # Sauvegarde optionnelle des URLs
        if save_urls:
            urls_file = self.output_dir / "urls_downloaded.txt"
            with open(urls_file, 'w', encoding='utf-8') as f:
                for url in urls:
                    f.write(url + '\n')
            self.logger.info(f"💾 URLs sauvegardées dans : {urls_file}\n")

        # Nom du manuscrit pour le template
        manuscript_name = self.get_manuscript_name()

        # Téléchargement avec barre de progression
        print(f"📥 Téléchargement de {len(urls)} images...\n")

        with tqdm(total=len(urls), desc="Téléchargement", unit="img") as pbar:
            # CORRECTION DU BUG : range(len(urls)) au lieu de range(1, len(urls))
            for i in range(len(urls)):
                url = urls[i]

                # Génération du nom de fichier (index commence à 1 pour lisibilité)
                filename = self.filename_template.format(
                    manuscript=manuscript_name,
                    index=i + 1,
                    total=len(urls)
                )
                file_path = self.output_dir / filename

                # ⭐ FONCTIONNALITÉ CLÉ : Skip si le fichier existe déjà
                if file_path.exists():
                    self.stats['skipped'] += 1
                    pbar.set_postfix({
                        'téléchargées': self.stats['downloaded'],
                        'ignorées': self.stats['skipped'],
                        'échouées': self.stats['failed']
                    })
                    pbar.update(1)
                    self.logger.debug(f"⊘ Skip (existe) : {filename}")
                    continue

                # Téléchargement de l'image
                success, size = self.download_image(url, file_path)

                if success:
                    self.stats['downloaded'] += 1
                    self.stats['total_size'] += size
                    self.logger.debug(f"✓ Téléchargée : {filename} ({self._format_size(size)})")
                else:
                    self.stats['failed'] += 1

                # Mise à jour de la barre de progression
                pbar.set_postfix({
                    'téléchargées': self.stats['downloaded'],
                    'ignorées': self.stats['skipped'],
                    'échouées': self.stats['failed']
                })
                pbar.update(1)

                # Rate limiting (sauf pour la dernière image)
                if i < len(urls) - 1 and success:
                    time.sleep(self.delay)

        # Affichage du résumé
        self.print_summary()

    def _format_size(self, size: int) -> str:
        """
        Formate une taille en octets de manière lisible

        Args:
            size: Taille en octets

        Returns:
            Chaîne formatée (ex: "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def print_summary(self):
        """Affiche un résumé des téléchargements"""
        print("\n" + "=" * 70)
        print("📊 RÉSUMÉ DU TÉLÉCHARGEMENT")
        print("=" * 70)
        print(f"Total d'images       : {self.stats['total']}")
        print(f"✓ Téléchargées       : {self.stats['downloaded']}")
        print(f"⊘ Ignorées (existent): {self.stats['skipped']}")
        print(f"✗ Échouées           : {self.stats['failed']}")
        print(f"Taille téléchargée   : {self._format_size(self.stats['total_size'])}")

        if self.stats['total'] > 0:
            success_rate = ((self.stats['downloaded'] + self.stats['skipped']) / self.stats['total']) * 100
            print(f"Taux de succès       : {success_rate:.1f}%")

        print("=" * 70)

        if self.stats['failed'] > 0:
            print(f"\n⚠️  {self.stats['failed']} image(s) n'ont pas pu être téléchargée(s)")
            print(f"   Consultez le log : {self.output_dir / 'download.log'}")

        if self.stats['downloaded'] > 0:
            print(f"\n✅ {self.stats['downloaded']} nouvelle(s) image(s) téléchargée(s) avec succès!")

        if self.stats['skipped'] > 0:
            print(f"ℹ️  {self.stats['skipped']} image(s) déjà présente(s), ignorée(s)")


def main():
    """
    Fonction principale - Configuration et lancement du téléchargement
    """
    # ========================================================================
    # 🔧 CONFIGURATION - Modifiez ces valeurs selon vos besoins
    # ========================================================================

    MANIFEST_PATH = "/home/titouan/Téléchargements/Manuscrit_télécharger/manifest.json"
    OUTPUT_DIR = "/home/titouan/Téléchargements/Manuscrit_télécharger/Latin_18108"

    # Template pour les noms de fichiers
    # Variables disponibles : {manuscript}, {index}, {total}
    # {index:04d} = index sur 4 chiffres avec zéros (0001, 0002, ...)
    FILENAME_TEMPLATE = "{manuscript}_{index:04d}.jpg"

    # Paramètres de téléchargement
    DELAY = 2.0          # Délai entre chaque téléchargement (secondes)
    MAX_RETRIES = 3      # Nombre de tentatives en cas d'échec
    TIMEOUT = 30         # Timeout des requêtes HTTP (secondes)
    SAVE_URLS = True     # Sauvegarder la liste des URLs dans un fichier

    # ========================================================================
    # 🚀 LANCEMENT DU TÉLÉCHARGEMENT
    # ========================================================================

    try:
        downloader = ManuscriptDownloader(
            manifest_path=MANIFEST_PATH,
            output_dir=OUTPUT_DIR,
            filename_template=FILENAME_TEMPLATE,
            delay=DELAY,
            max_retries=MAX_RETRIES,
            timeout=TIMEOUT
        )

        downloader.download_all(save_urls=SAVE_URLS)

    except KeyboardInterrupt:
        print("\n\n⚠️  Téléchargement interrompu par l'utilisateur")
        print("💡 Relancez le script pour reprendre le téléchargement (les fichiers existants seront ignorés)")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur fatale : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
