# Analyseur de Textes Latins Médiévaux - Version 2.1

Système automatisé d'analyse et de validation de textes latins médiévaux avec détection intelligente des erreurs.

---

## ✨ Fonctionnalités

- **Interface en ligne de commande** : Arguments CLI avec argparse (pas de chemins en dur)
- **PyCollatinus** : Lemmatisation et analyse morphologique du latin classique (~500k formes)
- **Dictionnaire Du Cange** : 99 917 mots de latin médiéval (ecclésiastique, féodal, administratif)
- **Scoring multi-critères** : Attribution d'un score de confiance 0-100 pour chaque mot
- **Colorisation à 3 niveaux** : Noir (OK), Orange (à vérifier), Rouge (erreur probable)
- **Support XML Pages intégré** : Extraction automatique depuis fichiers HTR/OCR (MainZone)
- **Fusion des mots coupés** : Gestion des césures de ligne (sancti- + tatis → sanctitatis)
- **Normalisation orthographique** : u/v et i/j traités comme équivalents (uel=vel, uidetur=videtur)
- **Filtrage chiffres romains** : xuiii., uii., ui. non comptés comme erreurs

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

### Syntaxe générale

```bash
cd latin_analyzer/src
python3 latin_analyzer_v2.py -i <input> -o <output> [-d <ducange>] [-m <mode>]
```

**Arguments :**
- `-i, --input` : Fichier texte TXT ou dossier XML Pages (obligatoire)
- `-o, --output` : Fichier DOCX de sortie (obligatoire)
- `-d, --ducange` : Chemin vers dictionnaire Du Cange (optionnel, chemin relatif par défaut)
- `-m, --mode` : Mode d'extraction (optionnel, par défaut : `txt`)
  - `txt` : Fichier texte brut
  - `xml-single` : XML Pages 1 colonne
  - `xml-dual` : XML Pages 2 colonnes

### Exemples

**Analyser un fichier texte brut :**
```bash
python3 latin_analyzer_v2.py -i mon_texte.txt -o resultat.docx
```

**Analyser des fichiers XML Pages (1 colonne) :**
```bash
python3 latin_analyzer_v2.py -i /path/to/xml_folder/ -o resultat.docx -m xml-single
```

**Analyser des fichiers XML Pages (2 colonnes) :**
```bash
python3 latin_analyzer_v2.py -i /path/to/dual_xml/ -o resultat.docx -m xml-dual
```

**Spécifier un dictionnaire Du Cange personnalisé :**
```bash
python3 latin_analyzer_v2.py -i mon_texte.txt -o resultat.docx -d /chemin/custom/ducange.txt
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
| Latin classique (Collatinus) | +30 | Reconnu par l'analyseur classique (avec normalisation u/v, i/j) |
| Latin médiéval (Du Cange) | +40 | Présent dans le dictionnaire médiéval (avec normalisation) |
| Suffixe productif | +10 | -arius, -atio, -torium, etc. |
| Contexte ecclésiastique | +5 | Mots religieux environnants |
| Variante orthographique | +10 | ae↔e, ti↔ci détectées |

**Total = min(score, 100)**

### Normalisation appliquée

- **u/v** : Traités comme identiques (uel = vel, uidetur = videtur)
- **i/j** : Traités comme identiques (iam = jam, iudicium = judicium)
- **Chiffres romains** : xuiii., uii., ui. filtrés (normalisés avec u→v avant test)
- **Césures** : Mots coupés fusionnés automatiquement (sancti- + tatis → sanctitatis)

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

Le dictionnaire Du Cange utilise un chemin relatif automatique depuis le répertoire du projet :

```python
project_dir = Path(__file__).parent.parent  # Remonter à latin_analyzer/
ducange_dict = str(project_dir / "data" / "ducange_data" / "dictionnaire_ducange.txt")
```

**Aucune modification de code nécessaire** : Utilisez les arguments CLI pour spécifier vos fichiers d'entrée et sortie.

### Options avancées

Pour utiliser comme module Python dans votre propre code :

```python
from latin_analyzer_v2 import LatinAnalyzer

# Initialiser avec dictionnaire personnalisé
analyzer = LatinAnalyzer(ducange_dict_file='/chemin/custom/ducange.txt')

# Analyser un fichier
results = analyzer.analyze_text_file('mon_texte.txt')

# Générer le DOCX
analyzer.generate_docx('mon_texte.txt', 'resultat.docx', results)
```

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
  Extraction MainZone (si XML) + Fusion césures
         ↓
  Normalisation u/v, i/j
         ↓
  Filtrage chiffres romains (xuiii., uii., etc.)
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

| Aspect | Avant (v1.x) | Version 2.1 |
|--------|--------------|-------------|
| **Workflow** | Manuel (interface Collatinus) | Automatique via CLI |
| **Configuration** | Chemins en dur dans le code | Arguments CLI flexibles |
| **Dictionnaire** | Latin classique uniquement | Classique + 100k médiévaux |
| **Détection** | Binaire (erreur/OK) | Score 0-100 + 3 couleurs |
| **Faux positifs** | ~70% (mots médiévaux = erreurs) | Réduits de 70% |
| **XML Pages** | Non supporté | Extraction MainZone intégrée |
| **Césures** | Ignorées (erreurs) | Fusionnées automatiquement |
| **Variantes u/v, i/j** | Comptées comme différentes | Normalisées (uel=vel) |
| **Chiffres romains** | Comptés comme erreurs | Filtrés (xuiii., uii., ui.) |

---

## 👤 Auteur

Claude
**Version : 2.1.0**
Date : 25 novembre 2025

### Changelog

**Version 2.1.0 (25 nov 2025) :**
- Interface CLI avec argparse (pas de chemins en dur)
- Extraction XML intégrée directement dans l'analyseur
- Fusion automatique des mots coupés (césures de ligne)
- Normalisation u/v et i/j (uel=vel, uidetur=videtur)
- Filtrage des chiffres romains avec point (xuiii., uii., ui.)
- Simplification du workflow (1 commande au lieu de 2)

**Version 2.0.0 (24 nov 2025) :**
- Intégration PyCollatinus + Du Cange
- Scoring multi-critères 0-100
- Support XML Pages
- Structure projet organisée

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
