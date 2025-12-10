"""
Interface de lemmatisation multi-backend

Fournit une interface unifiée pour la lemmatisation latine via :
- TreeTagger (rapide, recommandé)
- CLTK (lent mais précis)
- Simple (fallback sans dépendance)
"""

from typing import List, Tuple, Optional, Union
from dataclasses import dataclass
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class LemmatizedToken:
    """Token avec annotations linguistiques"""
    word: str
    pos: str
    lemma: str
    features: Optional[str] = None  # Traits morphologiques optionnels


class TreeTaggerLemmatizer:
    """
    Lemmatiseur utilisant TreeTagger (RECOMMANDÉ)

    TreeTagger est rapide et efficace pour le latin.
    ~1 minute pour 350 pages vs ~1h+ pour CLTK.

    Prérequis:
        1. Installer TreeTagger: https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/
        2. pip install treetaggerwrapper

    Usage:
        lemmatizer = TreeTaggerLemmatizer(treetagger_path="/opt/treetagger")
        result = lemmatizer.lemmatize("Dominus enim dicit")
    """

    # Mapping des POS tags TreeTagger Latin vers tags simplifiés
    POS_MAPPING = {
        # Tags TreeTagger pour le latin
        "N": "NOM",       # Nom
        "NOM": "NOM",
        "V": "VER",       # Verbe
        "VER": "VER",
        "ADJ": "ADJ",     # Adjectif
        "ADV": "ADV",     # Adverbe
        "PRON": "PRO",    # Pronom
        "PRO": "PRO",
        "PREP": "PRP",    # Préposition
        "PRP": "PRP",
        "CONJ": "CON",    # Conjonction
        "CON": "CON",
        "NUM": "NUM",     # Numéral
        "INT": "INT",     # Interjection
        "SENT": "PUNCT",  # Ponctuation de fin
        "PON": "PUNCT",   # Ponctuation
        "PUNCT": "PUNCT",
        # Fallback
        "UNKNOWN": "UNK",
        "UNK": "UNK",
    }

    PUNCTUATION = set(".,;:!?()[]«»\"'„‟⁊-–—")

    def __init__(
        self,
        treetagger_path: Optional[str] = None,
        language: str = "latin"
    ):
        """
        Args:
            treetagger_path: Chemin vers l'installation TreeTagger
            language: Langue (latin par défaut)
        """
        self.treetagger_path = treetagger_path
        self.language = language
        self._tagger = None
        self._initialized = False

    def _initialize(self) -> None:
        """Initialise TreeTagger (lazy loading)"""
        if self._initialized:
            return

        try:
            import treetaggerwrapper

            # Détermine le chemin TreeTagger
            tagdir = self.treetagger_path

            # Chemins par défaut selon l'OS
            if not tagdir:
                import os
                import platform

                if platform.system() == "Linux":
                    possible_paths = [
                        "/opt/treetagger",
                        "/usr/local/treetagger",
                        "/usr/share/treetagger",
                        os.path.expanduser("~/treetagger"),
                    ]
                elif platform.system() == "Darwin":  # macOS
                    possible_paths = [
                        "/usr/local/treetagger",
                        "/opt/treetagger",
                        os.path.expanduser("~/treetagger"),
                    ]
                else:  # Windows
                    possible_paths = [
                        "C:\\TreeTagger",
                        "C:\\Program Files\\TreeTagger",
                    ]

                for path in possible_paths:
                    if os.path.exists(path):
                        tagdir = path
                        break

            if not tagdir:
                raise FileNotFoundError(
                    "TreeTagger non trouvé. Spécifiez le chemin avec treetagger_path "
                    "ou installez TreeTagger dans un emplacement standard."
                )

            logger.info(f"Initialisation de TreeTagger depuis {tagdir}...")

            self._tagger = treetaggerwrapper.TreeTagger(
                TAGLANG="la",  # Latin
                TAGDIR=tagdir,
            )
            self._initialized = True
            logger.info("TreeTagger initialisé avec succès")

        except ImportError:
            raise ImportError(
                "treetaggerwrapper n'est pas installé. "
                "Installez-le avec: pip install treetaggerwrapper"
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de TreeTagger: {e}")
            raise

    def lemmatize(self, text: str) -> List[LemmatizedToken]:
        """
        Lemmatise un texte

        Args:
            text: Texte à lemmatiser

        Returns:
            Liste de LemmatizedToken
        """
        self._initialize()

        if not text or not text.strip():
            return []

        try:
            # TreeTagger retourne des lignes "word\tPOS\tlemma"
            tags = self._tagger.tag_text(text)
            return self._process_tags(tags)
        except Exception as e:
            logger.error(f"Erreur de lemmatisation TreeTagger: {e}")
            return self._fallback_tokenize(text)

    def lemmatize_tokens(self, tokens: List[str]) -> List[LemmatizedToken]:
        """Lemmatise une liste de tokens"""
        text = " ".join(tokens)
        return self.lemmatize(text)

    def _process_tags(self, tags: List[str]) -> List[LemmatizedToken]:
        """
        Traite les tags TreeTagger

        Args:
            tags: Liste de lignes "word\\tPOS\\tlemma"

        Returns:
            Liste de LemmatizedToken
        """
        import treetaggerwrapper

        results = []

        for tag in tags:
            # Parse le tag
            if isinstance(tag, treetaggerwrapper.Tag):
                word = tag.word
                pos = tag.pos
                lemma = tag.lemma
            elif isinstance(tag, str) and "\t" in tag:
                parts = tag.split("\t")
                word = parts[0] if len(parts) > 0 else ""
                pos = parts[1] if len(parts) > 1 else "UNK"
                lemma = parts[2] if len(parts) > 2 else word
            else:
                continue

            # Ignore les tags vides
            if not word:
                continue

            # Gère les lemmes inconnus
            if lemma == "<unknown>" or not lemma:
                lemma = word.lower()

            # Simplifie le POS
            pos_simplified = self.POS_MAPPING.get(pos, pos)
            if pos_simplified == pos and len(pos) > 3:
                # Essaie de mapper le préfixe (ex: "VER:inf" -> "VER")
                prefix = pos.split(":")[0] if ":" in pos else pos[:3]
                pos_simplified = self.POS_MAPPING.get(prefix, "UNK")

            # Gère la ponctuation
            if self._is_punctuation(word):
                pos_simplified = "PUNCT"
                lemma = word

            results.append(LemmatizedToken(
                word=word,
                pos=pos_simplified,
                lemma=lemma.lower() if lemma else word.lower(),
            ))

        return results

    def _is_punctuation(self, token: str) -> bool:
        """Vérifie si le token est de la ponctuation"""
        return all(c in self.PUNCTUATION for c in token)

    def _fallback_tokenize(self, text: str) -> List[LemmatizedToken]:
        """Fallback si TreeTagger échoue"""
        pattern = re.compile(r'([.,;:!?\(\)\[\]«»""\'„‟⁊])')
        tokenized = pattern.sub(r' \1 ', text)
        tokens = tokenized.split()

        results = []
        for token in tokens:
            if self._is_punctuation(token):
                pos = "PUNCT"
            else:
                pos = "UNK"

            results.append(LemmatizedToken(
                word=token,
                pos=pos,
                lemma=token.lower(),
            ))

        return results

    @property
    def is_initialized(self) -> bool:
        """Retourne True si TreeTagger est initialisé"""
        return self._initialized


class CLTKLemmatizer:
    """
    Lemmatiseur utilisant CLTK (Classical Language Toolkit)

    CLTK est spécialisé pour les langues classiques (latin, grec, etc.)
    et fournit lemmatisation, POS tagging et analyse morphologique.

    Prérequis:
        pip install cltk

    Usage:
        lemmatizer = CLTKLemmatizer(language="lat")
        result = lemmatizer.lemmatize("Dominus enim dicit")
        # [LemmatizedToken(word="Dominus", pos="NOUN", lemma="dominus"), ...]
    """

    # Mapping des POS tags CLTK vers tags simplifiés
    POS_MAPPING = {
        # Tags Universal Dependencies
        "NOUN": "NOM",
        "PROPN": "NPR",
        "VERB": "VER",
        "ADJ": "ADJ",
        "ADV": "ADV",
        "PRON": "PRO",
        "DET": "DET",
        "ADP": "PRP",
        "CONJ": "CON",
        "CCONJ": "CON",
        "SCONJ": "CON",
        "NUM": "NUM",
        "PART": "PAR",
        "INTJ": "INT",
        "PUNCT": "PUNCT",
        "X": "X",
        # Fallback
        "UNKNOWN": "UNK",
    }

    # Ponctuation pour annotation directe
    PUNCTUATION = set(".,;:!?()[]«»\"'„‟⁊-–—")

    def __init__(
        self,
        language: str = "lat",
        use_simplified_pos: bool = True
    ):
        """
        Args:
            language: Code langue CLTK (lat pour latin)
            use_simplified_pos: Utiliser les tags POS simplifiés
        """
        self.language = language
        self.use_simplified_pos = use_simplified_pos
        self._nlp = None
        self._initialized = False

    def _initialize(self) -> None:
        """Initialise CLTK (lazy loading)"""
        if self._initialized:
            return

        try:
            from cltk import NLP
            from cltk.data.fetch import FetchCorpus

            # Télécharge les modèles si nécessaire
            logger.info(f"Initialisation de CLTK pour '{self.language}'...")

            # Fetch les données nécessaires
            try:
                corpus_downloader = FetchCorpus(language=self.language)
                corpus_downloader.import_corpus(f"{self.language}_models_cltk")
            except Exception as e:
                logger.warning(f"Téléchargement des modèles (peut-être déjà présents): {e}")

            # Initialise le NLP
            self._nlp = NLP(language=self.language, suppress_banner=True)
            self._initialized = True
            logger.info("CLTK initialisé avec succès")

        except ImportError:
            raise ImportError(
                "CLTK n'est pas installé. Installez-le avec: pip install cltk"
            )
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de CLTK: {e}")
            raise

    def lemmatize(self, text: str) -> List[LemmatizedToken]:
        """
        Lemmatise un texte

        Args:
            text: Texte à lemmatiser

        Returns:
            Liste de LemmatizedToken
        """
        self._initialize()

        if not text or not text.strip():
            return []

        try:
            doc = self._nlp.analyze(text=text)
            return self._process_doc(doc)
        except Exception as e:
            logger.error(f"Erreur de lemmatisation: {e}")
            # Fallback: retourne les mots sans annotation
            return self._fallback_tokenize(text)

    def lemmatize_tokens(self, tokens: List[str]) -> List[LemmatizedToken]:
        """
        Lemmatise une liste de tokens

        Args:
            tokens: Liste de tokens

        Returns:
            Liste de LemmatizedToken
        """
        # Reconstruit le texte pour CLTK
        text = " ".join(tokens)
        return self.lemmatize(text)

    def _process_doc(self, doc) -> List[LemmatizedToken]:
        """
        Traite un document CLTK

        Args:
            doc: Document CLTK analysé

        Returns:
            Liste de LemmatizedToken
        """
        results = []

        for word in doc.words:
            # Récupère les annotations
            word_text = word.string
            pos = getattr(word, 'upos', 'X') or 'X'
            lemma = getattr(word, 'lemma', word_text) or word_text

            # Gère la ponctuation
            if self._is_punctuation(word_text):
                pos = "PUNCT"
                lemma = word_text

            # Simplifie le POS si demandé
            if self.use_simplified_pos:
                pos = self.POS_MAPPING.get(pos, pos)

            # Nettoie le lemme
            lemma = self._clean_lemma(lemma, word_text)

            results.append(LemmatizedToken(
                word=word_text,
                pos=pos,
                lemma=lemma,
            ))

        return results

    def _is_punctuation(self, token: str) -> bool:
        """Vérifie si le token est de la ponctuation"""
        return all(c in self.PUNCTUATION for c in token)

    def _clean_lemma(self, lemma: str, word: str) -> str:
        """
        Nettoie le lemme

        Args:
            lemma: Lemme brut
            word: Mot original

        Returns:
            Lemme nettoyé
        """
        if not lemma or lemma == "None":
            return word.lower()

        # Retire les suffixes numériques (ex: "sum1" -> "sum")
        lemma = re.sub(r'\d+$', '', lemma)

        # Met en minuscules
        lemma = lemma.lower()

        return lemma if lemma else word.lower()

    def _fallback_tokenize(self, text: str) -> List[LemmatizedToken]:
        """
        Fallback si CLTK échoue: tokenisation simple sans annotation

        Args:
            text: Texte à tokeniser

        Returns:
            Liste de LemmatizedToken avec POS="UNK"
        """
        # Pattern pour séparer la ponctuation
        pattern = re.compile(r'([.,;:!?\(\)\[\]«»""\'„‟⁊])')
        tokenized = pattern.sub(r' \1 ', text)
        tokens = tokenized.split()

        results = []
        for token in tokens:
            if self._is_punctuation(token):
                pos = "PUNCT"
            else:
                pos = "UNK"

            results.append(LemmatizedToken(
                word=token,
                pos=pos,
                lemma=token.lower(),
            ))

        return results

    @property
    def is_initialized(self) -> bool:
        """Retourne True si CLTK est initialisé"""
        return self._initialized


class SimpleLemmatizer:
    """
    Lemmatiseur simple sans dépendance externe

    Utilisé comme fallback si CLTK n'est pas disponible.
    Retourne le mot en minuscules comme lemme.
    """

    PUNCTUATION = set(".,;:!?()[]«»\"'„‟⁊-–—")

    def lemmatize(self, text: str) -> List[LemmatizedToken]:
        """Lemmatise un texte (version simple)"""
        pattern = re.compile(r'([.,;:!?\(\)\[\]«»""\'„‟⁊])')
        tokenized = pattern.sub(r' \1 ', text)
        tokens = tokenized.split()

        results = []
        for token in tokens:
            if all(c in self.PUNCTUATION for c in token):
                pos = "PUNCT"
            else:
                pos = "UNK"

            results.append(LemmatizedToken(
                word=token,
                pos=pos,
                lemma=token.lower(),
            ))

        return results

    def lemmatize_tokens(self, tokens: List[str]) -> List[LemmatizedToken]:
        """Lemmatise une liste de tokens"""
        return self.lemmatize(" ".join(tokens))


def create_lemmatizer(
    backend: str = "treetagger",
    language: str = "lat",
    treetagger_path: Optional[str] = None
) -> Union[TreeTaggerLemmatizer, CLTKLemmatizer, SimpleLemmatizer]:
    """
    Factory pour créer un lemmatiseur

    Args:
        backend: "treetagger" (recommandé), "cltk", ou "simple"
        language: Code langue
        treetagger_path: Chemin TreeTagger (optionnel)

    Returns:
        Instance de lemmatiseur

    Performance comparée (350 pages de latin):
        - TreeTagger: ~1 minute (RECOMMANDÉ)
        - CLTK: ~1h+ (précis mais très lent)
        - Simple: instantané (pas de lemmatisation réelle)
    """
    if backend == "treetagger":
        try:
            return TreeTaggerLemmatizer(treetagger_path=treetagger_path, language=language)
        except ImportError:
            logger.warning("TreeTagger non disponible, essai de CLTK...")
            backend = "cltk"
        except FileNotFoundError as e:
            logger.warning(f"TreeTagger: {e}")
            logger.warning("Essai de CLTK...")
            backend = "cltk"

    if backend == "cltk":
        try:
            logger.warning(
                "ATTENTION: CLTK est très lent (~1h pour 350 pages). "
                "Utilisez TreeTagger pour de meilleures performances."
            )
            return CLTKLemmatizer(language=language)
        except ImportError:
            logger.warning("CLTK non disponible, utilisation du lemmatiseur simple")
            return SimpleLemmatizer()

    # Fallback
    return SimpleLemmatizer()
