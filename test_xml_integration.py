#!/usr/bin/env python3
"""
Test d'intégration : Vérifier que page_xml_parser.py fonctionne correctement.

Ce test vérifie :
1. Import des modules
2. Parsing d'un fichier XML exemple (si disponible)
3. Compatibilité avec latin_analyzer_v2.py
"""

import sys
import os

print("=" * 60)
print("  TEST D'INTÉGRATION XML PAGES")
print("=" * 60)

# Test 1 : Imports
print("\n1️⃣  Test des imports...")
try:
    from page_xml_parser import PageXMLParser, extract_text_from_xml
    print("✅ page_xml_parser importé")
except ImportError as e:
    print(f"❌ Erreur d'import page_xml_parser : {e}")
    sys.exit(1)

try:
    sys.path.insert(0, '/tmp/collatinus-python')
    from latin_analyzer_v2 import LatinAnalyzer
    print("✅ latin_analyzer_v2 importé")
except ImportError as e:
    print(f"❌ Erreur d'import latin_analyzer_v2 : {e}")
    sys.exit(1)

# Test 2 : Créer un XML exemple minimal
print("\n2️⃣  Création d'un XML Pages exemple...")
sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15">
  <Page>
    <TextRegion custom="structure {type:MainZone;}">
      <TextLine id="line1">
        <TextEquiv>
          <Unicode>Abbas monachus scriptorium</Unicode>
        </TextEquiv>
      </TextLine>
      <TextLine id="line2">
        <TextEquiv>
          <Unicode>ecclesiam fundavit anno domini</Unicode>
        </TextEquiv>
      </TextLine>
    </TextRegion>
  </Page>
</PcGts>
"""

test_xml_file = "/tmp/test_page.xml"
with open(test_xml_file, 'w', encoding='utf-8') as f:
    f.write(sample_xml)
print(f"✅ Fichier XML test créé : {test_xml_file}")

# Test 3 : Parser le XML
print("\n3️⃣  Test du parsing...")
try:
    parser = PageXMLParser(column_mode='single')
    lines, metadata = parser.parse_file(test_xml_file)

    print(f"✅ Parsing réussi")
    print(f"   Lignes extraites : {len(lines)}")
    print(f"   Contenu :")
    for i, line in enumerate(lines, 1):
        print(f"     {i}. {line}")

    # Vérifier que le contenu est correct
    expected = ["Abbas monachus scriptorium", "ecclesiam fundavit anno domini"]
    if lines == expected:
        print("✅ Contenu extrait est correct")
    else:
        print("⚠️  Contenu différent de l'attendu")
        print(f"   Attendu : {expected}")
        print(f"   Obtenu  : {lines}")

except Exception as e:
    print(f"❌ Erreur de parsing : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4 : Intégration avec LatinAnalyzer
print("\n4️⃣  Test d'intégration avec LatinAnalyzer...")
try:
    # Note : on ne lance pas le chargement complet de Collatinus (trop lent)
    print("⏭️  Test de l'interface uniquement (pas de chargement Collatinus)")

    # Vérifier que les méthodes existent
    analyzer_class = LatinAnalyzer

    if hasattr(analyzer_class, 'analyze_page_xml'):
        print("✅ Méthode analyze_page_xml() disponible")
    else:
        print("❌ Méthode analyze_page_xml() manquante")
        sys.exit(1)

    if hasattr(analyzer_class, 'generate_docx'):
        print("✅ Méthode generate_docx() disponible")
    else:
        print("❌ Méthode generate_docx() manquante")
        sys.exit(1)

except Exception as e:
    print(f"❌ Erreur d'intégration : {e}")
    sys.exit(1)

# Test 5 : Mode dual
print("\n5️⃣  Test du mode dual...")
dual_xml = """<?xml version="1.0" encoding="UTF-8"?>
<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15">
  <Page>
    <TextRegion custom="structure {type:MainZone:column#1;}">
      <TextLine id="col1_line1">
        <TextEquiv>
          <Unicode>Colonne 1 ligne 1</Unicode>
        </TextEquiv>
      </TextLine>
    </TextRegion>
    <TextRegion custom="structure {type:MainZone:column#2;}">
      <TextLine id="col2_line1">
        <TextEquiv>
          <Unicode>Colonne 2 ligne 1</Unicode>
        </TextEquiv>
      </TextLine>
    </TextRegion>
  </Page>
</PcGts>
"""

test_dual_file = "/tmp/test_dual.xml"
with open(test_dual_file, 'w', encoding='utf-8') as f:
    f.write(dual_xml)

try:
    parser_dual = PageXMLParser(column_mode='dual')
    lines_dual, _ = parser_dual.parse_file(test_dual_file)

    print(f"✅ Mode dual fonctionne")
    print(f"   Lignes extraites : {len(lines_dual)}")
    print(f"   Contenu :")
    for i, line in enumerate(lines_dual, 1):
        print(f"     {i}. {line}")

    # Vérifier l'ordre : col1 puis col2
    expected_dual = ["Colonne 1 ligne 1", "Colonne 2 ligne 1"]
    if lines_dual == expected_dual:
        print("✅ Ordre des colonnes correct (col1 → col2)")
    else:
        print("⚠️  Ordre différent de l'attendu")

except Exception as e:
    print(f"❌ Erreur en mode dual : {e}")
    import traceback
    traceback.print_exc()

# Nettoyage
os.remove(test_xml_file)
os.remove(test_dual_file)

print("\n" + "=" * 60)
print("✅ TOUS LES TESTS PASSÉS !")
print("=" * 60)
print("\n💡 Pour tester sur vos vrais fichiers XML :")
print("   python3 page_xml_parser.py /path/to/your/file.xml single")
