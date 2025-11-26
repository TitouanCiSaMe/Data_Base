#!/usr/bin/env python3
"""
Analyse des mots orange (non reconnus) dans les résultats de l'analyseur latin.

Ce script extrait et analyse les mots en orange (score 40-74) pour comprendre
pourquoi ils ne sont pas reconnus et proposer des améliorations.

Usage:
    python3 analyze_orange_words.py /chemin/vers/resultat.docx

Auteur: Claude
Date: 2025-11-25
"""

import sys
import re
from collections import Counter
from pathlib import Path
import docx
from docx.shared import RGBColor


def extract_orange_words(docx_path):
    """
    Extrait tous les mots en orange du document DOCX.

    Args:
        docx_path (str): Chemin vers le fichier DOCX

    Returns:
        list: Liste de tuples (mot, ligne_num)
    """
    doc = docx.Document(docx_path)
    orange_words = []

    for para_num, para in enumerate(doc.paragraphs):
        # Skip headers
        if para_num < 5:
            continue

        for run in para.runs:
            word = run.text.strip()
            if not word or len(word) < 2:
                continue

            # Vérifier si orange
            if run.font.color and run.font.color.rgb:
                rgb = run.font.color.rgb
                if rgb == RGBColor(255, 140, 0):  # Orange
                    # Nettoyer la ponctuation
                    clean_word = word.strip('.,;:!?()[]{}""\'')
                    if clean_word and len(clean_word) >= 2:
                        orange_words.append((clean_word.lower(), para_num))

    return orange_words


def analyze_patterns(words_list):
    """
    Analyse les patterns des mots non reconnus.

    Args:
        words_list (list): Liste de mots

    Returns:
        dict: Statistiques et patterns détectés
    """
    stats = {
        'total': len(words_list),
        'unique': len(set(words_list)),
        'avg_length': sum(len(w) for w in words_list) / len(words_list) if words_list else 0,
        'length_distribution': Counter(len(w) for w in words_list),
        'frequency': Counter(words_list),
        'patterns': {
            'contains_ae': sum(1 for w in words_list if 'ae' in w),
            'contains_oe': sum(1 for w in words_list if 'oe' in w),
            'contains_ph': sum(1 for w in words_list if 'ph' in w),
            'double_consonants': sum(1 for w in words_list if re.search(r'([bcdfghjklmnpqrstvwxz])\1', w)),
            'ends_with_us': sum(1 for w in words_list if w.endswith('us')),
            'ends_with_is': sum(1 for w in words_list if w.endswith('is')),
            'ends_with_um': sum(1 for w in words_list if w.endswith('um')),
            'ends_with_a': sum(1 for w in words_list if w.endswith('a')),
            'starts_with_vowel': sum(1 for w in words_list if w[0] in 'aeiou'),
            'very_short': sum(1 for w in words_list if len(w) <= 3),
            'very_long': sum(1 for w in words_list if len(w) >= 12),
            'has_numbers': sum(1 for w in words_list if any(c.isdigit() for c in w)),
            'has_uppercase': sum(1 for w in words_list if any(c.isupper() for c in w)),
        }
    }

    return stats


def categorize_words(words_list):
    """
    Catégorise les mots par type potentiel.

    Args:
        words_list (list): Liste de mots

    Returns:
        dict: Mots catégorisés
    """
    categories = {
        'possible_proper_nouns': [],  # Commence par majuscule
        'possible_abbreviations': [],  # Très courts (2-3 lettres)
        'possible_ocr_errors': [],  # Caractères suspects
        'medieval_spelling': [],  # Variantes orthographiques
        'compound_words': [],  # Mots composés ou préfixes
    }

    for word in set(words_list):
        # Noms propres potentiels (commence par majuscule dans le texte original)
        if word[0].isupper():
            categories['possible_proper_nouns'].append(word)

        # Abréviations potentielles
        if len(word) <= 3:
            categories['possible_abbreviations'].append(word)

        # Erreurs OCR potentielles (caractères rares, patterns suspects)
        if re.search(r'[0-9]|rn|cl(?!a)|li(?![a-z])', word):
            categories['possible_ocr_errors'].append(word)

        # Variantes orthographiques médiévales
        if 'ae' in word or 'oe' in word or 'ph' in word or re.search(r'([bcdfghjklmnpqrstvwxz])\1', word):
            categories['medieval_spelling'].append(word)

    return categories


def print_report(docx_path, orange_words, stats, categories):
    """
    Affiche le rapport d'analyse complet.

    Args:
        docx_path (str): Chemin du fichier analysé
        orange_words (list): Liste des mots orange
        stats (dict): Statistiques générales
        categories (dict): Mots catégorisés
    """
    print("=" * 80)
    print("ANALYSE DES MOTS ORANGE (NON RECONNUS)")
    print("=" * 80)
    print(f"\nFichier analysé : {docx_path}")
    print(f"Date : {Path(docx_path).stat().st_mtime}")

    # Statistiques générales
    print("\n" + " 📊 STATISTIQUES GÉNÉRALES ".center(80, '-'))
    print(f"  Total de mots orange : {stats['total']}")
    print(f"  Mots uniques : {stats['unique']}")
    print(f"  Longueur moyenne : {stats['avg_length']:.1f} caractères")

    # Distribution par longueur
    print("\n" + " 📏 DISTRIBUTION PAR LONGUEUR ".center(80, '-'))
    for length in sorted(stats['length_distribution'].keys())[:15]:
        count = stats['length_distribution'][length]
        percent = count * 100 / stats['total']
        bar = '█' * int(percent / 2)
        print(f"  {length:2d} caractères : {count:4d} ({percent:5.1f}%) {bar}")

    # Patterns détectés
    print("\n" + " 🔍 PATTERNS DÉTECTÉS ".center(80, '-'))
    for pattern, count in stats['patterns'].items():
        if count > 0:
            percent = count * 100 / stats['total']
            print(f"  {pattern:25s} : {count:4d} ({percent:5.1f}%)")

    # TOP 50 mots les plus fréquents
    print("\n" + " 🏆 TOP 50 MOTS LES PLUS FRÉQUENTS ".center(80, '-'))
    print(f"  {'Rang':<6} {'Fréquence':<12} {'Mot'}")
    print(f"  {'-'*6} {'-'*12} {'-'*50}")

    for rank, (word, count) in enumerate(stats['frequency'].most_common(50), 1):
        print(f"  {rank:<6d} {count:<12d} {word}")

    # Catégories
    print("\n" + " 📂 CATÉGORISATION DES MOTS ".center(80, '-'))

    for category, words in categories.items():
        if words:
            print(f"\n  {category.replace('_', ' ').title()} ({len(words)} mots) :")
            # Afficher 15 premiers exemples
            for word in sorted(words)[:15]:
                freq = stats['frequency'][word.lower()]
                print(f"    - {word} (x{freq})")
            if len(words) > 15:
                print(f"    ... et {len(words) - 15} autres")

    # Recommandations
    print("\n" + " 💡 RECOMMANDATIONS ".center(80, '-'))

    if stats['patterns']['contains_ae'] > 10:
        print("  ✓ Ajouter la normalisation ae ↔ e (variantes médiévales)")

    if stats['patterns']['contains_ph'] > 5:
        print("  ✓ Ajouter la normalisation ph ↔ f")

    if stats['patterns']['double_consonants'] > 20:
        print("  ✓ Tester les variantes avec géminées simplifiées (mm→m, nn→n)")

    if len(categories['possible_proper_nouns']) > 10:
        print("  ✓ Créer un dictionnaire de noms propres (toponymes, anthroponymes)")

    if len(categories['possible_abbreviations']) > 20:
        print("  ✓ Créer un dictionnaire d'abréviations médiévales courantes")

    if len(categories['possible_ocr_errors']) > 30:
        print("  ✓ Implémenter la correction d'erreurs OCR (rn→m, cl→d, etc.)")

    # Estimations d'impact
    print("\n" + " 📈 ESTIMATION D'IMPACT DES AMÉLIORATIONS ".center(80, '-'))

    # Variantes orthographiques
    variants_impact = (stats['patterns']['contains_ae'] +
                      stats['patterns']['contains_ph'] +
                      stats['patterns']['double_consonants'])
    variants_percent = variants_impact * 100 / stats['total']
    print(f"  Variantes orthographiques : +{variants_percent:.1f}% potentiel")

    # Noms propres
    proper_nouns_percent = len(categories['possible_proper_nouns']) * 100 / stats['total']
    print(f"  Dictionnaire noms propres : +{proper_nouns_percent:.1f}% potentiel")

    # Abréviations
    abbrev_percent = len(categories['possible_abbreviations']) * 100 / stats['total']
    print(f"  Dictionnaire abréviations : +{abbrev_percent:.1f}% potentiel")

    # Total estimé
    total_improvement = min(variants_percent + proper_nouns_percent + abbrev_percent, 13.0)
    print(f"\n  🎯 AMÉLIORATION TOTALE ESTIMÉE : +{total_improvement:.1f}% (86% → {86 + total_improvement:.0f}%)")

    print("\n" + "=" * 80)


def main():
    """Fonction principale."""
    if len(sys.argv) != 2:
        print("Usage: python3 analyze_orange_words.py <resultat.docx>")
        sys.exit(1)

    docx_path = sys.argv[1]

    if not Path(docx_path).exists():
        print(f"❌ Erreur : Fichier introuvable : {docx_path}")
        sys.exit(1)

    print("🔄 Extraction des mots orange en cours...")
    orange_words = extract_orange_words(docx_path)

    if not orange_words:
        print("✅ Aucun mot orange trouvé dans le document !")
        sys.exit(0)

    print(f"✅ {len(orange_words)} mots orange extraits")

    print("🔄 Analyse des patterns en cours...")
    words_only = [w for w, _ in orange_words]
    stats = analyze_patterns(words_only)

    print("🔄 Catégorisation des mots en cours...")
    categories = categorize_words(words_only)

    # Afficher le rapport
    print_report(docx_path, orange_words, stats, categories)


if __name__ == "__main__":
    main()
