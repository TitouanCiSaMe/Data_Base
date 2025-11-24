# 🚀 Démarrage rapide

## Installation en 1 commande

```bash
bash setup.sh
```

**Ou manuellement :**

```bash
# 1. Installer les bibliothèques
pip install python-docx lxml unidecode

# 2. Cloner PyCollatinus
cd /tmp && git clone https://github.com/PonteIneptique/collatinus-python.git

# 3. Patch Python 3.11
sed -i 's/from collections import OrderedDict, Callable/from collections import OrderedDict\nfrom collections.abc import Callable/' \
    /tmp/collatinus-python/pycollatinus/util.py

# 4. Télécharger Du Cange
cd /home/user/Data_Base && python3 download_ducange.py
```

---

## Utilisation

### 📄 Analyser des fichiers XML Pages

```bash
# Extraction seule
python3 page_xml_parser.py /path/to/xml_folder/ single

# Analyse complète avec colorisation
python3 -c "
from latin_analyzer_v2 import LatinAnalyzer
from page_xml_parser import PageXMLParser

analyzer = LatinAnalyzer(ducange_dict_file='ducange_data/dictionnaire_ducange.txt')
results = analyzer.analyze_page_xml('/path/to/xml/', column_mode='single')

parser = PageXMLParser(column_mode='single')
text, _ = parser.parse_folder('/path/to/xml/')
analyzer.generate_docx(text.split('\n'), 'resultat.docx', results)
"
```

---

### 📝 Analyser un fichier texte brut

```python
from latin_analyzer_v2 import LatinAnalyzer

analyzer = LatinAnalyzer(ducange_dict_file='ducange_data/dictionnaire_ducange.txt')
results = analyzer.analyze_text_file('texte.txt')
analyzer.generate_docx('texte.txt', 'resultat.docx', results)
```

---

## Tests

```bash
# Test PyCollatinus
python3 test_pycollatinus.py

# Test XML Pages
python3 test_xml_integration.py
```

---

## Structure des fichiers

```
requirements.txt         → Liste des dépendances
setup.sh                 → Installation automatique
INSTALL.md               → Guide complet
QUICKSTART.md            → Ce guide
README_AMELIORATIONS.md  → Documentation Phase 1
GUIDE_XML_PAGES.md       → Documentation XML Pages
```

---

## Aide

**Problème d'import ?**
```bash
pip install -r requirements.txt
```

**PyCollatinus manquant ?**
```bash
cd /tmp && git clone https://github.com/PonteIneptique/collatinus-python.git
```

**Dictionnaire Du Cange manquant ?**
```bash
python3 download_ducange.py
```

---

Pour plus de détails : **INSTALL.md**
