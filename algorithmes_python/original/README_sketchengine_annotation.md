# Annotation de corpus pour SketchEngine

Ce script permet d'annoter un corpus d'articles de presse avec toutes leurs métadonnées pour une utilisation dans **SketchEngine**.

## 🎯 Fonctionnement

Le script :
1. **Lit le CSV** avec toutes les métadonnées des articles
2. **Parse le fichier texte** pour extraire les articles complets
3. **Associe uniquement par titre** (fuzzy matching à 70%)
4. **Génère un fichier annoté XML** avec TOUTES les métadonnées du CSV injectées dans les balises `<doc>`

## 🚀 Utilisation

### Commande de base

```bash
python annotate_corpus_for_sketchengine.py
```

### Avec paramètres personnalisés

```bash
python annotate_corpus_for_sketchengine.py \
    --csv articles_metadata_liberation.csv \
    --txt liberation_01012020_31122022(1).txt \
    --output corpus_liberation_annotated.txt
```

## 📋 Format du fichier de sortie

Le script génère un fichier XML avec la structure suivante :

```xml
<?xml version="1.0" encoding="UTF-8"?>
<corpus name="Liberation" source="Libération" created="2025-11-19">

<doc id="LIB_2020_001"
     title="Un laboratoire israélien a-t-il développé un vaccin contre le Covid-19 ?"
     subtitle="Un laboratoire, parmi d'autres, a annoncé..."
     date="2020-03-05"
     year="2020"
     month="03"
     day="17"
     url="https://www.liberation.fr/..."
     matched="true"
     source_start_line="1"
     source_end_line="17">
Un laboratoire, parmi d'autres, a annoncé être en train de développer...
[Contenu complet de l'article]
</doc>

<doc id="LIB_2020_002" ...>
...
</doc>

</corpus>
```

## 🏷️ Métadonnées disponibles dans les balises

Chaque balise `<doc>` contient :

| Attribut | Description | Exemple |
|----------|-------------|---------|
| `id` | Identifiant unique (LIB_YYYY_NNN) | `LIB_2020_001` |
| `title` | Titre de l'article | `"Vaccins contre le Covid-19..."` |
| `subtitle` | Sous-titre/chapô | `"Quels sérums sont autorisés..."` |
| `date` | Date complète (YYYY-MM-DD) | `2020-03-05` |
| `year` | Année seule | `2020` |
| `month` | Mois (01-12) | `03` |
| `day` | Jour (01-31) | `05` |
| `url` | Lien vers l'article | `https://www.liberation.fr/...` |
| `matched` | Article trouvé dans le texte ? | `true` ou `false` |
| `source_start_line` | Ligne de début dans le fichier source | `1` |
| `source_end_line` | Ligne de fin dans le fichier source | `17` |

**Important** : Toutes les colonnes du CSV sont automatiquement ajoutées comme attributs. Si votre CSV contient d'autres colonnes (auteur, catégorie, etc.), elles seront incluses.

## 📊 Fichiers générés

| Fichier | Description |
|---------|-------------|
| `[fichier]_annotated.txt` | Corpus annoté au format SketchEngine |
| `[fichier]_annotated_report.txt` | Rapport détaillé de l'annotation |

## 📤 Upload dans SketchEngine

### Étape 1 : Préparer le fichier

Le fichier généré (`*_annotated.txt`) est directement compatible avec SketchEngine.

### Étape 2 : Créer un corpus dans SketchEngine

1. Connectez-vous à [SketchEngine](https://www.sketchengine.eu/)
2. Cliquez sur **"My Corpora"**
3. Puis **"Create corpus"**

### Étape 3 : Upload

1. Sélectionnez **"From file on my computer"**
2. Uploadez votre fichier `*_annotated.txt`
3. SketchEngine détectera automatiquement :
   - Le format XML
   - Les balises `<doc>`
   - Tous les attributs (métadonnées)

### Étape 4 : Configuration

SketchEngine vous demandera :
- **Language** : Sélectionnez `French`
- **Corpus name** : Donnez un nom à votre corpus
- **Attributes** : Les métadonnées seront automatiquement détectées

Cliquez sur **"Create corpus"**

## 🔍 Requêtes avec métadonnées dans SketchEngine

Une fois le corpus uploadé, vous pouvez utiliser les métadonnées dans vos requêtes CQL :

### Exemples de requêtes

#### 1. Rechercher "vaccin" uniquement dans les articles de 2020

```cql
[word="vaccin"] within <doc year="2020"/>
```

#### 2. Rechercher "Covid" dans les articles de mars 2020

```cql
[word="Covid.*"] within <doc year="2020" month="03"/>
```

#### 3. Rechercher des articles contenant "confinement" ET "masque"

```cql
<doc/> containing [word="confinement"] containing [word="masque"]
```

#### 4. Filtrer par titre (regex)

```cql
[word="virus"] within <doc title=".*Covid.*"/>
```

#### 5. Rechercher dans les articles appariés uniquement

```cql
[word="pandémie"] within <doc matched="true"/>
```

#### 6. Comparer deux périodes

```cql
# Période 1 : 2020
[lemma="vaccin"] within <doc year="2020"/>

# Période 2 : 2021
[lemma="vaccin"] within <doc year="2021"/>
```

## 📈 Analyses possibles dans SketchEngine

Grâce aux métadonnées, vous pouvez :

### 1. Analyse diachronique (évolution dans le temps)

- Comparer la fréquence de mots clés par année
- Observer l'évolution du vocabulaire (2020 vs 2021 vs 2022)
- Identifier les pics d'utilisation de termes

**Menu** : `Keywords` → Filtrer par `year`

### 2. Collocations par période

- Trouver les cooccurrences de "vaccin" en 2020
- Comparer avec les cooccurrences en 2021

**Menu** : `Word Sketch` → Filtrer par `date`

### 3. Concordances filtrées

- Afficher tous les contextes de "masque" en mars 2020
- Comparer avec avril 2020

**Menu** : `Concordance` → Advanced → `<doc>` attributes

### 4. Fréquences

- Calculer la fréquence de "confinement" par mois
- Identifier les mois avec le plus d'articles sur un sujet

**Menu** : `Frequency` → Text types → `month`

## 🎨 Personnalisation

### Ajouter des métadonnées personnalisées au CSV

Le script injecte **automatiquement** toutes les colonnes du CSV dans les balises XML.

**Exemple** : Si votre CSV contient :

```csv
Titre,Sous-titre,Date,Lien,Auteur,Catégorie
"Article 1","Description",2020-01-01,"https://...",Jean Dupont,Santé
```

Le fichier annoté contiendra :

```xml
<doc id="LIB_2020_001"
     title="Article 1"
     subtitle="Description"
     date="2020-01-01"
     url="https://..."
     auteur="Jean Dupont"
     catégorie="Santé"
     ...>
```

### Modifier le seuil de matching

Dans le script `annotate_corpus_for_sketchengine.py`, ligne ~148 :

```python
# Passer de 70% à 60% pour accepter plus de matches
if best_score >= 0.60:  # Au lieu de 0.70
    return best_match
```

### Changer le format de l'ID

Dans la fonction `generate_id()`, ligne ~156 :

```python
# Format actuel : LIB_YYYY_NNN
return f"LIB_{year}_{index:03d}"

# Format alternatif : LIBERATION_2020_001
return f"LIBERATION_{year}_{index:03d}"

# Format avec date complète : LIB_2020-03-05_001
return f"LIB_{csv_article['Date']}_{index:03d}"
```

## 🔧 Dépannage

### Problème : Taux d'appariement très faible (<10%)

**Causes possibles** :
- Périodes différentes entre CSV et fichier texte
- Titres très différents entre les deux sources
- Structure du fichier texte non conforme

**Solutions** :
1. Vérifier les périodes :
   ```bash
   # Dans le CSV
   cut -d',' -f4 articles_metadata_liberation.csv | sort | uniq

   # Dans le TXT
   grep -E '^\d{4}-\d{2}-\d{2}$' liberation_*.txt | sort | uniq
   ```

2. Comparer manuellement quelques titres :
   ```bash
   # 5 premiers titres du CSV
   head -5 articles_metadata_liberation.csv | cut -d',' -f2

   # 10 premières lignes du TXT
   head -20 liberation_*.txt
   ```

3. Baisser le seuil de matching (voir section Personnalisation)

### Problème : SketchEngine ne détecte pas les métadonnées

**Solution** : Vérifiez que le fichier XML est bien formé :

```bash
# Vérifier la syntaxe XML
xmllint --noout liberation_*_annotated.txt
```

Si erreur, vérifiez que les caractères spéciaux sont bien échappés :
- `&` → `&amp;`
- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;`
- `'` → `&apos;`

### Problème : Encodage incorrect dans SketchEngine

**Solution** : Le fichier doit être en UTF-8. Vérifier :

```bash
file -i liberation_*_annotated.txt
# Devrait afficher : charset=utf-8
```

Si ce n'est pas le cas, convertir :

```bash
iconv -f ISO-8859-1 -t UTF-8 input.txt > output.txt
```

## 📚 Ressources

- [Documentation SketchEngine - Annotation](https://www.sketchengine.eu/guide/annotating-corpus-text/)
- [SketchEngine - CQL Query Language](https://www.sketchengine.eu/documentation/corpus-querying/)
- [SketchEngine - Working with Attributes](https://www.sketchengine.eu/documentation/working-with-attributes/)

## 🆚 Différence avec les autres scripts

| Script | Usage | Sortie |
|--------|-------|--------|
| `add_article_ids.py` | Ajouter des IDs au CSV | CSV enrichi + JSON mapping |
| `add_article_ids_optimized.py` | Version optimisée du précédent | CSV enrichi + JSON + rapport |
| **`annotate_corpus_for_sketchengine.py`** ⭐ | **Annoter pour SketchEngine** | **Fichier XML annoté prêt pour upload** |

**Recommandation** : Pour SketchEngine, utilisez `annotate_corpus_for_sketchengine.py` directement.

## 💡 Conseils d'utilisation

### Pour un corpus de qualité

1. **Nettoyer le CSV en amont**
   - Supprimer les doublons
   - Vérifier que les dates sont au format YYYY-MM-DD
   - S'assurer que tous les champs importants sont remplis

2. **Vérifier la structure du fichier texte**
   - Format attendu : Titre → ligne vide → Sous-titre → ligne vide → Date → Contenu
   - Utiliser toujours le même séparateur (lignes vides)

3. **Faire un test sur un petit échantillon**
   ```bash
   # Créer un petit CSV de test (10 articles)
   head -11 articles_metadata_liberation.csv > test.csv

   # Lancer le script
   python annotate_corpus_for_sketchengine.py --csv test.csv

   # Vérifier le résultat
   less liberation_*_annotated.txt
   ```

### Pour l'analyse dans SketchEngine

1. **Commencer par des requêtes simples**
   - Rechercher un mot clé : `[word="vaccin"]`
   - Observer les contextes : Menu `Concordance`

2. **Exploiter les métadonnées progressivement**
   - Filtrer par année d'abord
   - Puis par mois pour affiner
   - Utiliser les autres attributs (URL, matched) si nécessaire

3. **Comparer des sous-corpus**
   - Créer un sous-corpus 2020 : `<doc year="2020"/>`
   - Créer un sous-corpus 2021 : `<doc year="2021"/>`
   - Comparer les fréquences, collocations, keywords

## 🎓 Exemple d'analyse complète

### Objectif : Étudier l'évolution du discours sur les vaccins (2020-2022)

#### Étape 1 : Annoter le corpus

```bash
python annotate_corpus_for_sketchengine.py \
    --csv articles_liberation_2020-2022.csv \
    --txt liberation_2020-2022_full.txt \
    --output corpus_liberation_vaccins.txt
```

#### Étape 2 : Upload dans SketchEngine

- Upload `corpus_liberation_vaccins.txt`
- Nom du corpus : "Libération COVID 2020-2022"

#### Étape 3 : Analyses

**3.1 Fréquence de "vaccin" par année**

```cql
# Menu: Frequency → Text types → year
[lemma="vaccin"]
```

**3.2 Collocations de "vaccin" en 2020 vs 2021**

```cql
# 2020
[lemma="vaccin"] within <doc year="2020"/>
→ Menu: Word Sketch

# 2021
[lemma="vaccin"] within <doc year="2021"/>
→ Menu: Word Sketch
```

**3.3 Mots-clés spécifiques à chaque année**

```cql
# Menu: Keywords
Focus corpus: <doc year="2020"/>
Reference corpus: <doc year="2021"/>
```

**3.4 Concordances filtrées**

```cql
# Articles mentionnant AstraZeneca en mars 2021
[word="AstraZeneca"] within <doc year="2021" month="03"/>
→ Menu: Concordance
```

## ✅ Checklist avant upload dans SketchEngine

- [ ] Le fichier `*_annotated.txt` a été généré sans erreur
- [ ] Le rapport montre un taux d'appariement acceptable
- [ ] Le fichier est en UTF-8
- [ ] La structure XML est valide (`xmllint` ne retourne pas d'erreur)
- [ ] Les métadonnées importantes sont présentes dans les balises `<doc>`
- [ ] Un test a été fait sur un petit échantillon

---

**Auteur** : Créé pour le projet Data_Base
**Date** : 2025-11-19
