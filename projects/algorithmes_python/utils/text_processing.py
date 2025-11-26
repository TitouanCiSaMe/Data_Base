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


def split_references(ref: str) -> List[str]:
    """
    Décompose une référence composite en références individuelles

    Gère les cas comme "C.9 q.3 c.17 vel 18 et c.21" qui devient:
    ["C.9 q.3 c.17", "C.9 q.3 c.18", "C.9 q.3 c.21"]

    Args:
        ref: Référence composite

    Returns:
        Liste de références individuelles

    Example:
        >>> split_references("C.9 q.3 c.17 vel 18 et c.21")
        ['C.9 q.3 c.17', 'C.9 q.3 c.18', 'C.9 q.3 c.21']
    """
    # Récupère la référence de base (avant "vel", "uel" ou "et")
    base = re.split(r'\b(?:vel|uel|et)\b', ref)[0].strip()
    refs = [base]

    # Recherche une alternative indiquée par "vel" ou "uel"
    m_vel = re.search(r'\b(?:vel|uel)\s*(\d+)', ref)
    if m_vel:
        alt_num = m_vel.group(1)
        alt_ref = replace_last_c_number(base, alt_num)
        refs.append(alt_ref)

    # Recherche une alternative indiquée par "et c.<nombre>"
    m_et = re.search(r'\bet\s*c\.?\s*(\d+)', ref)
    if m_et:
        alt_num2 = m_et.group(1)
        alt_ref2 = replace_last_c_number(base, alt_num2)
        refs.append(alt_ref2)

    # Supprime d'éventuels doublons
    unique_refs = []
    for r in refs:
        if r not in unique_refs:
            unique_refs.append(r)
    return unique_refs


def replace_last_c_number(ref: str, new_number: str) -> str:
    """
    Remplace le dernier segment du type "c.<nombre>" dans une référence

    Args:
        ref: Référence originale
        new_number: Nouveau numéro à utiliser

    Returns:
        Référence modifiée

    Example:
        >>> replace_last_c_number("C.9 q.3 c.17", "18")
        'C.9 q.3 c.18'
    """
    pattern = re.compile(r'(c\.?\s*\d+)(?!.*c\.?\s*\d+)')
    match = pattern.search(ref)
    if match:
        start, end = match.span()
        new_val = "c." + new_number
        new_ref = ref[:start] + new_val + ref[end:]
        return new_ref.strip()
    return ref


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


def normalize_canonical_reference(ref: str) -> str:
    """
    Normalise une référence canonique (spécifique au décret de Gratien)

    Args:
        ref: Référence à normaliser

    Returns:
        Référence normalisée

    Example:
        >>> normalize_canonical_reference("Dist. 4 c. 134")
        'd 4 c 134'
    """
    if not ref or not isinstance(ref, str):
        return ""

    # Supprime les espaces en trop et met en minuscules
    normalized = normalize_whitespace(ref.lower())

    # Standardise les abréviations courantes du décret de Gratien
    replacements = {
        'dist.': 'd',
        'distinctio': 'd',
        'causa': 'c',
        'questio': 'q',
        'canon': 'c',
        'de consecratione': 'decons',
        'decons.': 'decons',
        'de cons.': 'decons',
        'de cons': 'decons',
    }

    for old, new in replacements.items():
        normalized = normalized.replace(old, new)

    # Supprime les points
    normalized = normalized.replace('.', '')

    return normalized


def extract_reference_parts(ref: str) -> set:
    """
    Extrait les parties d'une référence canonique pour comparaison

    Args:
        ref: Référence à analyser

    Returns:
        Set des parties identifiées

    Example:
        >>> extract_reference_parts("D.4 c.134")
        {'d4', 'c134'}
    """
    if not ref:
        return set()

    normalized = normalize_canonical_reference(ref)
    parts = set()

    # Trouve les parties numériques (d4, c44, q6, etc.)
    number_parts = re.findall(r'[dqc]\s*\d+', normalized)
    # Supprime les espaces
    parts.update(p.replace(' ', '') for p in number_parts)

    # Ajoute "decons" si présent
    if 'decons' in normalized:
        parts.add('decons')

    return parts
