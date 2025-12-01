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

    def __init__(self, csv_path: str, txt_path: str, output_path: str = None,
                 column_mapping: Dict[str, str] = None, corpus_name: str = None,
                 corpus_source: str = None, id_prefix: str = None, csv_delimiter: str = ',',
                 debug: bool = False):
        """
        Initialise l'annotateur de corpus.

        Args:
            csv_path: Chemin vers le fichier CSV des métadonnées
            txt_path: Chemin vers le fichier texte des articles
            output_path: Chemin du fichier annoté (par défaut: corpus_annotated.txt)
            column_mapping: Mapping des colonnes CSV vers les noms standardisés.
                           Par défaut: {'title': 'Titre', 'subtitle': 'Sous-titre',
                                       'date': 'Date', 'url': 'Lien'}
            corpus_name: Nom du corpus (par défaut: basé sur le fichier)
            corpus_source: Source du corpus (par défaut: basé sur le fichier)
            id_prefix: Préfixe pour les IDs (par défaut: LIB)
            csv_delimiter: Délimiteur du CSV (par défaut: ',')
            debug: Mode debug pour afficher les détails du matching
        """
        self.csv_path = Path(csv_path)
        self.txt_path = Path(txt_path)
        self.csv_delimiter = csv_delimiter
        self.debug = debug

        if output_path:
            self.output_path = Path(output_path)
        else:
            self.output_path = self.txt_path.parent / f"{self.txt_path.stem}_annotated.txt"

        # Mapping des colonnes (standardisation)
        if column_mapping is None:
            # Mapping par défaut pour Libération
            self.column_mapping = {
                'title': 'Titre',
                'subtitle': 'Sous-titre',
                'date': 'Date',
                'url': 'Lien'
            }
        else:
            self.column_mapping = column_mapping

        # Paramètres du corpus
        self.corpus_name = corpus_name or "Liberation"
        self.corpus_source = corpus_source or "Libération"
        self.id_prefix = id_prefix or "LIB"

        self.articles_metadata = []
        self.articles_text = []
        self.matched_count = 0
        self.unmatched_articles = []
        self.matched_articles = []  # Pour stocker les articles appariés

    def _get_column(self, article: Dict, key: str, default: str = "") -> str:
        """
        Récupère une valeur de colonne en utilisant le mapping.

        Args:
            article: Dictionnaire de l'article
            key: Clé standardisée ('title', 'subtitle', 'date', 'url')
            default: Valeur par défaut si la colonne n'existe pas

        Returns:
            Valeur de la colonne ou default
        """
        column_name = self.column_mapping.get(key)
        if column_name and column_name in article:
            return article[column_name]
        return default

    def load_csv(self) -> List[Dict]:
        """Charge le fichier CSV des métadonnées."""
        print(f"📖 Lecture du fichier CSV: {self.csv_path}")
        print(f"   ℹ️  Délimiteur utilisé: '{self.csv_delimiter}'")

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=self.csv_delimiter)
            self.articles_metadata = list(reader)

        print(f"   ✓ {len(self.articles_metadata)} articles avec métadonnées chargés")

        # Afficher les colonnes détectées pour debug
        if self.articles_metadata:
            # Filtrer les clés None qui peuvent apparaître si le CSV a des colonnes vides
            columns = [col for col in self.articles_metadata[0].keys() if col is not None and col.strip()]
            print(f"   ℹ️  Colonnes détectées: {', '.join(columns)}")

        return self.articles_metadata

    def parse_text_file(self) -> List[Dict]:
        """
        Parse le fichier texte pour extraire les articles.

        Structure FIXE attendue (TOUJOURS la même) :
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

        # Première passe : trouver toutes les dates (marqueurs d'articles)
        date_positions = []
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')

        for i, line in enumerate(lines):
            if date_pattern.match(line.strip()):
                date_positions.append(i)

        if self.debug:
            print(f"   🔍 DEBUG - {len(date_positions)} dates trouvées dans le fichier")

        # Deuxième passe : extraire chaque article à partir des dates
        for idx, date_line in enumerate(date_positions):
            # La structure est fixe : remonter de 4 lignes pour trouver le titre
            # date_line - 4 = titre
            # date_line - 3 = vide
            # date_line - 2 = sous-titre
            # date_line - 1 = vide
            # date_line = date

            if date_line < 4:
                continue  # Pas assez de lignes avant pour avoir un titre

            title_line = date_line - 4
            subtitle_line = date_line - 2

            title = lines[title_line].strip()
            subtitle = lines[subtitle_line].strip()
            date = lines[date_line].strip()

            # Vérifier que la ligne avant le titre est vide (fin de l'article précédent)
            if title_line > 0 and lines[title_line - 1].strip():
                # Ce n'est probablement pas un début d'article valide
                continue

            # Le contenu commence après la date et la ligne vide
            content_start = date_line + 2 if date_line + 1 < len(lines) and not lines[date_line + 1].strip() else date_line + 1

            # Le contenu se termine au prochain article (ou à la fin du fichier)
            if idx + 1 < len(date_positions):
                # Prochain article : remonter jusqu'à la ligne vide avant le prochain titre
                next_title_line = date_positions[idx + 1] - 4
                content_end = next_title_line - 1 if next_title_line > 0 and not lines[next_title_line - 1].strip() else next_title_line
            else:
                content_end = len(lines)

            # Extraire le contenu
            content_lines = lines[content_start:content_end]
            content = ''.join(content_lines).strip()

            article = {
                'title': title,
                'subtitle': subtitle,
                'date': date,
                'content': content,
                'start_line': title_line,
                'end_line': content_end - 1,
                'title_normalized': self.normalize_text(title)
            }
            articles.append(article)

        self.articles_text = articles
        print(f"   ✓ {len(articles)} articles extraits du fichier texte")

        if self.debug and len(articles) > 0:
            print(f"   🔍 DEBUG - Premiers titres extraits:")
            for art in articles[:3]:
                print(f"      • {art['title'][:60]}...")

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
        # Retirer les points de suspension et autres marques de troncature
        text = text.replace('...', '').replace('…', '')
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
        Calcule un score de similarité entre deux titres.

        Returns:
            Score entre 0 et 1
        """
        return SequenceMatcher(None, text1, text2).ratio()

    def find_best_match(self, csv_title: str) -> Optional[Dict]:
        """
        Trouve le meilleur article du texte correspondant au titre du CSV.

        Gère les titres tronqués en vérifiant d'abord si l'un est un préfixe de l'autre.

        Args:
            csv_title: Titre de l'article dans le CSV

        Returns:
            Article du fichier texte ou None
        """
        csv_title_norm = self.normalize_text(csv_title)

        if self.debug:
            print(f"\n🔍 DEBUG - Recherche de match pour: {csv_title[:60]}...")
            print(f"   Titre normalisé: {csv_title_norm[:60]}...")

        best_match = None
        best_score = 0.0
        best_txt_title = ""

        for txt_article in self.articles_text:
            txt_title_norm = txt_article['title_normalized']

            # Vérifier d'abord si un titre est un préfixe de l'autre (titres tronqués)
            # On considère un préfixe valide s'il fait au moins 30 caractères
            if len(csv_title_norm) >= 30 or len(txt_title_norm) >= 30:
                shorter = csv_title_norm if len(csv_title_norm) < len(txt_title_norm) else txt_title_norm
                longer = txt_title_norm if len(csv_title_norm) < len(txt_title_norm) else csv_title_norm

                # Si le titre court est un préfixe du titre long, c'est un match parfait
                if longer.startswith(shorter) and len(shorter) >= 30:
                    if self.debug:
                        print(f"   ✅ Match parfait (préfixe) avec: {txt_article['title'][:60]}...")
                    return txt_article

            # Sinon, utiliser le fuzzy matching classique
            score = self.similarity_score(csv_title_norm, txt_title_norm)

            if score > best_score:
                best_score = score
                best_match = txt_article
                best_txt_title = txt_article['title']

        if self.debug:
            print(f"   Meilleur score: {best_score:.2%}")
            if best_match:
                print(f"   Meilleur match: {best_txt_title[:60]}...")
            else:
                print(f"   ❌ Aucun match trouvé (seuil: 70%)")

        # Seuil de 70% pour considérer un match
        if best_score >= 0.70:
            return best_match

        return None

    def generate_id(self, index: int, date_str: str = "") -> str:
        """
        Génère un identifiant unique.

        Format: PREFIX_YYYY_NNN (ex: LIB_2020_001, FIG_2020_001)

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

        return f"{self.id_prefix}_{year}_{index:03d}"

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

        # Ajouter les métadonnées standardisées en utilisant le mapping
        title = self._get_column(metadata, 'title')
        if title:
            attributes.append(f'title="{self.escape_xml(title)}"')

        subtitle = self._get_column(metadata, 'subtitle')
        if subtitle:
            attributes.append(f'subtitle="{self.escape_xml(subtitle)}"')

        date = self._get_column(metadata, 'date')
        if date:
            attributes.append(f'date="{self.escape_xml(date)}"')
            # Ajouter aussi année, mois, jour séparément pour faciliter les requêtes
            date_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', date)
            if date_match:
                attributes.append(f'year="{date_match.group(1)}"')
                attributes.append(f'month="{date_match.group(2)}"')
                attributes.append(f'day="{date_match.group(3)}"')

        url = self._get_column(metadata, 'url')
        if url:
            attributes.append(f'url="{self.escape_xml(url)}"')

        # Ajouter des métadonnées supplémentaires si disponibles
        # (exclure les colonnes déjà traitées via le mapping)
        mapped_columns = set(self.column_mapping.values())
        for key in metadata:
            if key not in mapped_columns:
                safe_key = key.lower().replace(' ', '_').replace('-', '_')
                attributes.append(f'{safe_key}="{self.escape_xml(metadata[key])}"')

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
        annotated_content.append(f'<corpus name="{self.corpus_name}" '
                                f'source="{self.corpus_source}" '
                                f'created="{datetime.now().strftime("%Y-%m-%d")}">')
        annotated_content.append('')

        # Traiter chaque article du CSV
        for i, csv_article in enumerate(self.articles_metadata, start=1):
            # Générer l'ID
            article_id = self.generate_id(i, self._get_column(csv_article, 'date'))

            # Trouver l'article correspondant dans le texte
            title = self._get_column(csv_article, 'title')
            if not title:
                # Si pas de titre, on ne peut pas faire le matching
                continue

            txt_article = self.find_best_match(title)

            if txt_article:
                self.matched_count += 1

                # Stocker l'article apparié pour les exports titres/sous-titres
                self.matched_articles.append({
                    'id': article_id,
                    'title': title,
                    'subtitle': self._get_column(csv_article, 'subtitle'),
                    'date': self._get_column(csv_article, 'date'),
                    'journal': self.corpus_source,
                    'url': self._get_column(csv_article, 'url')
                })

                # Balise d'ouverture avec métadonnées
                doc_tag = self.create_doc_tag(article_id, csv_article, txt_article)
                annotated_content.append(doc_tag)

                # Contenu de l'article
                annotated_content.append(txt_article['content'])

                # Balise de fermeture
                annotated_content.append('</doc>')
                annotated_content.append('')
            else:
                # Article non trouvé : on ne l'inclut pas dans le corpus annoté
                self.unmatched_articles.append({
                    'id': article_id,
                    'title': title,
                    'date': self._get_column(csv_article, 'date')
                })

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
   • Corpus des titres: {self.output_path.stem}_titles.txt
   • Corpus des sous-titres: {self.output_path.stem}_subtitles.txt

📝 Format SketchEngine:
   • Chaque article est dans une balise <doc>
   • Tous les attributs du CSV sont inclus dans les balises
   • Attributs disponibles: id, title, subtitle, date, year, month, day, url

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

    def save_titles_txt(self) -> Path:
        """
        Génère un fichier texte annoté contenant uniquement les titres.

        Format: Corpus XML avec balises <doc> contenant les titres seuls

        Returns:
            Chemin du fichier généré
        """
        titles_path = self.output_path.parent / f"{self.output_path.stem}_titles.txt"
        print(f"\n📋 Génération du corpus des titres: {titles_path}")

        content = []

        # En-tête du corpus
        content.append('<?xml version="1.0" encoding="UTF-8"?>')
        content.append('<corpus name="Liberation_Titles" '
                      'source="Libération - Titres" '
                      f'created="{datetime.now().strftime("%Y-%m-%d")}">')
        content.append('')

        for article in self.matched_articles:
            # Balise d'ouverture avec métadonnées
            attributes = [
                f'id="{article["id"]}"',
                f'date="{article["date"]}"',
                f'journal="{article["journal"]}"',
                f'url="{self.escape_xml(article["url"])}"'
            ]

            # Ajouter année, mois, jour si date disponible
            if article['date']:
                date_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', article['date'])
                if date_match:
                    attributes.append(f'year="{date_match.group(1)}"')
                    attributes.append(f'month="{date_match.group(2)}"')
                    attributes.append(f'day="{date_match.group(3)}"')

            content.append('<doc ' + ' '.join(attributes) + '>')

            # Le titre comme contenu
            content.append(article['title'])

            content.append('</doc>')
            content.append('')

        # Fermeture du corpus
        content.append('</corpus>')

        # Sauvegarder
        with open(titles_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))

        print(f"   ✓ {len(self.matched_articles)} titres exportés")
        return titles_path

    def save_subtitles_txt(self) -> Path:
        """
        Génère un fichier texte annoté contenant uniquement les sous-titres.

        Format: Corpus XML avec balises <doc> contenant les sous-titres seuls

        Returns:
            Chemin du fichier généré
        """
        subtitles_path = self.output_path.parent / f"{self.output_path.stem}_subtitles.txt"
        print(f"\n📋 Génération du corpus des sous-titres: {subtitles_path}")

        content = []

        # En-tête du corpus
        content.append('<?xml version="1.0" encoding="UTF-8"?>')
        content.append('<corpus name="Liberation_Subtitles" '
                      'source="Libération - Sous-titres" '
                      f'created="{datetime.now().strftime("%Y-%m-%d")}">')
        content.append('')

        count = 0
        for article in self.matched_articles:
            # N'inclure que si le sous-titre existe
            if not article['subtitle']:
                continue

            count += 1

            # Balise d'ouverture avec métadonnées
            attributes = [
                f'id="{article["id"]}"',
                f'date="{article["date"]}"',
                f'journal="{article["journal"]}"',
                f'url="{self.escape_xml(article["url"])}"'
            ]

            # Ajouter année, mois, jour si date disponible
            if article['date']:
                date_match = re.match(r'(\d{4})-(\d{2})-(\d{2})', article['date'])
                if date_match:
                    attributes.append(f'year="{date_match.group(1)}"')
                    attributes.append(f'month="{date_match.group(2)}"')
                    attributes.append(f'day="{date_match.group(3)}"')

            content.append('<doc ' + ' '.join(attributes) + '>')

            # Le sous-titre comme contenu
            content.append(article['subtitle'])

            content.append('</doc>')
            content.append('')

        # Fermeture du corpus
        content.append('</corpus>')

        # Sauvegarder
        with open(subtitles_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))

        print(f"   ✓ {count} sous-titres exportés")
        return subtitles_path

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

        # Générer les fichiers supplémentaires
        self.save_titles_txt()
        self.save_subtitles_txt()

        # Générer le rapport
        self.save_report()

        print("✅ Annotation terminée avec succès!\n")


def main():
    """Fonction principale avec support des arguments."""
    parser = argparse.ArgumentParser(
        description='Annote un corpus d\'articles avec métadonnées pour SketchEngine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:

  # Avec les valeurs par défaut (Libération)
  python annotate_corpus_for_sketchengine.py --csv metadata.csv --txt corpus.txt

  # Pour Le Figaro avec preset (CSV avec point-virgule)
  python annotate_corpus_for_sketchengine.py \\
    --csv articles_figaro.csv \\
    --txt corpus_figaro.txt \\
    --preset figaro \\
    --delimiter ";"

  # Avec mapping manuel
  python annotate_corpus_for_sketchengine.py \\
    --csv metadata.csv --txt corpus.txt \\
    --title-col "Title" --subtitle-col "Subtitle" \\
    --date-col "PublishDate" --url-col "URL" \\
    --corpus-name "Figaro" --corpus-source "Le Figaro" \\
    --id-prefix "FIG"
        """
    )
    parser.add_argument(
        '--csv',
        required=True,
        help='Chemin vers le fichier CSV des métadonnées'
    )
    parser.add_argument(
        '--txt',
        required=True,
        help='Chemin vers le fichier texte des articles'
    )
    parser.add_argument(
        '--output',
        help='Chemin du fichier annoté de sortie (défaut: [fichier]_annotated.txt)'
    )
    parser.add_argument(
        '--preset',
        choices=['liberation', 'figaro'],
        help='Utiliser un preset prédéfini pour un journal (liberation ou figaro)'
    )
    parser.add_argument(
        '--title-col',
        help='Nom de la colonne contenant le titre (défaut: Titre)'
    )
    parser.add_argument(
        '--subtitle-col',
        help='Nom de la colonne contenant le sous-titre (défaut: Sous-titre)'
    )
    parser.add_argument(
        '--date-col',
        help='Nom de la colonne contenant la date (défaut: Date)'
    )
    parser.add_argument(
        '--url-col',
        help='Nom de la colonne contenant l\'URL (défaut: Lien)'
    )
    parser.add_argument(
        '--corpus-name',
        help='Nom du corpus (défaut: Liberation)'
    )
    parser.add_argument(
        '--corpus-source',
        help='Source du corpus (défaut: Libération)'
    )
    parser.add_argument(
        '--id-prefix',
        help='Préfixe pour les IDs d\'articles (défaut: LIB)'
    )
    parser.add_argument(
        '--delimiter',
        default=',',
        help='Délimiteur du CSV (défaut: ,). Utiliser ";" pour les CSV français standards'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Activer le mode debug pour voir les détails du matching'
    )

    args = parser.parse_args()

    # Déterminer le mapping de colonnes
    column_mapping = None
    corpus_name = args.corpus_name
    corpus_source = args.corpus_source
    id_prefix = args.id_prefix

    # Appliquer les presets si spécifié
    if args.preset == 'liberation':
        column_mapping = {
            'title': 'Titre',
            'subtitle': 'Sous-titre',
            'date': 'Date',
            'url': 'Lien'
        }
        corpus_name = corpus_name or "Liberation"
        corpus_source = corpus_source or "Libération"
        id_prefix = id_prefix or "LIB"
    elif args.preset == 'figaro':
        # Preset pour Le Figaro (ajuster selon le format réel)
        column_mapping = {
            'title': 'Titre',
            'subtitle': 'Sous-titre',
            'date': 'Date',
            'url': 'Lien'
        }
        corpus_name = corpus_name or "Figaro"
        corpus_source = corpus_source or "Le Figaro"
        id_prefix = id_prefix or "FIG"

    # Les arguments individuels remplacent le preset
    if any([args.title_col, args.subtitle_col, args.date_col, args.url_col]):
        column_mapping = {
            'title': args.title_col or 'Titre',
            'subtitle': args.subtitle_col or 'Sous-titre',
            'date': args.date_col or 'Date',
            'url': args.url_col or 'Lien'
        }

    # Créer l'annotateur et lancer le traitement
    annotator = CorpusAnnotator(
        args.csv,
        args.txt,
        args.output,
        column_mapping=column_mapping,
        corpus_name=corpus_name,
        corpus_source=corpus_source,
        id_prefix=id_prefix,
        csv_delimiter=args.delimiter,
        debug=args.debug
    )
    annotator.process()


if __name__ == "__main__":
    main()
