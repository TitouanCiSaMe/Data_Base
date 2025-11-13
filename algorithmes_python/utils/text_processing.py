"""
Utilitaires pour le traitement de texte

Fonctions réutilisables pour extraction, normalisation et manipulation de texte.
"""

import re
from typing import Any, Iterator, List


def extract_ids_recursive(json_obj: Any, target_key: str) -> Iterator[Any]:
    """
    Extrait récursivement toutes les valeurs d'une clé spécifique dans une structure JSON

    Args:
        json_obj: Objet JSON (dict ou list)
        target_key: Clé à rechercher

    Yields:
        Valeurs trouvées pour la clé cible

    Example:
        >>> data = {"items": [{"@id": "1", "nested": {"@id": "2"}}]}
        >>> list(extract_ids_recursive(data, "@id"))
        ['1', '2']
    """
    if isinstance(json_obj, dict):
        for k, v in json_obj.items():
            if k == target_key:
                yield v
            else:
                yield from extract_ids_recursive(v, target_key)
    elif isinstance(json_obj, list):
        for item in json_obj:
            yield from extract_ids_recursive(item, target_key)


def normalize_whitespace(text: str) -> str:
    """
    Normalise les espaces dans un texte

    Args:
        text: Texte à normaliser

    Returns:
        Texte avec espaces normalisés

    Example:
        >>> normalize_whitespace("hello    world  \\n  test")
        'hello world test'
    """
    return re.sub(r'\s+', ' ', text.strip())


def remove_punctuation(text: str, keep: str = '') -> str:
    """
    Supprime la ponctuation d'un texte

    Args:
        text: Texte à traiter
        keep: Caractères de ponctuation à conserver

    Returns:
        Texte sans ponctuation

    Example:
        >>> remove_punctuation("hello, world!", keep=',')
        'hello, world'
    """
    import string
    punctuation = ''.join(c for c in string.punctuation if c not in keep)
    return text.translate(str.maketrans('', '', punctuation))


def extract_numbers(text: str) -> List[int]:
    """
    Extrait tous les nombres d'un texte

    Args:
        text: Texte source

    Returns:
        Liste des nombres trouvés

    Example:
        >>> extract_numbers("C.15 q.6 c.2")
        [15, 6, 2]
    """
    return [int(n) for n in re.findall(r'\d+', text)]


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Tronque un texte à une longueur maximale

    Args:
        text: Texte à tronquer
        max_length: Longueur maximale
        suffix: Suffixe à ajouter si tronqué

    Returns:
        Texte tronqué

    Example:
        >>> truncate_text("Hello world this is a long text", 15)
        'Hello world...'
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calcule la distance de Levenshtein entre deux chaînes

    Args:
        s1: Première chaîne
        s2: Deuxième chaîne

    Returns:
        Distance de Levenshtein

    Example:
        >>> levenshtein_distance("kitten", "sitting")
        3
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # coût d'insertion, suppression ou substitution
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]
