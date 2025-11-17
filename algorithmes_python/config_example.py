"""
Exemples de configuration pour XMLCorpusProcessor.

Ce fichier contient plusieurs configurations prêtes à l'emploi
pour différents cas d'usage typiques.
"""

import logging
from xml_corpus_processor import XMLCorpusProcessor, ProcessingConfig


# ============================================================================
# EXEMPLE 1 : Configuration minimale
# ============================================================================

def exemple_minimal():
    """Configuration la plus simple possible."""
    config = ProcessingConfig(
        input_folder="/chemin/vers/dossier_xml",
        output_file="/chemin/vers/sortie.txt",
        language='la'
    )

    processor = XMLCorpusProcessor(config)
    processor.process_corpus()


# ============================================================================
# EXEMPLE 2 : Manuscrit latin avec métadonnées complètes
# ============================================================================

def exemple_manuscrit_latin():
    """Traitement d'un manuscrit latin théologique."""
    config = ProcessingConfig(
        input_folder="/data/manuscripts/anselm/tractatus_decretum",
        output_file="/output/corpus/decretum_dei_fuit.txt",
        language='la',  # Latin
        log_level=logging.INFO,
        metadata={
            "edition_id": "Edi-52",
            "title": "Das Schrifttum des Schule Anselms von Laon",
            "language": "Latin",
            "author": "Anonyme",
            "source": "tractatus 'Decretum Dei fuit'",
            "type": "Théologie",
            "date": "1100-1150",
            "lieu": "France",
            "ville": "Laon"
        },
        page_numbering_source='filename',
        starting_page_number=361,  # Le manuscrit commence à la page 361
        include_empty_folios=True
    )

    processor = XMLCorpusProcessor(config)
    processor.process_corpus()


# ============================================================================
# EXEMPLE 3 : Texte français moderne
# ============================================================================

def exemple_texte_francais():
    """Traitement d'un texte en français."""
    config = ProcessingConfig(
        input_folder="/data/corpus/francais/texte_moderne",
        output_file="/output/corpus/francais_moderne.txt",
        language='fr',  # Français
        log_level=logging.INFO,
        metadata={
            "edition_id": "FR-2025-001",
            "title": "Corpus de français moderne",
            "language": "Français",
            "author": "Divers",
            "date": "2000-2025",
            "type": "Littérature"
        },
        page_numbering_source='numbering_zone',  # Utilise les numéros du XML
        include_empty_folios=False  # Exclut les pages vides
    )

    processor = XMLCorpusProcessor(config)
    processor.process_corpus()


# ============================================================================
# EXEMPLE 4 : Traitement avec numérotation depuis XML
# ============================================================================

def exemple_numerotation_xml():
    """Utilise les numéros de page présents dans le XML."""
    config = ProcessingConfig(
        input_folder="/data/manuscripts/numbered",
        output_file="/output/corpus_numbered.txt",
        language='la',
        page_numbering_source='numbering_zone',  # Important !
        include_empty_folios=True
    )

    processor = XMLCorpusProcessor(config)
    processor.process_corpus()


# ============================================================================
# EXEMPLE 5 : Logging détaillé pour debug
# ============================================================================

def exemple_debug_mode():
    """Mode debug avec logging maximal."""
    # Configuration du logging personnalisé
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('corpus_processing_debug.log'),
            logging.StreamHandler()
        ]
    )

    config = ProcessingConfig(
        input_folder="/data/test/small_corpus",
        output_file="/output/test_corpus.txt",
        language='la',
        log_level=logging.DEBUG,  # Maximum de détails
        metadata={"test": "true"}
    )

    processor = XMLCorpusProcessor(config)
    processor.process_corpus()


# ============================================================================
# EXEMPLE 6 : Traitement par lot de plusieurs manuscrits
# ============================================================================

def exemple_traitement_par_lot():
    """Traite plusieurs manuscrits en une seule exécution."""
    manuscripts = [
        {
            "name": "tractatus_1",
            "folder": "/data/manuscripts/tractatus_1",
            "start_page": 1,
            "author": "Anselm von Laon"
        },
        {
            "name": "tractatus_2",
            "folder": "/data/manuscripts/tractatus_2",
            "start_page": 50,
            "author": "Wilhelm von Champeaux"
        },
        {
            "name": "tractatus_3",
            "folder": "/data/manuscripts/tractatus_3",
            "start_page": 120,
            "author": "Anonyme"
        }
    ]

    # Métadonnées communes
    base_metadata = {
        "edition_id": "Edi-52",
        "language": "Latin",
        "type": "Théologie",
        "date": "1100-1150",
        "lieu": "France"
    }

    for ms in manuscripts:
        print(f"\n{'='*60}")
        print(f"Traitement de {ms['name']}")
        print(f"{'='*60}\n")

        # Fusion des métadonnées
        metadata = {
            **base_metadata,
            "manuscript": ms['name'],
            "author": ms['author']
        }

        config = ProcessingConfig(
            input_folder=ms['folder'],
            output_file=f"/output/corpus/{ms['name']}_corpus.txt",
            language='la',
            metadata=metadata,
            starting_page_number=ms['start_page']
        )

        try:
            processor = XMLCorpusProcessor(config)
            processor.process_corpus()
            print(f"✓ {ms['name']} traité avec succès")
        except Exception as e:
            print(f"✗ Erreur lors du traitement de {ms['name']}: {e}")


# ============================================================================
# EXEMPLE 7 : Corpus multilingue
# ============================================================================

def exemple_corpus_multilingue():
    """Traite plusieurs langues avec configurations différentes."""
    corpus_configs = [
        {
            "name": "Latin",
            "folder": "/data/corpus/latin",
            "language": "la",
            "output": "/output/corpus_latin.txt"
        },
        {
            "name": "Français",
            "folder": "/data/corpus/francais",
            "language": "fr",
            "output": "/output/corpus_francais.txt"
        },
        {
            "name": "Allemand",
            "folder": "/data/corpus/allemand",
            "language": "de",
            "output": "/output/corpus_allemand.txt"
        }
    ]

    for corpus in corpus_configs:
        print(f"\nTraitement du corpus {corpus['name']}...")

        config = ProcessingConfig(
            input_folder=corpus['folder'],
            output_file=corpus['output'],
            language=corpus['language'],
            metadata={
                "corpus_name": corpus['name'],
                "language": corpus['name']
            }
        )

        processor = XMLCorpusProcessor(config)
        processor.process_corpus()


# ============================================================================
# EXEMPLE 8 : Configuration depuis variables d'environnement
# ============================================================================

def exemple_avec_variables_env():
    """Utilise les variables d'environnement pour la configuration."""
    import os

    config = ProcessingConfig(
        input_folder=os.getenv('CORPUS_INPUT_FOLDER', '/data/default'),
        output_file=os.getenv('CORPUS_OUTPUT_FILE', '/output/default.txt'),
        language=os.getenv('CORPUS_LANGUAGE', 'la'),
        log_level=logging.DEBUG if os.getenv('DEBUG') == 'true' else logging.INFO,
        metadata={
            "processing_date": os.getenv('PROCESSING_DATE', '2025'),
            "processor": os.getenv('USER', 'unknown')
        }
    )

    processor = XMLCorpusProcessor(config)
    processor.process_corpus()


# ============================================================================
# EXEMPLE 9 : Sans folios vides (pour analyses statistiques)
# ============================================================================

def exemple_sans_folios_vides():
    """Exclut les folios vides pour des analyses statistiques."""
    config = ProcessingConfig(
        input_folder="/data/manuscripts/corpus",
        output_file="/output/corpus_clean.txt",
        language='la',
        metadata={
            "title": "Corpus nettoyé (sans folios vides)",
            "clean": "true"
        },
        include_empty_folios=False  # Important !
    )

    processor = XMLCorpusProcessor(config)
    processor.process_corpus()


# ============================================================================
# EXEMPLE 10 : Configuration pour production
# ============================================================================

def exemple_production():
    """Configuration recommandée pour la production."""
    # Logging vers fichier
    log_file = '/var/log/corpus_processing.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()  # Également vers console
        ]
    )

    config = ProcessingConfig(
        input_folder="/production/data/manuscripts/input",
        output_file="/production/data/corpus/output/corpus_final.txt",
        language='la',
        log_level=logging.INFO,
        metadata={
            "edition_id": "PROD-2025",
            "title": "Corpus de production",
            "version": "1.0",
            "date": "2025-11-17",
            "processor": "XMLCorpusProcessor v2.0"
        },
        page_numbering_source='filename',
        starting_page_number=1,
        include_empty_folios=True
    )

    try:
        processor = XMLCorpusProcessor(config)
        processor.process_corpus()
        print("✓ Traitement terminé avec succès")
        return 0
    except Exception as e:
        print(f"✗ Erreur fatale : {e}")
        logging.error(f"Erreur fatale durant le traitement : {e}")
        return 1


# ============================================================================
# Point d'entrée principal
# ============================================================================

if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║         XMLCorpusProcessor - Exemples de configuration        ║
╚═══════════════════════════════════════════════════════════════╝

Choisissez un exemple :

1.  Configuration minimale
2.  Manuscrit latin avec métadonnées complètes
3.  Texte français moderne
4.  Numérotation depuis XML
5.  Mode debug
6.  Traitement par lot
7.  Corpus multilingue
8.  Configuration avec variables d'environnement
9.  Sans folios vides
10. Configuration production

Entrez le numéro (ou 'q' pour quitter) : """, end='')

    choix = input().strip()

    exemples = {
        '1': exemple_minimal,
        '2': exemple_manuscrit_latin,
        '3': exemple_texte_francais,
        '4': exemple_numerotation_xml,
        '5': exemple_debug_mode,
        '6': exemple_traitement_par_lot,
        '7': exemple_corpus_multilingue,
        '8': exemple_avec_variables_env,
        '9': exemple_sans_folios_vides,
        '10': exemple_production
    }

    if choix in exemples:
        print(f"\n{'='*60}")
        print(f"Exécution de l'exemple {choix}")
        print(f"{'='*60}\n")
        exemples[choix]()
    elif choix.lower() == 'q':
        print("Au revoir !")
    else:
        print("Choix invalide.")
