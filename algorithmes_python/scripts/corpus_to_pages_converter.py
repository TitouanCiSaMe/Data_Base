#!/usr/bin/env python3
"""
Convertisseur de corpus vertical vers pages texte standard
Convertit un fichier corpus vertical en dossier de pages texte individuelles
"""

import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import logging
from dataclasses import dataclass
import json

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


def main():
    """Fonction principale avec exemple d'usage"""

    # Configuration - MODIFIEZ CES CHEMINS SELON VOS BESOINS
    corpus_file = "/home/titouan/Bureau/HyperBase/Tractatus de Trinitate.txt"  # Votre fichier corpus
    output_directory = "/home/titouan/Bureau/Tractatus de Trinitate"  # Dossier de sortie

    # Vérifier que le fichier corpus existe
    if not Path(corpus_file).exists():
        print(f"❌ Fichier corpus non trouvé: {corpus_file}")
        print("📝 Veuillez modifier le chemin dans la fonction main()")
        return 1

    # Créer le convertisseur
    converter = CorpusToPageConverter(
        corpus_file=corpus_file,
        output_directory=output_directory,
        create_metadata_index=True,
        create_combined_file=True,  # ← NOUVEAU: Active le fichier combiné
        text_format="clean",  # "clean", "diplomatic", "annotated"
        include_lemmas=False,
        page_filename_template="page_{page_number:03d}_{folio}.txt"
    )

    try:
        # Lancer la conversion
        converter.convert_corpus()

        print("✅ Conversion terminée avec succès!")
        print(f"📁 Fichiers créés dans: {output_directory}")
        print(f"📄 Texte complet: texte_complet.txt")
        print(f"📋 Index: pages_index.json")
        print(f"🖼️  Correspondance images: images_mapping.txt")

    except Exception as e:
        print(f"❌ Erreur lors de la conversion: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
