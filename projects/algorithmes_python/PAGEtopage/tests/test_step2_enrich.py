"""
Tests unitaires pour l'étape 2: Enrichissement
"""

import pytest
from pathlib import Path
import tempfile

from PAGEtopage.config import Config
from PAGEtopage.models import (
    ExtractedPage, PageMetadata, AnnotatedPage,
    Token, Sentence
)
from PAGEtopage.step2_enrich import EnrichmentProcessor, Tokenizer
from PAGEtopage.step2_enrich.lemmatizer import SimpleLemmatizer, CLTKLemmatizer


class TestTokenizer:
    """Tests pour le tokeniseur"""

    def test_tokenize_simple_sentence(self):
        """Test tokenisation phrase simple"""
        tokenizer = Tokenizer()
        result = tokenizer.tokenize_text("Dominus dicit.")

        assert len(result) == 1
        assert result[0] == ["Dominus", "dicit", "."]

    def test_tokenize_multiple_sentences(self):
        """Test tokenisation plusieurs phrases"""
        tokenizer = Tokenizer()
        result = tokenizer.tokenize_text("Dominus dicit. Amen.")

        assert len(result) == 2
        assert result[0] == ["Dominus", "dicit", "."]
        assert result[1] == ["Amen", "."]

    def test_tokenize_with_punctuation(self):
        """Test tokenisation avec ponctuation variée"""
        tokenizer = Tokenizer()
        result = tokenizer.tokenize_text("Quid est? Nihil!")

        assert len(result) == 2
        assert "?" in result[0]
        assert "!" in result[1]

    def test_tokenize_lines(self):
        """Test tokenisation depuis lignes"""
        tokenizer = Tokenizer()
        lines = ["Dominus dicit", "in evangelio."]
        result = tokenizer.tokenize_lines(lines)

        assert len(result) == 1
        assert "Dominus" in result[0]
        assert "evangelio" in result[0]

    def test_is_punctuation(self):
        """Test détection ponctuation"""
        tokenizer = Tokenizer()

        assert tokenizer.is_punctuation(".")
        assert tokenizer.is_punctuation(",")
        assert tokenizer.is_punctuation("!")
        assert not tokenizer.is_punctuation("word")

    def test_preserve_case(self):
        """Test préservation de la casse"""
        tokenizer = Tokenizer(preserve_case=True)
        result = tokenizer.tokenize_text("Dominus DICIT.")

        assert result[0][0] == "Dominus"
        assert result[0][1] == "DICIT"

    def test_empty_text(self):
        """Test texte vide"""
        tokenizer = Tokenizer()

        assert tokenizer.tokenize_text("") == []
        assert tokenizer.tokenize_text("   ") == []


class TestSimpleLemmatizer:
    """Tests pour le lemmatiseur simple"""

    def test_lemmatize_simple(self):
        """Test lemmatisation simple"""
        lemmatizer = SimpleLemmatizer()
        result = lemmatizer.lemmatize("Dominus dicit.")

        assert len(result) == 3
        assert result[0].word == "Dominus"
        assert result[0].lemma == "dominus"
        assert result[2].pos == "PUNCT"

    def test_lemmatize_tokens(self):
        """Test lemmatisation de tokens"""
        lemmatizer = SimpleLemmatizer()
        result = lemmatizer.lemmatize_tokens(["Dominus", "dicit"])

        assert len(result) == 2
        assert result[0].word == "Dominus"
        assert result[1].word == "dicit"


class TestCLTKLemmatizer:
    """Tests pour le lemmatiseur CLTK"""

    def test_initialization(self):
        """Test que CLTK peut être initialisé"""
        try:
            lemmatizer = CLTKLemmatizer(language="lat")
            assert not lemmatizer.is_initialized
        except ImportError:
            pytest.skip("CLTK non installé")

    def test_lemmatize_with_cltk(self):
        """Test lemmatisation avec CLTK"""
        try:
            lemmatizer = CLTKLemmatizer(language="lat")
            result = lemmatizer.lemmatize("Dominus dicit.")

            assert len(result) >= 2
            # Vérifie que les tokens ont été annotés
            assert all(hasattr(t, 'pos') for t in result)
            assert all(hasattr(t, 'lemma') for t in result)
        except ImportError:
            pytest.skip("CLTK non installé")
        except Exception as e:
            # CLTK peut échouer si les modèles ne sont pas téléchargés
            pytest.skip(f"CLTK non configuré: {e}")


class TestEnrichmentProcessor:
    """Tests pour le processeur d'enrichissement"""

    def test_process_page(self):
        """Test enrichissement d'une page"""
        config = Config()
        config.enrichment.lemmatizer = "simple"  # Utilise le lemmatiseur simple

        processor = EnrichmentProcessor(config)

        metadata = PageMetadata(
            folio="test.xml",
            page_number=1,
            corpus_metadata={"author": "Test"}
        )
        extracted = ExtractedPage(
            metadata=metadata,
            lines=["Dominus dicit.", "Amen."]
        )

        annotated = processor.process_page(extracted)

        assert isinstance(annotated, AnnotatedPage)
        assert len(annotated.sentences) == 2
        assert annotated.metadata.folio == "test.xml"

    def test_process_empty_page(self):
        """Test enrichissement page vide"""
        config = Config()
        config.enrichment.lemmatizer = "simple"

        processor = EnrichmentProcessor(config)

        metadata = PageMetadata(folio="empty.xml", page_number=1)
        extracted = ExtractedPage(metadata=metadata, lines=[])

        annotated = processor.process_page(extracted)

        assert annotated.is_empty
        assert len(annotated.sentences) == 0

    def test_process_pages(self):
        """Test enrichissement de plusieurs pages"""
        config = Config()
        config.enrichment.lemmatizer = "simple"

        processor = EnrichmentProcessor(config)

        pages = []
        for i in range(3):
            metadata = PageMetadata(folio=f"page_{i}.xml", page_number=i)
            pages.append(ExtractedPage(
                metadata=metadata,
                lines=[f"Text page {i}."]
            ))

        annotated = processor.process_pages(pages)

        assert len(annotated) == 3
        assert processor.processed_count == 3

    def test_save_vertical(self):
        """Test sauvegarde en format vertical"""
        config = Config()
        config.enrichment.lemmatizer = "simple"
        config.corpus.edition_id = "TEST-001"

        processor = EnrichmentProcessor(config)

        metadata = PageMetadata(
            folio="test.xml",
            page_number=1,
            running_title="Test Title",
            corpus_metadata={"edition_id": "TEST-001"}
        )
        extracted = ExtractedPage(
            metadata=metadata,
            lines=["Dominus dicit."]
        )

        annotated = [processor.process_page(extracted)]

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            temp_path = Path(f.name)

        try:
            processor.save_vertical(annotated, temp_path)

            assert temp_path.exists()

            content = temp_path.read_text(encoding="utf-8")
            assert "<doc" in content
            assert "folio=" in content
            assert "<s>" in content
            assert "</s>" in content
            assert "</doc>" in content
        finally:
            temp_path.unlink(missing_ok=True)


class TestToken:
    """Tests pour le modèle Token"""

    def test_to_vertical_line(self):
        """Test formatage en ligne verticale"""
        token = Token(word="Dominus", pos="NOM", lemma="dominus")
        assert token.to_vertical_line() == "Dominus\tNOM\tdominus"

    def test_from_vertical_line(self):
        """Test parsing depuis ligne verticale"""
        token = Token.from_vertical_line("Dominus\tNOM\tdominus")

        assert token.word == "Dominus"
        assert token.pos == "NOM"
        assert token.lemma == "dominus"

    def test_from_vertical_line_incomplete(self):
        """Test parsing ligne incomplète"""
        token = Token.from_vertical_line("Dominus")

        assert token.word == "Dominus"
        assert token.pos == "UNK"


class TestSentence:
    """Tests pour le modèle Sentence"""

    def test_to_vertical(self):
        """Test formatage en vertical"""
        sentence = Sentence(
            tokens=[
                Token(word="Dominus", pos="NOM", lemma="dominus"),
                Token(word=".", pos="PUNCT", lemma=".")
            ],
            id=1
        )

        vertical = sentence.to_vertical()

        assert "<s>" in vertical
        assert "</s>" in vertical
        assert "Dominus\tNOM\tdominus" in vertical

    def test_get_text(self):
        """Test récupération du texte"""
        sentence = Sentence(
            tokens=[
                Token(word="Dominus", pos="NOM", lemma="dominus"),
                Token(word="dicit", pos="VER", lemma="dico"),
                Token(word=".", pos="PUNCT", lemma=".")
            ],
            id=1
        )

        text = sentence.get_text()
        assert "Dominus" in text
        assert "dicit" in text


class TestAnnotatedPage:
    """Tests pour le modèle AnnotatedPage"""

    def test_to_vertical(self):
        """Test formatage complet en vertical"""
        metadata = PageMetadata(
            folio="test.xml",
            page_number=1,
            running_title="Test",
            corpus_metadata={"edition_id": "TEST"}
        )

        sentence = Sentence(
            tokens=[Token(word="Amen", pos="INT", lemma="amen")],
            id=1
        )

        page = AnnotatedPage(metadata=metadata, sentences=[sentence])
        vertical = page.to_vertical()

        assert '<doc folio="test.xml"' in vertical
        assert 'page_number="1"' in vertical
        assert 'edition_id="TEST"' in vertical
        assert "<s>" in vertical
        assert "Amen\tINT\tamen" in vertical
        assert "</doc>" in vertical
