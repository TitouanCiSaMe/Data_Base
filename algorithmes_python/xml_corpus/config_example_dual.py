"""
Exemple de configuration pour le traitement de corpus en mode dual-column.

Ce script illustre comment utiliser XMLCorpusProcessor pour traiter des manuscrits
où chaque fichier XML contient deux colonnes de texte (column#1 et column#2).

En mode 'dual', chaque colonne devient une page distincte dans le corpus final.

Auteur: TitouanCiSaMe
Licence: MIT
"""

import logging
import sys
import os

# Ajout du répertoire parent au path pour importer le module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xml_corpus.xml_corpus_processor import XMLCorpusProcessor, ProcessingConfig


def main():
    """
    Exemple d'utilisation pour traiter un manuscrit avec deux colonnes par page.

    Structure attendue dans les fichiers XML:
    - TextRegion[@custom='structure {type:MainZone:column#1;}']
    - TextRegion[@custom='structure {type:MainZone:column#2;}']
    """

    # Configuration du traitement en mode dual
    config = ProcessingConfig(
        # Dossiers d'entrée et de sortie
        input_folder="/chemin/vers/dossier/xml/",
        output_file="/chemin/vers/sortie/corpus.txt",

        # Paramètres de traitement
        language='la',  # Langue pour TreeTagger (latin)
        log_level=logging.INFO,

        # Métadonnées du corpus
        metadata={
            "edition_id": "Edi-60",
            "title": "Anselms von Laon systematische Sentenzen",
            "language": "Latin",
            "author": "Anonyme",
            "source": "Sententie diuine pagine",
            "type": "Droit Canonique",
            "date": "1100-1150",
            "lieu": "France",
            "ville": ""
        },

        # Paramètres de numérotation
        page_numbering_source='filename',  # 'filename' ou 'numbering_zone'
        starting_page_number=3,  # Numéro de la première colonne

        # Gestion des folios vides
        include_empty_folios=True,  # Inclure les colonnes vides avec empty="true"

        # MODE DUAL : crucial pour le traitement de deux colonnes
        column_mode='dual'  # 'single' pour une colonne, 'dual' pour deux colonnes
    )

    # Création et exécution du processeur
    print("=== Traitement du corpus en mode dual-column ===")
    print(f"Dossier source : {config.input_folder}")
    print(f"Fichier de sortie : {config.output_file}")
    print(f"Mode de colonnes : {config.column_mode}")
    print(f"Page de départ : {config.starting_page_number}")
    print()

    try:
        processor = XMLCorpusProcessor(config)
        processor.process_corpus()
        print("\n✓ Traitement terminé avec succès!")

    except FileNotFoundError as e:
        print(f"✗ Erreur : {e}")
        print("Vérifiez que le dossier d'entrée existe.")
        sys.exit(1)

    except ValueError as e:
        print(f"✗ Erreur de configuration : {e}")
        sys.exit(1)

    except Exception as e:
        print(f"✗ Erreur inattendue : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def example_single_mode():
    """
    Exemple complémentaire : traitement en mode single-column.

    Utilisez ce mode si vos fichiers XML n'ont qu'une seule MainZone
    sans identifiant de colonne.
    """
    config = ProcessingConfig(
        input_folder="/chemin/vers/dossier/xml/",
        output_file="/chemin/vers/sortie/corpus.txt",
        language='la',
        column_mode='single',  # Mode par défaut
        starting_page_number=1
    )

    processor = XMLCorpusProcessor(config)
    processor.process_corpus()


if __name__ == "__main__":
    # Lancer l'exemple dual par défaut
    main()

    # Pour tester le mode single, décommentez la ligne suivante:
    # example_single_mode()
