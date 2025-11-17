"""
Module de traitement de corpus XML pour extraction et lemmatisation.

Ce module fournit une classe XMLCorpusProcessor pour traiter des corpus XML,
extraire le texte, gérer les mots coupés avec trait d'union, et lemmatiser
le contenu à l'aide de TreeTagger.

Auteur: TitouanCiSaMe
Licence: MIT
"""

import os
import logging
import re
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import xml.etree.ElementTree as ET
import treetaggerwrapper


# Constantes
DEFAULT_LANGUAGE = 'la'
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Patterns regex compilés pour meilleures performances
PATTERNS = {
    'page_number': re.compile(r'_(\d+)(?:\.xml)?$'),
    'hyphenated_word': re.compile(r'(.*)(\w+)-\s*$'),
    'number_in_text': re.compile(r'\d+'),
    'line_numbers': re.compile(r'^\d+\s*|\s*\d+$'),
}


@dataclass
class PageMetadata:
    """Métadonnées d'une page du corpus."""
    filename: str
    page_number: int
    running_title: str
    is_empty: bool = False


@dataclass
class ProcessingConfig:
    """Configuration pour le traitement du corpus."""
    input_folder: str
    output_file: str
    language: str = DEFAULT_LANGUAGE
    log_level: int = logging.INFO
    metadata: Optional[Dict[str, str]] = None
    page_numbering_source: str = 'filename'
    starting_page_number: int = 1
    include_empty_folios: bool = True


class XMLCorpusProcessor:
    """
    Processeur de corpus XML pour extraction et lemmatisation.

    Cette classe permet de :
    - Extraire le texte de fichiers XML structurés
    - Gérer les mots coupés avec trait d'union
    - Lemmatiser le texte avec TreeTagger
    - Générer un corpus vertical annoté

    Attributes:
        config (ProcessingConfig): Configuration du processeur
        logger (logging.Logger): Logger pour le suivi des opérations
        tagger (treetaggerwrapper.TreeTagger): Instance de TreeTagger

    Example:
        >>> config = ProcessingConfig(
        ...     input_folder="/path/to/xml",
        ...     output_file="/path/to/output.txt",
        ...     language='la'
        ... )
        >>> processor = XMLCorpusProcessor(config)
        >>> processor.process_corpus()
    """

    def __init__(self, config: ProcessingConfig):
        """
        Initialise le processeur de corpus XML.

        Args:
            config: Configuration du processeur

        Raises:
            ValueError: Si les paramètres de configuration sont invalides
            FileNotFoundError: Si le dossier d'entrée n'existe pas
        """
        self.config = config
        if self.config.metadata is None:
            self.config.metadata = {}

        # Configuration du logger
        self._setup_logging()
        self.logger = logging.getLogger(__name__)

        # Validation
        self._validate_paths()
        self._validate_params()

        # Initialisation de TreeTagger (fait une seule fois)
        self.tagger = None

    def _setup_logging(self) -> None:
        """Configure le système de logging."""
        logging.basicConfig(
            level=self.config.log_level,
            format=DEFAULT_LOG_FORMAT
        )

    def _validate_paths(self) -> None:
        """
        Valide et crée les chemins nécessaires.

        Raises:
            FileNotFoundError: Si le dossier d'entrée n'existe pas
            ValueError: Si les chemins semblent suspects (path traversal)
        """
        input_folder = os.path.abspath(self.config.input_folder)

        if not os.path.exists(input_folder):
            raise FileNotFoundError(
                f"Le dossier d'entrée n'existe pas : {input_folder}"
            )

        # Créer le dossier de sortie si nécessaire
        output_dir = os.path.dirname(os.path.abspath(self.config.output_file))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            self.logger.info(f"Dossier de sortie créé : {output_dir}")

    def _validate_params(self) -> None:
        """
        Valide les paramètres de configuration.

        Raises:
            ValueError: Si les paramètres sont invalides
        """
        valid_sources = ['filename', 'numbering_zone']
        if self.config.page_numbering_source not in valid_sources:
            raise ValueError(
                f"Source de numérotation invalide: {self.config.page_numbering_source}. "
                f"Valeurs acceptées: {', '.join(valid_sources)}"
            )

        if (not isinstance(self.config.starting_page_number, int) or
            self.config.starting_page_number < 1):
            raise ValueError(
                f"Le numéro de page de départ doit être un entier positif: "
                f"{self.config.starting_page_number}"
            )

    def _extract_page_number_from_filename(self, filename: str) -> Optional[int]:
        """
        Extrait le numéro de page à partir du nom de fichier.

        Fonctionne avec des formats comme "FR674821001_001_E550779-4_0053.xml"

        Args:
            filename: Nom du fichier XML

        Returns:
            Numéro de page extrait, ou None si non trouvé

        Example:
            >>> processor._extract_page_number_from_filename("doc_0053.xml")
            53
        """
        match = PATTERNS['page_number'].search(filename)
        if match:
            number = int(match.group(1))
            self.logger.debug(f"Numéro de page extrait de '{filename}': {number}")
            return number

        self.logger.warning(f"Aucun numéro trouvé dans le nom de fichier: {filename}")
        return None

    def _extract_page_number_from_numbering_zone(self, root: ET.Element) -> Optional[int]:
        """
        Extrait le numéro de page depuis la zone NumberingZone dans le XML.

        Args:
            root: Élément racine de l'arbre XML

        Returns:
            Numéro de page extrait, ou None si non trouvé
        """
        try:
            # Recherche de la zone de numérotation
            numbering_zone = root.find(
                ".//TextRegion[@custom='structure {type:NumberingZone;}']"
            )

            if numbering_zone is not None:
                text_equiv = numbering_zone.find(".//TextEquiv/Unicode")
                if text_equiv is not None and text_equiv.text:
                    number_text = text_equiv.text.strip()
                    match = PATTERNS['number_in_text'].search(number_text)
                    if match:
                        return int(match.group(0))

            return None

        except ET.ParseError as e:
            self.logger.error(f"Erreur de parsing XML lors de l'extraction du numéro: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Erreur inattendue lors de l'extraction du numéro: {e}")
            return None

    def _merge_hyphenated_words(self, lines: List[str]) -> List[str]:
        """
        Fusionne les mots coupés avec trait d'union entre deux lignes.

        Cette méthode détecte les mots qui se terminent par un trait d'union
        en fin de ligne et les fusionne avec le début de la ligne suivante.

        Args:
            lines: Liste des lignes à traiter

        Returns:
            Liste des lignes avec mots fusionnés

        Example:
            >>> lines = ["sancti-", "tatis"]
            >>> processor._merge_hyphenated_words(lines)
            ["sanctitatis"]
        """
        processed_lines = []
        i = 0

        while i < len(lines):
            current_line = lines[i].strip()

            # Détection des mots coupés avec trait d'union
            match = PATTERNS['hyphenated_word'].search(current_line)

            if match and i + 1 < len(lines):
                prefix_text = match.group(1)  # Texte avant le mot coupé
                prefix_word = match.group(2)  # Première partie du mot coupé

                # Récupération de la ligne suivante
                next_line = lines[i + 1].strip()
                next_line_parts = next_line.split(' ', 1)

                if next_line_parts:
                    # Fusion du mot
                    suffix_word = next_line_parts[0]
                    fused_word = prefix_word + suffix_word

                    # Construction de la nouvelle ligne
                    new_line = prefix_text + fused_word

                    # Ajout du reste de la ligne suivante si présent
                    if len(next_line_parts) > 1:
                        new_line += ' ' + next_line_parts[1]

                    processed_lines.append(new_line)
                    i += 2  # Sauter la ligne suivante
                    continue

            # Pas de fusion nécessaire
            processed_lines.append(current_line)
            i += 1

        return processed_lines

    def _clean_lines(self, lines: List[str]) -> List[str]:
        """
        Nettoie les lignes de texte.

        Supprime les numéros de ligne et filtre les lignes vides ou trop courtes.

        Args:
            lines: Liste des lignes à nettoyer

        Returns:
            Liste des lignes nettoyées
        """
        cleaned_lines = []

        for line in lines:
            # Supprimer les numéros de ligne en début/fin
            line = PATTERNS['line_numbers'].sub('', line)
            line = line.strip()

            # Filtrer les lignes vides ou trop courtes
            if line and len(line) > 2:
                cleaned_lines.append(line)

        return cleaned_lines

    def _remove_xml_namespaces(self, root: ET.Element) -> None:
        """
        Supprime les namespaces XML de manière sûre.

        Note: Modifie l'élément en place.

        Args:
            root: Élément racine de l'arbre XML
        """
        for elem in root.iter():
            if '}' in elem.tag:
                elem.tag = elem.tag.split('}', 1)[1]

    def _process_xml_page(self, file_path: str) -> Tuple[Optional[int], str, List[str]]:
        """
        Traite un fichier XML individuel.

        Args:
            file_path: Chemin complet vers le fichier XML

        Returns:
            Tuple contenant (numéro de page, titre courant, lignes de texte)

        Raises:
            ET.ParseError: Si le fichier XML est mal formé
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Nettoyer les espaces de noms
            self._remove_xml_namespaces(root)

            # Extraction du titre courant
            running_title_elem = root.find(
                ".//TextRegion[@custom='structure {type:RunningTitleZone;}']"
                "//TextEquiv/Unicode"
            )
            running_title = (
                running_title_elem.text.strip()
                if running_title_elem is not None and running_title_elem.text
                else "No running title"
            )

            # Extraction du numéro de page depuis NumberingZone si demandé
            page_number = None
            if self.config.page_numbering_source == 'numbering_zone':
                page_number = self._extract_page_number_from_numbering_zone(root)

            # Extraction des lignes - UNIQUEMENT de la première MainZone
            lines = []
            first_main_zone = root.find(
                ".//TextRegion[@custom='structure {type:MainZone;}']"
            )

            if first_main_zone is not None:
                for text_line in first_main_zone.findall(".//TextLine"):
                    text_equiv = text_line.find(".//TextEquiv/Unicode")
                    if text_equiv is not None and text_equiv.text:
                        lines.append(text_equiv.text.strip())

            # Nettoyage et fusion des mots coupés
            lines = self._clean_lines(lines)
            lines = self._merge_hyphenated_words(lines)

            return page_number, running_title, lines

        except ET.ParseError as e:
            self.logger.error(f"Erreur de parsing XML pour {file_path}: {e}")
            raise
        except IOError as e:
            self.logger.error(f"Erreur de lecture du fichier {file_path}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Erreur inattendue lors du traitement de {file_path}: {e}")
            return None, "No running title", []

    def _lemmatize_line(self, line: str) -> List[Tuple[str, str, str]]:
        """
        Lemmatise une ligne de texte avec TreeTagger.

        Args:
            line: Ligne de texte à lemmatiser

        Returns:
            Liste de tuples (mot, pos, lemme)

        Example:
            >>> processor._lemmatize_line("Dominus est")
            [('Dominus', 'NOM', 'dominus'), ('est', 'V', 'sum')]
        """
        if self.tagger is None:
            raise RuntimeError("TreeTagger n'est pas initialisé")

        try:
            tagged = self.tagger.tag_text(line)
            lemmatized_words = []

            for word in tagged:
                parts = word.split("\t")
                if len(parts) == 3:
                    lemmatized_words.append((parts[0], parts[1], parts[2]))
                else:
                    self.logger.debug(f"Format inattendu pour: {word}")

            return lemmatized_words

        except Exception as e:
            self.logger.error(f"Erreur lors de la lemmatisation de '{line}': {e}")
            return []

    def _get_sorted_xml_files(self) -> List[str]:
        """
        Récupère et trie les fichiers XML du dossier d'entrée.

        Returns:
            Liste des noms de fichiers XML triés par numéro de page

        Raises:
            ValueError: Si aucun fichier XML n'est trouvé
        """
        xml_files = [
            f for f in os.listdir(self.config.input_folder)
            if f.endswith(".xml")
        ]

        if not xml_files:
            raise ValueError(
                f"Aucun fichier XML trouvé dans {self.config.input_folder}"
            )

        self.logger.info(f"{len(xml_files)} fichiers XML trouvés")

        # Tri des fichiers par numéro extrait
        xml_files_sorted = sorted(
            xml_files,
            key=lambda x: self._extract_page_number_from_filename(x) or float('inf')
        )

        self.logger.debug(f"Ordre de traitement: {xml_files_sorted}")
        return xml_files_sorted

    def _initialize_tagger(self) -> treetaggerwrapper.TreeTagger:
        """
        Initialise TreeTagger.

        Returns:
            Instance de TreeTagger configurée

        Raises:
            RuntimeError: Si TreeTagger ne peut pas être initialisé
        """
        try:
            self.logger.info(f"Initialisation de TreeTagger (langue: {self.config.language})")
            tagger = treetaggerwrapper.TreeTagger(TAGLANG=self.config.language)
            return tagger
        except Exception as e:
            self.logger.error(f"Impossible d'initialiser TreeTagger: {e}")
            raise RuntimeError(f"Échec de l'initialisation de TreeTagger: {e}")

    def _calculate_page_number(
        self,
        filename: str,
        relative_index: int,
        numbering_zone_page: Optional[int]
    ) -> int:
        """
        Calcule le numéro de page selon la source configurée.

        Args:
            filename: Nom du fichier
            relative_index: Index relatif du fichier (commence à 1)
            numbering_zone_page: Numéro extrait de NumberingZone (peut être None)

        Returns:
            Numéro de page calculé
        """
        if self.config.page_numbering_source == 'filename':
            return self.config.starting_page_number + relative_index - 1
        else:  # 'numbering_zone'
            if numbering_zone_page is None:
                self.logger.warning(
                    f"Aucun numéro dans NumberingZone pour {filename}, "
                    f"utilisation de l'index: {relative_index}"
                )
                return relative_index
            return numbering_zone_page

    def _format_document(
        self,
        metadata: PageMetadata,
        lines: List[str]
    ) -> str:
        """
        Formate un document avec ses métadonnées et son contenu lemmatisé.

        Args:
            metadata: Métadonnées de la page
            lines: Lignes de texte à inclure

        Returns:
            Document formaté en chaîne de caractères
        """
        # Préparation des attributs de métadonnées
        metadata_attrs = ' '.join([
            f'{k}="{v}"' for k, v in self.config.metadata.items()
        ])

        # En-tête du document
        doc_header = (
            f'<doc folio="{metadata.filename}" '
            f'page_number="{metadata.page_number}" '
            f'running_title="{metadata.running_title}" '
            f'{metadata_attrs}'
        )

        if metadata.is_empty:
            doc_header += ' empty="true"'

        doc_header += '>\n'

        # Si vide, retourner juste l'en-tête
        if metadata.is_empty or not lines:
            return doc_header + '</doc>\n\n'

        # Lemmatisation et formatage du contenu
        content_lines = []
        for line in lines:
            lemmatized_words = self._lemmatize_line(line)
            if lemmatized_words:
                sentence = "<s>\n"
                sentence += "\n".join(
                    f"{w}\t{p}\t{l}" for w, p, l in lemmatized_words
                )
                sentence += "\n</s>\n"
                content_lines.append(sentence)

        return doc_header + "".join(content_lines) + '</doc>\n\n'

    def _process_all_files(
        self,
        xml_files: List[str]
    ) -> List[Tuple[int, str]]:
        """
        Traite tous les fichiers XML.

        Args:
            xml_files: Liste des fichiers XML à traiter

        Returns:
            Liste de tuples (numéro de page, contenu du document)
        """
        documents = []
        empty_folios = []
        relative_index = 0

        for filename in xml_files:
            file_path = os.path.join(self.config.input_folder, filename)
            relative_index += 1

            try:
                # Traitement du fichier
                numbering_zone_page, running_title, lines = self._process_xml_page(file_path)

                # Calcul du numéro de page
                page_number = self._calculate_page_number(
                    filename,
                    relative_index,
                    numbering_zone_page
                )

                # Création des métadonnées
                is_empty = not lines
                metadata = PageMetadata(
                    filename=filename,
                    page_number=page_number,
                    running_title=running_title,
                    is_empty=is_empty
                )

                # Gestion des folios vides
                if is_empty:
                    empty_folios.append((filename, page_number))
                    if not self.config.include_empty_folios:
                        self.logger.info(
                            f"Folio vide ignoré : {filename} (Page {page_number})"
                        )
                        continue
                    else:
                        self.logger.info(
                            f"Folio vide inclus : {filename} (Page {page_number})"
                        )

                # Formatage et stockage
                document_content = self._format_document(metadata, lines)
                documents.append((page_number, document_content))

                if not is_empty:
                    self.logger.info(
                        f"Traitement réussi : {filename} (Page {page_number})"
                    )

            except ET.ParseError as e:
                self.logger.error(f"Fichier XML invalide {filename}: {e}")
                continue
            except Exception as e:
                self.logger.error(f"Erreur lors du traitement de {filename}: {e}")
                continue

        # Affichage du résumé des folios vides
        if empty_folios:
            self.logger.info(f"\n--- Résumé des folios vides ---")
            for folio, page_number in empty_folios:
                self.logger.info(f"  - {folio} (Page {page_number})")
            self.logger.info(f"Total de folios vides : {len(empty_folios)}")

        return documents

    def _write_output(self, documents: List[Tuple[int, str]]) -> None:
        """
        Écrit les documents traités dans le fichier de sortie.

        Args:
            documents: Liste de tuples (numéro de page, contenu)

        Raises:
            IOError: Si l'écriture échoue
        """
        # Tri par numéro de page
        documents.sort(key=lambda x: x[0])

        try:
            with open(self.config.output_file, "w", encoding="utf-8") as output:
                for _, document in documents:
                    output.write(document)

            self.logger.info(
                f"Extraction terminée. {len(documents)} documents écrits dans "
                f"'{self.config.output_file}'"
            )

        except IOError as e:
            self.logger.error(f"Erreur lors de l'écriture du fichier de sortie: {e}")
            raise

    def process_corpus(self) -> None:
        """
        Lance le traitement complet du corpus.

        Cette méthode orchestre toutes les étapes :
        1. Récupération et tri des fichiers XML
        2. Initialisation de TreeTagger
        3. Traitement de chaque fichier
        4. Écriture du fichier de sortie

        Raises:
            ValueError: Si aucun fichier XML n'est trouvé
            RuntimeError: Si TreeTagger ne peut pas être initialisé
            IOError: Si l'écriture échoue
        """
        self.logger.info("=== Début du traitement du corpus ===")
        self.logger.info(f"Dossier d'entrée : {self.config.input_folder}")
        self.logger.info(f"Fichier de sortie : {self.config.output_file}")

        # Étape 1 : Récupération des fichiers
        xml_files = self._get_sorted_xml_files()

        # Étape 2 : Initialisation de TreeTagger
        self.tagger = self._initialize_tagger()

        # Étape 3 : Traitement des fichiers
        documents = self._process_all_files(xml_files)

        # Étape 4 : Écriture du résultat
        self._write_output(documents)

        self.logger.info("=== Traitement terminé avec succès ===")


def main():
    """Point d'entrée principal du script."""
    # Configuration du traitement
    config = ProcessingConfig(
        input_folder="/home/titouan/NoSketch/Das Schrifttum des Schule Anselms von Laon und Wilhelms von Champeaux in deutschen Bibliotheken/tractatus 'Decretum Dei fuit'/",
        output_file="/home/titouan/Bureau/HyperBase/tractatus 'Decretum Dei fuit.txt",
        language='la',
        log_level=logging.INFO,
        metadata={
            "edition_id": "Edi-52",
            "title": "Das Schrifttum des Schule Anselms von Laon und Wilhelms von Champeaux in deutschen Bibliotheken",
            "language": "Latin",
            "author": "Anonyme",
            "source": "tractatus 'Decretum Dei fuit",
            "type": "Théologie",
            "date": "1100-1150",
            "lieu": "France",
            "ville": ""
        },
        page_numbering_source='filename',
        starting_page_number=361,
        include_empty_folios=True
    )

    # Création et exécution du processeur
    processor = XMLCorpusProcessor(config)
    processor.process_corpus()


if __name__ == "__main__":
    main()
