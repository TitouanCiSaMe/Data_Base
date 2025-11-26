# Guide d'utilisation : Analyse de fichiers XML Pages

## 🎯 Objectif

Ce guide explique comment utiliser l'analyseur latin V2 avec des **fichiers XML Pages** (format standard HTR/OCR).

L'extraction du texte utilise **exactement la même logique** que `xml_corpus_processor.py` pour garantir la cohérence entre :
- Le pipeline NoSketch (format vertical)
- L'analyse de texte latin médiéval

---

## 📋 Prérequis

Les fichiers doivent être au format **PAGE XML** avec la structure :
```xml
<TextRegion custom="structure {type:MainZone;}">
  <TextLine>
    <TextEquiv>
      <Unicode>abbas monachus scriptorium</Unicode>
    </TextEquiv>
  </TextLine>
</TextRegion>
```

**Modes supportés** :
- **Single** : `MainZone` unique par fichier (1 fichier = 1 page)
- **Dual** : `MainZone:column#1` et `MainZone:column#2` (1 fichier = 2 colonnes)

---

## 🚀 Utilisation rapide

### Option 1 : Ligne de commande (extraction seule)

```bash
# Extraire le texte d'un seul fichier XML
python3 page_xml_parser.py fichier.xml single

# Extraire le texte d'un dossier (mode single)
python3 page_xml_parser.py /chemin/vers/dossier/ single

# Extraire le texte d'un dossier (mode dual - 2 colonnes)
python3 page_xml_parser.py /chemin/vers/dossier/ dual
```

---

### Option 2 : Analyse complète avec colorisation

**Script Python** :

```python
from latin_analyzer_v2 import LatinAnalyzer
from page_xml_parser import PageXMLParser

# Configuration
xml_folder = "/path/to/xml_pages"
output_docx = "/path/to/resultat.docx"
column_mode = 'single'  # ou 'dual'
ducange_dict = "/home/user/Data_Base/ducange_data/dictionnaire_ducange.txt"

# Initialiser l'analyseur
analyzer = LatinAnalyzer(ducange_dict_file=ducange_dict)

# Analyser (extraction MainZone automatique)
results = analyzer.analyze_page_xml(xml_folder, column_mode=column_mode)

# Récupérer les lignes pour le DOCX
parser = PageXMLParser(column_mode=column_mode)
text, metadata = parser.parse_folder(xml_folder)
lines = text.split('\n')

# Générer le document Word colorisé
analyzer.generate_docx(lines, output_docx, results)
```

---

## 📁 Structure de vos fichiers

### Cas 1 : Fichiers séparés (single)

```
corpus/
├── page_001.xml  → MainZone unique
├── page_002.xml  → MainZone unique
├── page_003.xml  → MainZone unique
└── ...
```

**Commande** :
```bash
python3 page_xml_parser.py corpus/ single
```

---

### Cas 2 : Double colonne (dual)

```
corpus_dual/
├── folio_01.xml  → MainZone:column#1 + MainZone:column#2
├── folio_02.xml  → MainZone:column#1 + MainZone:column#2
└── ...
```

**Commande** :
```bash
python3 page_xml_parser.py corpus_dual/ dual
```

---

## 🔧 Adapter latin_analyzer_v2.py

Éditer la fonction `main_xml_pages()` (ligne ~424) :

```python
def main_xml_pages():
    # ⚙️  ADAPTER CES CHEMINS ⚙️
    xml_input = "/home/votre_user/vos_fichiers_xml"
    output_docx = "/home/votre_user/resultat_analyse.docx"
    column_mode = 'single'  # ou 'dual'
    ducange_dict = "/home/user/Data_Base/ducange_data/dictionnaire_ducange.txt"

    # Le reste du code reste identique
    # ...
```

Puis exécuter :
```python
if __name__ == "__main__":
    sys.exit(main_xml_pages())  # ← Appeler main_xml_pages au lieu de main
```

---

## 📊 Exemple de workflow complet

### Étape 1 : Vérifier l'extraction

```bash
# Tester sur un fichier
python3 page_xml_parser.py corpus/page_001.xml single

# Output attendu :
# 📄 Fichier : page_001.xml
# 📄 Page : 1
# 📄 Titre courant : Decretum Gratiani
# 📄 Lignes extraites : 42
# ============================================================
# abbas monachus scriptorium
# ecclesiam fundavit anno domini
# ...
```

---

### Étape 2 : Analyser avec colorisation

```python
from latin_analyzer_v2 import LatinAnalyzer
from page_xml_parser import PageXMLParser

# Init
analyzer = LatinAnalyzer(ducange_dict_file="ducange_data/dictionnaire_ducange.txt")

# Analyser
results = analyzer.analyze_page_xml("corpus/", column_mode='single')

# Output :
# 📂 Traitement de 50 fichiers XML...
# ✅ 2150 lignes extraites de 50 fichiers
# 🔍 Analyse en cours...
# ✅ Analyse terminée : 12350 mots traités
#
# 📊 Distribution des scores :
#   ✅ Noir (bons mots)      : 10500 (85%)
#   ⚠️  Orange (douteux)      : 1200 (10%)
#   ❌ Rouge (erreurs prob.) : 650 (5%)
```

---

### Étape 3 : Générer le DOCX

```python
# Récupérer les lignes originales
parser = PageXMLParser(column_mode='single')
text, metadata = parser.parse_folder("corpus/")
lines = text.split('\n')

# Générer avec colorisation
analyzer.generate_docx(lines, "resultat.docx", results)

# Output :
# 📝 Génération du document Word...
# ✅ Document créé : resultat.docx
```

---

## 🎨 Résultat dans le DOCX

```
Légende : Noir = OK  Orange = À vérifier  Rouge = Erreur probable
________________________________________________________________________________

Abbas monasterium scriptorium ecclesiam fundavit.
^^^^^             ^^^^^^^^^^^                        (noir)
       ^^^^^^^^^^                                    (noir)
                               ^^^^^^^^               (orange - à vérifier)
                                        ^^^^^^^       (rouge - erreur probable)
```

---

## 🔄 Correspondance avec xml_corpus_processor.py

| Élément | xml_corpus_processor | page_xml_parser | Identique ? |
|---------|---------------------|----------------|-------------|
| XPath MainZone | `TextRegion[@custom='structure {type:MainZone;}']` | Idem | ✅ |
| XPath Dual col1 | `MainZone:column#1` | Idem | ✅ |
| XPath Dual col2 | `MainZone:column#2` | Idem | ✅ |
| Extraction TextLine | `.//TextLine` | Idem | ✅ |
| Extraction texte | `.//TextEquiv/Unicode` | Idem | ✅ |
| Nettoyage namespace | `_remove_xml_namespaces()` | `_remove_namespaces()` | ✅ |
| Running title | `RunningTitleZone` | Idem | ✅ |
| Page numbering | `NumberingZone` | Idem | ✅ |

**Garantie** : Le texte extrait est **identique** entre les deux systèmes.

---

## 🛠️ Options avancées

### Conserver les métadonnées de page

```python
parser = PageXMLParser(column_mode='single')
text, metadata_list = parser.parse_folder("corpus/")

for meta in metadata_list:
    print(f"Page {meta['page_number']} : {meta['running_title']}")
    print(f"  Fichier : {meta['filename']}")
```

---

### Traiter un seul fichier

```python
parser = PageXMLParser(column_mode='single')
lines, metadata = parser.parse_file("corpus/page_042.xml")

print(f"Page {metadata['page_number']} : {len(lines)} lignes")
print('\n'.join(lines))
```

---

### Mode dual avec traitement séparé des colonnes

```python
from page_xml_parser import PageXMLParser
import xml.etree.ElementTree as ET

# Parser manuel pour accès colonne par colonne
tree = ET.parse("folio.xml")
root = tree.getroot()

# ... extraire col1 et col2 séparément si besoin
```

---

## ❓ FAQ

### Q1 : Mes fichiers n'ont pas de MainZone, que faire ?

**R** : Vérifiez l'attribut `custom` de vos `TextRegion`. S'il est différent (ex: `type:TextZone`), modifiez les XPath dans `page_xml_parser.py` ligne 162 :

```python
main_zone = root.find(
    ".//TextRegion[@custom='structure {type:VotreTypeIci;}']"
)
```

---

### Q2 : J'ai un mix de pages single et dual ?

**R** : Séparez-les dans deux dossiers :
```bash
corpus_single/  → analyser avec mode='single'
corpus_dual/    → analyser avec mode='dual'
```

Puis fusionnez les résultats.

---

### Q3 : Comment tester rapidement l'extraction ?

**R** : Utilisez le mode standalone :
```bash
python3 page_xml_parser.py mon_fichier.xml single | head -20
```

Vous devriez voir le texte brut extrait des MainZone.

---

### Q4 : Ça plante avec "prefix 'xml' not found" ?

**R** : Problème de namespace. Vérifiez que votre XML a bien :
```xml
<PcGts xmlns="http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15">
```

Le parser nettoie automatiquement les namespaces.

---

## 📚 Fichiers liés

- **`page_xml_parser.py`** : Module d'extraction (standalone)
- **`latin_analyzer_v2.py`** : Système complet d'analyse
- **`xml_corpus_processor.py`** : Processeur NoSketch (référence)

---

## ✅ Checklist de vérification

- [ ] Mes fichiers XML ont des `MainZone` (ou `MainZone:column#1/2`)
- [ ] J'ai testé l'extraction sur 1 fichier avec `page_xml_parser.py`
- [ ] Le texte extrait correspond à ce que j'attends
- [ ] J'ai adapté `column_mode` selon ma structure (single/dual)
- [ ] Les chemins dans `main_xml_pages()` pointent vers mes fichiers
- [ ] Le dictionnaire Du Cange est présent (`ducange_data/dictionnaire_ducange.txt`)

---

**Auteur** : Claude
**Date** : 24 novembre 2025
**Version** : 2.0.0
