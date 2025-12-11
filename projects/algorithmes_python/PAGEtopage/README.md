# PAGEtopage - Guide d'utilisation

## Qu'est-ce que PAGEtopage ?

**PAGEtopage** est un outil qui transforme vos fichiers XML (issus de la transcription automatique HTR/OCR, par exemple avec Transkribus ou eScriptorium) en fichiers texte exploitables, avec annotations linguistiques (lemmes, parties du discours).

### Le pipeline en 3 étapes

```
Fichiers XML PAGE     →     Format Vertical     →     Fichiers Texte
   (HTR/OCR)              (annoté/lemmatisé)         (exploitables)

   ÉTAPE 1                    ÉTAPE 2                   ÉTAPE 3
   extract                    enrich                    export
```

---

## Prérequis

### 1. Installer Python

**Windows :**
1. Allez sur https://www.python.org/downloads/
2. Téléchargez Python 3.10 ou plus récent
3. Lancez l'installateur
4. **IMPORTANT** : Cochez la case "Add Python to PATH" avant de cliquer sur "Install"

**Mac :**
1. Ouvrez le Terminal (Applications → Utilitaires → Terminal)
2. Tapez : `python3 --version`
3. Si Python n'est pas installé, le système vous proposera de l'installer

**Linux :**
Python est généralement pré-installé. Vérifiez avec : `python3 --version`

### 2. Installer les dépendances

Ouvrez un terminal (ou "Invite de commandes" sur Windows) et tapez :

```bash
pip install pyyaml treetaggerwrapper
```

> **Note** : Sur Mac/Linux, utilisez `pip3` au lieu de `pip` si la commande ne fonctionne pas.

**TreeTagger s'installe automatiquement !**
TreeTagger (outil de lemmatisation rapide) sera téléchargé et installé automatiquement lors de la première utilisation. Pas besoin de configuration manuelle !

---

## Installation de PAGEtopage

### Option A : Téléchargement direct

1. Téléchargez le dossier `PAGEtopage` depuis le dépôt GitHub
2. Placez-le dans un dossier de votre choix (par exemple `C:\Mes_Projets\` ou `~/Projets/`)

### Option B : Cloner le dépôt (si vous avez Git)

```bash
git clone https://github.com/TitouanCiSaMe/Data_Base.git
cd Data_Base/projects/algorithmes_python
```

---

## Préparation de vos fichiers

### Structure recommandée

Créez un dossier de travail avec cette structure :

```
mon_projet/
├── xml_pages/              ← Mettez vos fichiers XML ici
│   ├── 0001.xml
│   ├── 0002.xml
│   └── ...
├── config.yaml             ← Fichier de configuration (voir ci-dessous)
└── output/                 ← Les résultats apparaîtront ici
```

### Créer le fichier de configuration

Créez un fichier `config.yaml` avec un éditeur de texte (Notepad, TextEdit, VS Code...) :

```yaml
# === MÉTADONNÉES DE VOTRE CORPUS ===
# Ces informations apparaîtront dans chaque page du corpus

corpus:
  edition_id: "Mon-Edition-001"           # Identifiant unique
  title: "Titre de votre manuscrit"       # Titre du document
  language: "Latin"                        # Langue (Latin, French, etc.)
  author: "Nom de l'auteur"               # Auteur
  source: "Source du manuscrit"           # Source
  type: "Type de document"                # Genre (Droit, Théologie, etc.)
  date: "1200"                            # Date approximative
  lieu: "France"                          # Lieu d'origine
  ville: "Paris"                          # Ville

# === PAGINATION ===
pagination:
  starting_page_number: 1                 # Numéro de la première page

# === EXTRACTION (Étape 1) ===
extraction:
  column_mode: single                     # "single" ou "dual" (2 colonnes)
  merge_hyphenated: true                  # Fusionner les mots coupés (re-/constituer)

# === ENRICHISSEMENT (Étape 2) ===
enrichment:
  lemmatizer: treetagger                  # Lemmatiseur pour le latin (rapide, auto-installé)
  language: lat                           # Code langue (lat = latin)

# === EXPORT (Étape 3) ===
export:
  format: scholarly                       # "scholarly" (recommandé), "clean", "diplomatic" ou "annotated"
  generate_index: true                    # Créer un fichier d'index JSON
  generate_combined: true                 # Créer un fichier texte complet
```

---

## Utilisation

### Ouvrir un terminal dans votre dossier de travail

**Windows :**
1. Ouvrez l'Explorateur de fichiers
2. Naviguez jusqu'au dossier contenant PAGEtopage
3. Cliquez dans la barre d'adresse et tapez `cmd`, puis Entrée

**Mac :**
1. Ouvrez le Terminal
2. Tapez `cd ` (avec un espace) puis glissez-déposez votre dossier dans le terminal
3. Appuyez sur Entrée

**Linux :**
1. Clic droit dans le dossier → "Ouvrir dans un terminal"

---

### Méthode 1 : Pipeline complet (recommandé pour débuter)

Une seule commande pour tout faire :

```bash
python -m PAGEtopage run --input ./xml_pages/ --output ./output/ --config config.yaml
```

**Explication :**
- `python -m PAGEtopage run` : Lance le pipeline complet
- `--input ./xml_pages/` : Dossier contenant vos fichiers XML
- `--output ./output/` : Dossier où seront créés les résultats
- `--config config.yaml` : Votre fichier de configuration

**Résultat :** Le dossier `output/` contiendra :
```
output/
├── corpus.vertical.txt     ← Corpus annoté complet
├── pages/                  ← Un fichier texte par page
│   ├── page_0001_0001.txt
│   ├── page_0002_0002.txt
│   └── ...
├── pages_index.json        ← Index des pages (métadonnées)
├── texte_complet.txt       ← Tout le texte en un fichier
├── corpus_stats.json       ← Statistiques du corpus
└── images_mapping.txt      ← Correspondance images/pages
```

---

### Méthode 2 : Étapes séparées (pour plus de contrôle)

#### Étape 1 : Extraction des XML

```bash
python -m PAGEtopage extract --input ./xml_pages/ --output ./extracted.json
```

Cette commande :
- Lit tous vos fichiers XML
- Extrait le texte de la zone principale (MainZone)
- Fusionne les mots coupés en fin de ligne
- Crée un fichier JSON intermédiaire

#### Étape 2 : Enrichissement (lemmatisation)

```bash
python -m PAGEtopage enrich --input ./extracted.json --output ./corpus.vertical.txt
```

Cette commande :
- Lit le JSON de l'étape 1
- Découpe le texte en phrases
- Analyse chaque mot (lemme, partie du discours)
- Crée le corpus au format vertical

> **Note** : La première exécution téléchargera automatiquement TreeTagger (~20 Mo). Les exécutions suivantes seront rapides (~1 minute pour 350 pages).

#### Étape 3 : Export en fichiers texte

```bash
python -m PAGEtopage export --input ./corpus.vertical.txt --output ./pages/ --format clean
```

Cette commande :
- Lit le corpus vertical
- Crée un fichier texte par page
- Génère les fichiers d'index

---

## Les formats de sortie

### Format "scholarly" (recommandé)

Format académique avec en-tête détaillé et texte en lignes continues :

```
================================================================================
PAGE 79
Source: Fraher_Induent_sancti_proofs_SK_poor.pdf_page_109.xml
Image: Fraher_Induent_sancti_proofs_SK_poor.pdf_page_109.jpg
Titre courant: DISTINCTIO OCTOGESIMA
Œuvre: Summa 'Induent sancti'
Auteur: Anonyme
Date: 1194
================================================================================
catum susceperit biennio in lectoratu erit, et sequenti quinquennio acolitus
et subdiaconus fiet, et de cetero superiores quandocumque poterit accipere...
```

### Format "clean"

Texte brut, facilement lisible :

```
Dominus enim dicit in evangelio. Qui perseveraverit usque in finem, hic salvus erit.
```

### Format "diplomatic"

Texte avec annotations entre parenthèses :

```
Dominus(NOM→dominus) enim(ADV→enim) dicit(VER→dico) in(PRP→in) evangelio(NOM→evangelium).
```

### Format "annotated"

Format tabulaire (pour analyse informatique) :

```
<s>
Dominus	NOM	dominus
enim	ADV	enim
dicit	VER	dico
</s>
```

Pour changer de format, modifiez `export: format:` dans `config.yaml` ou utilisez l'option `--format` :

```bash
python -m PAGEtopage export --input ./corpus.vertical.txt --output ./pages/ --format scholarly
```

---

## Comprendre le format vertical

Le format vertical est le format intermédiaire utilisé par les linguistes. Voici un exemple :

```xml
<doc folio="0042.xml" page_number="42" running_title="Liber I" edition_id="Edi-7"
     title="Mon Manuscrit" language="Latin" author="Auteur" date="1188">
<s>
Dominus	NOM	dominus
enim	ADV	enim
dicit	VER	dico
.	PUNCT	.
</s>
<s>
Amen	INT	amen
.	PUNCT	.
</s>
</doc>
```

**Explication :**
- `<doc ...>` : Début d'une page avec toutes ses métadonnées
- `<s>` : Début d'une phrase
- `Dominus	NOM	dominus` : Mot → Partie du discours → Lemme
- `</s>` : Fin de phrase
- `</doc>` : Fin de page

**Abréviations des parties du discours :**
| Code | Signification | Exemple |
|------|---------------|---------|
| NOM | Nom | dominus, rex |
| VER | Verbe | dicit, est |
| ADJ | Adjectif | bonus, magnus |
| ADV | Adverbe | enim, usque |
| PRO | Pronom | qui, hic |
| PRP | Préposition | in, de, ad |
| CON | Conjonction | et, sed |
| PUNCT | Ponctuation | . , ; |

---

## Résolution des problèmes courants

### "python n'est pas reconnu comme commande"

**Cause :** Python n'est pas dans le PATH système.

**Solution Windows :**
1. Réinstallez Python en cochant "Add Python to PATH"
2. Ou utilisez le chemin complet : `C:\Python310\python.exe -m PAGEtopage ...`

**Solution Mac/Linux :**
Utilisez `python3` au lieu de `python` :
```bash
python3 -m PAGEtopage run --input ./xml_pages/ --output ./output/ --config config.yaml
```

### "No module named PAGEtopage"

**Cause :** Vous n'êtes pas dans le bon dossier.

**Solution :**
1. Vérifiez que vous êtes dans le dossier contenant `PAGEtopage/`
2. La commande `ls` (Mac/Linux) ou `dir` (Windows) doit afficher le dossier PAGEtopage

### "No module named treetaggerwrapper"

**Cause :** Les dépendances ne sont pas installées.

**Solution :**
```bash
pip install treetaggerwrapper pyyaml
```

### "FileNotFoundError: config.yaml"

**Cause :** Le fichier de configuration n'existe pas ou le chemin est incorrect.

**Solution :**
1. Vérifiez que `config.yaml` existe dans votre dossier de travail
2. Utilisez le chemin complet si nécessaire : `--config /chemin/complet/vers/config.yaml`

### L'enrichissement prend du temps la première fois

**Cause :** TreeTagger est téléchargé automatiquement (~20 Mo).

**Solution :** Patientez, les prochaines exécutions seront très rapides (~1 minute pour 350 pages).

### Erreur d'installation automatique de TreeTagger

**Cause :** Problème de connexion internet ou permissions insuffisantes.

**Solution :** TreeTagger sera installé dans le dossier `PAGEtopage/vendor/treetagger`. Assurez-vous d'avoir :
- Une connexion internet active
- Les droits d'écriture dans le dossier PAGEtopage

### Caractères étranges dans le texte

**Cause :** Problème d'encodage.

**Solution :** Vérifiez que vos fichiers XML sont en UTF-8. La plupart des logiciels HTR exportent déjà en UTF-8.

### Apostrophes et guillemets dans config.yaml

Si votre titre contient des apostrophes (') ou guillemets ("), utilisez des guillemets doubles pour entourer la valeur :

```yaml
corpus:
  title: "Summa 'Induent sancti'"  # ✓ Correct
  author: "Jean de la Rochelle"    # ✓ Correct
```

Si la valeur contient des guillemets doubles, échappez-les ou utilisez des guillemets simples :

```yaml
corpus:
  title: 'Il dit "Veni"'          # ✓ Correct
  title: "Il dit \"Veni\""        # ✓ Correct aussi
```

---

## Exemples pratiques

### Exemple 1 : Traiter un manuscrit simple

```bash
# 1. Créez votre dossier de travail
mkdir mon_manuscrit
cd mon_manuscrit

# 2. Copiez vos XML dans un sous-dossier
mkdir xml_pages
# (copiez vos fichiers .xml dans xml_pages/)

# 3. Créez config.yaml (voir modèle ci-dessus)

# 4. Lancez le traitement
python -m PAGEtopage run --input ./xml_pages/ --output ./resultats/ --config config.yaml
```

### Exemple 2 : Manuscrit à deux colonnes

Modifiez `config.yaml` :
```yaml
extraction:
  column_mode: dual    # Changez "single" en "dual"
```

### Exemple 3 : Obtenir différents formats de sortie

```bash
# D'abord, créez le corpus vertical
python -m PAGEtopage run --input ./xml_pages/ --output ./output/ --config config.yaml

# Puis exportez dans chaque format
python -m PAGEtopage export --input ./output/corpus.vertical.txt --output ./format_scholarly/ --format scholarly
python -m PAGEtopage export --input ./output/corpus.vertical.txt --output ./format_clean/ --format clean
python -m PAGEtopage export --input ./output/corpus.vertical.txt --output ./format_diplo/ --format diplomatic
python -m PAGEtopage export --input ./output/corpus.vertical.txt --output ./format_annot/ --format annotated
```

---

## Aide et commandes utiles

### Afficher l'aide générale

```bash
python -m PAGEtopage --help
```

### Afficher l'aide d'une commande spécifique

```bash
python -m PAGEtopage extract --help
python -m PAGEtopage enrich --help
python -m PAGEtopage export --help
```

### Générer un fichier de configuration vide

```bash
python -m PAGEtopage init --output ma_config.yaml
```

### Mode verbeux (affiche plus de détails)

Ajoutez `-v` pour voir ce qui se passe :

```bash
python -m PAGEtopage run -v --input ./xml_pages/ --output ./output/ --config config.yaml
```

---

## Glossaire

| Terme | Définition |
|-------|------------|
| **XML PAGE** | Format de fichier utilisé par les logiciels HTR/OCR (Transkribus, eScriptorium) |
| **HTR** | Handwritten Text Recognition - Reconnaissance automatique d'écriture manuscrite |
| **OCR** | Optical Character Recognition - Reconnaissance optique de caractères |
| **Lemme** | Forme de base d'un mot (ex: "dicit" → "dico") |
| **POS** | Part of Speech - Partie du discours (nom, verbe, adjectif...) |
| **Format vertical** | Format d'annotation linguistique avec un mot par ligne |
| **TreeTagger** | Outil de lemmatisation et POS tagging rapide pour le latin |
| **MainZone** | Zone de texte principal dans un fichier XML PAGE |
| **Folio** | Feuillet d'un manuscrit (une page) |

---

## Support

En cas de problème :
1. Vérifiez les messages d'erreur dans le terminal
2. Consultez la section "Résolution des problèmes" ci-dessus
3. Ouvrez une issue sur GitHub : https://github.com/TitouanCiSaMe/Data_Base/issues
