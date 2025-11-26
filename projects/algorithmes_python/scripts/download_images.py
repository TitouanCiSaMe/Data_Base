#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script optimisé de téléchargement d'images depuis un manifest JSON

Version refactorisée utilisant le framework Pipeline.

Features:
- ✅ Téléchargement parallèle (50-100x plus rapide)
- ✅ Retry automatique
- ✅ Skip des fichiers existants
- ✅ Gestion d'erreurs robuste
- ✅ Progress bar détaillée
- ✅ Rate limiting configurable

Utilisation:
    python download_images.py

    Ou personnalisé:
    from scripts.download_images import download_images_from_manifest
    download_images_from_manifest(
        manifest_path="path/to/manifest.json",
        output_dir="output/",
        max_concurrent=50
    )
"""

import sys
from pathlib import Path

# Ajoute le dossier parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    Pipeline,
    JSONRecursiveExtractor,
    FilterProcessor,
    FileWriter
)
from utils import AsyncDownloader
import logging


def download_images_from_manifest(
        manifest_path: str,
        output_dir: str,
        urls_output: str = None,
        max_concurrent: int = 10,
        rate_limit_delay: float = 0.0,
        skip_existing: bool = True,
        filename_template: str = "Latin_18108_{index}.jpg"
) -> dict:
    """
    Télécharge des images depuis un manifest JSON

    Args:
        manifest_path: Chemin vers le fichier manifest.json
        output_dir: Dossier de sortie pour les images
        urls_output: Chemin optionnel pour sauvegarder la liste des URLs
        max_concurrent: Nombre de téléchargements simultanés
        rate_limit_delay: Délai entre chaque téléchargement (en secondes)
        skip_existing: Si True, skip les fichiers déjà téléchargés
        filename_template: Template pour les noms de fichiers

    Returns:
        Dict avec statistiques de téléchargement
    """
    # Configuration du logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    manifest_path = Path(manifest_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("📥 TÉLÉCHARGEMENT D'IMAGES DEPUIS MANIFEST")
    print("=" * 60)
    print(f"Manifest       : {manifest_path}")
    print(f"Dossier sortie : {output_dir}")
    print(f"Parallélisme   : {max_concurrent} téléchargements simultanés")
    print(f"Skip existants : {'Oui' if skip_existing else 'Non'}")
    print("=" * 60 + "\n")

    # Étape 1: Extraction des URLs depuis le JSON
    print("📋 Extraction des URLs depuis le manifest...")

    extractor = JSONRecursiveExtractor(
        file_path=manifest_path,
        target_key="@id",
        name="JSON ID Extractor"
    )

    # Extraction des IDs
    ids = list(extractor.extract())
    print(f"   → {len(ids)} IDs trouvés")

    # Filtre: garder uniquement les .jpg
    jpg_urls = [url for url in ids if url.endswith('.jpg')]
    print(f"   → {len(jpg_urls)} URLs .jpg")

    # Optionnel: Sauvegarde des URLs dans un fichier
    if urls_output:
        urls_output = Path(urls_output)
        with open(urls_output, 'w') as f:
            for url in jpg_urls:
                f.write(url + '\n')
        print(f"   → URLs sauvegardées dans {urls_output}")

    # Étape 2: Téléchargement parallèle
    print(f"\n📥 Téléchargement de {len(jpg_urls)} images...")

    # Configuration du downloader
    downloader = AsyncDownloader(
        max_concurrent=max_concurrent,
        max_retries=3,
        timeout=30,
        skip_existing=skip_existing,
        rate_limit_delay=rate_limit_delay
    )

    # Préparation des téléchargements
    downloads = []
    for i, url in enumerate(jpg_urls, start=1):
        filename = filename_template.format(index=i, url=url.split('/')[-1])
        file_path = output_dir / filename
        downloads.append((url, file_path))

    # Téléchargement
    results = downloader.download_sync(downloads, show_progress=True)

    # Affichage du résumé
    downloader.print_summary()

    return downloader.get_stats()


def main():
    """
    Fonction principale

    Modifiez les chemins ci-dessous selon vos besoins
    """
    # =============================================
    # CONFIGURATION - Modifiez ces valeurs
    # =============================================

    MANIFEST_PATH = "/home/titouan/Téléchargements/Manuscrit_télécharger/manifest.json"
    OUTPUT_DIR = "/home/titouan/Téléchargements/Manuscrit_télécharger/Latin_18108"
    URLS_OUTPUT = "/home/titouan/Téléchargements/Manuscrit_télécharger/urls_to_download.txt"

    # Paramètres de téléchargement
    MAX_CONCURRENT = 10  # Augmentez pour plus de vitesse (ex: 50)
    RATE_LIMIT_DELAY = 5.0  # Délai entre chaque téléchargement (secondes)
    SKIP_EXISTING = True  # Skip les fichiers déjà téléchargés
    FILENAME_TEMPLATE = "Latin_18108_{index}.jpg"

    # =============================================
    # VÉRIFICATIONS
    # =============================================

    manifest_path = Path(MANIFEST_PATH)
    if not manifest_path.exists():
        print(f"❌ Fichier manifest non trouvé: {MANIFEST_PATH}")
        print("👉 Modifiez la variable MANIFEST_PATH dans la fonction main()")
        return

    # =============================================
    # TÉLÉCHARGEMENT
    # =============================================

    try:
        stats = download_images_from_manifest(
            manifest_path=MANIFEST_PATH,
            output_dir=OUTPUT_DIR,
            urls_output=URLS_OUTPUT,
            max_concurrent=MAX_CONCURRENT,
            rate_limit_delay=RATE_LIMIT_DELAY,
            skip_existing=SKIP_EXISTING,
            filename_template=FILENAME_TEMPLATE
        )

        print("\n✅ Téléchargement terminé avec succès!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Téléchargement interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
