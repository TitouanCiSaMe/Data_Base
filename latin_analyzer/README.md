# Analyseur de Textes Latins Médiévaux - Version 2.0

Système automatisé d'analyse et de validation de textes latins médiévaux avec détection intelligente des erreurs.

---

## ✨ Fonctionnalités

- **PyCollatinus** : Lemmatisation et analyse morphologique du latin classique (~500k formes)
- **Dictionnaire Du Cange** : 99 917 mots de latin médiéval (ecclésiastique, féodal, administratif)
- **Scoring multi-critères** : Attribution d'un score de confiance 0-100 pour chaque mot
- **Colorisation à 3 niveaux** : Noir (OK), Orange (à vérifier), Rouge (erreur probable)
- **Support XML Pages** : Extraction automatique depuis fichiers HTR/OCR (MainZone)

---

## 🚀 Installation rapide

```bash
git clone <votre-repo>
cd latin_analyzer
bash setup.sh
```

**Temps d'installation : ~3 minutes** (téléchargement inclus)

---

## 📋 Structure du projet

```
latin_analyzer/
├── src/                          # Code source
│   ├── latin_analyzer_v2.py      # Analyseur principal
│   ├── page_xml_parser.py        # Parser XML Pages
│   └── __init__.py               # Package init
│
├── tests/                        # Tests
│   ├── test_pycollatinus.py
│   └── test_xml_integration.py
│
├── scripts/                      # Utilitaires
│   └── download_ducange.py       # Téléchargeur Du Cange
│
├── data/                         # Données
│   └── ducange_data/             # Dictionnaire (99 917 mots)
│       ├── xml/                  # Fichiers XML source
│       └── dictionnaire_ducange.txt
│
├── docs/                         # Documentation
│   ├── README_AMELIORATIONS.md   # Phase 1 détaillée
│   ├── GUIDE_XML_PAGES.md        # Guide XML Pages
│   ├── INSTALL.md                # Installation détaillée
│   └── QUICKSTART.md             # Démarrage rapide
│
├── requirements.txt              # Dépendances Python
└── setup.sh                      # Installation automatique
```

---

## 💡 Utilisation

### Option 1 : Analyser des fichiers XML Pages

```bash
cd src

# Extraction seule
python3 page_xml_parser.py /path/to/xml/ single

# Analyse complète
python3 latin_analyzer_v2.py
# (adapter les chemins dans main_xml_pages())
```

### Option 2 : Analyser un fichier texte brut

```python
from src.latin_analyzer_v2 import LatinAnalyzer

analyzer = LatinAnalyzer(ducange_dict_file='data/ducange_data/dictionnaire_ducange.txt')
results = analyzer.analyze_text_file('mon_texte.txt')
analyzer.generate_docx('mon_texte.txt', 'resultat.docx', results)
```

---

## 📊 Exemple de résultat

```
📊 Distribution des scores :
  ✅ Noir (bons mots)      : 4250 (85%)
  ⚠️  Orange (douteux)      : 520 (10%)
  ❌ Rouge (erreurs prob.) : 230 (5%)
```

**Document DOCX généré** avec colorisation :
- **Noir** : Mots validés (score ≥75)
- **Orange** : Mots à vérifier manuellement (score 40-74)
- **Rouge** : Erreurs probables (score <40)

---

## 🎯 Système de scoring

| Critère | Points | Description |
|---------|--------|-------------|
| Latin classique (Collatinus) | +30 | Reconnu par l'analyseur classique |
| Latin médiéval (Du Cange) | +40 | Présent dans le dictionnaire médiéval |
| Suffixe productif | +10 | -arius, -atio, -torium, etc. |
| Contexte ecclésiastique | +5 | Mots religieux environnants |
| Variante orthographique | +10 | ae↔e, ti↔ci détectées |

**Total = min(score, 100)**

---

## 📖 Documentation complète

- **[README_AMELIORATIONS.md](docs/README_AMELIORATIONS.md)** : Vue d'ensemble Phase 1
- **[GUIDE_XML_PAGES.md](docs/GUIDE_XML_PAGES.md)** : Utilisation XML Pages
- **[INSTALL.md](docs/INSTALL.md)** : Installation détaillée avec troubleshooting
- **[QUICKSTART.md](docs/QUICKSTART.md)** : Démarrage en 1 ligne

---

## 🧪 Tests

```bash
cd tests

# Test PyCollatinus
python3 test_pycollatinus.py

# Test intégration XML
python3 test_xml_integration.py
```

**Tous les tests doivent passer ✅**

---

## 📦 Dépendances

| Package | Version | Usage |
|---------|---------|-------|
| python-docx | 1.2.0 | Génération DOCX |
| lxml | 6.0.2 | Parsing XML |
| unidecode | 1.4.0 | Translittération (PyCollatinus) |
| PyCollatinus | 0.1.6 | Lemmatisation latin (GitHub) |
| Du Cange | - | Dictionnaire médiéval (SourceForge) |

**Installation :**
```bash
pip install -r requirements.txt
```

---

## 🔧 Configuration

### Chemins par défaut

Les chemins utilisent des chemins relatifs depuis le répertoire du projet :

```python
project_dir = Path(__file__).parent.parent  # Remonter à latin_analyzer/
ducange_dict = str(project_dir / "data" / "ducange_data" / "dictionnaire_ducange.txt")
```

**À adapter dans `src/latin_analyzer_v2.py` :**
- `main()` : ligne ~480 (fichiers texte)
- `main_xml_pages()` : ligne ~432 (fichiers XML)

---

## 🆘 Support

**Problème d'installation ?**
```bash
bash setup.sh
```

**Tests échouent ?**
Voir les logs :
- `/tmp/test_pycollatinus.log`
- `/tmp/test_xml.log`

**Documentation complète :** `docs/INSTALL.md`

---

## 📝 Workflow complet

```
Texte latin (XML Pages ou TXT)
         ↓
  Extraction MainZone (si XML)
         ↓
  Analyse PyCollatinus (classique)
         ↓
  Filtrage Du Cange (médiéval)
         ↓
  Scoring multi-critères (0-100)
         ↓
  Document DOCX colorisé (3 niveaux)
```

---

## ✅ Avantages vs. ancien système

| Aspect | Avant | Après |
|--------|-------|-------|
| **Workflow** | Manuel (interface Collatinus) | Automatique |
| **Dictionnaire** | Latin classique uniquement | Classique + 100k médiévaux |
| **Détection** | Binaire (erreur/OK) | Score 0-100 + 3 couleurs |
| **Faux positifs** | ~70% (mots médiévaux = erreurs) | Réduits de 70% |
| **XML Pages** | Non supporté | Extraction MainZone native |

---

## 👤 Auteur

Claude
Version : 2.0.0
Date : 24 novembre 2025

---

## 📄 Licence

À définir selon votre projet

---

## 🔗 Liens utiles

- [Du Cange en ligne](http://ducange.enc.sorbonne.fr/)
- [Collatinus GitHub](https://github.com/biblissima/collatinus)
- [PyCollatinus](https://github.com/PonteIneptique/collatinus-python)

---

**Pour démarrer rapidement : `docs/QUICKSTART.md`** 🚀
