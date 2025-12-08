"""
Tests unitaires pour l'étape 3: Export
"""

import pytest
from pathlib import Path
import tempfile
import json

from PAGEtopage.config import Config
from PAGEtopage.models import (
    AnnotatedPage, AnnotatedCorpus, PageMetadata,
    Token, Sentence
)
from PAGEtopage.step3_export import (
    TextExporter, VerticalParser,
    CleanFormatter, DiplomaticFormatter, AnnotatedFormatter
)


# Chemin vers les fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestVerticalParser:
    """Tests pour le parseur de format vertical"""

    def test_parse_sample_file(self):
        """Test parsing du fichier vertical exemple"""
        parser = VerticalParser()
        sample_file = FIXTURES_DIR / "sample_vertical.txt"

        if not sample_file.exists():
            pytest.skip("Fichier sample_vertical.txt non trouvé")

        corpus = parser.parse_file(sample_file)

        assert isinstance(corpus, AnnotatedCorpus)
        assert len(corpus.pages) == 2

    def test_parse_metadata(self):
        """Test parsing des métadonnées"""
        parser = VerticalParser()
        sample_file = FIXTURES_DIR / "sample_vertical.txt"

        if not sample_file.exists():
            pytest.skip("Fichier sample_vertical.txt non trouvé")

        corpus = parser.parse_file(sample_file)
        page = corpus.pages[0]

        assert page.metadata.folio == "0042_1.xml"
        assert page.metadata.page_number == 1
        assert page.metadata.running_title == "De Trinitate Liber I"
        assert page.metadata.corpus_metadata.get("edition_id") == "Edi-7"

    def test_parse_sentences(self):
        """Test parsing des phrases"""
        parser = VerticalParser()
        sample_file = FIXTURES_DIR / "sample_vertical.txt"

        if not sample_file.exists():
            pytest.skip("Fichier sample_vertical.txt non trouvé")

        corpus = parser.parse_file(sample_file)
        page = corpus.pages[0]

        assert len(page.sentences) == 2

        # Vérifie la première phrase
        first_sentence = page.sentences[0]
        assert len(first_sentence.tokens) >= 3
        assert first_sentence.tokens[0].word == "Dominus"
        assert first_sentence.tokens[0].pos == "NOM"
        assert first_sentence.tokens[0].lemma == "dominus"

    def test_parse_content(self):
        """Test parsing de contenu brut"""
        parser = VerticalParser()

        content = '''<doc folio="test.xml" page_number="1" running_title="Test">
<s>
Word1	POS1	lemma1
Word2	POS2	lemma2
</s>
</doc>'''

        corpus = parser.parse_content(content)

        assert len(corpus.pages) == 1
        assert corpus.pages[0].metadata.folio == "test.xml"
        assert len(corpus.pages[0].sentences) == 1
        assert len(corpus.pages[0].sentences[0].tokens) == 2

    def test_parse_empty_page(self):
        """Test parsing page vide"""
        parser = VerticalParser()

        content = '''<doc folio="empty.xml" page_number="1" running_title="Empty">
</doc>'''

        corpus = parser.parse_content(content)

        assert len(corpus.pages) == 1
        assert corpus.pages[0].is_empty


class TestCleanFormatter:
    """Tests pour le formateur clean"""

    def test_format_simple_sentence(self):
        """Test formatage phrase simple"""
        formatter = CleanFormatter()

        sentence = Sentence(
            tokens=[
                Token(word="Dominus", pos="NOM", lemma="dominus"),
                Token(word="dicit", pos="VER", lemma="dico"),
                Token(word=".", pos="PUNCT", lemma=".")
            ],
            id=1
        )

        result = formatter.format_sentence(sentence)

        assert result == "Dominus dicit."

    def test_format_page(self):
        """Test formatage page complète"""
        formatter = CleanFormatter()

        metadata = PageMetadata(folio="test.xml", page_number=1)
        page = AnnotatedPage(
            metadata=metadata,
            sentences=[
                Sentence(tokens=[
                    Token(word="Amen", pos="INT", lemma="amen"),
                    Token(word=".", pos="PUNCT", lemma=".")
                ], id=1)
            ]
        )

        result = formatter.format_page(page)
        assert result == "Amen."

    def test_format_without_punctuation(self):
        """Test formatage sans ponctuation"""
        formatter = CleanFormatter(include_punctuation=False)

        sentence = Sentence(
            tokens=[
                Token(word="Dominus", pos="NOM", lemma="dominus"),
                Token(word=".", pos="PUNCT", lemma=".")
            ],
            id=1
        )

        result = formatter.format_sentence(sentence)
        assert result == "Dominus"


class TestDiplomaticFormatter:
    """Tests pour le formateur diplomatic"""

    def test_format_with_annotations(self):
        """Test formatage avec annotations"""
        formatter = DiplomaticFormatter()

        sentence = Sentence(
            tokens=[
                Token(word="Dominus", pos="NOM", lemma="dominus"),
                Token(word=".", pos="PUNCT", lemma=".")
            ],
            id=1
        )

        result = formatter.format_sentence(sentence)

        assert "Dominus(NOM→dominus)" in result
        assert result.endswith(".")

    def test_format_without_lemma(self):
        """Test formatage sans lemme"""
        formatter = DiplomaticFormatter(show_lemma=False)

        sentence = Sentence(
            tokens=[
                Token(word="Dominus", pos="NOM", lemma="dominus")
            ],
            id=1
        )

        result = formatter.format_sentence(sentence)

        assert result == "Dominus(NOM)"

    def test_custom_separator(self):
        """Test séparateur personnalisé"""
        formatter = DiplomaticFormatter(separator=":")

        sentence = Sentence(
            tokens=[
                Token(word="Dominus", pos="NOM", lemma="dominus")
            ],
            id=1
        )

        result = formatter.format_sentence(sentence)
        assert "NOM:dominus" in result


class TestAnnotatedFormatter:
    """Tests pour le formateur annotated"""

    def test_format_tabular(self):
        """Test formatage tabulaire"""
        formatter = AnnotatedFormatter()

        sentence = Sentence(
            tokens=[
                Token(word="Dominus", pos="NOM", lemma="dominus"),
                Token(word="dicit", pos="VER", lemma="dico")
            ],
            id=1
        )

        result = formatter.format_sentence(sentence)

        assert "<s>" in result
        assert "</s>" in result
        assert "Dominus\tNOM\tdominus" in result
        assert "dicit\tVER\tdico" in result

    def test_format_without_markers(self):
        """Test formatage sans marqueurs de phrase"""
        formatter = AnnotatedFormatter(include_sentence_markers=False)

        sentence = Sentence(
            tokens=[Token(word="Amen", pos="INT", lemma="amen")],
            id=1
        )

        result = formatter.format_sentence(sentence)

        assert "<s>" not in result
        assert "</s>" not in result


class TestTextExporter:
    """Tests pour l'exporteur de texte"""

    def test_export_single_page(self):
        """Test export d'une page"""
        config = Config()
        config.export.format = "clean"
        config.export.generate_index = False
        config.export.generate_combined = False

        exporter = TextExporter(config)

        metadata = PageMetadata(
            folio="test.xml",
            page_number=1,
            corpus_metadata={"edition_id": "TEST"}
        )
        page = AnnotatedPage(
            metadata=metadata,
            sentences=[
                Sentence(tokens=[
                    Token(word="Amen", pos="INT", lemma="amen"),
                    Token(word=".", pos="PUNCT", lemma=".")
                ], id=1)
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_folder = Path(tmpdir)
            page_files = exporter.export_pages([page], output_folder)

            assert len(page_files) == 1
            assert exporter.exported_count == 1

            # Vérifie le contenu du fichier
            output_file = output_folder / list(page_files.values())[0]
            content = output_file.read_text(encoding="utf-8")
            assert "Amen." in content

    def test_export_with_index(self):
        """Test export avec génération d'index"""
        config = Config()
        config.export.format = "clean"
        config.export.generate_index = True
        config.export.generate_combined = True

        exporter = TextExporter(config)

        metadata = PageMetadata(folio="test.xml", page_number=1)
        page = AnnotatedPage(
            metadata=metadata,
            sentences=[
                Sentence(tokens=[
                    Token(word="Test", pos="NOM", lemma="test")
                ], id=1)
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_folder = Path(tmpdir)
            exporter.export_pages([page], output_folder)

            # Vérifie la présence des fichiers d'index
            assert (output_folder / "pages_index.json").exists()
            assert (output_folder / "texte_complet.txt").exists()
            assert (output_folder / "corpus_stats.json").exists()

    def test_export_from_vertical_file(self):
        """Test export depuis fichier vertical"""
        sample_file = FIXTURES_DIR / "sample_vertical.txt"

        if not sample_file.exists():
            pytest.skip("Fichier sample_vertical.txt non trouvé")

        config = Config()
        config.export.format = "clean"
        config.export.generate_index = False
        config.export.generate_combined = False

        exporter = TextExporter(config)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_folder = Path(tmpdir)
            page_files = exporter.export(sample_file, output_folder)

            assert len(page_files) == 2

    def test_filename_pattern(self):
        """Test pattern de nom de fichier"""
        config = Config()
        config.export.page_filename_pattern = "folio_{folio}_p{number:03d}.txt"

        exporter = TextExporter(config)

        metadata = PageMetadata(folio="0042.xml", page_number=5)
        page = AnnotatedPage(metadata=metadata, sentences=[])

        filename = exporter._generate_filename(page)
        assert filename == "folio_0042_p005.txt"

    def test_set_format(self):
        """Test changement de format"""
        config = Config()
        exporter = TextExporter(config)

        exporter.set_format("diplomatic")
        assert config.export.format == "diplomatic"
        assert isinstance(exporter.formatter, DiplomaticFormatter)


class TestIndexGeneration:
    """Tests pour la génération d'index"""

    def test_pages_index_content(self):
        """Test contenu de l'index des pages"""
        config = Config()
        config.export.generate_index = True
        config.export.generate_combined = False

        exporter = TextExporter(config)

        metadata = PageMetadata(
            folio="test.xml",
            page_number=1,
            running_title="Test Title",
            corpus_metadata={"edition_id": "TEST-001", "author": "Author"}
        )
        page = AnnotatedPage(
            metadata=metadata,
            sentences=[
                Sentence(tokens=[
                    Token(word="Word", pos="NOM", lemma="word")
                ], id=1)
            ]
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_folder = Path(tmpdir)
            exporter.export_pages([page], output_folder)

            index_file = output_folder / "pages_index.json"
            with open(index_file, "r", encoding="utf-8") as f:
                index = json.load(f)

            assert "pages" in index
            assert len(index["pages"]) == 1

            page_entry = index["pages"][0]
            assert page_entry["folio"] == "test.xml"
            assert page_entry["page_number"] == 1
            assert page_entry["sentence_count"] == 1
            assert page_entry["edition_id"] == "TEST-001"
