#!/usr/bin/env python3
"""
Convertisseur de corpus vertical vers pages texte standard
Convertit un fichier corpus vertical en dossier de pages texte individuelles

USAGE:
    # Fichier unique
    python corpus_to_pages_converter.py corpus.txt -o output_dir/

    # Plusieurs fichiers
    python corpus_to_pages_converter.py file1.txt file2.txt file3.txt -o output_dir/

    # Tous les fichiers .txt d'un dossier
    python corpus_to_pages_converter.py --directory corpus_dir/ -o output_dir/

    # Avec options avancées
    python corpus_to_pages_converter.py corpus.txt -o output/ --format diplomatic --lemmas
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from dataclasses import dataclass
import json
import argparse
import sys

@dataclass
class PageMetadata:
    """Métadonnées d'une page"""
    folio: str
    page_number: int
    running_title: str
    image_filename: str  # Nom de l'image source
    metadata: Dict[str, str]

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour sauvegarde JSON"""
        return {
            'folio': self.folio,
            'page_number': self.page_number,
            'running_title': self.running_title,
            'image_filename': self.image_filename,
            'metadata': self.metadata
        }


class CorpusToPageConverter:
    """Convertit un corpus vertical en pages texte individuelles"""

    def __init__(self,
                 corpus_file: str,
                 output_directory: str,
                 create_metadata_index: bool = True,
                 create_combined_file: bool = True,
                 text_format: str = "clean",  # "clean", "diplomatic", "annotated"
                 include_lemmas: bool = False,
                 page_filename_template: str = "page_{page_number:04d}_{folio}.txt"):
        """
        Initialise le convertisseur

        Args:
            corpus_file: Chemin vers le fichier corpus vertical
            output_directory: Dossier de sortie pour les pages
            create_metadata_index: Créer un fichier JSON avec les métadonnées
            create_combined_file: Créer un fichier combiné avec toutes les pages
            text_format: Format de sortie du texte
            include_lemmas: Inclure les lemmes en annotation
            page_filename_template: Template pour noms de fichiers
        """
        self.corpus_file = Path(corpus_file)
        self.output_directory = Path(output_directory)
        self.create_metadata_index = create_metadata_index
        self.create_combined_file = create_combined_file
        self.text_format = text_format
        self.include_lemmas = include_lemmas
        self.page_filename_template = page_filename_template

        # Configuration du logging
        self._setup_logging()

        # Statistiques
        self.stats = {
            'pages_processed': 0,
            'words_converted': 0,
            'sentences_converted': 0,
            'empty_pages': 0
        }

        # Index des métadonnées et contenu des pages
        self.pages_metadata: List[PageMetadata] = []
        self.pages_content: List[tuple] = []  # (metadata, content)

        # Validation
        self._validate_inputs()

    def _setup_logging(self):
        """Configure le logging"""
        # Créer d'abord le dossier de sortie
        self.output_directory.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(
                    self.output_directory / 'conversion.log',
                    encoding='utf-8'
                )
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _validate_inputs(self):
        """Valide les paramètres d'entrée"""
        if not self.corpus_file.exists():
            raise FileNotFoundError(f"Fichier corpus non trouvé: {self.corpus_file}")

        # Vérifier le format de texte
        valid_formats = ["clean", "diplomatic", "annotated"]
        if self.text_format not in valid_formats:
            raise ValueError(f"Format invalide: {self.text_format}. Formats supportés: {valid_formats}")

        self.logger.info(f"Conversion configurée:")
        self.logger.info(f"  - Format: {self.text_format}")
        self.logger.info(f"  - Lemmes: {'oui' if self.include_lemmas else 'non'}")
        self.logger.info(f"  - Fichier combiné: {'oui' if self.create_combined_file else 'non'}")
        self.logger.info(f"  - Sortie: {self.output_directory}")

    def _extract_doc_metadata(self, doc_line: str) -> Dict[str, str]:
        """Extrait les métadonnées d'une ligne <doc>"""
        metadata = {}

        # Pattern pour extraire les attributs
        attr_pattern = r'(\w+)="([^"]*)"'
        matches = re.findall(attr_pattern, doc_line)

        for key, value in matches:
            metadata[key] = value

        return metadata

    def _get_image_filename_from_folio(self, folio: str) -> str:
        """
        Génère le nom probable de l'image à partir du folio
        """
        # Le folio contient déjà l'extension .xml, on la remplace
        if folio.endswith('.xml'):
            # Tenter différents formats d'image courants
            base_name = folio[:-4]  # Enlever .xml
            possible_extensions = ['.jpg', '.jpeg', '.png', '.tif', '.tiff']

            # Retourner le nom avec l'extension la plus probable
            return f"{base_name}.jpg"  # Format le plus courant

        return folio

    def _get_page_filename(self, metadata: PageMetadata) -> str:
        """Génère le nom de fichier pour une page"""
        clean_folio = re.sub(r'[^\w\-_.]', '_', metadata.folio)
        return self.page_filename_template.format(
            page_number=metadata.page_number,
            folio=clean_folio.replace('.xml', '')
        )

    def _format_text_clean(self, words_data: List[tuple]) -> str:
        """Format texte propre (mots seulement)"""
        text_parts = []

        for word, pos, lemma in words_data:
            # Gestion de la ponctuation
            if pos in ['PUN', 'SENT']:
                # Coller la ponctuation au mot précédent
                if text_parts and word not in ['"', "'", '(', '«']:
                    text_parts[-1] += word
                else:
                    text_parts.append(word)
            else:
                text_parts.append(word)

        return ' '.join(text_parts)

    def _format_text_diplomatic(self, words_data: List[tuple]) -> str:
        """Format diplomatique (avec indications POS)"""
        text_parts = []

        for word, pos, lemma in words_data:
            if pos in ['PUN', 'SENT']:
                text_parts.append(word)
            else:
                if self.include_lemmas and lemma != word:
                    text_parts.append(f"{word}({pos}→{lemma})")
                else:
                    text_parts.append(f"{word}({pos})")

        return ' '.join(text_parts)

    def _format_text_annotated(self, words_data: List[tuple]) -> str:
        """Format annoté (avec toutes les informations)"""
        lines = []

        for word, pos, lemma in words_data:
            if pos in ['PUN', 'SENT']:
                lines.append(word)
            else:
                lines.append(f"{word}\t{pos}\t{lemma}")

        return '\n'.join(lines)

    def _process_sentence(self, sentence_lines: List[str]) -> str:
        """Traite une phrase (entre <s> et </s>)"""
        words_data = []

        for line in sentence_lines:
            line = line.strip()
            if not line or line.startswith('<'):
                continue

            parts = line.split('\t')
            if len(parts) >= 3:
                word, pos, lemma = parts[0], parts[1], parts[2]
                words_data.append((word, pos, lemma))

        if not words_data:
            return ""

        # Appliquer le formatage selon le mode choisi
        if self.text_format == "clean":
            return self._format_text_clean(words_data)
        elif self.text_format == "diplomatic":
            return self._format_text_diplomatic(words_data)
        elif self.text_format == "annotated":
            return self._format_text_annotated(words_data)

        return ""

    def _create_page_header(self, metadata: PageMetadata) -> str:
        """Crée l'en-tête de la page"""
        header_lines = []
        header_lines.append("=" * 80)
        header_lines.append(f"PAGE {metadata.page_number}")
        header_lines.append(f"Source: {metadata.folio}")
        header_lines.append(f"Image: {metadata.image_filename}")
        header_lines.append(f"Titre courant: {metadata.running_title}")

        # Métadonnées importantes
        if 'title' in metadata.metadata:
            header_lines.append(f"Œuvre: {metadata.metadata['title']}")
        if 'author' in metadata.metadata:
            header_lines.append(f"Auteur: {metadata.metadata['author']}")
        if 'date' in metadata.metadata:
            header_lines.append(f"Date: {metadata.metadata['date']}")

        header_lines.append("=" * 80)
        header_lines.append("")

        return '\n'.join(header_lines)

    def convert_corpus(self) -> None:
        """Convertit le corpus en pages individuelles"""
        self.logger.info("Début de la conversion du corpus")

        current_page_content = []
        current_metadata = None
        current_sentence = []
        in_sentence = False

        with open(self.corpus_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                if not line:
                    continue

                # Début d'un nouveau document
                if line.startswith('<doc '):
                    # Sauvegarder la page précédente si elle existe
                    if current_metadata:
                        self._save_page(current_metadata, current_page_content)

                    # Extraire les métadonnées du nouveau document
                    metadata_dict = self._extract_doc_metadata(line)

                    # Remplacer les dates vides par "unknown" pour conformité Dublin Core
                    if 'date' in metadata_dict and not metadata_dict['date'].strip():
                        metadata_dict['date'] = 'unknown'

                    current_metadata = PageMetadata(
                        folio=metadata_dict.get('folio', f'unknown_{line_num}'),
                        page_number=int(metadata_dict.get('page_number', 0)),
                        running_title=metadata_dict.get('running_title', 'Sans titre'),
                        image_filename=self._get_image_filename_from_folio(
                            metadata_dict.get('folio', f'unknown_{line_num}')
                        ),
                        metadata=metadata_dict
                    )

                    current_page_content = []
                    continue

                # Fin d'un document
                elif line.startswith('</doc>'):
                    if in_sentence and current_sentence:
                        # Terminer la phrase en cours
                        sentence_text = self._process_sentence(current_sentence)
                        if sentence_text:
                            current_page_content.append(sentence_text)
                        current_sentence = []
                        in_sentence = False
                    continue

                # Début d'une phrase
                elif line.startswith('<s>'):
                    in_sentence = True
                    current_sentence = []
                    continue

                # Fin d'une phrase
                elif line.startswith('</s>'):
                    if current_sentence:
                        sentence_text = self._process_sentence(current_sentence)
                        if sentence_text:
                            current_page_content.append(sentence_text)
                            self.stats['sentences_converted'] += 1

                    current_sentence = []
                    in_sentence = False
                    continue

                # Ligne de données (mot\tpos\tlemma)
                elif in_sentence and '\t' in line:
                    current_sentence.append(line)
                    self.stats['words_converted'] += 1

        # Sauvegarder la dernière page
        if current_metadata:
            self._save_page(current_metadata, current_page_content)

        # Créer les fichiers additionnels
        if self.create_metadata_index:
            self._create_metadata_index()

        if self.create_combined_file:
            self._create_combined_text()

        self._create_images_mapping()

        self._log_final_stats()

    def _save_page(self, metadata: PageMetadata, content: List[str]) -> None:
        """Sauvegarde une page dans un fichier"""
        filename = self._get_page_filename(metadata)
        filepath = self.output_directory / filename

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # Écrire l'en-tête
                f.write(self._create_page_header(metadata))

                # Écrire le contenu
                if content:
                    if self.text_format == "annotated":
                        # Format annoté : garder les retours à la ligne
                        f.write('\n\n'.join(content))
                    else:
                        # Formats clean/diplomatic : paragraphes
                        f.write('\n\n'.join(content))
                else:
                    f.write("[PAGE VIDE]")
                    self.stats['empty_pages'] += 1

                f.write('\n')

            # Stocker les métadonnées et le contenu pour le fichier combiné
            self.pages_metadata.append(metadata)
            self.pages_content.append((metadata, content))
            self.stats['pages_processed'] += 1

            self.logger.debug(f"Page sauvegardée: {filename}")

        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde de {filename}: {e}")

    def _create_combined_text(self) -> None:
        """Crée un fichier combiné avec toutes les pages"""
        combined_file = self.output_directory / "texte_complet.txt"

        self.logger.info("Création du fichier texte combiné...")

        try:
            with open(combined_file, 'w', encoding='utf-8') as f:
                for i, (metadata, content) in enumerate(self.pages_content):
                    # Séparateur simple avec numéro de page
                    if i > 0:
                        f.write('\n\n')

                    f.write(f"--- PAGE {metadata.page_number} ---\n\n")

                    # Contenu de la page
                    if content:
                        if self.text_format == "annotated":
                            f.write('\n\n'.join(content))
                        else:
                            f.write('\n\n'.join(content))
                    else:
                        f.write("[PAGE VIDE]")

                    f.write('\n')

            self.logger.info(f"✓ Fichier combiné créé: {combined_file}")
            self.logger.info(f"  Total: {len(self.pages_content)} pages combinées")

        except Exception as e:
            self.logger.error(f"Erreur lors de la création du fichier combiné: {e}")

    def _create_metadata_index(self) -> None:
        """Crée un fichier JSON avec l'index des métadonnées"""
        index_file = self.output_directory / "pages_index.json"

        index_data = {
            'conversion_info': {
                'corpus_source': str(self.corpus_file),
                'conversion_date': datetime.now().isoformat(),
                'text_format': self.text_format,
                'include_lemmas': self.include_lemmas,
                'total_pages': len(self.pages_metadata)
            },
            'statistics': self.stats,
            'pages': [page.to_dict() for page in self.pages_metadata]
        }

        try:
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Index des métadonnées créé: {index_file}")

        except Exception as e:
            self.logger.error(f"Erreur lors de la création de l'index: {e}")

    def _create_images_mapping(self) -> None:
        """Crée un fichier de correspondance images <-> pages"""
        mapping_file = self.output_directory / "images_mapping.txt"

        try:
            with open(mapping_file, 'w', encoding='utf-8') as f:
                f.write("# Correspondance Images <-> Pages texte\n")
                f.write("# Format: image_filename -> page_filename (page_number)\n\n")

                for metadata in self.pages_metadata:
                    page_filename = self._get_page_filename(metadata)
                    f.write(f"{metadata.image_filename} -> {page_filename} (page {metadata.page_number})\n")

            self.logger.info(f"Fichier de correspondance créé: {mapping_file}")

        except Exception as e:
            self.logger.error(f"Erreur lors de la création du mapping: {e}")

    def _log_final_stats(self) -> None:
        """Affiche les statistiques finales"""
        self.logger.info("=" * 60)
        self.logger.info("CONVERSION TERMINÉE")
        self.logger.info("=" * 60)
        self.logger.info(f"Pages traitées: {self.stats['pages_processed']}")
        self.logger.info(f"Pages vides: {self.stats['empty_pages']}")
        self.logger.info(f"Phrases converties: {self.stats['sentences_converted']}")
        self.logger.info(f"Mots convertis: {self.stats['words_converted']}")
        self.logger.info(f"Dossier de sortie: {self.output_directory}")
        self.logger.info("=" * 60)


class BatchConverter:
    """Gère la conversion de plusieurs fichiers corpus"""

    def __init__(self,
                 corpus_files: List[Path],
                 output_base_directory: Path,
                 **converter_options):
        """
        Initialise le convertisseur batch

        Args:
            corpus_files: Liste de fichiers corpus à convertir
            output_base_directory: Dossier de base pour les sorties
            **converter_options: Options à passer au convertisseur
        """
        self.corpus_files = corpus_files
        self.output_base_directory = output_base_directory
        self.converter_options = converter_options

        self.results = []
        self.total_files = len(corpus_files)
        self.success_count = 0
        self.error_count = 0

    def convert_all(self) -> bool:
        """Convertit tous les fichiers"""
        print(f"\n{'=' * 70}")
        print(f"CONVERSION BATCH: {self.total_files} fichier(s) à traiter")
        print(f"{'=' * 70}\n")

        for i, corpus_file in enumerate(self.corpus_files, 1):
            print(f"\n[{i}/{self.total_files}] Traitement de: {corpus_file.name}")
            print("-" * 70)

            try:
                # Créer un sous-dossier pour chaque corpus
                corpus_name = corpus_file.stem
                output_dir = self.output_base_directory / corpus_name

                # Créer le convertisseur pour ce fichier
                converter = CorpusToPageConverter(
                    corpus_file=str(corpus_file),
                    output_directory=str(output_dir),
                    **self.converter_options
                )

                # Convertir
                converter.convert_corpus()

                self.results.append({
                    'file': corpus_file.name,
                    'status': 'success',
                    'output_dir': output_dir,
                    'stats': converter.stats
                })
                self.success_count += 1

                print(f"✓ Conversion réussie")
                print(f"  Sortie: {output_dir}")

            except Exception as e:
                self.results.append({
                    'file': corpus_file.name,
                    'status': 'error',
                    'error': str(e)
                })
                self.error_count += 1

                print(f"✗ Erreur: {e}")

        # Résumé final
        self._print_summary()

        return self.error_count == 0

    def _print_summary(self):
        """Affiche le résumé de la conversion batch"""
        print(f"\n{'=' * 70}")
        print("RÉSUMÉ DE LA CONVERSION BATCH")
        print(f"{'=' * 70}")
        print(f"Total: {self.total_files} fichier(s)")
        print(f"✓ Réussis: {self.success_count}")
        print(f"✗ Erreurs: {self.error_count}")
        print(f"{'=' * 70}\n")

        if self.error_count > 0:
            print("Fichiers en erreur:")
            for result in self.results:
                if result['status'] == 'error':
                    print(f"  - {result['file']}: {result['error']}")


def parse_arguments() -> argparse.Namespace:
    """Parse les arguments de ligne de commande"""
    parser = argparse.ArgumentParser(
        description="Convertisseur de corpus vertical vers pages texte",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXEMPLES D'UTILISATION:

  # Convertir un seul fichier
  python corpus_to_pages_converter.py corpus.txt -o output/

  # Convertir plusieurs fichiers (chacun dans son sous-dossier)
  python corpus_to_pages_converter.py file1.txt file2.txt file3.txt -o output/

  # Convertir tous les .txt d'un dossier
  python corpus_to_pages_converter.py --directory corpus_dir/ -o output/

  # Format diplomatique avec lemmes
  python corpus_to_pages_converter.py corpus.txt -o output/ --format diplomatic --lemmas

  # Sans fichier combiné ni métadonnées
  python corpus_to_pages_converter.py corpus.txt -o output/ --no-combined --no-metadata

FORMATS DE SORTIE:
  - clean:      Texte propre, mots uniquement
  - diplomatic: Texte avec annotations POS
  - annotated:  Format tabulaire complet (mot + POS + lemme)
        """
    )

    # Fichiers d'entrée
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        'corpus_files',
        nargs='*',
        default=[],
        help='Fichier(s) corpus à convertir'
    )
    input_group.add_argument(
        '--directory', '-d',
        type=str,
        help='Dossier contenant les fichiers corpus (.txt)'
    )

    # Sortie
    parser.add_argument(
        '--output', '-o',
        type=str,
        required=True,
        help='Dossier de sortie'
    )

    # Options de format
    parser.add_argument(
        '--format', '-f',
        type=str,
        choices=['clean', 'diplomatic', 'annotated'],
        default='clean',
        help='Format de sortie du texte (défaut: clean)'
    )

    parser.add_argument(
        '--lemmas', '-l',
        action='store_true',
        help='Inclure les lemmes dans les annotations'
    )

    # Options de fichiers de sortie
    parser.add_argument(
        '--no-combined',
        action='store_true',
        help='Ne pas créer le fichier texte complet'
    )

    parser.add_argument(
        '--no-metadata',
        action='store_true',
        help='Ne pas créer le fichier JSON de métadonnées'
    )

    # Template de nom de fichier
    parser.add_argument(
        '--template',
        type=str,
        default='page_{page_number:04d}_{folio}.txt',
        help='Template pour les noms de fichiers de pages'
    )

    # Pattern de recherche pour --directory
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.txt',
        help='Pattern de fichiers à chercher avec --directory (défaut: *.txt)'
    )

    return parser.parse_args()


def get_corpus_files(args: argparse.Namespace) -> List[Path]:
    """Récupère la liste des fichiers corpus à traiter"""
    corpus_files = []

    if args.directory:
        # Mode dossier: chercher tous les fichiers correspondant au pattern
        directory = Path(args.directory)
        if not directory.exists():
            print(f"❌ Dossier non trouvé: {directory}")
            sys.exit(1)

        if not directory.is_dir():
            print(f"❌ Le chemin n'est pas un dossier: {directory}")
            sys.exit(1)

        corpus_files = list(directory.glob(args.pattern))

        if not corpus_files:
            print(f"❌ Aucun fichier {args.pattern} trouvé dans: {directory}")
            sys.exit(1)

        print(f"✓ {len(corpus_files)} fichier(s) trouvé(s) dans {directory}")

    else:
        # Mode fichiers directs
        for file_path in args.corpus_files:
            path = Path(file_path)
            if not path.exists():
                print(f"❌ Fichier non trouvé: {path}")
                sys.exit(1)
            corpus_files.append(path)

    return corpus_files


def main():
    """Fonction principale avec interface CLI"""
    args = parse_arguments()

    # Récupérer la liste des fichiers à traiter
    corpus_files = get_corpus_files(args)

    # Préparer les options du convertisseur
    converter_options = {
        'create_metadata_index': not args.no_metadata,
        'create_combined_file': not args.no_combined,
        'text_format': args.format,
        'include_lemmas': args.lemmas,
        'page_filename_template': args.template
    }

    output_dir = Path(args.output)

    try:
        if len(corpus_files) == 1:
            # Conversion d'un seul fichier
            print(f"\n🔄 Conversion de: {corpus_files[0].name}")
            print(f"📁 Sortie: {output_dir}\n")

            converter = CorpusToPageConverter(
                corpus_file=str(corpus_files[0]),
                output_directory=str(output_dir),
                **converter_options
            )

            converter.convert_corpus()

            print("\n✅ Conversion terminée avec succès!")
            print(f"📁 Fichiers créés dans: {output_dir}")
            if not args.no_combined:
                print(f"📄 Texte complet: texte_complet.txt")
            if not args.no_metadata:
                print(f"📋 Index: pages_index.json")
            print(f"🖼️  Correspondance images: images_mapping.txt")

        else:
            # Conversion batch de plusieurs fichiers
            batch_converter = BatchConverter(
                corpus_files=corpus_files,
                output_base_directory=output_dir,
                **converter_options
            )

            success = batch_converter.convert_all()

            if not success:
                return 1

            print("✅ Conversion batch terminée!")
            print(f"📁 Fichiers créés dans: {output_dir}/")

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Conversion interrompue par l'utilisateur")
        return 1

    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
