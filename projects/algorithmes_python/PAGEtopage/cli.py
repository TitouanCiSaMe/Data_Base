"""
Interface en ligne de commande pour PAGEtopage

Fournit les commandes:
    - extract : XML PAGE → JSON
    - enrich  : JSON → Format Vertical
    - export  : Format Vertical → Texte
    - run     : Pipeline complet

Usage:
    python -m PAGEtopage extract --input ./xml/ --output ./extracted/
    python -m PAGEtopage enrich --input ./extracted/ --output ./vertical/
    python -m PAGEtopage export --input ./vertical/ --output ./pages/
    python -m PAGEtopage run --input ./xml/ --output ./output/ --config config.yaml
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from .config import Config
from .step1_extract import XMLPageExtractor
from .step2_enrich import EnrichmentProcessor
from .step3_export import TextExporter

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("PAGEtopage")


def create_parser() -> argparse.ArgumentParser:
    """Crée le parser d'arguments"""

    parser = argparse.ArgumentParser(
        prog="PAGEtopage",
        description="Pipeline de traitement XML PAGE → Format Vertical → Texte",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Étape 1: Extraction XML → JSON
  python -m PAGEtopage extract --input ./xml/ --output ./extracted/

  # Étape 2: Enrichissement JSON → Vertical
  python -m PAGEtopage enrich --input ./extracted/ --output ./vertical/

  # Étape 3: Export Vertical → Texte
  python -m PAGEtopage export --input ./vertical/ --output ./pages/

  # Pipeline complet
  python -m PAGEtopage run --input ./xml/ --output ./output/ --config config.yaml
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mode verbeux (debug)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commandes disponibles")

    # === Commande EXTRACT ===
    extract_parser = subparsers.add_parser(
        "extract",
        help="Étape 1: Extrait le texte des fichiers XML PAGE"
    )
    extract_parser.add_argument(
        "--input", "-i",
        required=True,
        help="Dossier contenant les fichiers XML PAGE"
    )
    extract_parser.add_argument(
        "--output", "-o",
        required=True,
        help="Chemin de sortie (fichier JSON ou dossier)"
    )
    extract_parser.add_argument(
        "--config", "-c",
        help="Fichier de configuration YAML"
    )
    extract_parser.add_argument(
        "--column-mode",
        choices=["single", "dual"],
        default="single",
        help="Mode de colonnes (single ou dual)"
    )
    extract_parser.add_argument(
        "--starting-page",
        type=int,
        default=1,
        help="Numéro de la première page"
    )
    extract_parser.add_argument(
        "--individual",
        action="store_true",
        help="Crée un fichier JSON par page"
    )

    # === Commande ENRICH ===
    enrich_parser = subparsers.add_parser(
        "enrich",
        help="Étape 2: Enrichit avec lemmatisation et POS tagging"
    )
    enrich_parser.add_argument(
        "--input", "-i",
        required=True,
        help="Fichier JSON ou dossier (sortie étape 1)"
    )
    enrich_parser.add_argument(
        "--output", "-o",
        required=True,
        help="Fichier de sortie vertical"
    )
    enrich_parser.add_argument(
        "--config", "-c",
        help="Fichier de configuration YAML"
    )
    enrich_parser.add_argument(
        "--lemmatizer",
        choices=["cltk", "simple"],
        default="cltk",
        help="Lemmatiseur à utiliser"
    )
    enrich_parser.add_argument(
        "--language",
        default="lat",
        help="Code langue (lat pour latin)"
    )

    # === Commande EXPORT ===
    export_parser = subparsers.add_parser(
        "export",
        help="Étape 3: Exporte vers fichiers texte"
    )
    export_parser.add_argument(
        "--input", "-i",
        required=True,
        help="Fichier vertical (sortie étape 2)"
    )
    export_parser.add_argument(
        "--output", "-o",
        required=True,
        help="Dossier de sortie"
    )
    export_parser.add_argument(
        "--config", "-c",
        help="Fichier de configuration YAML"
    )
    export_parser.add_argument(
        "--format", "-f",
        choices=["clean", "diplomatic", "annotated"],
        default="clean",
        help="Format de sortie"
    )
    export_parser.add_argument(
        "--no-index",
        action="store_true",
        help="Ne pas générer les fichiers d'index"
    )
    export_parser.add_argument(
        "--no-combined",
        action="store_true",
        help="Ne pas générer le texte complet"
    )

    # === Commande RUN (pipeline complet) ===
    run_parser = subparsers.add_parser(
        "run",
        help="Exécute le pipeline complet"
    )
    run_parser.add_argument(
        "--input", "-i",
        required=True,
        help="Dossier contenant les fichiers XML PAGE"
    )
    run_parser.add_argument(
        "--output", "-o",
        required=True,
        help="Dossier de sortie"
    )
    run_parser.add_argument(
        "--config", "-c",
        required=True,
        help="Fichier de configuration YAML"
    )
    run_parser.add_argument(
        "--keep-intermediate",
        action="store_true",
        help="Conserve les fichiers intermédiaires"
    )

    # === Commande INIT (génère un fichier de config) ===
    init_parser = subparsers.add_parser(
        "init",
        help="Génère un fichier de configuration exemple"
    )
    init_parser.add_argument(
        "--output", "-o",
        default="config.yaml",
        help="Chemin du fichier de configuration"
    )

    return parser


def cmd_extract(args) -> int:
    """Exécute la commande extract"""
    logger.info("=== ÉTAPE 1: EXTRACTION XML ===")

    # Charge ou crée la config
    if args.config:
        config = Config.from_yaml(args.config)
    else:
        config = Config()

    # Applique les options CLI
    config.extraction.column_mode = args.column_mode
    config.pagination.starting_page_number = args.starting_page

    # Crée l'extracteur
    extractor = XMLPageExtractor(config)

    # Extrait
    pages = extractor.extract_folder(args.input)

    if not pages:
        logger.error("Aucune page extraite")
        return 1

    # Sauvegarde
    output_path = Path(args.output)
    if args.individual:
        extractor.save_individual_json(pages, output_path)
    else:
        if output_path.suffix != ".json":
            output_path = output_path / "extracted.json"
        extractor.save_to_json(pages, output_path)

    logger.info(f"✓ {len(pages)} pages extraites → {output_path}")
    return 0


def cmd_enrich(args) -> int:
    """Exécute la commande enrich"""
    logger.info("=== ÉTAPE 2: ENRICHISSEMENT ===")

    # Charge ou crée la config
    if args.config:
        config = Config.from_yaml(args.config)
    else:
        config = Config()

    # Applique les options CLI
    config.enrichment.lemmatizer = args.lemmatizer
    config.enrichment.language = args.language

    # Crée le processeur
    processor = EnrichmentProcessor(config)

    # Traite
    input_path = Path(args.input)
    if input_path.is_file():
        pages = processor.process_json(input_path)
    else:
        pages = processor.process_json_folder(input_path)

    if not pages:
        logger.error("Aucune page enrichie")
        return 1

    # Sauvegarde
    output_path = Path(args.output)
    if output_path.suffix == "":
        output_path = output_path / "corpus.vertical.txt"
    processor.save_vertical(pages, output_path)

    logger.info(f"✓ {len(pages)} pages enrichies → {output_path}")
    return 0


def cmd_export(args) -> int:
    """Exécute la commande export"""
    logger.info("=== ÉTAPE 3: EXPORT ===")

    # Charge ou crée la config
    if args.config:
        config = Config.from_yaml(args.config)
    else:
        config = Config()

    # Applique les options CLI
    config.export.format = args.format
    config.export.generate_index = not args.no_index
    config.export.generate_combined = not args.no_combined

    # Crée l'exporteur
    exporter = TextExporter(config)

    # Exporte
    page_files = exporter.export(args.input, args.output)

    logger.info(f"✓ {len(page_files)} pages exportées → {args.output}")
    return 0


def cmd_run(args) -> int:
    """Exécute le pipeline complet"""
    logger.info("=== PIPELINE COMPLET ===")

    # Charge la config
    config = Config.from_yaml(args.config)

    # Valide
    errors = config.validate()
    if errors:
        for error in errors:
            logger.error(f"Erreur de configuration: {error}")
        return 1

    output_folder = Path(args.output)
    output_folder.mkdir(parents=True, exist_ok=True)

    # === ÉTAPE 1 ===
    logger.info("--- Étape 1: Extraction XML ---")
    extractor = XMLPageExtractor(config)
    extracted_pages = extractor.extract_folder(args.input)

    if not extracted_pages:
        logger.error("Aucune page extraite")
        return 1

    if args.keep_intermediate:
        intermediate_json = output_folder / "intermediate" / "extracted.json"
        extractor.save_to_json(extracted_pages, intermediate_json)

    # === ÉTAPE 2 ===
    logger.info("--- Étape 2: Enrichissement ---")
    processor = EnrichmentProcessor(config)
    annotated_pages = processor.process_pages(extracted_pages)

    if args.keep_intermediate:
        intermediate_vertical = output_folder / "intermediate" / "corpus.vertical.txt"
        processor.save_vertical(annotated_pages, intermediate_vertical)

    # Sauvegarde le vertical final
    vertical_path = output_folder / "corpus.vertical.txt"
    processor.save_vertical(annotated_pages, vertical_path)

    # === ÉTAPE 3 ===
    logger.info("--- Étape 3: Export ---")
    exporter = TextExporter(config)
    pages_folder = output_folder / "pages"
    page_files = exporter.export_pages(annotated_pages, pages_folder)

    # Résumé
    logger.info("=" * 50)
    logger.info("✓ PIPELINE TERMINÉ")
    logger.info(f"  Pages traitées: {len(annotated_pages)}")
    logger.info(f"  Vertical: {vertical_path}")
    logger.info(f"  Pages texte: {pages_folder}")
    logger.info("=" * 50)

    return 0


def cmd_init(args) -> int:
    """Génère un fichier de configuration exemple"""
    output_path = Path(args.output)

    if output_path.exists():
        response = input(f"{output_path} existe déjà. Écraser? [y/N] ")
        if response.lower() != "y":
            logger.info("Annulé")
            return 0

    # Crée une config par défaut avec exemples
    config = Config()
    config.corpus.edition_id = "Edi-1"
    config.corpus.title = "Mon Corpus"
    config.corpus.language = "Latin"
    config.corpus.author = "Auteur"
    config.corpus.source = "Source"
    config.corpus.type = "Type"
    config.corpus.date = "Date"
    config.corpus.lieu = "Lieu"
    config.corpus.ville = "Ville"

    config.to_yaml(output_path)

    logger.info(f"✓ Configuration créée: {output_path}")
    logger.info("  Éditez ce fichier pour configurer votre pipeline.")
    return 0


def main() -> int:
    """Point d'entrée principal"""
    parser = create_parser()
    args = parser.parse_args()

    # Mode verbeux
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Dispatch
    if args.command == "extract":
        return cmd_extract(args)
    elif args.command == "enrich":
        return cmd_enrich(args)
    elif args.command == "export":
        return cmd_export(args)
    elif args.command == "run":
        return cmd_run(args)
    elif args.command == "init":
        return cmd_init(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
