#!/usr/bin/env python3
"""
Script pour télécharger et extraire le lexique Du Cange depuis SourceForge.
Crée un dictionnaire de latin médiéval à partir des 90 000 entrées.
"""

import os
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


def download_ducange_xml(output_dir="ducange_xml"):
    """
    Télécharge tous les fichiers XML du Du Cange depuis SourceForge.

    Args:
        output_dir (str): Répertoire de destination

    Returns:
        list: Liste des fichiers téléchargés
    """
    # Créer le répertoire de sortie
    os.makedirs(output_dir, exist_ok=True)

    # URL de base sur SourceForge
    base_url = "https://sourceforge.net/p/ducange/code/HEAD/tree/xml/"

    # Liste des lettres A-Z
    letters = [chr(i) for i in range(ord('A'), ord('Z') + 1)]

    downloaded_files = []

    print("📥 Téléchargement des fichiers XML du Du Cange...")
    print(f"Source : {base_url}")
    print(f"Destination : {output_dir}/")
    print("-" * 60)

    for letter in letters:
        filename = f"{letter}.xml"
        url = f"{base_url}{filename}?format=raw"
        output_path = os.path.join(output_dir, filename)

        # Vérifier si le fichier existe déjà
        if os.path.exists(output_path):
            print(f"✓ {filename} (déjà téléchargé)")
            downloaded_files.append(output_path)
            continue

        try:
            print(f"⬇ {filename}...", end=" ", flush=True)
            urllib.request.urlretrieve(url, output_path)

            # Vérifier la taille du fichier
            size_kb = os.path.getsize(output_path) / 1024
            print(f"OK ({size_kb:.1f} KB)")

            downloaded_files.append(output_path)

            # Petit délai pour ne pas surcharger le serveur
            time.sleep(0.5)

        except Exception as e:
            print(f"❌ Erreur : {e}")

    print("-" * 60)
    print(f"✅ {len(downloaded_files)} fichiers téléchargés")

    return downloaded_files


def parse_ducange_xml(xml_file):
    """
    Parse un fichier XML Du Cange et extrait les lemmes (mots-vedettes).

    Args:
        xml_file (str): Chemin vers le fichier XML

    Returns:
        set: Ensemble des lemmes trouvés
    """
    lemmas = set()

    try:
        # Parser le XML avec gestion des namespaces TEI
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Namespaces TEI et XML
        ns = {
            'tei': 'http://www.tei-c.org/ns/1.0',
            'xml': 'http://www.w3.org/XML/1998/namespace'
        }

        # Trouver toutes les entrées
        entries = root.findall('.//tei:entry', ns)

        for entry in entries:
            # Récupérer l'ID de l'entrée (souvent c'est le lemme principal)
            entry_id = entry.get('{http://www.w3.org/XML/1998/namespace}id')
            if entry_id:
                # Nettoyer l'ID (enlever les numéros)
                clean_id = re.sub(r'\d+$', '', entry_id).strip()
                clean_id = re.sub(r'^[0-9\-]+', '', clean_id).strip()
                if clean_id and len(clean_id) > 1:
                    lemmas.add(clean_id.lower())

            # Trouver tous les <form> qui contiennent les lemmes
            forms = entry.findall('.//tei:form', ns)
            for form in forms:
                if form.text:
                    # Nettoyer le texte du lemme
                    lemma_text = form.text.strip()
                    # Enlever les chiffres, ponctuation
                    lemma_text = re.sub(r'[0-9.,;:\(\)\[\]]', '', lemma_text)
                    # Enlever les espaces multiples
                    lemma_text = ' '.join(lemma_text.split())

                    if lemma_text and len(lemma_text) > 1:
                        # Ajouter chaque mot si c'est une expression
                        for word in lemma_text.split():
                            word = word.strip().lower()
                            if len(word) > 1 and word.isalpha():
                                lemmas.add(word)

            # Extraire aussi les formes dans <foreign> (variantes)
            foreign_forms = entry.findall('.//tei:foreign[@xml:lang="lat"]', ns)
            for foreign in foreign_forms:
                if foreign.text:
                    text = foreign.text.strip().lower()
                    text = re.sub(r'[0-9.,;:\(\)\[\]]', '', text)
                    for word in text.split():
                        word = word.strip()
                        if len(word) > 1 and word.isalpha():
                            lemmas.add(word)

    except Exception as e:
        print(f"⚠️  Erreur lors du parsing de {xml_file}: {e}")

    return lemmas


def extract_all_lemmas(xml_dir="ducange_xml"):
    """
    Extrait tous les lemmes de tous les fichiers XML Du Cange.

    Args:
        xml_dir (str): Répertoire contenant les fichiers XML

    Returns:
        set: Ensemble de tous les lemmes
    """
    all_lemmas = set()

    print("\n📖 Extraction des lemmes depuis les fichiers XML...")
    print("-" * 60)

    xml_files = sorted(Path(xml_dir).glob("*.xml"))

    for xml_file in xml_files:
        print(f"📄 {xml_file.name}...", end=" ", flush=True)
        lemmas = parse_ducange_xml(xml_file)
        all_lemmas.update(lemmas)
        print(f"{len(lemmas)} lemmes → Total: {len(all_lemmas)}")

    print("-" * 60)
    print(f"✅ Total de lemmes uniques extraits : {len(all_lemmas)}")

    return all_lemmas


def save_medieval_dictionary(lemmas, output_file="dictionnaire_ducange.txt"):
    """
    Sauvegarde les lemmes dans un fichier texte trié.

    Args:
        lemmas (set): Ensemble des lemmes
        output_file (str): Fichier de sortie

    Returns:
        str: Chemin du fichier créé
    """
    print(f"\n💾 Sauvegarde du dictionnaire...")

    # Trier les lemmes
    sorted_lemmas = sorted(lemmas)

    # Écrire dans le fichier
    with open(output_file, 'w', encoding='utf-8') as f:
        for lemma in sorted_lemmas:
            f.write(f"{lemma}\n")

    # Statistiques
    size_kb = os.path.getsize(output_file) / 1024
    print(f"✅ Dictionnaire sauvegardé : {output_file}")
    print(f"   • {len(sorted_lemmas)} entrées")
    print(f"   • {size_kb:.1f} KB")

    return output_file


def main():
    """Fonction principale."""
    print("=" * 60)
    print("  EXTRACTEUR DE LEXIQUE DU CANGE")
    print("  Latin médiéval - École nationale des chartes")
    print("=" * 60)

    # Répertoire de travail
    work_dir = Path(__file__).parent / "ducange_data"
    xml_dir = work_dir / "xml"
    dict_file = work_dir / "dictionnaire_ducange.txt"

    # Créer les répertoires
    work_dir.mkdir(exist_ok=True)

    # Étape 1 : Téléchargement
    print("\n🔹 ÉTAPE 1 : Téléchargement des fichiers XML")
    downloaded_files = download_ducange_xml(str(xml_dir))

    if not downloaded_files:
        print("❌ Aucun fichier téléchargé. Arrêt.")
        return 1

    # Étape 2 : Extraction des lemmes
    print("\n🔹 ÉTAPE 2 : Extraction des lemmes")
    all_lemmas = extract_all_lemmas(str(xml_dir))

    if not all_lemmas:
        print("❌ Aucun lemme extrait. Arrêt.")
        return 1

    # Étape 3 : Sauvegarde
    print("\n🔹 ÉTAPE 3 : Sauvegarde du dictionnaire")
    dict_path = save_medieval_dictionary(all_lemmas, str(dict_file))

    print("\n" + "=" * 60)
    print("✅ TERMINÉ !")
    print(f"📁 Fichier créé : {dict_path}")
    print(f"🎯 Vous pouvez maintenant utiliser ce dictionnaire pour filtrer")
    print(f"   les faux positifs dans vos textes latins médiévaux.")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
