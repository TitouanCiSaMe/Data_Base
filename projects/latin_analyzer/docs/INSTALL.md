# Guide d'installation - Analyseur de textes latins médiévaux

## 📋 Prérequis

- **Python 3.8+** (testé sur Python 3.11)
- **pip** (gestionnaire de packages Python)
- **git** (pour cloner PyCollatinus)

---

## 🚀 Installation rapide

### 1. Installer les bibliothèques Python

```bash
cd /home/user/Data_Base

# Installer toutes les dépendances
pip install -r requirements.txt
```

**Ou manuellement :**
```bash
pip install python-docx==1.2.0
pip install lxml==6.0.2
pip install unidecode==1.4.0
```

---

### 2. Installer PyCollatinus (depuis GitHub)

⚠️ **PyCollatinus via pip est cassé**, il faut le cloner :

```bash
cd /tmp
git clone https://github.com/PonteIneptique/collatinus-python.git

# Fix pour Python 3.11+
sed -i 's/from collections import OrderedDict, Callable/from collections import OrderedDict\nfrom collections.abc import Callable/' \
    /tmp/collatinus-python/pycollatinus/util.py
```

**Le code l'utilisera via** :
```python
sys.path.insert(0, '/tmp/collatinus-python')
from pycollatinus import Lemmatiseur
```

---

### 3. Télécharger le dictionnaire Du Cange (optionnel)

Si tu n'as pas encore le dictionnaire :

```bash
cd /home/user/Data_Base
python3 download_ducange.py
```

Cela va :
- Télécharger 24 fichiers XML (78 MB)
- Extraire 99 917 mots de latin médiéval
- Créer `ducange_data/dictionnaire_ducange.txt`

---

## ✅ Vérifier l'installation

### Test 1 : Bibliothèques Python

```bash
python3 -c "import docx; import lxml; import unidecode; print('✅ Toutes les libs sont OK')"
```

**Sortie attendue :**
```
✅ Toutes les libs sont OK
```

---

### Test 2 : PyCollatinus

```bash
python3 test_pycollatinus.py
```

**Sortie attendue :**
```
============================================================
  TEST DE PYCOLLATINUS
============================================================

1️⃣  Import de PyCollatinus...
✅ Import réussi

2️⃣  Initialisation du lemmatiseur...
✅ Lemmatiseur initialisé

3️⃣  Test sur une phrase simple...
✅ abbas         → reconnu (3 analyse(s))
✅ monachus      → reconnu (2 analyse(s))
✅ scriptorium   → reconnu (7 analyse(s))

============================================================
✅ PyCollatinus fonctionne correctement !
============================================================
```

---

### Test 3 : Intégration XML Pages

```bash
python3 test_xml_integration.py
```

**Sortie attendue :**
```
============================================================
  TEST D'INTÉGRATION XML PAGES
============================================================

✅ page_xml_parser importé
✅ latin_analyzer_v2 importé
✅ Parsing réussi
✅ Mode dual fonctionne

============================================================
✅ TOUS LES TESTS PASSÉS !
============================================================
```

---

## 🐛 Résolution de problèmes

### Erreur : `No module named 'docx'`

```bash
pip install python-docx
```

---

### Erreur : `No module named 'unidecode'`

```bash
pip install unidecode
```

---

### Erreur : `cannot import name 'Callable' from 'collections'`

C'est un problème de compatibilité Python 3.11+. Appliquer le patch :

```bash
sed -i 's/from collections import OrderedDict, Callable/from collections import OrderedDict\nfrom collections.abc import Callable/' \
    /tmp/collatinus-python/pycollatinus/util.py
```

---

### Erreur : `prefix 'xml' not found in prefix map` (Du Cange)

Le namespace XML n'est pas déclaré. Le script `download_ducange.py` gère déjà ce problème (ligne 93-96).

Si tu as encore l'erreur, vérifie que tu as bien la dernière version.

---

### PyCollatinus très lent au premier chargement

**Normal !** Le premier chargement prend 10-15 secondes.

Pour l'optimiser :
```python
lemmatizer = Lemmatiseur()
lemmatizer.compile()  # Crée un cache pré-compilé
```

---

## 📦 Structure finale après installation

```
Data_Base/
├── requirements.txt                    # Dépendances Python
├── INSTALL.md                          # Ce guide
│
├── download_ducange.py                 # Téléchargeur Du Cange
├── ducange_data/
│   ├── xml/                           # 24 fichiers XML (78 MB)
│   └── dictionnaire_ducange.txt       # 99 917 mots (937 KB)
│
├── page_xml_parser.py                  # Parser XML Pages
├── latin_analyzer_v2.py                # Analyseur principal
│
├── test_pycollatinus.py                # Tests PyCollatinus
├── test_xml_integration.py             # Tests intégration
│
└── /tmp/collatinus-python/             # PyCollatinus (cloné)
    └── pycollatinus/
```

---

## 🌐 Environnement virtuel (recommandé)

Pour isoler les dépendances :

```bash
# Créer un venv
python3 -m venv venv_latin

# Activer
source venv_latin/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Cloner PyCollatinus
cd /tmp
git clone https://github.com/PonteIneptique/collatinus-python.git
sed -i 's/from collections import OrderedDict, Callable/from collections import OrderedDict\nfrom collections.abc import Callable/' \
    /tmp/collatinus-python/pycollatinus/util.py
```

**Utilisation ensuite :**
```bash
source venv_latin/bin/activate
python3 latin_analyzer_v2.py
```

---

## 📚 Versions testées

| Package | Version | Python |
|---------|---------|--------|
| python-docx | 1.2.0 | 3.11 |
| lxml | 6.0.2 | 3.11 |
| unidecode | 1.4.0 | 3.11 |
| PyCollatinus | 0.1.6 (GitHub) | 3.11 |

---

## 🆘 Support

Si tu rencontres d'autres problèmes :

1. Vérifie la version de Python : `python3 --version` (≥ 3.8)
2. Vérifie les installations : `pip list | grep -E "docx|lxml|unidecode"`
3. Lance tous les tests : `python3 test_pycollatinus.py && python3 test_xml_integration.py`

---

**Auteur** : Claude
**Date** : 24 novembre 2025
**Version** : 2.0.0
