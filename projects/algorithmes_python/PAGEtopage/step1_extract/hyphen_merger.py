"""
Fusion des mots coupés en fin de ligne

Gère les mots coupés par un tiret en fin de ligne dans les textes OCR/HTR.
"""

import re
from typing import List
import logging

logger = logging.getLogger(__name__)


class HyphenMerger:
    """
    Fusionne les mots coupés par un tiret en fin de ligne

    Les manuscrits et imprimés anciens coupent souvent les mots en fin de ligne
    avec un tiret. Cette classe détecte ces cas et fusionne les parties.

    Exemple:
        Input:  ["consti-", "tutio est"]
        Output: ["constitutio est"]
    """

    # Patterns de tirets de fin de ligne
    HYPHEN_PATTERNS = [
        r"-$",      # Tiret simple
        r"⸗$",      # Tiret double (manuscrit)
        r"¬$",      # Signe de coupure
        r"=$",      # Égal utilisé comme tiret
    ]

    def __init__(self, preserve_original: bool = False):
        """
        Args:
            preserve_original: Si True, garde une trace du mot original
        """
        self.preserve_original = preserve_original
        self._merged_count = 0
        self._pattern = re.compile("|".join(self.HYPHEN_PATTERNS))

    def merge_lines(self, lines: List[str]) -> List[str]:
        """
        Fusionne les mots coupés dans une liste de lignes

        Args:
            lines: Liste de lignes de texte

        Returns:
            Liste de lignes avec mots fusionnés
        """
        if not lines:
            return []

        self._merged_count = 0
        result = []
        carry_over = ""

        for i, line in enumerate(lines):
            line = line.strip()

            if not line:
                if carry_over:
                    result.append(carry_over)
                    carry_over = ""
                result.append("")
                continue

            # Si on a un report de la ligne précédente
            if carry_over:
                # Fusionne avec le premier mot de cette ligne
                line = self._merge_with_next(carry_over, line)
                carry_over = ""

            # Vérifie si cette ligne finit par un tiret
            if self._ends_with_hyphen(line):
                # Extrait la partie avant le tiret pour la reporter
                carry_over = self._remove_trailing_hyphen(line)
                self._merged_count += 1
            else:
                result.append(line)

        # Gère le dernier carry_over s'il existe
        if carry_over:
            result.append(carry_over)

        logger.debug(f"Fusionné {self._merged_count} mots coupés")
        return result

    def _ends_with_hyphen(self, line: str) -> bool:
        """Vérifie si la ligne finit par un tiret de coupure"""
        return bool(self._pattern.search(line.rstrip()))

    def _remove_trailing_hyphen(self, line: str) -> str:
        """Retire le tiret de fin de ligne"""
        return self._pattern.sub("", line.rstrip())

    def _merge_with_next(self, previous: str, current: str) -> str:
        """
        Fusionne la fin de la ligne précédente avec le début de la courante

        Args:
            previous: Fin de la ligne précédente (sans tiret)
            current: Ligne courante complète

        Returns:
            Ligne fusionnée
        """
        # Trouve le premier mot de la ligne courante
        words = current.split(None, 1)

        if not words:
            return previous

        first_word = words[0]
        rest = words[1] if len(words) > 1 else ""

        # Fusionne
        merged_word = previous + first_word

        if rest:
            return f"{merged_word} {rest}"
        return merged_word

    @property
    def merged_count(self) -> int:
        """Nombre de mots fusionnés lors du dernier appel"""
        return self._merged_count


def merge_hyphenated_words(lines: List[str]) -> List[str]:
    """
    Fonction utilitaire pour fusionner les mots coupés

    Args:
        lines: Liste de lignes de texte

    Returns:
        Liste de lignes avec mots fusionnés
    """
    merger = HyphenMerger()
    return merger.merge_lines(lines)
