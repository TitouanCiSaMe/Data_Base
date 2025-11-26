# Ajout d'identifiants aux articles de Libération

Ce dossier contient des scripts pour ajouter des identifiants uniques aux articles de Libération et les associer à un fichier texte.

## 📁 Fichiers

- **`add_article_ids.py`** - Version de base (simple, pour petits fichiers)
- **`add_article_ids_optimized.py`** - Version optimisée (recommandée)
- **`articles_metadata_liberation.csv`** - CSV source avec métadonnées
- **`articles_metadata_liberation_with_ids.csv`** - CSV enrichi avec IDs
- **`articles_id_mapping.json`** - Mapping ID ↔ articles
- **`unmatched_articles.txt`** - Liste des articles non appariés

## 🚀 Usage

### Version optimisée (recommandée)

```bash
# Utilisation basique
python add_article_ids_optimized.py

# Avec paramètres personnalisés
python add_article_ids_optimized.py \
    --csv articles_metadata_liberation.csv \
    --txt liberation_01012020_31122022(1).txt \
    --output ./resultats
```

### Version de base

```bash
python add_article_ids.py
```

## 📊 Comparaison des versions

| Caractéristique | Version de base | Version optimisée |
|---|---|---|
| **Taille fichiers supportée** | < 100 Mo | < 500 Mo |
| **Parsing du texte** | Algorithme simple | Structure explicite |
| **Matching** | Mots en commun | Fuzzy matching + dates |
| **Indexation** | Non | Oui (titres normalisés) |
| **Progression** | Non | Oui (tous les 50 articles) |
| **Taux d'appariement** | ~8-10% | ~13-15% |
| **Rapport détaillé** | Basique | + fichier des non-appariés |

## 💡 Recommandations par taille de fichier

### Petits fichiers (< 100 Mo)
✅ Les deux versions fonctionnent bien

```bash
python add_article_ids.py
```

### Fichiers moyens (100 Mo - 500 Mo)
✅ Utilisez la version optimisée

```bash
python add_article_ids_optimized.py
```

### Gros fichiers (500 Mo - 2 Go)
⚠️ La version optimisée fonctionne mais peut être lente

**Optimisations possibles :**
- Augmenter la RAM disponible
- Traiter par batch (voir section ci-dessous)
- Utiliser `pandas` avec chunks

### Très gros fichiers (> 2 Go)
❌ Les versions actuelles ne sont pas adaptées

**Solutions :**
1. **Découper les fichiers** en parties plus petites
2. **Utiliser une base de données** (SQLite) pour l'indexation
3. **Traitement par chunks** avec pandas :

```python
# Exemple de traitement par chunks
import pandas as pd

chunk_size = 10000
for chunk in pd.read_csv('huge_file.csv', chunksize=chunk_size):
    # Traiter chaque chunk
    process_chunk(chunk)
```

## 🔧 Amélioration du taux d'appariement

Le taux d'appariement dépend de :

### ✅ Facteurs positifs
- **Périodes identiques** - CSV et TXT couvrent les mêmes dates
- **Titres identiques** - Pas de modification entre sources
- **Dates présentes** - Bonus de +20% si dates correspondent

### ❌ Facteurs négatifs
- **Périodes différentes** - Ex: CSV 2024-2025 vs TXT 2020-2022
- **Titres reformulés** - Modifications éditoriales
- **Caractères spéciaux** - Guillemets différents, accents, etc.

### 💡 Pour améliorer l'appariement

Si votre taux est faible (<30%), vérifiez :

1. **Les périodes** - Assurez-vous que CSV et TXT couvrent les mêmes dates
   ```bash
   # Vérifier les dates dans le CSV
   cut -d',' -f4 articles_metadata_liberation.csv | sort | uniq

   # Vérifier les dates dans le TXT
   grep -E '^\d{4}-\d{2}-\d{2}$' liberation_*.txt | sort | uniq
   ```

2. **Ajuster le seuil** - Dans le code, ligne ~185 :
   ```python
   # Passer de 65% à 55% si les titres varient beaucoup
   if best_score >= 0.55:  # Au lieu de 0.65
       return best_match
   ```

3. **Ajouter des métadonnées** - Utiliser plus de champs (auteur, catégorie, etc.)

## 📝 Format des identifiants

Format : `LIB_YYYY_NNN`

- **LIB** - Préfixe pour Libération
- **YYYY** - Année de l'article (ou XXXX si date inconnue)
- **NNN** - Numéro séquentiel (001, 002, etc.)

Exemples :
- `LIB_2024_001` - Premier article de 2024
- `LIB_2025_042` - 42ème article de 2025
- `LIB_XXXX_015` - 15ème article sans date

## 🏗️ Architecture pour très gros fichiers

Si vous devez traiter régulièrement des fichiers > 2 Go, voici une architecture recommandée :

```python
import sqlite3
import pandas as pd

# 1. Charger le CSV dans SQLite
conn = sqlite3.connect('articles.db')
df = pd.read_csv('huge.csv', chunksize=10000)
for chunk in df:
    chunk.to_sql('articles', conn, if_exists='append', index=False)

# 2. Créer des index
conn.execute('CREATE INDEX idx_title ON articles(Titre)')
conn.execute('CREATE INDEX idx_date ON articles(Date)')

# 3. Parser le fichier texte par chunks
def parse_text_chunks(filepath, chunk_size=1000000):
    with open(filepath, 'r') as f:
        while True:
            lines = f.readlines(chunk_size)
            if not lines:
                break
            yield parse_lines(lines)

# 4. Requêtes SQL pour le matching
cursor = conn.execute(
    "SELECT * FROM articles WHERE Titre LIKE ?",
    (f"%{title}%",)
)
```

## 🐛 Dépannage

### Problème : "MemoryError"
**Solution :** Réduire la taille du fichier ou utiliser chunks

### Problème : Taux d'appariement très faible (<5%)
**Causes possibles :**
- Périodes différentes entre CSV et TXT
- Structure du fichier texte différente
- Encodage incorrect

**Solution :** Vérifier manuellement quelques titres :
```bash
# Dans le CSV
head -5 articles_metadata_liberation.csv

# Dans le TXT
head -50 liberation_*.txt
```

### Problème : Script très lent
**Solutions :**
- Vérifier la RAM disponible : `free -h`
- Réduire la taille des fichiers
- Utiliser la version optimisée

## 📚 Dépendances

Bibliothèques Python requises :

```bash
# Standard (inclus dans Python)
- csv
- json
- re
- pathlib
- argparse
- difflib

# Optionnelles pour très gros fichiers
pip install pandas  # Traitement par chunks
pip install fuzzywuzzy  # Matching avancé
pip install python-Levenshtein  # Accélération fuzzy
```

## 🎯 Cas d'usage

### 1. Enrichir un CSV avec des IDs uniques
```bash
python add_article_ids_optimized.py --csv my_articles.csv
```

### 2. Associer CSV et fichier texte
```bash
python add_article_ids_optimized.py \
    --csv metadata.csv \
    --txt articles_full_text.txt
```

### 3. Générer uniquement le mapping JSON
Le mapping est toujours généré dans `articles_id_mapping.json`

### 4. Traiter plusieurs fichiers
```bash
for file in *.csv; do
    python add_article_ids_optimized.py --csv "$file"
done
```

## 📄 License

Ce code est fourni tel quel pour le projet Data_Base.

## 👤 Auteur

Créé avec Claude pour le projet de recherche Data_Base.
