#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour annoter un corpus d'articles avec métadonnées pour SketchEngine.

Ce script :
1. Lit le CSV de métadonnées et le fichier texte
2. Associe les articles UNIQUEMENT par titre (fuzzy matching)
3. Génère un fichier annoté au format SketchEngine avec toutes les métadonnées
4. Format : <doc id="..." title="..." date="..." ...>contenu</doc>

Usage:
    python annotate_corpus_for_sketchengine.py [--csv FILE] [--txt FILE] [--output FILE]
"""

import csv
import re
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from difflib import SequenceMatcher
from datetime import datetime


class CorpusAnnotator:
    """Classe pour annoter un corpus avec métadonnées pour SketchEngine."""

    def __init__(self, csv_path: str, txt_path: str, output_path: str = None):
        """
        Initialise l'annotateur de corpus.

        Args:
            csv_path: Chemin vers le fichier CSV des métadonnées
            txt_path: Chemin vers le fichier texte des articles
            output_path: Chemin du fichier annoté (par défaut: corpus_annotated.txt)
        """
        self.csv_path = Path(csv_path)
        self.txt_path = Path(txt_path)

        if output_path:
            self.output_path = Path(output_path)
        else:
            self.output_path = self.txt_path.parent / f"{self.txt_path.stem}_annotated.txt"

        self.articles_metadata = []
        self.articles_text = []
        self.matched_count = 0
        self.unmatched_articles = []

    def load_csv(self) -> List[Dict]:
        """Charge le fichier CSV des métadonnées."""
        print(f"📖 Lecture du fichier CSV: {self.csv_path}")

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.articles_metadata = list(reader)

        print(f"   ✓ {len(self.articles_metadata)} articles avec métadonnées chargés")
        return self.articles_metadata

    def parse_text_file(self) -> List[Dict]:
        """
        Parse le fichier texte pour extraire les articles.

        Structure attendue :
        - Ligne n : Titre
        - Ligne n+1 : vide
        - Ligne n+2 : Sous-titre
        - Ligne n+3 : vide
        - Ligne n+4 : Date (YYYY-MM-DD)
        - Ligne n+5 : vide
        - Lignes suivantes : Contenu
        """
        print(f"📖 Lecture du fichier texte: {self.txt_path}")

        with open(self.txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        articles = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Détecter un titre (ligne non vide suivie d'une ligne vide)
            if line and i + 1 < len(lines) and not lines[i + 1].strip():
                title = line
                start_line = i
                i += 2  # Passer le titre et la ligne vide

                # Lire le sous-titre
                subtitle = ""
                if i < len(lines) and lines[i].strip():
                    subtitle = lines[i].strip()
                    i += 1
                    if i < len(lines) and not lines[i].strip():
                        i += 1

                # Lire la date
                date = ""
                if i < len(lines):
                    potential_date = lines[i].strip()
                    if re.match(r'^\d{4}-\d{2}-\d{2}$', potential_date):
                        date = potential_date
                        i += 1
                        if i < len(lines) and not lines[i].strip():
                            i += 1

                # Lire le contenu jusqu'au prochain article
                content_lines = []
                while i < len(lines):
                    # Détecter le prochain article
                    if (i + 2 < len(lines) and
                        lines[i].strip() and
                        not lines[i + 1].strip() and
                        lines[i + 2].strip() and
                        self._looks_like_title(lines[i].strip())):
                        break
                    content_lines.append(lines[i])
                    i += 1

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
            else:
                i += 1

        self.articles_text = articles
        print(f"   ✓ {len(articles)} articles extraits du fichier texte")
        return articles

    def _looks_like_title(self, text: str) -> bool:
        """Détermine si une ligne ressemble à un titre."""
        if not text or len(text) > 250:
            return False
        if text.endswith('?'):
            return True
        if not text[0].isupper():
            return False
        punct_count = sum(1 for c in text if c in '.,:;')
        return punct_count <= 3

    def normalize_text(self, text: str) -> str:
        """Normalise le texte pour la comparaison des titres."""
        text = text.lower()
        # Supprimer les guillemets et apostrophes
        for char in ['«', '»', '"', '"', '"', "'", "'", '`', '…']:
            text = text.replace(char, ' ')
        # Supprimer la ponctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def similarity_score(self, text1: str, text2: str) -> float:
        """
        Calcule un score de similarité entre deux titres.

        Returns:
            Score entre 0 et 1
        """
        return SequenceMatcher(None, text1, text2).ratio()

    def find_best_match(self, csv_title: str) -> Optional[Dict]:
        """
        Trouve le meilleur article du texte correspondant au titre du CSV.

        Args:
            csv_title: Titre de l'article dans le CSV

        Returns:
            Article du fichier texte ou None
        """
        csv_title_norm = self.normalize_text(csv_title)

        best_match = None
        best_score = 0.0

        for txt_article in self.articles_text:
            score = self.similarity_score(csv_title_norm, txt_article['title_normalized'])

            if score > best_score:
                best_score = score
                best_match = txt_article

        # Seuil de 70% pour considérer un match
        if best_score >= 0.70:
            return best_match

        return None

    def generate_id(self, index: int, date_str: str = "") -> str:
        """
        Génère un identifiant unique.

        Format: LIB_YYYY_NNN

        Args:
            index: Numéro séquentiel
            date_str: Date au format YYYY-MM-DD

        Returns:
            ID unique
        """
        year = "XXXX"
        if date_str:
            match = re.match(r'(\d{4})-\d{2}-\d{2}', date_str)
            if match:
                year = match.group(1)

        return f"LIB_{year}_{index:03d}"

    def escape_xml(self, text: str) -> str:
        """Échappe les caractères spéciaux XML."""
        if not text:
            return ""
        text = str(text)
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')
        return text

    def create_doc_tag(self, article_id: str, metadata: Dict, txt_article: Dict = None) -> str:
        """
        Crée la balise d'ouverture <doc> avec tous les attributs.

        Args:
            article_id: ID de l'article (ex: LIB_2020_001)
            metadata: Dictionnaire des métadonnées du CSV
            txt_article: Article du fichier texte (optionnel)

        Returns:
            Balise <doc ...> avec tous les attributs
        """
        attributes = [f'id="{article_id}"']

        # Ajouter toutes les métadonnées du CSV
        if metadata.get('Titre'):
            attributes.append(f'title="{self.escape_xml(metadata["Titre"])}"')

        if metadata.get('Sous-titre'):
            attributes.append(f'subtitle="{self.escape_xml(metadata["Sous-titre"])}"')

        if metadata.get('Date'):
            attributes.append(f'date="{self.escape_xml(metadata["Date"])}"')
            # Ajouter aussi année, mois, jour séparément pour faciliter les requêtes
            date_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', metadata['Date'])
            if date_match:
                attributes.append(f'year="{date_match.group(1)}"')
                attributes.append(f'month="{date_match.group(2)}"')
                attributes.append(f'day="{date_match.group(3)}"')

        if metadata.get('Lien'):
            attributes.append(f'url="{self.escape_xml(metadata["Lien"])}"')

        # Ajouter des métadonnées supplémentaires si disponibles
        # (pour l'extensibilité future)
        for key in metadata:
            if key not in ['Titre', 'Sous-titre', 'Date', 'Lien']:
                safe_key = key.lower().replace(' ', '_').replace('-', '_')
                attributes.append(f'{safe_key}="{self.escape_xml(metadata[key])}"')

        # Informations de matching
        if txt_article:
            attributes.append('matched="true"')
            attributes.append(f'source_start_line="{txt_article["start_line"]}"')
            attributes.append(f'source_end_line="{txt_article["end_line"]}"')
        else:
            attributes.append('matched="false"')

        return '<doc ' + ' '.join(attributes) + '>'

    def annotate_corpus(self) -> str:
        """
        Crée le corpus annoté avec toutes les métadonnées.

        Returns:
            Chemin du fichier annoté
        """
        print(f"\n🔖 Annotation du corpus...")

        annotated_content = []

        # En-tête du corpus
        annotated_content.append('<?xml version="1.0" encoding="UTF-8"?>')
        annotated_content.append('<corpus name="Liberation" '
                                'source="Libération" '
                                f'created="{datetime.now().strftime("%Y-%m-%d")}">')
        annotated_content.append('')

        # Traiter chaque article du CSV
        for i, csv_article in enumerate(self.articles_metadata, start=1):
            # Générer l'ID
            article_id = self.generate_id(i, csv_article.get('Date', ''))

            # Trouver l'article correspondant dans le texte
            txt_article = self.find_best_match(csv_article['Titre'])

            if txt_article:
                self.matched_count += 1
                # Balise d'ouverture avec métadonnées
                doc_tag = self.create_doc_tag(article_id, csv_article, txt_article)
                annotated_content.append(doc_tag)

                # Contenu de l'article
                annotated_content.append(txt_article['content'])

                # Balise de fermeture
                annotated_content.append('</doc>')
                annotated_content.append('')
            else:
                # Article non trouvé dans le texte, mais on garde les métadonnées
                self.unmatched_articles.append({
                    'id': article_id,
                    'title': csv_article['Titre'],
                    'date': csv_article.get('Date', '')
                })

                # On peut choisir de l'inclure quand même avec un contenu vide
                doc_tag = self.create_doc_tag(article_id, csv_article, None)
                annotated_content.append(doc_tag)
                annotated_content.append(f'<!-- Article non trouvé dans le fichier texte -->')
                annotated_content.append('</doc>')
                annotated_content.append('')

            # Afficher la progression
            if i % 50 == 0:
                print(f"   → Traité {i}/{len(self.articles_metadata)} articles...")

        # Fermeture du corpus
        annotated_content.append('</corpus>')

        # Sauvegarder le fichier annoté
        print(f"\n💾 Sauvegarde du corpus annoté: {self.output_path}")

        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(annotated_content))

        file_size = self.output_path.stat().st_size / 1024 / 1024  # En Mo
        print(f"   ✓ Fichier sauvegardé ({file_size:.2f} Mo)")

        return str(self.output_path)

    def save_report(self):
        """Génère un rapport de l'annotation."""
        report_path = self.output_path.parent / f"{self.output_path.stem}_report.txt"

        total = len(self.articles_metadata)
        match_rate = (self.matched_count / total * 100) if total > 0 else 0

        report = f"""
╔══════════════════════════════════════════════════════════════╗
║           RAPPORT D'ANNOTATION DU CORPUS                      ║
╚══════════════════════════════════════════════════════════════╝

📊 Statistiques:
   • Total d'articles dans le CSV: {total}
   • Articles extraits du fichier texte: {len(self.articles_text)}
   • Articles appariés: {self.matched_count}
   • Articles non appariés: {len(self.unmatched_articles)}
   • Taux d'appariement: {match_rate:.1f}%

📁 Fichiers générés:
   • Corpus annoté: {self.output_path.name}
   • Taille: {self.output_path.stat().st_size / 1024 / 1024:.2f} Mo

📝 Format SketchEngine:
   • Chaque article est dans une balise <doc>
   • Tous les attributs du CSV sont inclus dans les balises
   • Attributs disponibles: id, title, subtitle, date, year, month, day, url, matched

🔍 Utilisation dans SketchEngine:
   1. Uploadez le fichier {self.output_path.name}
   2. Les métadonnées seront automatiquement détectées
   3. Vous pourrez filtrer par date, titre, etc.
   4. Exemple de requête: [word="vaccin"] within <doc date="2020-.*"/>

"""

        if self.unmatched_articles:
            report += f"\n⚠️  {len(self.unmatched_articles)} articles non trouvés dans le fichier texte:\n\n"
            for article in self.unmatched_articles[:10]:  # Afficher les 10 premiers
                report += f"   • {article['id']}: {article['title'][:60]}...\n"

            if len(self.unmatched_articles) > 10:
                report += f"\n   ... et {len(self.unmatched_articles) - 10} autres\n"

        print(report)

        # Sauvegarder le rapport
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"📄 Rapport sauvegardé: {report_path}\n")

    def process(self):
        """Exécute le processus complet d'annotation."""
        print("\n" + "="*70)
        print("   ANNOTATION DU CORPUS POUR SKETCHENGINE")
        print("="*70 + "\n")

        # Charger les données
        self.load_csv()
        self.parse_text_file()

        # Annoter le corpus
        self.annotate_corpus()

        # Générer le rapport
        self.save_report()

        print("✅ Annotation terminée avec succès!\n")


def main():
    """Fonction principale avec support des arguments."""
    parser = argparse.ArgumentParser(
        description='Annote un corpus d\'articles avec métadonnées pour SketchEngine'
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
        help='Chemin du fichier annoté de sortie (défaut: [fichier]_annotated.txt)'
    )

    args = parser.parse_args()

    # Créer l'annotateur et lancer le traitement
    annotator = CorpusAnnotator(args.csv, args.txt, args.output)
    annotator.process()


if __name__ == "__main__":
    main()
