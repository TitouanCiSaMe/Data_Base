"""
Tests unitaires pour l'étape 1: Extraction XML
"""

import pytest
from pathlib import Path
import tempfile
import json

from PAGEtopage.config import Config
from PAGEtopage.models import ExtractedPage, PageMetadata
from PAGEtopage.step1_extract import XMLPageExtractor, ZoneParser, HyphenMerger


# Chemin vers les fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestHyphenMerger:
    """Tests pour la fusion des mots coupés"""

    def test_merge_simple_hyphen(self):
        """Test fusion simple avec tiret"""
        merger = HyphenMerger()
        lines = ["consti-", "tutio est magna."]
        result = merger.merge_lines(lines)

        assert len(result) == 1
        assert result[0] == "constitutio est magna."

    def test_merge_multiple_hyphens(self):
        """Test fusion de plusieurs mots coupés"""
        merger = HyphenMerger()
        lines = [
            "Domi-",
            "nus dicit in evan-",
            "gelio sancto."
        ]
        result = merger.merge_lines(lines)

        assert len(result) == 1
        assert result[0] == "Dominus dicit in evangelio sancto."

    def test_no_hyphen(self):
        """Test sans tiret"""
        merger = HyphenMerger()
        lines = ["Dominus dicit.", "Amen."]
        result = merger.merge_lines(lines)

        assert len(result) == 2
        assert result[0] == "Dominus dicit."
        assert result[1] == "Amen."

    def test_empty_lines(self):
        """Test avec lignes vides"""
        merger = HyphenMerger()
        lines = ["Dominus", "", "dicit."]
        result = merger.merge_lines(lines)

        assert "" in result

    def test_merged_count(self):
        """Test du compteur de fusions"""
        merger = HyphenMerger()
        lines = ["consti-", "tutio", "magna-", "nimis"]
        merger.merge_lines(lines)

        assert merger.merged_count == 2


class TestZoneParser:
    """Tests pour le parseur de zones XML"""

    def test_parse_sample_file(self):
        """Test parsing du fichier exemple"""
        parser = ZoneParser()
        sample_xml = FIXTURES_DIR / "sample_page.xml"

        if not sample_xml.exists():
            pytest.skip("Fichier sample_page.xml non trouvé")

        zones = parser.parse_file(str(sample_xml))

        assert "main" in zones
        assert "running_title" in zones
        assert "numbering" in zones

    def test_extract_running_title(self):
        """Test extraction du titre courant"""
        parser = ZoneParser()
        sample_xml = FIXTURES_DIR / "sample_page.xml"

        if not sample_xml.exists():
            pytest.skip("Fichier sample_page.xml non trouvé")

        import xml.etree.ElementTree as ET
        tree = ET.parse(sample_xml)
        root = tree.getroot()

        title = parser.extract_running_title(root)
        assert "De Trinitate" in title

    def test_extract_main_zone_lines(self):
        """Test extraction des lignes de la zone principale"""
        parser = ZoneParser()
        sample_xml = FIXTURES_DIR / "sample_page.xml"

        if not sample_xml.exists():
            pytest.skip("Fichier sample_page.xml non trouvé")

        import xml.etree.ElementTree as ET
        tree = ET.parse(sample_xml)
        root = tree.getroot()

        lines = parser.extract_main_zone_lines(root, column_mode="single")

        assert len(lines) >= 1
        assert any("Dominus" in line for line in lines)


class TestXMLPageExtractor:
    """Tests pour l'extracteur XML principal"""

    def test_extract_single_file(self):
        """Test extraction d'un fichier unique"""
        config = Config()
        extractor = XMLPageExtractor(config)

        sample_xml = FIXTURES_DIR / "sample_page.xml"

        if not sample_xml.exists():
            pytest.skip("Fichier sample_page.xml non trouvé")

        page = extractor.extract_file(sample_xml)

        assert isinstance(page, ExtractedPage)
        assert page.metadata.folio == "sample_page.xml"
        assert len(page.lines) > 0

    def test_metadata_extraction(self):
        """Test extraction des métadonnées"""
        config = Config()
        config.corpus.edition_id = "TEST-001"
        config.corpus.author = "Test Author"

        extractor = XMLPageExtractor(config)
        sample_xml = FIXTURES_DIR / "sample_page.xml"

        if not sample_xml.exists():
            pytest.skip("Fichier sample_page.xml non trouvé")

        page = extractor.extract_file(sample_xml)

        assert page.metadata.corpus_metadata["edition_id"] == "TEST-001"
        assert page.metadata.corpus_metadata["author"] == "Test Author"

    def test_save_to_json(self):
        """Test sauvegarde en JSON"""
        config = Config()
        extractor = XMLPageExtractor(config)

        sample_xml = FIXTURES_DIR / "sample_page.xml"

        if not sample_xml.exists():
            pytest.skip("Fichier sample_page.xml non trouvé")

        page = extractor.extract_file(sample_xml)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            extractor.save_to_json([page], temp_path)

            assert temp_path.exists()

            with open(temp_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert "pages" in data
            assert len(data["pages"]) == 1
        finally:
            temp_path.unlink(missing_ok=True)

    def test_page_number_from_filename(self):
        """Test extraction du numéro de page depuis le nom de fichier"""
        config = Config()
        config.pagination.starting_page_number = 1

        extractor = XMLPageExtractor(config)

        # Test différents patterns
        assert extractor._extract_page_number_from_filename("0042.xml", 0) == 42
        assert extractor._extract_page_number_from_filename("0042_1.xml", 0) == 42
        assert extractor._extract_page_number_from_filename("page_0015.xml", 0) == 15
        assert extractor._extract_page_number_from_filename("folio_7.xml", 0) == 7

        # Fallback
        assert extractor._extract_page_number_from_filename("unknown.xml", 5) == 6


class TestExtractedPage:
    """Tests pour le modèle ExtractedPage"""

    def test_to_dict(self):
        """Test conversion en dictionnaire"""
        metadata = PageMetadata(
            folio="test.xml",
            page_number=1,
            running_title="Test Title",
            corpus_metadata={"author": "Test"}
        )
        page = ExtractedPage(metadata=metadata, lines=["Line 1", "Line 2"])

        data = page.to_dict()

        assert data["metadata"]["folio"] == "test.xml"
        assert data["lines"] == ["Line 1", "Line 2"]

    def test_from_dict(self):
        """Test création depuis dictionnaire"""
        data = {
            "metadata": {
                "folio": "test.xml",
                "page_number": 1,
                "running_title": "Test",
                "corpus_metadata": {}
            },
            "lines": ["Line 1"],
            "is_empty": False
        }

        page = ExtractedPage.from_dict(data)

        assert page.metadata.folio == "test.xml"
        assert page.lines == ["Line 1"]

    def test_is_empty(self):
        """Test détection page vide"""
        metadata = PageMetadata(folio="test.xml", page_number=1)

        # Page avec contenu
        page1 = ExtractedPage(metadata=metadata, lines=["Content"])
        assert not page1.is_empty

        # Page vide
        page2 = ExtractedPage(metadata=metadata, lines=[])
        assert page2.is_empty

        # Page avec lignes vides
        page3 = ExtractedPage(metadata=metadata, lines=["", "  "])
        assert page3.is_empty

    def test_get_full_text(self):
        """Test récupération du texte complet"""
        metadata = PageMetadata(folio="test.xml", page_number=1)
        page = ExtractedPage(metadata=metadata, lines=["Line 1", "Line 2"])

        assert page.get_full_text() == "Line 1\nLine 2"
