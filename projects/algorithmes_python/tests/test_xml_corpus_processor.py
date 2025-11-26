"""
Tests unitaires pour XMLCorpusProcessor.

Pour exécuter les tests :
    pytest test_xml_corpus_processor.py -v

Pour exécuter avec couverture :
    pytest test_xml_corpus_processor.py --cov=xml_corpus --cov-report=html
"""

import unittest
import tempfile
import os
import logging
from pathlib import Path
import xml.etree.ElementTree as ET

# Import du module à tester
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from xml_corpus import (
    XMLCorpusProcessor,
    ProcessingConfig,
    PageMetadata,
    PATTERNS
)


class TestProcessingConfig(unittest.TestCase):
    """Tests pour la classe ProcessingConfig."""

    def test_config_with_defaults(self):
        """Test création de config avec valeurs par défaut."""
        config = ProcessingConfig(
            input_folder="/test/input",
            output_file="/test/output.txt"
        )

        self.assertEqual(config.language, 'la')
        self.assertEqual(config.log_level, logging.INFO)
        self.assertEqual(config.page_numbering_source, 'filename')
        self.assertEqual(config.starting_page_number, 1)
        self.assertTrue(config.include_empty_folios)
        self.assertEqual(config.column_mode, 'single')  # Nouveau: mode par défaut

    def test_config_with_custom_values(self):
        """Test création de config avec valeurs personnalisées."""
        metadata = {"title": "Test", "author": "Test Author"}
        config = ProcessingConfig(
            input_folder="/test/input",
            output_file="/test/output.txt",
            language='fr',
            metadata=metadata,
            starting_page_number=50
        )

        self.assertEqual(config.language, 'fr')
        self.assertEqual(config.metadata, metadata)
        self.assertEqual(config.starting_page_number, 50)


class TestPageMetadata(unittest.TestCase):
    """Tests pour la classe PageMetadata."""

    def test_page_metadata_creation(self):
        """Test création de métadonnées de page."""
        metadata = PageMetadata(
            filename="test_001.xml",
            page_number=1,
            running_title="Test Title",
            is_empty=False
        )

        self.assertEqual(metadata.filename, "test_001.xml")
        self.assertEqual(metadata.page_number, 1)
        self.assertEqual(metadata.running_title, "Test Title")
        self.assertFalse(metadata.is_empty)

    def test_page_metadata_default_empty(self):
        """Test valeur par défaut de is_empty."""
        metadata = PageMetadata(
            filename="test.xml",
            page_number=1,
            running_title="Title"
        )

        self.assertFalse(metadata.is_empty)


class TestPatterns(unittest.TestCase):
    """Tests pour les patterns regex."""

    def test_page_number_pattern(self):
        """Test extraction de numéro de page depuis nom de fichier."""
        pattern = PATTERNS['page_number']

        # Formats valides
        self.assertEqual(pattern.search("doc_0001.xml").group(1), "0001")
        self.assertEqual(pattern.search("FR674821001_001_E550779-4_0053.xml").group(1), "0053")
        self.assertEqual(pattern.search("manuscript_123").group(1), "123")

        # Formats invalides
        self.assertIsNone(pattern.search("document.xml"))
        self.assertIsNone(pattern.search("no_numbers_here.xml"))

    def test_hyphenated_word_pattern(self):
        """Test détection de mots coupés avec trait d'union."""
        pattern = PATTERNS['hyphenated_word']

        # Mot coupé valide
        match = pattern.search("Sancti-")
        self.assertIsNotNone(match)
        self.assertEqual(match.group(2), "Sancti")

        # Mot coupé avec préfixe
        match = pattern.search("In nomine sancti-")
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "In nomine ")
        self.assertEqual(match.group(2), "sancti")

        # Pas de trait d'union
        self.assertIsNone(pattern.search("Sanctitas"))


class TestXMLCorpusProcessor(unittest.TestCase):
    """Tests pour la classe XMLCorpusProcessor."""

    def setUp(self):
        """Prépare l'environnement de test."""
        # Créer un dossier temporaire
        self.temp_dir = tempfile.mkdtemp()
        self.output_file = os.path.join(self.temp_dir, "output.txt")

        # Créer des fichiers XML de test
        self._create_test_xml_files()

    def tearDown(self):
        """Nettoie après les tests."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_test_xml_files(self):
        """Crée des fichiers XML de test."""
        # XML simple avec contenu
        xml_content_1 = """<?xml version="1.0" encoding="UTF-8"?>
<PcGts>
    <Page>
        <TextRegion custom='structure {type:RunningTitleZone;}'>
            <TextEquiv>
                <Unicode>Test Title</Unicode>
            </TextEquiv>
        </TextRegion>
        <TextRegion custom='structure {type:MainZone;}'>
            <TextLine>
                <TextEquiv>
                    <Unicode>Dominus enim dicit</Unicode>
                </TextEquiv>
            </TextLine>
            <TextLine>
                <TextEquiv>
                    <Unicode>in evangelio sancto</Unicode>
                </TextEquiv>
            </TextLine>
        </TextRegion>
    </Page>
</PcGts>"""
        with open(os.path.join(self.temp_dir, "test_0001.xml"), "w", encoding="utf-8") as f:
            f.write(xml_content_1)

        # XML avec mot coupé
        xml_content_2 = """<?xml version="1.0" encoding="UTF-8"?>
<PcGts>
    <Page>
        <TextRegion custom='structure {type:MainZone;}'>
            <TextLine>
                <TextEquiv>
                    <Unicode>sancti-</Unicode>
                </TextEquiv>
            </TextLine>
            <TextLine>
                <TextEquiv>
                    <Unicode>tatis est magna</Unicode>
                </TextEquiv>
            </TextLine>
        </TextRegion>
    </Page>
</PcGts>"""
        with open(os.path.join(self.temp_dir, "test_0002.xml"), "w", encoding="utf-8") as f:
            f.write(xml_content_2)

        # XML vide (sans MainZone)
        xml_content_3 = """<?xml version="1.0" encoding="UTF-8"?>
<PcGts>
    <Page>
        <TextRegion custom='structure {type:NumberingZone;}'>
            <TextEquiv>
                <Unicode>3</Unicode>
            </TextEquiv>
        </TextRegion>
    </Page>
</PcGts>"""
        with open(os.path.join(self.temp_dir, "test_0003.xml"), "w", encoding="utf-8") as f:
            f.write(xml_content_3)

    def test_processor_initialization(self):
        """Test initialisation du processeur."""
        config = ProcessingConfig(
            input_folder=self.temp_dir,
            output_file=self.output_file,
            language='la'
        )

        processor = XMLCorpusProcessor(config)
        self.assertIsNotNone(processor)
        self.assertEqual(processor.config, config)

    def test_validate_paths_invalid_input(self):
        """Test validation avec dossier d'entrée inexistant."""
        config = ProcessingConfig(
            input_folder="/nonexistent/folder",
            output_file=self.output_file
        )

        with self.assertRaises(FileNotFoundError):
            XMLCorpusProcessor(config)

    def test_validate_params_invalid_source(self):
        """Test validation avec source de numérotation invalide."""
        config = ProcessingConfig(
            input_folder=self.temp_dir,
            output_file=self.output_file,
            page_numbering_source='invalid_source'
        )

        with self.assertRaises(ValueError):
            XMLCorpusProcessor(config)

    def test_validate_params_invalid_page_number(self):
        """Test validation avec numéro de page invalide."""
        config = ProcessingConfig(
            input_folder=self.temp_dir,
            output_file=self.output_file,
            starting_page_number=-1
        )

        with self.assertRaises(ValueError):
            XMLCorpusProcessor(config)

    def test_extract_page_number_from_filename(self):
        """Test extraction de numéro depuis nom de fichier."""
        config = ProcessingConfig(
            input_folder=self.temp_dir,
            output_file=self.output_file
        )
        processor = XMLCorpusProcessor(config)

        # Formats valides
        self.assertEqual(processor._extract_page_number_from_filename("doc_0001.xml"), 1)
        self.assertEqual(processor._extract_page_number_from_filename("test_0053.xml"), 53)

        # Format invalide
        self.assertIsNone(processor._extract_page_number_from_filename("nodoc.xml"))

    def test_merge_hyphenated_words(self):
        """Test fusion de mots coupés."""
        config = ProcessingConfig(
            input_folder=self.temp_dir,
            output_file=self.output_file
        )
        processor = XMLCorpusProcessor(config)

        # Cas simple
        lines = ["sancti-", "tatis"]
        result = processor._merge_hyphenated_words(lines)
        self.assertEqual(result, ["sanctitatis"])

        # Mot coupé avec texte avant
        lines = ["In nomine sancti-", "tatis est"]
        result = processor._merge_hyphenated_words(lines)
        self.assertEqual(result, ["In nomine sanctitatis est"])

        # Pas de trait d'union
        lines = ["sanctitas", "magna"]
        result = processor._merge_hyphenated_words(lines)
        self.assertEqual(result, ["sanctitas", "magna"])

    def test_clean_lines(self):
        """Test nettoyage des lignes."""
        config = ProcessingConfig(
            input_folder=self.temp_dir,
            output_file=self.output_file
        )
        processor = XMLCorpusProcessor(config)

        # Lignes avec numéros
        lines = ["1 Dominus est", "Sanctus dominus 2", "  "]
        result = processor._clean_lines(lines)
        self.assertEqual(result, ["Dominus est", "Sanctus dominus"])

        # Lignes trop courtes (< 3 caractères)
        lines = ["ab", "abc", "abcd"]
        result = processor._clean_lines(lines)
        self.assertEqual(result, ["abc", "abcd"])

    def test_get_sorted_xml_files(self):
        """Test récupération et tri des fichiers XML."""
        config = ProcessingConfig(
            input_folder=self.temp_dir,
            output_file=self.output_file
        )
        processor = XMLCorpusProcessor(config)

        files = processor._get_sorted_xml_files()

        # Vérifier qu'on a bien 3 fichiers
        self.assertEqual(len(files), 3)

        # Vérifier le tri
        self.assertEqual(files[0], "test_0001.xml")
        self.assertEqual(files[1], "test_0002.xml")
        self.assertEqual(files[2], "test_0003.xml")

    def test_get_sorted_xml_files_empty_folder(self):
        """Test avec dossier sans XML."""
        empty_dir = tempfile.mkdtemp()
        config = ProcessingConfig(
            input_folder=empty_dir,
            output_file=self.output_file
        )
        processor = XMLCorpusProcessor(config)

        with self.assertRaises(ValueError):
            processor._get_sorted_xml_files()

        os.rmdir(empty_dir)

    def test_calculate_page_number_filename_mode(self):
        """Test calcul de numéro de page en mode filename."""
        config = ProcessingConfig(
            input_folder=self.temp_dir,
            output_file=self.output_file,
            page_numbering_source='filename',
            starting_page_number=100
        )
        processor = XMLCorpusProcessor(config)

        # Index 1 → page 100
        result = processor._calculate_page_number("test.xml", 1, None)
        self.assertEqual(result, 100)

        # Index 5 → page 104
        result = processor._calculate_page_number("test.xml", 5, None)
        self.assertEqual(result, 104)

    def test_calculate_page_number_numbering_zone_mode(self):
        """Test calcul de numéro de page en mode numbering_zone."""
        config = ProcessingConfig(
            input_folder=self.temp_dir,
            output_file=self.output_file,
            page_numbering_source='numbering_zone'
        )
        processor = XMLCorpusProcessor(config)

        # Avec numéro extrait
        result = processor._calculate_page_number("test.xml", 1, 53)
        self.assertEqual(result, 53)

        # Sans numéro extrait (fallback sur index)
        result = processor._calculate_page_number("test.xml", 2, None)
        self.assertEqual(result, 2)

    def test_format_document_empty(self):
        """Test formatage d'un document vide."""
        config = ProcessingConfig(
            input_folder=self.temp_dir,
            output_file=self.output_file,
            metadata={"test": "value"}
        )
        processor = XMLCorpusProcessor(config)

        metadata = PageMetadata(
            filename="test.xml",
            page_number=1,
            running_title="Title",
            is_empty=True
        )

        result = processor._format_document(metadata, [])

        self.assertIn('empty="true"', result)
        self.assertIn('test="value"', result)
        self.assertIn('<doc', result)
        self.assertIn('</doc>', result)

    # Note : Les tests avec TreeTagger nécessitent l'installation de TreeTagger
    # et sont commentés pour ne pas bloquer l'exécution des tests
    """
    def test_lemmatize_line(self):
        config = ProcessingConfig(
            input_folder=self.temp_dir,
            output_file=self.output_file,
            language='la'
        )
        processor = XMLCorpusProcessor(config)
        processor.tagger = processor._initialize_tagger()

        result = processor._lemmatize_line("Dominus est")
        self.assertIsInstance(result, list)
        if result:
            self.assertEqual(len(result[0]), 3)  # (word, pos, lemma)
    """


class TestIntegration(unittest.TestCase):
    """Tests d'intégration (sans TreeTagger)."""

    def setUp(self):
        """Prépare l'environnement de test."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_file = os.path.join(self.temp_dir, "output.txt")

        # Créer un fichier XML simple
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<PcGts>
    <Page>
        <TextRegion custom='structure {type:MainZone;}'>
            <TextLine>
                <TextEquiv>
                    <Unicode>Test line</Unicode>
                </TextEquiv>
            </TextLine>
        </TextRegion>
    </Page>
</PcGts>"""
        with open(os.path.join(self.temp_dir, "test_0001.xml"), "w", encoding="utf-8") as f:
            f.write(xml_content)

    def tearDown(self):
        """Nettoie après les tests."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_process_xml_page(self):
        """Test traitement d'une page XML en mode single."""
        config = ProcessingConfig(
            input_folder=self.temp_dir,
            output_file=self.output_file,
            column_mode='single'
        )
        processor = XMLCorpusProcessor(config)

        file_path = os.path.join(self.temp_dir, "test_0001.xml")
        page_num, title, columns = processor._process_xml_page(file_path)

        self.assertIsNone(page_num)  # Pas de NumberingZone
        self.assertEqual(title, "No running title")  # Pas de RunningTitleZone

        # Vérifier qu'on a une seule colonne
        self.assertEqual(len(columns), 1)
        col_id, lines = columns[0]
        self.assertIsNone(col_id)  # En mode single, pas d'identifiant de colonne
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], "Test line")


class TestDualColumnMode(unittest.TestCase):
    """Tests pour le mode dual-column."""

    def setUp(self):
        """Prépare l'environnement de test."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_file = os.path.join(self.temp_dir, "output.txt")

        # Créer un fichier XML avec deux colonnes
        xml_dual_content = """<?xml version="1.0" encoding="UTF-8"?>
<PcGts>
    <Page>
        <TextRegion custom='structure {type:RunningTitleZone;}'>
            <TextEquiv>
                <Unicode>Dual Column Test</Unicode>
            </TextEquiv>
        </TextRegion>
        <TextRegion custom='structure {type:MainZone:column#1;}'>
            <TextLine>
                <TextEquiv>
                    <Unicode>Column 1 line 1</Unicode>
                </TextEquiv>
            </TextLine>
            <TextLine>
                <TextEquiv>
                    <Unicode>Column 1 line 2</Unicode>
                </TextEquiv>
            </TextLine>
        </TextRegion>
        <TextRegion custom='structure {type:MainZone:column#2;}'>
            <TextLine>
                <TextEquiv>
                    <Unicode>Column 2 line 1</Unicode>
                </TextEquiv>
            </TextLine>
            <TextLine>
                <TextEquiv>
                    <Unicode>Column 2 line 2</Unicode>
                </TextEquiv>
            </TextLine>
        </TextRegion>
    </Page>
</PcGts>"""
        with open(os.path.join(self.temp_dir, "dual_0001.xml"), "w", encoding="utf-8") as f:
            f.write(xml_dual_content)

        # Créer un fichier avec une seule colonne remplie
        xml_partial_content = """<?xml version="1.0" encoding="UTF-8"?>
<PcGts>
    <Page>
        <TextRegion custom='structure {type:MainZone:column#1;}'>
            <TextLine>
                <TextEquiv>
                    <Unicode>Only column 1</Unicode>
                </TextEquiv>
            </TextLine>
        </TextRegion>
    </Page>
</PcGts>"""
        with open(os.path.join(self.temp_dir, "dual_0002.xml"), "w", encoding="utf-8") as f:
            f.write(xml_partial_content)

    def tearDown(self):
        """Nettoie après les tests."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_dual_column_config(self):
        """Test configuration en mode dual."""
        config = ProcessingConfig(
            input_folder=self.temp_dir,
            output_file=self.output_file,
            column_mode='dual'
        )

        self.assertEqual(config.column_mode, 'dual')

    def test_dual_column_validation(self):
        """Test validation du mode de colonnes."""
        config = ProcessingConfig(
            input_folder=self.temp_dir,
            output_file=self.output_file,
            column_mode='invalid_mode'
        )

        with self.assertRaises(ValueError):
            XMLCorpusProcessor(config)

    def test_extract_dual_columns(self):
        """Test extraction de deux colonnes."""
        config = ProcessingConfig(
            input_folder=self.temp_dir,
            output_file=self.output_file,
            column_mode='dual'
        )
        processor = XMLCorpusProcessor(config)

        file_path = os.path.join(self.temp_dir, "dual_0001.xml")
        page_num, title, columns = processor._process_xml_page(file_path)

        # Vérifier qu'on a deux colonnes
        self.assertEqual(len(columns), 2)

        # Vérifier colonne 1
        col1_id, col1_lines = columns[0]
        self.assertEqual(col1_id, "col1")
        self.assertEqual(len(col1_lines), 2)
        self.assertEqual(col1_lines[0], "Column 1 line 1")

        # Vérifier colonne 2
        col2_id, col2_lines = columns[1]
        self.assertEqual(col2_id, "col2")
        self.assertEqual(len(col2_lines), 2)
        self.assertEqual(col2_lines[0], "Column 2 line 1")

    def test_extract_partial_dual_columns(self):
        """Test extraction avec une seule colonne remplie."""
        config = ProcessingConfig(
            input_folder=self.temp_dir,
            output_file=self.output_file,
            column_mode='dual'
        )
        processor = XMLCorpusProcessor(config)

        file_path = os.path.join(self.temp_dir, "dual_0002.xml")
        page_num, title, columns = processor._process_xml_page(file_path)

        # Vérifier qu'on a deux colonnes (dont une vide)
        self.assertEqual(len(columns), 2)

        # Colonne 1 remplie
        col1_id, col1_lines = columns[0]
        self.assertEqual(col1_id, "col1")
        self.assertEqual(len(col1_lines), 1)

        # Colonne 2 vide
        col2_id, col2_lines = columns[1]
        self.assertEqual(col2_id, "col2")
        self.assertEqual(len(col2_lines), 0)

    def test_page_metadata_with_column(self):
        """Test métadonnées avec identifiant de colonne."""
        metadata = PageMetadata(
            filename="test.xml",
            page_number=1,
            running_title="Title",
            column="col1"
        )

        self.assertEqual(metadata.column, "col1")

    def test_format_document_with_column(self):
        """Test formatage avec identifiant de colonne."""
        config = ProcessingConfig(
            input_folder=self.temp_dir,
            output_file=self.output_file,
            column_mode='dual'
        )
        processor = XMLCorpusProcessor(config)

        metadata = PageMetadata(
            filename="test.xml",
            page_number=1,
            running_title="Title",
            column="col1",
            is_empty=True
        )

        result = processor._format_document(metadata, [])

        # Vérifier que le folio contient l'identifiant de colonne
        self.assertIn('folio="test.xml-col1"', result)
        self.assertIn('page_number="1"', result)


def run_tests():
    """Exécute tous les tests."""
    # Créer une suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Ajouter tous les tests
    suite.addTests(loader.loadTestsFromTestCase(TestProcessingConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestPageMetadata))
    suite.addTests(loader.loadTestsFromTestCase(TestPatterns))
    suite.addTests(loader.loadTestsFromTestCase(TestXMLCorpusProcessor))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestDualColumnMode))

    # Exécuter les tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Retourner le code de sortie
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit_code = run_tests()
    exit(exit_code)
