# Guide d'utilisation - Annotation multi-journaux

## Problème résolu

Le script `annotate_corpus_for_sketchengine.py` avait des noms de colonnes **hardcodés** pour Libération (`Titre`, `Sous-titre`, `Date`, `Lien`). Cela causait une **KeyError** avec des CSV d'autres journaux ayant des noms de colonnes différents.

## Solution

Le script accepte maintenant un **mapping de colonnes configurable** pour s'adapter à n'importe quel format de CSV.

---

## 🔍 Diagnostic rapide

Avant d'utiliser le script, vérifiez les noms de colonnes de votre CSV :

```bash
head -1 /chemin/vers/votre_fichier.csv
```

**Exemple pour Libération :**
```
Titre,Sous-titre,Date,Lien
```

**Si vos colonnes sont différentes** (ex: `Title,Subtitle,PublishDate,URL`), vous devez configurer le mapping.

---

## 📋 Méthode 1 : Avec preset (recommandé)

### Pour Libération (par défaut)
```bash
python annotate_corpus_for_sketchengine.py \
  --csv articles_metadata_liberation.csv \
  --txt liberation_corpus.txt \
  --preset liberation
```

### Pour Le Figaro
```bash
python annotate_corpus_for_sketchengine.py \
  --csv articles_metadata_figaro.csv \
  --txt corpus_figaro.txt \
  --preset figaro
```

---

## 🛠️ Méthode 2 : Mapping manuel des colonnes

Si vos colonnes ont des noms personnalisés, utilisez les arguments individuels :

```bash
python annotate_corpus_for_sketchengine.py \
  --csv articles_metadata.csv \
  --txt corpus.txt \
  --title-col "Title" \
  --subtitle-col "Subtitle" \
  --date-col "PublishDate" \
  --url-col "URL" \
  --corpus-name "MonJournal" \
  --corpus-source "Mon Journal" \
  --id-prefix "MJ"
```

### Arguments disponibles

| Argument | Description | Défaut |
|----------|-------------|--------|
| `--csv` | Fichier CSV des métadonnées | *requis* |
| `--txt` | Fichier texte du corpus | *requis* |
| `--output` | Fichier de sortie | `[fichier]_annotated.txt` |
| `--preset` | Preset prédéfini (`liberation`, `figaro`) | Aucun |
| `--title-col` | Nom de la colonne titre | `Titre` |
| `--subtitle-col` | Nom de la colonne sous-titre | `Sous-titre` |
| `--date-col` | Nom de la colonne date | `Date` |
| `--url-col` | Nom de la colonne URL | `Lien` |
| `--corpus-name` | Nom du corpus | `Liberation` |
| `--corpus-source` | Source du corpus | `Libération` |
| `--id-prefix` | Préfixe des IDs (3 lettres) | `LIB` |

---

## 🔧 Cas d'usage typiques

### Cas 1 : Vos colonnes ont exactement les mêmes noms que Libération
```bash
# Pas de configuration nécessaire !
python annotate_corpus_for_sketchengine.py \
  --csv votre_fichier.csv \
  --txt votre_corpus.txt
```

### Cas 2 : Vous avez des colonnes avec des noms en anglais
```bash
python annotate_corpus_for_sketchengine.py \
  --csv articles.csv \
  --txt corpus.txt \
  --title-col "Title" \
  --subtitle-col "Subtitle" \
  --date-col "Date" \
  --url-col "Link"
```

### Cas 3 : Vous traitez Le Figaro
```bash
# 1. D'abord, vérifier les colonnes de votre CSV
head -1 /home/titouan/Documents/Github/data/Figaro/articles_metadata_figaro.csv

# 2. Si les colonnes sont identiques à Libération, utilisez le preset
python annotate_corpus_for_sketchengine.py \
  --csv /home/titouan/Documents/Github/data/Figaro/articles_metadata_figaro.csv \
  --txt /home/titouan/Documents/Github/data/Figaro/corpus.txt \
  --preset figaro

# 3. Sinon, spécifiez les colonnes manuellement
python annotate_corpus_for_sketchengine.py \
  --csv /home/titouan/Documents/Github/data/Figaro/articles_metadata_figaro.csv \
  --txt /home/titouan/Documents/Github/data/Figaro/corpus.txt \
  --title-col "VotreColonneTitre" \
  --subtitle-col "VotreColonneSousTitre" \
  --date-col "VotreColonneDate" \
  --url-col "VotreColonneURL" \
  --corpus-name "Figaro" \
  --corpus-source "Le Figaro" \
  --id-prefix "FIG"
```

---

## 📊 Sortie du script

Lors de l'exécution, le script affiche maintenant les **colonnes détectées** :

```
📖 Lecture du fichier CSV: articles_metadata.csv
   ✓ 2186 articles avec métadonnées chargés
   ℹ️  Colonnes détectées: Titre, Sous-titre, Date, Lien
```

Cela vous permet de vérifier rapidement si les noms de colonnes correspondent à votre configuration.

---

## ⚙️ Fonctionnalités avancées

### Auto-détection des colonnes supplémentaires
Toutes les colonnes du CSV qui ne sont pas mappées (`title`, `subtitle`, `date`, `url`) sont **automatiquement ajoutées** comme attributs XML.

**Exemple :**
Si votre CSV contient une colonne `Auteur`, elle sera ajoutée comme `<doc auteur="...">`.

### IDs générés
Les IDs sont générés au format : `{PREFIX}_{ANNÉE}_{NUMERO}`

**Exemples :**
- `LIB_2020_001` pour Libération
- `FIG_2022_042` pour Le Figaro
- `MJ_2023_999` pour un journal personnalisé

---

## 🐛 Résolution de problèmes

### Erreur : `KeyError: 'Titre'`
**Cause :** Votre CSV n'a pas de colonne nommée `Titre`.

**Solution :** Utilisez `--title-col` pour spécifier le nom correct :
```bash
--title-col "VotreNomDeColonne"
```

### Erreur : Aucun article apparié
**Cause :** Le fuzzy matching ne trouve pas de correspondance entre CSV et TXT.

**Solutions possibles :**
1. Vérifiez que les titres dans le CSV et le TXT sont similaires
2. Réduisez le seuil de similarité dans le code (ligne 195, actuellement 0.70)
3. Vérifiez que le fichier TXT respecte le format attendu

### Colonne détectée mais vide
**Cause :** La colonne existe mais n'a pas de valeur pour certains articles.

**Solution :** C'est normal ! Le script utilise `.get()` avec une valeur par défaut vide.

---

## 📝 Exemples complets

### Exemple 1 : Libération (configuration par défaut)
```bash
python annotate_corpus_for_sketchengine.py \
  --csv projects/algorithmes_python/original/articles_metadata_liberation.csv \
  --txt projects/algorithmes_python/original/liberation_01012020_31122022\(1\).txt \
  --output liberation_annotated.txt
```

### Exemple 2 : Le Figaro avec preset
```bash
python annotate_corpus_for_sketchengine.py \
  --csv /home/titouan/Documents/Github/data/Figaro/articles_metadata_figaro.csv \
  --txt /home/titouan/Documents/Github/data/Figaro/corpus.txt \
  --preset figaro \
  --output figaro_annotated.txt
```

### Exemple 3 : Journal personnalisé avec toutes les options
```bash
python annotate_corpus_for_sketchengine.py \
  --csv mon_journal.csv \
  --txt mon_corpus.txt \
  --title-col "Headline" \
  --subtitle-col "Subheadline" \
  --date-col "PublicationDate" \
  --url-col "WebURL" \
  --corpus-name "MonJournal" \
  --corpus-source "Mon Journal Quotidien" \
  --id-prefix "MJQ" \
  --output mon_journal_annotated.txt
```

---

## 🎯 Pour votre cas spécifique (Le Figaro)

**Étape 1 : Vérifier les colonnes**
```bash
head -1 /home/titouan/Documents/Github/data/Figaro/articles_metadata_figaro.csv
```

**Étape 2a : Si les colonnes sont `Titre,Sous-titre,Date,Lien`**
```bash
python annotate_corpus_for_sketchengine.py \
  --csv /home/titouan/Documents/Github/data/Figaro/articles_metadata_figaro.csv \
  --txt /home/titouan/Documents/Github/data/Figaro/corpus.txt \
  --preset figaro
```

**Étape 2b : Si les colonnes sont différentes (ex: `Title,Subtitle,Date,URL`)**
```bash
python annotate_corpus_for_sketchengine.py \
  --csv /home/titouan/Documents/Github/data/Figaro/articles_metadata_figaro.csv \
  --txt /home/titouan/Documents/Github/data/Figaro/corpus.txt \
  --title-col "Title" \
  --subtitle-col "Subtitle" \
  --date-col "Date" \
  --url-col "URL" \
  --corpus-name "Figaro" \
  --corpus-source "Le Figaro" \
  --id-prefix "FIG"
```

---

## 📦 Fichiers générés

Le script génère 4 fichiers :

1. **`corpus_annotated.txt`** : Corpus complet annoté (XML)
2. **`corpus_annotated_titles.txt`** : Corpus des titres seuls
3. **`corpus_annotated_subtitles.txt`** : Corpus des sous-titres seuls
4. **`corpus_annotated_report.txt`** : Rapport d'annotation

---

## 💡 Astuce

Pour créer un preset permanent pour votre journal, modifiez la section `main()` du script et ajoutez votre configuration dans le bloc `elif args.preset == 'votre_journal':`.
