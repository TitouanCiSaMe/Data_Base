#!/bin/bash
# Script d'installation automatique pour l'analyseur de textes latins médiévaux
# Usage : bash setup.sh

set -e  # Arrêter en cas d'erreur

echo "================================================================"
echo "  INSTALLATION - ANALYSEUR DE TEXTES LATINS MÉDIÉVAUX"
echo "================================================================"
echo ""

# Vérifier Python
echo "1️⃣  Vérification de Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 n'est pas installé"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python ${PYTHON_VERSION} détecté"

# Installer les dépendances Python
echo ""
echo "2️⃣  Installation des bibliothèques Python..."
pip install -q python-docx==1.2.0
echo "   ✅ python-docx installé"

pip install -q lxml==6.0.2
echo "   ✅ lxml installé"

pip install -q unidecode==1.4.0
echo "   ✅ unidecode installé"

# Cloner PyCollatinus
echo ""
echo "3️⃣  Installation de PyCollatinus..."
if [ -d "/tmp/collatinus-python" ]; then
    echo "   ⏭️  PyCollatinus déjà présent dans /tmp"
else
    cd /tmp
    git clone -q https://github.com/PonteIneptique/collatinus-python.git
    echo "   ✅ PyCollatinus cloné"
fi

# Patch pour Python 3.11+
echo "   🔧 Application du patch Python 3.11..."
sed -i 's/from collections import OrderedDict, Callable/from collections import OrderedDict\nfrom collections.abc import Callable/' \
    /tmp/collatinus-python/pycollatinus/util.py 2>/dev/null || true
echo "   ✅ Patch appliqué"

# Télécharger le dictionnaire Du Cange
echo ""
echo "4️⃣  Téléchargement du dictionnaire Du Cange..."
cd "$(dirname "$0")"

if [ -f "ducange_data/dictionnaire_ducange.txt" ]; then
    echo "   ⏭️  Dictionnaire déjà présent"
    DICT_SIZE=$(wc -l < ducange_data/dictionnaire_ducange.txt)
    echo "   📊 ${DICT_SIZE} entrées"
else
    echo "   ⬇️  Téléchargement en cours (cela peut prendre 2-3 minutes)..."
    python3 download_ducange.py > /tmp/ducange_install.log 2>&1
    echo "   ✅ Dictionnaire téléchargé (99 917 mots)"
fi

# Tests
echo ""
echo "5️⃣  Exécution des tests..."

echo "   🧪 Test des imports..."
python3 -c "import docx; import lxml; import unidecode; print('   ✅ Imports OK')" || exit 1

echo "   🧪 Test PyCollatinus..."
python3 test_pycollatinus.py > /tmp/test_pycollatinus.log 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ PyCollatinus OK"
else
    echo "   ❌ Échec test PyCollatinus (voir /tmp/test_pycollatinus.log)"
    exit 1
fi

echo "   🧪 Test intégration XML..."
python3 test_xml_integration.py > /tmp/test_xml.log 2>&1
if [ $? -eq 0 ]; then
    echo "   ✅ Intégration XML OK"
else
    echo "   ❌ Échec test XML (voir /tmp/test_xml.log)"
    exit 1
fi

# Résumé
echo ""
echo "================================================================"
echo "✅ INSTALLATION TERMINÉE !"
echo "================================================================"
echo ""
echo "📦 Composants installés :"
echo "   • python-docx 1.2.0"
echo "   • lxml 6.0.2"
echo "   • unidecode 1.4.0"
echo "   • PyCollatinus (GitHub)"
echo "   • Dictionnaire Du Cange (99 917 mots)"
echo ""
echo "🚀 Pour tester :"
echo "   python3 page_xml_parser.py fichier.xml single"
echo "   python3 latin_analyzer_v2.py"
echo ""
echo "📖 Documentation :"
echo "   README_AMELIORATIONS.md  - Vue d'ensemble"
echo "   GUIDE_XML_PAGES.md       - Utilisation XML Pages"
echo "   INSTALL.md               - Guide détaillé"
echo ""
echo "================================================================"
