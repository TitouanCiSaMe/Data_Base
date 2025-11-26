#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'intégration des identifiants du décret de Gratien dans les fichiers XML.
Version améliorée pour traiter les références composites et pour privilégier
la colonne "Alias_Allegations_20e" si la note contient " d." ou " a.".
Utilisation dans PyCharm.
"""

import pandas as pd
import xml.etree.ElementTree as ET
import re
from difflib import SequenceMatcher
import os


def replace_last_c_number(ref: str, new_number: str) -> str:
    """
    Remplace le dernier segment du type "c.<nombre>" dans une référence par "c.<new_number>".

    Exemple :
      Input : ("C.9 q.3 c.17", "18")
      Output : "C.9 q.3 c.18"
    """
    pattern = re.compile(r'(c\.?\s*\d+)(?!.*c\.?\s*\d+)')
    match = pattern.search(ref)
    if match:
        start, end = match.span()
        new_val = "c." + new_number
        new_ref = ref[:start] + new_val + ref[end:]
        return new_ref.strip()
    return ref


def split_references(ref: str) -> list:
    """
    Extrait toutes les références d'une chaîne composite.

    Exemple :
      Input : "C.9 q.3 c.17 vel 18 et c.21"
      Output : ["C.9 q.3 c.17", "C.9 q.3 c.18", "C.9 q.3 c.21"]
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


class GratienMatcher:
    """Classe pour matcher les références du décret de Gratien"""

    def __init__(self, csv_path: str):
        """
        Initialise le matcher avec le fichier CSV des références

        Args:
            csv_path (str): Chemin vers le fichier CSV contenant les références
        """
        self.csv_path = csv_path
        self.df = None
        self.load_csv()

    def load_csv(self):
        """Charge le fichier CSV des références"""
        try:
            self.df = pd.read_csv(self.csv_path, encoding='utf-8')
            print(f"✓ CSV chargé: {len(self.df)} références trouvées")
            print(f"Colonnes disponibles: {list(self.df.columns)}")
        except Exception as e:
            print(f"❌ Erreur lors du chargement du CSV: {e}")
            raise

    def normalize_reference(self, ref: str) -> str:
        """Normalise une référence canonique pour faciliter la comparaison"""
        if pd.isna(ref) or not ref:
            return ""

        # Supprime les espaces en trop et met en minuscules
        normalized = re.sub(r'\s+', ' ', str(ref).lower().strip())

        # Standardise les abréviations courantes du décret de Gratien
        normalized = normalized.replace('dist.', 'd.')
        normalized = normalized.replace('distinctio', 'd.')
        normalized = normalized.replace('causa', 'c.')
        normalized = normalized.replace('questio', 'q.')
        normalized = normalized.replace('canon', 'c.')
        normalized = normalized.replace('de consecratione', 'de cons')
        normalized = normalized.replace('decons.', 'de cons')
        normalized = normalized.replace('decons', 'de cons')

        # Supprime les points
        normalized = normalized.replace('.', '')

        return normalized

    def extract_reference_parts(self, ref: str) -> set:
        """Extrait les parties d'une référence pour une comparaison plus flexible"""
        if not ref:
            return set()

        normalized = self.normalize_reference(ref)
        parts = set()

        # Trouve les parties numériques, par exemple D.4, c.44, q.6, etc.
        number_parts = re.findall(r'[dqc]\d+', normalized)
        parts.update(number_parts)

        # Ajoute "de cons" si présent
        if 'de cons' in normalized:
            parts.add('decons')

        return parts

    def is_gratien_reference(self, ref: str) -> bool:
        """Vérifie si une référence correspond au décret de Gratien"""
        if not ref:
            return False

        patterns = [
            r'[dD]\.?\s*\d+\s*c\.?\s*\d+',  # Ex : D.4 c.134, D.92 c.2, etc.
            r'[cC]\.?\s*\d+\s*q\.?\s*\d+\s*c\.?\s*\d+',  # Ex : C.15 q.6 c.2, etc.
            r'de\s*cons',  # Références de consecratione
        ]

        for pattern in patterns:
            if re.search(pattern, ref):
                return True
        return False

    def similarity_score(self, ref1: str, ref2: str) -> float:
        """Calcule un score de similarité entre deux références"""
        # Méthode 1: comparaison textuelle classique
        norm1 = self.normalize_reference(ref1)
        norm2 = self.normalize_reference(ref2)
        if not norm1 or not norm2:
            return 0
        text_score = SequenceMatcher(None, norm1, norm2).ratio()

        # Méthode 2: comparaison par parties (plus flexible quant à l'ordre)
        parts1 = self.extract_reference_parts(ref1)
        parts2 = self.extract_reference_parts(ref2)

        if not parts1 or not parts2:
            return text_score

        # Calcul du score basé sur les parties communes
        common_parts = parts1.intersection(parts2)
        all_parts = parts1.union(parts2)
        parts_score = len(common_parts) / len(all_parts) if all_parts else 0

        # Score combiné (les parties communes sont légèrement pénalisées)
        combined_score = max(text_score, parts_score * 0.9)

        return combined_score

    def find_best_match(self, xml_ref: str, threshold: float = 0.7):
        """
        Trouve la meilleure correspondance dans le CSV pour une référence XML.

        Si dans la référence (note) apparaît " d." ou " a.",
        le matching sera effectué en se basant exclusivement sur la colonne "Alias_Allegations_20e".
        """
        best_match = None
        best_score = 0

        # Vérification : si la référence comporte " d." ou " a.", on utilise uniquement "Alias_Allegations_20e"
        if " d." in xml_ref or " a." in xml_ref:
            for _, row in self.df.iterrows():
                if 'Alias_Allegations_20e' in row and pd.notna(row['Alias_Allegations_20e']):
                    score = self.similarity_score(xml_ref, row['Alias_Allegations_20e'])
                    if score > best_score and score >= threshold:
                        best_score = score
                        best_match = row
            return best_match, best_score

        # Sinon, on teste d'abord sur la colonne "Allegations", puis sur "Alias_Allegations_20e"
        for _, row in self.df.iterrows():
            score = self.similarity_score(xml_ref, row['Allegations'])
            if score > best_score and score >= threshold:
                best_score = score
                best_match = row

            if 'Alias_Allegations_20e' in row and pd.notna(row['Alias_Allegations_20e']):
                score = self.similarity_score(xml_ref, row['Alias_Allegations_20e'])
                if score > best_score and score >= threshold:
                    best_score = score
                    best_match = row

        return best_match, best_score

    def process_xml_file(self, xml_input_path: str, xml_output_path: str, threshold: float = 0.7) -> dict:
        """
        Traite un fichier XML en ajoutant les références Gratien.

        Pour chaque note, si le texte contient des références composites,
        celles-ci sont découpées et traitées individuellement.

        Args:
            xml_input_path (str): Chemin du fichier XML d'entrée
            xml_output_path (str): Chemin du fichier XML de sortie
            threshold (float): Seuil de similarité minimum
        """
        try:
            # Parse du fichier XML
            tree = ET.parse(xml_input_path)
            root = tree.getroot()

            # Statistiques
            matches_found = 0
            total_references = 0
            gratien_references = 0

            print(f"\n🔍 Traitement du fichier: {xml_input_path}")
            print("-" * 60)

            # Pour chaque balise <note> contenant un <allegation>
            for note in root.findall('.//note'):
                allegation = note.find('allegation')
                if allegation is not None:
                    total_references += 1
                    ref_text = allegation.text.strip() if allegation.text else ""

                    # Découpage pour gérer les références composites
                    ref_list = split_references(ref_text)
                    found_ids = []  # Stockage des identifiants trouvés

                    for single_ref in ref_list:
                        if self.is_gratien_reference(single_ref):
                            gratien_references += 1
                            match, score = self.find_best_match(single_ref, threshold)
                            if match is not None:
                                matches_found += 1
                                found_ids.append(str(match['Identifiant']))
                                print(
                                    f"✓ '{single_ref}' → '{match['Allegations']}' (Ref: {match['Identifiant']}, score: {score:.2f})")
                            else:
                                print(f"⚠ Pas de correspondance pour: '{single_ref}' (score < {threshold})")
                        else:
                            print(f"• '{single_ref}' → Non-Gratien (ignoré)")
                    # Si des correspondances ont été trouvées, on stocke les identifiants séparés par des virgules
                    if found_ids:
                        note.set('gratien_refs', ",".join(found_ids))

            # Sauvegarde du XML modifié avec encodage UTF-8
            tree.write(xml_output_path, encoding='utf-8', xml_declaration=True)

            # Rapport final
            print("\n" + "=" * 60)
            print("📊 RAPPORT FINAL")
            print("=" * 60)
            print(f"Total de références trouvées: {total_references}")
            print(f"Références de Gratien: {gratien_references}")
            print(f"Correspondances trouvées: {matches_found}")
            if gratien_references > 0:
                print(f"Taux de succès Gratien: {matches_found / gratien_references * 100:.1f}%")
            print(f"Fichier sauvegardé: {xml_output_path}")

            return {
                'total_references': total_references,
                'gratien_references': gratien_references,
                'matches_found': matches_found,
                'success_rate': matches_found / gratien_references * 100 if gratien_references > 0 else 0
            }

        except Exception as e:
            print(f"❌ Erreur lors du traitement: {e}")
            raise

    def test_matching(self, test_references: list = None):
        """
        Teste le matching avec quelques références.

        Args:
            test_references (list): Liste de références à tester.
        """
        if test_references is None:
            test_references = [
                'D.19 c.3',
                'C.15 q.6 c.2',
                'D.4 c.134 de cons',
                'de cons. D.4 c.44',  # Cas de test particulier
                'Dig. 35.1.59',
                'C.9 q.3 c.17 vel 18 et c.21',
                'C.9 q.3 c.17 d.12'  # Exemple avec " d." pour forcer l'utilisation de l'alias
            ]

        print("\n🧪 TEST DE CORRESPONDANCES")
        print("-" * 40)

        for ref in test_references:
            # Découpage des références composites
            ref_list = split_references(ref)
            for single_ref in ref_list:
                match, score = self.find_best_match(single_ref)
                if match is not None:
                    print(
                        f"✓ '{single_ref}' → '{match['Allegations']}' (Ref: {match['Identifiant']}, score: {score:.2f})")
                    # Affiche les parties extraites pour le debug
                    parts1 = self.extract_reference_parts(single_ref)
                    parts2 = self.extract_reference_parts(match['Allegations'])
                    print(f"   Parties XML: {parts1} | CSV: {parts2}")
                else:
                    if self.is_gratien_reference(single_ref):
                        print(f"⚠ '{single_ref}' → Gratien mais pas de correspondance")
                        parts = self.extract_reference_parts(single_ref)
                        print(f"   Parties extraites: {parts}")
                    else:
                        print(f"• '{single_ref}' → Non-Gratien (ignoré)")


def main():
    """Fonction principale - À adapter selon vos besoins"""

    # =============================================
    # CONFIGURATION - Modifiez ces chemins
    # =============================================
    CSV_PATH = "/home/titouan/Bureau/Test_ID/Grat_ID.csv"  # Chemin vers le fichier CSV
    XML_INPUT_DIR = "/home/titouan/Bureau/Test_ID/XML_Animal"  # Dossier des fichiers XML d'entrée
    XML_OUTPUT_DIR = "/home/titouan/Bureau/Test_ID/XML_Animal_102"  # Dossier des fichiers XML modifiés
    THRESHOLD = 0.7  # Seuil de similarité (0.0 à 1.0)

    # =============================================
    # VÉRIFICATIONS
    # =============================================
    if not os.path.exists(CSV_PATH):
        print(f"❌ Fichier CSV non trouvé: {CSV_PATH}")
        print("👉 Modifiez la variable CSV_PATH dans la fonction main()")
        return

    if not os.path.isdir(XML_INPUT_DIR):
        print(f"❌ Dossier XML d'entrée non trouvé: {XML_INPUT_DIR}")
        print("👉 Modifiez la variable XML_INPUT_DIR dans la fonction main()")
        return

    # Création du dossier de sortie si nécessaire
    if not os.path.exists(XML_OUTPUT_DIR):
        os.makedirs(XML_OUTPUT_DIR)
        print(f"Création du dossier de sortie: {XML_OUTPUT_DIR}")

    # =============================================
    # TRAITEMENT
    # =============================================
    try:
        matcher = GratienMatcher(CSV_PATH)

        # Option de test
        print("Voulez-vous d'abord tester quelques correspondances ? (y/n)")
        if input().lower().startswith('y'):
            matcher.test_matching()
            print("\nContinuer avec le traitement complet ? (y/n)")
            if not input().lower().startswith('y'):
                return

        # Traitement de chaque fichier XML dans le dossier d'entrée
        print("\n🔍 Traitement des fichiers XML dans le dossier...")
        for file_name in os.listdir(XML_INPUT_DIR):
            if file_name.lower().endswith('.xml'):
                xml_input_path = os.path.join(XML_INPUT_DIR, file_name)
                xml_output_path = os.path.join(XML_OUTPUT_DIR, file_name)
                print("\n" + "-" * 60)
                matcher.process_xml_file(xml_input_path, xml_output_path, THRESHOLD)

        print(f"\n🎉 Traitement complet terminé !")

    except Exception as e:
        print(f"❌ Erreur: {e}")


def process_files(csv_path: str, xml_input_dir: str, xml_output_dir: str, threshold: float = 0.7) -> dict:
    """
    Fonction simplifiée pour une utilisation directe dans PyCharm.
    Traite tous les fichiers XML d'un dossier.

    Usage:
        from gratien_matcher import process_files
        process_files("mon_csv.csv", "dossier_xml_input", "dossier_xml_output")
    """
    matcher = GratienMatcher(csv_path)

    if not os.path.isdir(xml_input_dir):
        raise Exception(f"Dossier XML d'entrée non trouvé: {xml_input_dir}")

    if not os.path.exists(xml_output_dir):
        os.makedirs(xml_output_dir)

    results = {}
    for file_name in os.listdir(xml_input_dir):
        if file_name.lower().endswith('.xml'):
            xml_input_path = os.path.join(xml_input_dir, file_name)
            xml_output_path = os.path.join(xml_output_dir, file_name)
            results[file_name] = matcher.process_xml_file(xml_input_path, xml_output_path, threshold)
    return results


if __name__ == "__main__":
    main()

