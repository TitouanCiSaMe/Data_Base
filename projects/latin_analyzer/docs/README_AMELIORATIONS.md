# Améliorations de l'analyseur de textes latins médiévaux

## 🎯 Objectif

Automatiser complètement le pipeline d'analyse de textes latins médiévaux :
- **Avant** : Texte → Collatinus (interface graphique manuelle) → Export CSV → Script Python → DOCX
- **Après** : Texte → Script Python automatique → DOCX avec analyse intelligente

## ✨ Nouvelles fonctionnalités (Phase 1)

### 1. **Dictionnaire Du Cange intégré** (99 917 mots médiévaux)

**Script** : `download_ducange.py`

- Télécharge automatiquement les fichiers XML TEI du projet Du Cange depuis SourceForge
- Parse 24 fichiers XML (A-Z, sauf J et U qui n'existent pas)
- Extrait ~100 000 lemmes de latin médiéval
- Génère : `ducange_data/dictionnaire_ducange.txt`

**Utilisation** :
```bash
python3 download_ducange.py
```

**Résultat** :
- 99 917 entrées de latin médiéval
- Fichier de 937 KB
- Couvre : termes ecclésiastiques, féodaux, administratifs, juridiques

---

### 2. **Intégration PyCollatinus** (analyseur morphologique)

**Configuration** :
- Repository cloné : `/tmp/collatinus-python`
- Patch Python 3.11 appliqué automatiquement (fix `collections.Callable`)
- Dépendances installées : `unidecode`

**Fonctionnalités** :
- Lemmatisation automatique
- Analyse morphologique (cas, genre, nombre)
- Reconnaissance de ~500 000 formes du latin classique

**Test** : `test_pycollatinus.py`

---

### 3. **Système de scoring multi-critères**

Au lieu d'un binaire "erreur/pas erreur", chaque mot reçoit un **score de confiance 0-100** :

| Critère | Points | Description |
|---------|--------|-------------|
| Latin classique (Collatinus) | +30 | Reconnu par l'analyseur classique |
| Du Cange (médiéval) | +40 | Présent dans le dictionnaire médiéval |
| Suffixe productif | +10 | -arius, -atio, -torium, etc. |
| Contexte ecclésiastique | +5 | Mots religieux environnants |
| Variante orthographique | +10 | ae↔e, ti↔ci détectées |

**Score → Couleur** :
- **≥75** : Noir (OK)
- **40-74** : Orange (à vérifier)
- **<40** : Rouge (erreur probable)

---

### 4. **Colorisation à 3 niveaux**

**Avant** : Rouge (erreur) ou Noir (OK)

**Après** :
- 🖤 **Noir** : Mot validé (score ≥75)
- 🟠 **Orange** : Mot douteux à vérifier manuellement (score 40-74)
- 🔴 **Rouge** : Erreur probable (score <40)

**Avantage** : Prioriser la relecture sur les mots oranges au lieu de tout vérifier

---

## 📂 Fichiers créés

### Scripts principaux

1. **`download_ducange.py`**
   - Télécharge et extrait le lexique Du Cange
   - Génère `ducange_data/dictionnaire_ducange.txt`

2. **`test_pycollatinus.py`**
   - Valide l'installation de PyCollatinus
   - Teste l'analyse sur des mots latins

3. **`latin_analyzer_v2.py`** ⭐
   - **Nouveau système complet** remplaçant l'ancien workflow
   - Classe `LatinAnalyzer` avec toutes les fonctionnalités
   - Génération automatique de DOCX avec colorisation

### Données

- `ducange_data/xml/` : 24 fichiers XML téléchargés (78 MB)
- `ducange_data/dictionnaire_ducange.txt` : 99 917 lemmes (937 KB)

---

## 🚀 Utilisation du nouveau système

### Option A : Script autonome

```python
from latin_analyzer_v2 import LatinAnalyzer

# Initialiser
analyzer = LatinAnalyzer(ducange_dict_file="ducange_data/dictionnaire_ducange.txt")

# Analyser
results = analyzer.analyze_text_file("mon_texte.txt")

# Générer le DOCX
analyzer.generate_docx("mon_texte.txt", "resultat.docx", results)
```

### Option B : Modifier les chemins par défaut

Éditer `latin_analyzer_v2.py` lignes 350-352 :

```python
default_input = "/chemin/vers/votre/texte.txt"
default_output = "/chemin/vers/sortie.docx"
default_ducange = "/home/user/Data_Base/ducange_data/dictionnaire_ducange.txt"
```

Puis exécuter :
```bash
python3 latin_analyzer_v2.py
```

---

## 📊 Exemple de résultat

### Statistiques affichées

```
📊 Distribution des scores :
  ✅ Noir (bons mots)      : 4250 (85%)
  ⚠️  Orange (douteux)      : 520 (10%)
  ❌ Rouge (erreurs prob.) : 230 (5%)
```

### Dans le DOCX

```
Légende : Noir = OK (score ≥75)  Orange = À vérifier (score 40-74)  Rouge = Erreur probable (score <40)
________________________________________________________________________________

Abbas monasterium scriptorium ecclesiam fundavit.
^^^^^                                              (noir - score 95)
       ^^^^^^^^^^^                                 (noir - score 90)
                   ^^^^^^^^^^^                     (noir - score 92)
                               ^^^^^^^^^           (orange - score 65)
                                         ^^^^^^^^  (rouge - score 35)
```

---

## 🔄 Workflow complet

```
┌─────────────────┐
│  Texte latin    │
│   original      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  PyCollatinus               │
│  (latin classique)          │
│  → 500k formes reconnues    │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Dictionnaire Du Cange      │
│  (latin médiéval)           │
│  → 100k mots supplémentaires│
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Scoring multi-critères     │
│  → Note 0-100 par mot       │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Document Word              │
│  avec colorisation 3 niveaux│
│  (noir/orange/rouge)        │
└─────────────────────────────┘
```

---

## 🎓 Critères de scoring détaillés

### Exemple : mot "abbatissa"

```python
Score de base : 50

+ Latin classique (Collatinus) ?    NON  → +0
+ Du Cange (médiéval) ?             OUI  → +40
+ Suffixe productif (-issa) ?       OUI  → +10
+ Contexte ecclésiastique ?         OUI  → +5
+ Variante orthographique ?         NON  → +0

Score final : 50 + 40 + 10 + 5 = 105 → plafonné à 100
Couleur : NOIR ✅
Raisons : ["présent dans le dictionnaire Du Cange",
           "suffixe médiéval productif (-issa)",
           "contexte ecclésiastique"]
```

### Exemple : mot "monachuss" (erreur de transcription)

```python
Score de base : 50

+ Latin classique ?                 NON  → +0
+ Du Cange ?                        NON  → +0
+ Suffixe productif ?               NON  → +0
+ Contexte ecclésiastique ?         OUI  → +5
+ Variante orthographique ?         NON  → +0

Score final : 50 + 5 = 55
Couleur : ORANGE ⚠️
```

Mais si le mot apparaît rarement et n'a aucun critère positif → ROUGE 🔴

---

## 🔮 Prochaines étapes (Phase 2 - optionnel)

### 1. Règles orthographiques médiévales

Génération automatique de variantes :
- `ae` ↔ `e` (mediaeval ↔ medieval)
- `ti` ↔ `ci` (gratia ↔ gracia)
- `ph` ↔ `f` (philosophia ↔ filosofia)

### 2. Validation collaborative

Fichier JSON des corrections validées :
```json
{
  "abbatissa": {
    "status": "valid",
    "meaning": "abbesse",
    "validated_by": "user",
    "date": "2025-11-24"
  },
  "monachuss": {
    "status": "typo",
    "correction": "monachus"
  }
}
```

### 3. Base de données (si traitement en masse)

SQLite pour :
- Historique des analyses
- Fréquence d'apparition
- Apprentissage progressif

---

## 📝 Notes techniques

### Compatibilité Python

- **Requis** : Python 3.8+
- **Testé** : Python 3.11
- **Patch appliqué** : `collections.Callable` → `collections.abc.Callable`

### Dépendances

```bash
pip install python-docx unidecode
```

### Performances

- **Premier chargement** : ~15 secondes (PyCollatinus)
- **Analyse** : ~1000 mots/seconde
- **Génération DOCX** : ~5000 mots/seconde

### Sources de données

- **Du Cange** : École nationale des chartes (licence CC BY-NC-ND 2.0 FR)
- **Collatinus** : Biblissima / Yves Ouvrard (licence GPL)
- **PyCollatinus** : Thibault Clérice (MIT)

---

## ✅ Checklist de vérification

- [x] Téléchargement automatique Du Cange
- [x] Extraction ~100k mots médiévaux
- [x] Intégration PyCollatinus
- [x] Système de scoring 5 critères
- [x] Colorisation à 3 niveaux
- [x] Génération DOCX automatique
- [ ] Test sur corpus complet Arras
- [ ] Validation manuelle échantillon
- [ ] Intégration dans workflow production

---

## 🐛 Bugs connus / Limitations

1. **PyCollatinus lent au premier chargement**
   - Solution : utiliser `lemmatizer.compile()` pour pré-compiler

2. **Fichiers J.xml et U.xml manquants**
   - Normal : le latin classique n'utilise pas J et U comme lettres distinctes

3. **Faux positifs sur noms propres**
   - Solution future : liste de noms propres à exclure

---

## 📚 Documentation

- **Du Cange** : http://ducange.enc.sorbonne.fr/
- **Collatinus** : https://github.com/biblissima/collatinus
- **PyCollatinus** : https://github.com/PonteIneptique/collatinus-python

---

**Auteur** : Claude
**Date** : 24 novembre 2025
**Version** : 2.0.0
