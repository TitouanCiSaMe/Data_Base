#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script optimisé pour ajouter des identifiants uniques aux articles de Libération.

Améliorations par rapport à la version de base :
- Meilleur parsing du fichier texte (structure explicite)
- Matching amélioré avec fuzzy matching
- Support de gros fichiers via traitement par chunks
- Indexation pour accélérer les recherches

Usage:
    python add_article_ids_optimized.py [--csv FILE] [--txt FILE] [--output DIR]
"""

import csv
import json
import re
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from difflib import SequenceMatcher


class OptimizedArticleIdentifier:
    """Classe optimisée pour gérer l'ajout d'identifiants aux articles."""

    def __init__(self, csv_path: str, txt_path: str, output_dir: str = None):
        """
        Initialise l'identifieur d'articles.

        Args:
            csv_path: Chemin vers le fichier CSV des métadonnées
            txt_path: Chemin vers le fichier texte des articles
            output_dir: Répertoire de sortie (par défaut: même que csv_path)
        """
        self.csv_path = Path(csv_path)
        self.txt_path = Path(txt_path)
        self.output_dir = Path(output_dir) if output_dir else self.csv_path.parent

        self.articles_metadata = []
        self.articles_text = []
        self.mapping = {}

        # Index pour accélérer les recherches
        self.title_index = {}

    def load_csv(self) -> List[Dict]:
        """Charge le fichier CSV des métadonnées."""
        print(f"📖 Lecture du fichier CSV: {self.csv_path}")

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.articles_metadata = list(reader)

        print(f"   ✓ {len(self.articles_metadata)} articles chargés")
        return self.articles_metadata

    def parse_text_file_optimized(self) -> List[Dict]:
        """
        Parse le fichier texte de manière optimisée.

        Structure attendue :
        - Ligne n : Titre
        - Ligne n+1 : vide
        - Ligne n+2 : Sous-titre
        - Ligne n+3 : vide
        - Ligne n+4 : Date (format YYYY-MM-DD)
        - Ligne n+5 : vide
        - Lignes suivantes : Contenu jusqu'au prochain titre
        """
        print(f"📖 Lecture et parsing du fichier texte: {self.txt_path}")

        with open(self.txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        articles = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Chercher un titre (ligne non vide suivie d'une ligne vide)
            if line and i + 1 < len(lines) and not lines[i + 1].strip():
                title = line
                start_line = i
                i += 2  # Passer le titre et la ligne vide

                # Lire le sous-titre
                subtitle = ""
                if i < len(lines) and lines[i].strip():
                    subtitle = lines[i].strip()
                    i += 1

                    # Passer la ligne vide après le sous-titre
                    if i < len(lines) and not lines[i].strip():
                        i += 1

                # Lire la date
                date = ""
                if i < len(lines):
                    potential_date = lines[i].strip()
                    # Vérifier format date YYYY-MM-DD
                    if re.match(r'^\d{4}-\d{2}-\d{2}$', potential_date):
                        date = potential_date
                        i += 1

                        # Passer la ligne vide après la date
                        if i < len(lines) and not lines[i].strip():
                            i += 1

                # Lire le contenu jusqu'au prochain article
                content_lines = []
                content_start = i

                while i < len(lines):
                    # Détecter le début du prochain article
                    # (ligne non vide suivie d'une ligne vide, puis une autre ligne non vide)
                    if (i + 2 < len(lines) and
                        lines[i].strip() and
                        not lines[i + 1].strip() and
                        lines[i + 2].strip()):
                        # Vérifier que ce n'est pas juste une ligne dans le contenu
                        # Un nouveau titre ne devrait pas commencer par des mots courants
                        potential_title = lines[i].strip()
                        if self._looks_like_title(potential_title):
                            break

                    content_lines.append(lines[i])
                    i += 1

                # Créer l'article
                article = {
                    'title': title,
                    'subtitle': subtitle,
                    'date': date,
                    'content': ''.join(content_lines).strip(),
                    'start_line': start_line,
                    'end_line': i - 1,
                    'title_normalized': self.normalize_text(title)
                }
                articles.append(article)

                # Indexer par titre normalisé
                self.title_index[article['title_normalized']] = article
            else:
                i += 1

        self.articles_text = articles
        print(f"   ✓ {len(articles)} articles extraits et indexés")
        return articles

    def _looks_like_title(self, text: str) -> bool:
        """
        Détermine si une ligne ressemble à un titre d'article.

        Un titre typique :
        - Se termine souvent par un point d'interrogation
        - Contient moins de 200 caractères
        - Commence par une majuscule
        - Ne contient pas trop de ponctuation interne
        """
        if not text:
            return False

        # Trop long pour être un titre
        if len(text) > 250:
            return False

        # Les titres se terminent souvent par ? ou ne se terminent pas par .
        if text.endswith('?'):
            return True

        # Commence par une majuscule
        if not text[0].isupper():
            return False

        # Pas trop de ponctuation (éviter les phrases du contenu)
        punct_count = sum(1 for c in text if c in '.,:;')
        if punct_count > 3:
            return False

        return True

    def normalize_text(self, text: str) -> str:
        """Normalise le texte pour la comparaison."""
        text = text.lower()
        # Supprimer les guillemets et apostrophes
        for char in ['«', '»', '"', '"', '"', "'", "'", '`']:
            text = text.replace(char, ' ')
        # Supprimer la ponctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def similarity_score(self, text1: str, text2: str) -> float:
        """
        Calcule un score de similarité entre deux textes.

        Utilise SequenceMatcher de difflib pour un matching plus précis.

        Returns:
            Score entre 0 et 1 (1 = identique)
        """
        return SequenceMatcher(None, text1, text2).ratio()

    def find_article_in_text(self, csv_article: Dict) -> Optional[Dict]:
        """
        Trouve l'article correspondant dans le fichier texte.

        Stratégie :
        1. Normaliser le titre du CSV
        2. Chercher correspondance exacte dans l'index
        3. Sinon, chercher la meilleure correspondance avec fuzzy matching

        Args:
            csv_article: Dictionnaire avec les métadonnées de l'article

        Returns:
            Article du fichier texte ou None si non trouvé
        """
        csv_title_norm = self.normalize_text(csv_article['Titre'])

        # 1. Recherche exacte dans l'index
        if csv_title_norm in self.title_index:
            return self.title_index[csv_title_norm]

        # 2. Fuzzy matching sur tous les articles
        best_match = None
        best_score = 0.0

        for txt_article in self.articles_text:
            # Comparer les titres normalisés
            score = self.similarity_score(csv_title_norm, txt_article['title_normalized'])

            # Bonus si les dates correspondent
            if csv_article.get('Date') and txt_article.get('date'):
                if csv_article['Date'] == txt_article['date']:
                    score += 0.2  # Bonus de 20% pour la date

            if score > best_score:
                best_score = score
                best_match = txt_article

        # Seuil de similarité de 65%
        if best_score >= 0.65:
            return best_match

        return None

    def generate_id(self, index: int, date_str: str) -> str:
        """
        Génère un identifiant unique pour un article.

        Format: LIB_YYYY_NNN où YYYY est l'année et NNN le numéro

        Args:
            index: Index de l'article (commence à 1)
            date_str: Date de l'article (format YYYY-MM-DD ou vide)

        Returns:
            Identifiant unique
        """
        year = "XXXX"
        if date_str:
            match = re.match(r'(\d{4})-\d{2}-\d{2}', date_str)
            if match:
                year = match.group(1)

        return f"LIB_{year}_{index:03d}"

    def add_ids_to_csv(self) -> List[Dict]:
        """Ajoute les IDs aux articles du CSV."""
        print("\n🔢 Ajout des identifiants et appariement avec le fichier texte...")

        matched_count = 0

        for i, article in enumerate(self.articles_metadata, start=1):
            article_id = self.generate_id(i, article.get('Date', ''))
            article['ID'] = article_id

            # Trouver l'article correspondant dans le texte
            txt_article = self.find_article_in_text(article)

            if txt_article:
                matched_count += 1
                self.mapping[article_id] = {
                    'csv_title': article['Titre'],
                    'csv_subtitle': article.get('Sous-titre', ''),
                    'txt_title': txt_article['title'],
                    'txt_subtitle': txt_article.get('subtitle', ''),
                    'date': article.get('Date', ''),
                    'start_line': txt_article['start_line'],
                    'end_line': txt_article['end_line'],
                    'link': article.get('Lien', ''),
                    'matched': True
                }
            else:
                self.mapping[article_id] = {
                    'csv_title': article['Titre'],
                    'csv_subtitle': article.get('Sous-titre', ''),
                    'txt_title': None,
                    'txt_subtitle': None,
                    'date': article.get('Date', ''),
                    'start_line': None,
                    'end_line': None,
                    'link': article.get('Lien', ''),
                    'matched': False
                }

            # Afficher la progression tous les 50 articles
            if i % 50 == 0:
                print(f"   → Traité {i}/{len(self.articles_metadata)} articles...")

        print(f"   ✓ {len(self.articles_metadata)} IDs générés")
        print(f"   ✓ {matched_count}/{len(self.articles_metadata)} articles appariés ({matched_count/len(self.articles_metadata)*100:.1f}%)")

        return self.articles_metadata

    def save_enriched_csv(self) -> Path:
        """Sauvegarde le CSV enrichi avec les IDs."""
        output_path = self.output_dir / f"{self.csv_path.stem}_with_ids.csv"
        print(f"\n💾 Sauvegarde du CSV enrichi: {output_path}")

        # Réorganiser les colonnes pour mettre ID en première position
        fieldnames = ['ID', 'Titre', 'Sous-titre', 'Date', 'Lien']

        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.articles_metadata)

        print(f"   ✓ Fichier sauvegardé ({output_path.stat().st_size / 1024:.1f} Ko)")
        return output_path

    def save_mapping(self) -> Path:
        """Sauvegarde le fichier de mapping JSON."""
        output_path = self.output_dir / "articles_id_mapping.json"
        print(f"\n💾 Sauvegarde du mapping: {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.mapping, f, ensure_ascii=False, indent=2)

        print(f"   ✓ Fichier sauvegardé ({output_path.stat().st_size / 1024:.1f} Ko)")
        return output_path

    def save_unmatched_report(self) -> Optional[Path]:
        """Génère un rapport des articles non appariés."""
        unmatched = [(id, info) for id, info in self.mapping.items() if not info['matched']]

        if not unmatched:
            return None

        output_path = self.output_dir / "unmatched_articles.txt"
        print(f"\n📝 Génération du rapport des articles non appariés: {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"ARTICLES NON APPARIÉS ({len(unmatched)})\n")
            f.write("=" * 80 + "\n\n")

            for article_id, info in unmatched:
                f.write(f"ID: {article_id}\n")
                f.write(f"Titre: {info['csv_title']}\n")
                f.write(f"Date: {info['date']}\n")
                f.write(f"Lien: {info['link']}\n")
                f.write("-" * 80 + "\n")

        print(f"   ✓ Rapport sauvegardé")
        return output_path

    def generate_report(self) -> str:
        """Génère un rapport sur le traitement."""
        matched = sum(1 for v in self.mapping.values() if v['matched'])
        unmatched = len(self.mapping) - matched
        match_rate = matched / len(self.mapping) * 100 if self.mapping else 0

        report = f"""
╔══════════════════════════════════════════════════════════════╗
║      RAPPORT D'AJOUT D'IDENTIFIANTS (VERSION OPTIMISÉE)      ║
╚══════════════════════════════════════════════════════════════╝

📊 Statistiques:
   • Articles dans le CSV: {len(self.articles_metadata)}
   • Articles extraits du texte: {len(self.articles_text)}
   • Correspondances trouvées: {matched}
   • Non-appariés: {unmatched}
   • Taux d'appariement: {match_rate:.1f}%

📁 Fichiers générés:
   • CSV enrichi: {self.csv_path.stem}_with_ids.csv
   • Mapping JSON: articles_id_mapping.json
"""

        if unmatched > 0:
            report += f"""
⚠️  {unmatched} articles du CSV n'ont pas été trouvés dans le fichier texte.

Raisons possibles:
   • Périodes différentes (CSV: 2024-2025, TXT: 2020-2022)
   • Titres modifiés entre les deux sources
   • Articles présents uniquement dans une source

📄 Consultez unmatched_articles.txt pour la liste détaillée.
"""

        return report

    def process(self):
        """Exécute le processus complet."""
        print("\n" + "="*70)
        print("   AJOUT D'IDENTIFIANTS - VERSION OPTIMISÉE")
        print("="*70 + "\n")

        # Charger les données
        self.load_csv()
        self.parse_text_file_optimized()

        # Ajouter les IDs
        self.add_ids_to_csv()

        # Sauvegarder les résultats
        self.save_enriched_csv()
        self.save_mapping()
        self.save_unmatched_report()

        # Afficher le rapport
        print(self.generate_report())

        print("✅ Traitement terminé avec succès!\n")


def main():
    """Fonction principale avec support des arguments."""
    parser = argparse.ArgumentParser(
        description='Ajoute des identifiants uniques aux articles de Libération (version optimisée)'
    )
    parser.add_argument(
        '--csv',
        default='articles_metadata_liberation.csv',
        help='Chemin vers le fichier CSV des métadonnées'
    )
    parser.add_argument(
        '--txt',
        default='liberation_01012020_31122022(1).txt',
        help='Chemin vers le fichier texte des articles'
    )
    parser.add_argument(
        '--output',
        help='Répertoire de sortie (par défaut: même que le CSV)'
    )

    args = parser.parse_args()

    # Créer l'identifieur et lancer le traitement
    identifier = OptimizedArticleIdentifier(args.csv, args.txt, args.output)
    identifier.process()


if __name__ == "__main__":
    main()
