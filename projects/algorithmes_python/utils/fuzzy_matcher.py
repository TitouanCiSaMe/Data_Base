"""
Fuzzy matching optimisé avec cache et indexation

Système de matching haute performance pour les références textuelles.
"""

import re
import pandas as pd
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Optional, Tuple, Dict, Set, List
import logging

from .text_processing import (
    normalize_canonical_reference,
    extract_reference_parts,
    split_references
)


# Regex pré-compilées pour meilleures performances
GRATIEN_PATTERNS = [
    re.compile(r'[dD]\.?\s*\d+\s*c\.?\s*\d+'),  # D.4 c.134
    re.compile(r'[cC]\.?\s*\d+\s*q\.?\s*\d+\s*c\.?\s*\d+'),  # C.15 q.6 c.2
    re.compile(r'de\s*cons', re.IGNORECASE),  # de consecratione
]


class FuzzyMatcher:
    """
    Matcher fuzzy optimisé avec cache et index

    Optimisations:
    - Cache LRU pour normalisation et similarité
    - Index inversé pour recherche rapide
    - Regex pré-compilées
    - Pré-calcul des références normalisées
    """

    def __init__(self,
                 data_source: pd.DataFrame,
                 reference_column: str = 'Allegations',
                 alias_column: Optional[str] = 'Alias_Allegations_20e',
                 id_column: str = 'Identifiant',
                 cache_size: int = 1024):
        """
        Args:
            data_source: DataFrame contenant les références
            reference_column: Nom de la colonne des références
            alias_column: Nom de la colonne des alias (optionnel)
            id_column: Nom de la colonne des identifiants
            cache_size: Taille du cache LRU
        """
        self.df = data_source
        self.reference_column = reference_column
        self.alias_column = alias_column
        self.id_column = id_column
        self.logger = logging.getLogger(self.__class__.__name__)

        # Configuration du cache
        self._normalize_cached = lru_cache(maxsize=cache_size)(self._normalize_uncached)
        self._similarity_cached = lru_cache(maxsize=cache_size)(self._similarity_uncached)

        # Pré-calcul des références normalisées
        self._precompute_normalized_references()

        # Construction de l'index
        self._build_index()

        self.logger.info(
            f"FuzzyMatcher initialisé avec {len(self.df)} références "
            f"(cache size: {cache_size})"
        )

    def _precompute_normalized_references(self):
        """Pré-calcule toutes les références normalisées"""
        self.logger.debug("Pré-calcul des références normalisées...")

        # Colonne de référence principale
        self.df['_normalized_ref'] = self.df[self.reference_column].apply(
            lambda x: self._normalize_cached(x) if pd.notna(x) else ""
        )

        # Colonne d'alias si disponible
        if self.alias_column and self.alias_column in self.df.columns:
            self.df['_normalized_alias'] = self.df[self.alias_column].apply(
                lambda x: self._normalize_cached(x) if pd.notna(x) else ""
            )

        # Extraction des parties pour recherche rapide
        self.df['_ref_parts'] = self.df['_normalized_ref'].apply(
            lambda x: extract_reference_parts(x) if x else set()
        )

    def _build_index(self):
        """Construit un index inversé pour recherche rapide"""
        self.logger.debug("Construction de l'index inversé...")

        self.index: Dict[str, List[int]] = {}

        for idx, row in self.df.iterrows():
            parts = row['_ref_parts']
            for part in parts:
                if part not in self.index:
                    self.index[part] = []
                self.index[part].append(idx)

        self.logger.debug(f"Index construit avec {len(self.index)} entrées")

    def _normalize_uncached(self, ref: str) -> str:
        """Version non cachée de la normalisation"""
        return normalize_canonical_reference(ref)

    def _similarity_uncached(self, ref1: str, ref2: str) -> float:
        """Version non cachée du calcul de similarité"""
        if not ref1 or not ref2:
            return 0.0

        # Similarité textuelle
        text_score = SequenceMatcher(None, ref1, ref2).ratio()

        # Similarité basée sur les parties
        parts1 = extract_reference_parts(ref1)
        parts2 = extract_reference_parts(ref2)

        if not parts1 or not parts2:
            return text_score

        common_parts = parts1.intersection(parts2)
        all_parts = parts1.union(parts2)
        parts_score = len(common_parts) / len(all_parts) if all_parts else 0

        # Score combiné (privilégie les parties communes)
        return max(text_score, parts_score * 0.9)

    def normalize_reference(self, ref: str) -> str:
        """
        Normalise une référence (version cachée)

        Args:
            ref: Référence à normaliser

        Returns:
            Référence normalisée
        """
        return self._normalize_cached(ref)

    def similarity_score(self, ref1: str, ref2: str) -> float:
        """
        Calcule le score de similarité (version cachée)

        Args:
            ref1: Première référence
            ref2: Deuxième référence

        Returns:
            Score de similarité (0.0 à 1.0)
        """
        norm1 = self._normalize_cached(ref1)
        norm2 = self._normalize_cached(ref2)

        # Utilisation d'un tuple pour le cache
        return self._similarity_cached(norm1, norm2)

    def is_gratien_reference(self, ref: str) -> bool:
        """
        Vérifie si une référence correspond au décret de Gratien

        Args:
            ref: Référence à vérifier

        Returns:
            True si c'est une référence Gratien
        """
        if not ref:
            return False

        for pattern in GRATIEN_PATTERNS:
            if pattern.search(ref):
                return True
        return False

    def find_candidates(self, query_ref: str, max_candidates: int = 50) -> List[int]:
        """
        Trouve les candidats potentiels en utilisant l'index

        Args:
            query_ref: Référence à rechercher
            max_candidates: Nombre maximum de candidats

        Returns:
            Liste des indices de candidats
        """
        query_parts = extract_reference_parts(query_ref)

        if not query_parts:
            # Pas de parties identifiées -> recherche exhaustive
            return list(range(len(self.df)))

        # Trouve les lignes qui partagent au moins une partie
        candidates = set()
        for part in query_parts:
            if part in self.index:
                candidates.update(self.index[part])

        # Limite le nombre de candidats
        return list(candidates)[:max_candidates]

    def find_best_match(self,
                        xml_ref: str,
                        threshold: float = 0.7,
                        use_candidates: bool = True) -> Tuple[Optional[pd.Series], float]:
        """
        Trouve la meilleure correspondance pour une référence

        Args:
            xml_ref: Référence à matcher
            threshold: Seuil de similarité minimum
            use_candidates: Si True, utilise l'index pour filtrer les candidats

        Returns:
            Tuple (meilleure correspondance, score) ou (None, 0)
        """
        best_match = None
        best_score = 0

        # Vérification : si " d." ou " a." dans la référence, utilise uniquement l'alias
        force_alias = " d." in xml_ref or " a." in xml_ref

        if force_alias and self.alias_column:
            # Recherche uniquement dans les alias
            for idx, row in self.df.iterrows():
                if pd.notna(row.get(self.alias_column)):
                    score = self.similarity_score(xml_ref, row[self.alias_column])
                    if score > best_score and score >= threshold:
                        best_score = score
                        best_match = row
            return best_match, best_score

        # Recherche normale : d'abord dans les candidats
        if use_candidates:
            candidate_indices = self.find_candidates(xml_ref)
        else:
            candidate_indices = list(range(len(self.df)))

        # Recherche dans les références principales
        for idx in candidate_indices:
            row = self.df.iloc[idx]

            # Test sur la référence principale
            score = self.similarity_score(xml_ref, row[self.reference_column])
            if score > best_score and score >= threshold:
                best_score = score
                best_match = row

            # Test sur l'alias si disponible
            if self.alias_column and pd.notna(row.get(self.alias_column)):
                score = self.similarity_score(xml_ref, row[self.alias_column])
                if score > best_score and score >= threshold:
                    best_score = score
                    best_match = row

        return best_match, best_score

    def match_reference(self,
                        ref: str,
                        threshold: float = 0.7) -> List[Tuple[str, float]]:
        """
        Matche une référence (peut être composite) et retourne tous les IDs trouvés

        Args:
            ref: Référence (peut être composite)
            threshold: Seuil de similarité

        Returns:
            Liste de tuples (id, score)
        """
        # Découpage des références composites
        ref_list = split_references(ref)
        results = []

        for single_ref in ref_list:
            if self.is_gratien_reference(single_ref):
                match, score = self.find_best_match(single_ref, threshold)
                if match is not None:
                    results.append((str(match[self.id_column]), score))

        return results

    def get_cache_info(self) -> dict:
        """
        Retourne les statistiques du cache

        Returns:
            Dict avec statistiques
        """
        return {
            'normalize_cache': self._normalize_cached.cache_info()._asdict(),
            'similarity_cache': self._similarity_cached.cache_info()._asdict(),
        }

    def clear_cache(self):
        """Vide le cache"""
        self._normalize_cached.cache_clear()
        self._similarity_cached.cache_clear()


def normalize_reference(ref: str) -> str:
    """
    Fonction standalone de normalisation

    Args:
        ref: Référence à normaliser

    Returns:
        Référence normalisée
    """
    return normalize_canonical_reference(ref)


def similarity_score(ref1: str, ref2: str) -> float:
    """
    Fonction standalone de calcul de similarité

    Args:
        ref1: Première référence
        ref2: Deuxième référence

    Returns:
        Score de similarité (0.0 à 1.0)
    """
    norm1 = normalize_reference(ref1)
    norm2 = normalize_reference(ref2)

    if not norm1 or not norm2:
        return 0.0

    # Similarité textuelle
    text_score = SequenceMatcher(None, norm1, norm2).ratio()

    # Similarité basée sur les parties
    parts1 = extract_reference_parts(ref1)
    parts2 = extract_reference_parts(ref2)

    if not parts1 or not parts2:
        return text_score

    common_parts = parts1.intersection(parts2)
    all_parts = parts1.union(parts2)
    parts_score = len(common_parts) / len(all_parts) if all_parts else 0

    return max(text_score, parts_score * 0.9)
