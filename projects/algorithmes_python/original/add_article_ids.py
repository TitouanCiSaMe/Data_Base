#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour ajouter des identifiants uniques aux articles de Libération.

Ce script :
1. Lit le fichier CSV des métadonnées d'articles
2. Ajoute une colonne ID avec des identifiants uniques (LIB_YYYY_NNN)
3. Crée un fichier de mapping entre les IDs et les articles du fichier texte
4. Génère un CSV enrichi et un fichier JSON de mapping

Usage:
    python add_article_ids.py
"""

import csv
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime


class ArticleIdentifier:
    """Classe pour gérer l'ajout d'identifiants aux articles."""

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

    def load_csv(self) -> List[Dict]:
        """Charge le fichier CSV des métadonnées."""
        print(f"📖 Lecture du fichier CSV: {self.csv_path}")

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.articles_metadata = list(reader)

        print(f"   ✓ {len(self.articles_metadata)} articles chargés")
        return self.articles_metadata

    def parse_text_file(self) -> List[Dict]:
        """Parse le fichier texte pour extraire les articles."""
        print(f"📖 Lecture du fichier texte: {self.txt_path}")

        with open(self.txt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Séparer les articles (identifiés par titre suivi de lignes vides)
        articles = []
        lines = content.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Un article commence par un titre (ligne non vide suivie d'une ligne vide)
            if line and i + 1 < len(lines) and not lines[i + 1].strip():
                title = line
                start_line = i

                # Chercher le sous-titre (ligne suivante non vide)
                subtitle = ""
                i += 2  # Passer la ligne vide
                if i < len(lines) and lines[i].strip():
                    subtitle = lines[i].strip()
                    i += 1

                # Chercher la date
                date = ""
                if i + 1 < len(lines) and not lines[i].strip() and lines[i + 1].strip():
                    i += 1  # Passer la ligne vide
                    potential_date = lines[i].strip()
                    # Vérifier si c'est une date (format YYYY-MM-DD)
                    if re.match(r'\d{4}-\d{2}-\d{2}', potential_date):
                        date = potential_date
                        i += 1

                # Le reste jusqu'au prochain titre est le contenu
                content_lines = []
                while i < len(lines):
                    # Détecter le prochain article (ligne non vide suivie d'une ligne vide)
                    if (i + 1 < len(lines) and
                        lines[i].strip() and
                        not lines[i + 1].strip() and
                        i + 2 < len(lines) and
                        lines[i + 2].strip()):
                        # Vérifier que ce n'est pas juste une ligne dans le contenu
                        # Un nouveau titre devrait avoir une structure particulière
                        break
                    content_lines.append(lines[i])
                    i += 1

                article = {
                    'title': title,
                    'subtitle': subtitle,
                    'date': date,
                    'content': '\n'.join(content_lines).strip(),
                    'start_line': start_line,
                    'end_line': i
                }
                articles.append(article)
            else:
                i += 1

        self.articles_text = articles
        print(f"   ✓ {len(articles)} articles extraits du fichier texte")
        return articles

    def normalize_text(self, text: str) -> str:
        """Normalise le texte pour la comparaison."""
        # Supprimer la ponctuation, espaces multiples, mettre en minuscules
        text = text.lower()
        # Supprimer les guillemets et apostrophes
        for char in ['«', '»', '"', '"', '"', "'", "'"]:
            text = text.replace(char, '')
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def find_article_in_text(self, csv_article: Dict) -> Dict:
        """
        Trouve l'article correspondant dans le fichier texte.

        Args:
            csv_article: Dictionnaire avec les métadonnées de l'article (Titre, Sous-titre, Date)

        Returns:
            Article du fichier texte ou None si non trouvé
        """
        csv_title_norm = self.normalize_text(csv_article['Titre'])

        best_match = None
        best_score = 0

        for txt_article in self.articles_text:
            txt_title_norm = self.normalize_text(txt_article['title'])

            # Calculer la similarité (simple: mots en commun)
            csv_words = set(csv_title_norm.split())
            txt_words = set(txt_title_norm.split())

            if csv_words and txt_words:
                common_words = csv_words & txt_words
                score = len(common_words) / max(len(csv_words), len(txt_words))

                if score > best_score:
                    best_score = score
                    best_match = txt_article

        # Seuil de similarité de 70%
        if best_score >= 0.7:
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
        # Extraire l'année de la date si disponible
        year = "XXXX"
        if date_str:
            match = re.match(r'(\d{4})-\d{2}-\d{2}', date_str)
            if match:
                year = match.group(1)

        return f"LIB_{year}_{index:03d}"

    def add_ids_to_csv(self) -> List[Dict]:
        """Ajoute les IDs aux articles du CSV."""
        print("\n🔢 Ajout des identifiants...")

        for i, article in enumerate(self.articles_metadata, start=1):
            article_id = self.generate_id(i, article.get('Date', ''))
            article['ID'] = article_id

            # Trouver l'article correspondant dans le texte
            txt_article = self.find_article_in_text(article)

            if txt_article:
                self.mapping[article_id] = {
                    'csv_title': article['Titre'],
                    'txt_title': txt_article['title'],
                    'date': article.get('Date', ''),
                    'start_line': txt_article['start_line'],
                    'end_line': txt_article['end_line'],
                    'link': article.get('Lien', ''),
                    'matched': True
                }
            else:
                self.mapping[article_id] = {
                    'csv_title': article['Titre'],
                    'txt_title': None,
                    'date': article.get('Date', ''),
                    'start_line': None,
                    'end_line': None,
                    'link': article.get('Lien', ''),
                    'matched': False
                }

        matched_count = sum(1 for v in self.mapping.values() if v['matched'])
        print(f"   ✓ {len(self.articles_metadata)} IDs générés")
        print(f"   ✓ {matched_count}/{len(self.articles_metadata)} articles associés au fichier texte")

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

        print(f"   ✓ Fichier sauvegardé")
        return output_path

    def save_mapping(self) -> Path:
        """Sauvegarde le fichier de mapping JSON."""
        output_path = self.output_dir / "articles_id_mapping.json"
        print(f"\n💾 Sauvegarde du mapping: {output_path}")

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.mapping, f, ensure_ascii=False, indent=2)

        print(f"   ✓ Fichier sauvegardé")
        return output_path

    def generate_report(self) -> str:
        """Génère un rapport sur le traitement."""
        matched = sum(1 for v in self.mapping.values() if v['matched'])
        unmatched = len(self.mapping) - matched

        report = f"""
╔══════════════════════════════════════════════════════════════╗
║           RAPPORT D'AJOUT D'IDENTIFIANTS                     ║
╚══════════════════════════════════════════════════════════════╝

📊 Statistiques:
   • Articles dans le CSV: {len(self.articles_metadata)}
   • Articles dans le texte: {len(self.articles_text)}
   • Correspondances trouvées: {matched}
   • Non-appariés: {unmatched}
   • Taux de correspondance: {matched/len(self.mapping)*100:.1f}%

📁 Fichiers générés:
   • CSV enrichi: {self.csv_path.stem}_with_ids.csv
   • Mapping JSON: articles_id_mapping.json
"""

        if unmatched > 0:
            report += f"\n⚠️  {unmatched} articles du CSV n'ont pas été trouvés dans le fichier texte.\n"
            report += "   Consultez le fichier JSON pour plus de détails.\n"

        return report

    def process(self):
        """Exécute le processus complet."""
        print("\n" + "="*70)
        print("   AJOUT D'IDENTIFIANTS AUX ARTICLES DE LIBERATION")
        print("="*70 + "\n")

        # Charger les données
        self.load_csv()
        self.parse_text_file()

        # Ajouter les IDs
        self.add_ids_to_csv()

        # Sauvegarder les résultats
        self.save_enriched_csv()
        self.save_mapping()

        # Afficher le rapport
        print(self.generate_report())

        print("✅ Traitement terminé avec succès!\n")


def main():
    """Fonction principale."""
    # Chemins des fichiers
    csv_path = "articles_metadata_liberation.csv"
    txt_path = "liberation_01012020_31122022(1).txt"

    # Créer l'identifieur et lancer le traitement
    identifier = ArticleIdentifier(csv_path, txt_path)
    identifier.process()


if __name__ == "__main__":
    main()
