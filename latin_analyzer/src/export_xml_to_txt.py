#!/usr/bin/env python3
"""
Script d'export : Extraire le texte des XML Pages vers fichier TXT.

Usage:
    python3 export_xml_to_txt.py <input_xml_ou_dossier> <output.txt> [single|dual]

Exemples:
    # Un fichier
    python3 export_xml_to_txt.py page_001.xml resultat.txt single

    # Un dossier
    python3 export_xml_to_txt.py /path/to/xml_folder/ corpus_complet.txt single

    # Mode dual
    python3 export_xml_to_txt.py /path/to/dual_xml/ corpus_dual.txt dual
"""

import sys
import os
from pathlib import Path

# Ajouter le dossier src au path si nécessaire
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from page_xml_parser import PageXMLParser


def export_to_txt(input_path, output_file, column_mode='single', include_metadata=False):
    """
    Exporte le texte extrait vers un fichier TXT.

    Args:
        input_path (str): Fichier XML ou dossier
        output_file (str): Fichier TXT de sortie
        column_mode (str): 'single' ou 'dual'
        include_metadata (bool): Inclure les métadonnées en en-tête
    """
    parser = PageXMLParser(column_mode=column_mode)

    print(f"📂 Extraction depuis : {input_path}")
    print(f"📄 Mode : {column_mode}")

    # Extraire le texte
    if os.path.isfile(input_path):
        lines, metadata = parser.parse_file(input_path)

        if include_metadata:
            header = [
                f"# Fichier : {metadata['filename']}",
                f"# Page : {metadata['page_number']}",
                f"# Titre courant : {metadata['running_title']}",
                f"# Lignes : {len(lines)}",
                "",
                "=" * 60,
                ""
            ]
            lines = header + lines

        print(f"✅ 1 fichier traité, {len(lines)} lignes extraites")

    elif os.path.isdir(input_path):
        text, metadata_list = parser.parse_folder(input_path)
        lines = text.split('\n')

        if include_metadata:
            header = [
                f"# Dossier source : {input_path}",
                f"# Fichiers traités : {len(metadata_list)}",
                f"# Lignes totales : {len(lines)}",
                f"# Mode : {column_mode}",
                "",
                "=" * 60,
                ""
            ]
            lines = header + lines

        print(f"✅ {len(metadata_list)} fichiers traités, {len(lines)} lignes extraites")

    else:
        print(f"❌ Chemin invalide : {input_path}")
        sys.exit(1)

    # Sauvegarder
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"💾 Texte sauvegardé : {output_file}")

    # Afficher les stats du fichier
    file_size = os.path.getsize(output_file) / 1024  # KB
    print(f"📊 Taille : {file_size:.1f} KB")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    input_path = sys.argv[1]
    output_file = sys.argv[2]
    column_mode = sys.argv[3] if len(sys.argv) > 3 else 'single'

    # Option --with-metadata pour inclure les infos en en-tête
    include_metadata = '--with-metadata' in sys.argv

    export_to_txt(input_path, output_file, column_mode, include_metadata)

    print("\n✅ Export terminé !")


if __name__ == "__main__":
    main()
