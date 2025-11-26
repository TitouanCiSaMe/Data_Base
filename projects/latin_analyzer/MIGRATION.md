# Migration vers la structure organisée

## 🔄 Qu'est-ce qui a changé ?

Tous les fichiers de l'analyseur latin ont été réorganisés dans une structure propre et modulaire.

---

## 📂 Ancienne structure (racine désordonnée)

```
Data_Base/
├── latin_analyzer_v2.py          ❌ Racine encombrée
├── page_xml_parser.py             ❌
├── download_ducange.py            ❌
├── test_pycollatinus.py           ❌
├── test_xml_integration.py        ❌
├── README_AMELIORATIONS.md        ❌
├── GUIDE_XML_PAGES.md             ❌
├── INSTALL.md                     ❌
├── QUICKSTART.md                  ❌
├── requirements.txt               ❌
├── setup.sh                       ❌
├── ducange_data/                  ❌
└── ... (autres fichiers du projet)
```

---

## ✅ Nouvelle structure (organisée)

```
Data_Base/
├── latin_analyzer/               ✅ Dossier dédié
│   ├── README.md                 ✅ Documentation principale
│   ├── requirements.txt          ✅ Dépendances
│   ├── setup.sh                  ✅ Installation
│   ├── .gitignore                ✅ Ignores Python
│   │
│   ├── src/                      ✅ Code source
│   │   ├── __init__.py
│   │   ├── latin_analyzer_v2.py
│   │   └── page_xml_parser.py
│   │
│   ├── tests/                    ✅ Tests
│   │   ├── test_pycollatinus.py
│   │   └── test_xml_integration.py
│   │
│   ├── scripts/                  ✅ Utilitaires
│   │   └── download_ducange.py
│   │
│   ├── data/                     ✅ Données
│   │   └── ducange_data/
│   │       ├── xml/
│   │       └── dictionnaire_ducange.txt
│   │
│   └── docs/                     ✅ Documentation
│       ├── README_AMELIORATIONS.md
│       ├── GUIDE_XML_PAGES.md
│       ├── INSTALL.md
│       └── QUICKSTART.md
│
└── ... (autres fichiers du projet - non touchés)
```

---

## 🔧 Changements dans le code

### 1. Imports mis à jour

**Avant :**
```python
from page_xml_parser import PageXMLParser
```

**Après :**
```python
# Import local si exécuté comme script, sinon import relatif
try:
    from page_xml_parser import PageXMLParser
except ImportError:
    from .page_xml_parser import PageXMLParser
```

---

### 2. Chemins relatifs

**Avant (chemins en dur) :**
```python
ducange_dict = "/home/user/Data_Base/ducange_data/dictionnaire_ducange.txt"
```

**Après (chemins relatifs) :**
```python
project_dir = Path(__file__).parent.parent  # Remonter à latin_analyzer/
ducange_dict = str(project_dir / "data" / "ducange_data" / "dictionnaire_ducange.txt")
```

---

### 3. Tests mis à jour

**Les tests ajoutent automatiquement `src/` au path :**
```python
from pathlib import Path

src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, '/tmp/collatinus-python')
```

---

## 🚀 Utilisation après migration

### Installation

```bash
cd latin_analyzer
bash setup.sh
```

### Exécution

**Option A : Depuis `src/`**
```bash
cd latin_analyzer/src
python3 latin_analyzer_v2.py
```

**Option B : Comme module Python**
```python
import sys
sys.path.insert(0, '/path/to/latin_analyzer/src')

from latin_analyzer_v2 import LatinAnalyzer
```

### Tests

```bash
cd latin_analyzer/tests
python3 test_xml_integration.py
```

---

## ✅ Avantages de la nouvelle structure

| Aspect | Avant | Après |
|--------|-------|-------|
| **Organisation** | 15+ fichiers à la racine | Dossier dédié organisé |
| **Clarté** | Mélangé avec autres projets | Séparation claire |
| **Imports** | Chemins absolus | Chemins relatifs |
| **Tests** | Dispersés | Dossier `tests/` |
| **Documentation** | Éparpillée | Dossier `docs/` |
| **Maintenance** | Difficile | Facile |
| **Distribution** | Impossible | `zip latin_analyzer/` |

---

## 📦 Pour déployer sur une autre machine

**Avant :** Copier 15+ fichiers manuellement

**Après :**
```bash
# Cloner juste le dossier latin_analyzer
git clone <repo>
cd latin_analyzer
bash setup.sh
```

---

## ⚠️ Points d'attention

### 1. Chemins des fichiers à analyser

**Avant :**
```python
default_input = "/home/titouan/Téléchargements/Arras/resultats/synthese_arborescence.txt"
```

**Après (inchangé) :**
```python
# Les fichiers d'entrée restent où ils étaient
# Seule la structure interne du projet a changé
default_input = "/home/titouan/Téléchargements/Arras/resultats/synthese_arborescence.txt"
```

### 2. Dictionnaire Du Cange

**Avant :**
```
/home/user/Data_Base/ducange_data/
```

**Après :**
```
/home/user/Data_Base/latin_analyzer/data/ducange_data/
```

**Le code utilise maintenant des chemins relatifs automatiques.**

---

## 🧪 Vérification

**Tous les tests doivent passer :**
```bash
cd latin_analyzer/tests
python3 test_pycollatinus.py      # ✅
python3 test_xml_integration.py   # ✅
```

---

## 📝 Fichiers supprimés de la racine

Ces fichiers ont été **déplacés** (pas supprimés) :

- ✅ `latin_analyzer_v2.py` → `latin_analyzer/src/`
- ✅ `page_xml_parser.py` → `latin_analyzer/src/`
- ✅ `download_ducange.py` → `latin_analyzer/scripts/`
- ✅ `test_*.py` → `latin_analyzer/tests/`
- ✅ `README_AMELIORATIONS.md` → `latin_analyzer/docs/`
- ✅ `GUIDE_XML_PAGES.md` → `latin_analyzer/docs/`
- ✅ `INSTALL.md` → `latin_analyzer/docs/`
- ✅ `QUICKSTART.md` → `latin_analyzer/docs/`
- ✅ `requirements.txt` → `latin_analyzer/`
- ✅ `setup.sh` → `latin_analyzer/`
- ✅ `ducange_data/` → `latin_analyzer/data/`

---

## 🎯 Prochaines étapes

1. ✅ Tester l'installation : `bash setup.sh`
2. ✅ Vérifier les tests : `python3 test_xml_integration.py`
3. ✅ Commiter la nouvelle structure : `git add latin_analyzer/`
4. ✅ Supprimer les anciens fichiers du commit : `git rm <fichiers>`
5. ✅ Pusher : `git push`

---

**Migration effectuée le :** 24 novembre 2025
**Structure validée :** ✅ Tous les tests passent
