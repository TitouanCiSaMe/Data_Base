# Convertisseur de Corpus Vertical vers Pages Texte

Outil pour convertir des fichiers corpus vertical (format HyperBase) en pages texte individuelles avec diverses options de formatage.

## 📋 Fonctionnalités

- ✅ Conversion de fichiers corpus vertical en pages individuelles
- ✅ Génération d'un fichier texte complet combinant toutes les pages
- ✅ Support du traitement **multi-fichiers** (batch)
- ✅ Index JSON des métadonnées de pages
- ✅ Fichier de correspondance images/pages
- ✅ 3 formats de sortie (clean, diplomatic, annotated)
- ✅ Interface en ligne de commande complète

---

## 🚀 Installation

Aucune dépendance externe requise, seulement Python 3.7+

```bash
# Vérifier la version Python
python3 --version

# Rendre le script exécutable (optionnel)
chmod +x corpus_to_pages_converter.py
```

---

## 📖 Utilisation

### Syntaxe de base

```bash
python3 corpus_to_pages_converter.py [OPTIONS] fichier(s) -o SORTIE
```

### 🔹 Cas d'usage 1 : Fichier unique

Convertir un seul fichier corpus :

```bash
python3 corpus_to_pages_converter.py mon_corpus.txt -o output_directory/
```

**Résultat :**
```
output_directory/
├── page_0001_folio1r.txt
├── page_0002_folio1v.txt
├── ...
├── texte_complet.txt        # Toutes les pages combinées
├── pages_index.json         # Métadonnées
├── images_mapping.txt        # Correspondance images
└── conversion.log
```

---

### 🔹 Cas d'usage 2 : Plusieurs fichiers

Convertir plusieurs fichiers en une seule commande :

```bash
python3 corpus_to_pages_converter.py corpus1.txt corpus2.txt corpus3.txt -o output/
```

**Résultat :** Chaque corpus dans son sous-dossier
```
output/
├── corpus1/
│   ├── page_0001_*.txt
│   ├── texte_complet.txt
│   └── ...
├── corpus2/
│   ├── page_0001_*.txt
│   ├── texte_complet.txt
│   └── ...
└── corpus3/
    └── ...
```

---

### 🔹 Cas d'usage 3 : Tous les fichiers d'un dossier

Convertir automatiquement tous les fichiers `.txt` d'un dossier :

```bash
python3 corpus_to_pages_converter.py --directory corpus_dir/ -o output/
```

Avec un pattern personnalisé :

```bash
# Traiter seulement les fichiers *_corpus.txt
python3 corpus_to_pages_converter.py -d corpus_dir/ -o output/ --pattern "*_corpus.txt"
```

---

## ⚙️ Options disponibles

### Options d'entrée

| Option | Description |
|--------|-------------|
| `fichiers` | Un ou plusieurs fichiers corpus à convertir |
| `-d, --directory DIR` | Traiter tous les fichiers d'un dossier |
| `--pattern PATTERN` | Pattern de recherche avec `--directory` (défaut: `*.txt`) |

### Options de sortie

| Option | Description |
|--------|-------------|
| `-o, --output DIR` | **Obligatoire**. Dossier de sortie |
| `--no-combined` | Ne pas créer le fichier texte complet |
| `--no-metadata` | Ne pas créer le fichier JSON de métadonnées |

### Options de format

| Option | Valeur | Description |
|--------|--------|-------------|
| `-f, --format` | `clean` | **(défaut)** Texte propre, mots uniquement |
| | `diplomatic` | Texte avec annotations POS : `mot(NOUN)` |
| | `annotated` | Format tabulaire complet : `mot\tPOS\tlemme` |
| `-l, --lemmas` | | Inclure les lemmes dans les annotations |

### Options avancées

| Option | Description |
|--------|-------------|
| `--template STR` | Template de nom de fichier<br>Défaut: `page_{page_number:04d}_{folio}.txt` |

---

## 📚 Exemples pratiques

### Exemple 1 : Format diplomatique avec lemmes

```bash
python3 corpus_to_pages_converter.py corpus.txt -o output/ \
    --format diplomatic --lemmas
```

**Sortie :**
```
Le(DET) philosophe(NOUN→philosophe) pense(VERB→penser) donc(ADV) il(PRON) est(VERB→être).
```

---

### Exemple 2 : Format annoté (tabulaire)

```bash
python3 corpus_to_pages_converter.py corpus.txt -o output/ \
    --format annotated
```

**Sortie :**
```
Le      DET     le
philosophe      NOUN    philosophe
pense   VERB    penser
donc    ADV     donc
```

---

### Exemple 3 : Conversion sans fichiers supplémentaires

```bash
python3 corpus_to_pages_converter.py corpus.txt -o output/ \
    --no-combined --no-metadata
```

Génère seulement les fichiers de pages individuelles.

---

### Exemple 4 : Batch avec format personnalisé

```bash
python3 corpus_to_pages_converter.py -d /corpus/HyperBase/ -o /sortie/ \
    --pattern "*.txt" \
    --format clean \
    --template "page_{page_number:03d}.txt"
```

---

## 📁 Structure des fichiers générés

### Fichier page individuelle

```
================================================================================
PAGE 42
Source: folio_42r.xml
Image: folio_42r.jpg
Titre courant: De Trinitate
Œuvre: Tractatus de Trinitate
Auteur: Thomas d'Aquin
Date: 1259
================================================================================

[Contenu de la page...]
```

### Fichier texte complet (`texte_complet.txt`)

```
--- PAGE 1 ---

[Contenu page 1]

--- PAGE 2 ---

[Contenu page 2]
...
```

### Index métadonnées (`pages_index.json`)

```json
{
  "conversion_info": {
    "corpus_source": "/path/to/corpus.txt",
    "conversion_date": "2025-01-15T10:30:00",
    "text_format": "clean",
    "total_pages": 150
  },
  "statistics": {
    "pages_processed": 150,
    "words_converted": 45230,
    "sentences_converted": 2341,
    "empty_pages": 2
  },
  "pages": [
    {
      "folio": "folio_1r.xml",
      "page_number": 1,
      "running_title": "De Trinitate",
      "image_filename": "folio_1r.jpg",
      "metadata": {...}
    }
  ]
}
```

---

## 🎯 Cas d'usage typiques

### Pour la recherche textuelle

```bash
# Format propre pour lecture/analyse
python3 corpus_to_pages_converter.py corpus.txt -o texte/ --format clean
```

### Pour l'analyse linguistique

```bash
# Format annoté avec toutes les informations
python3 corpus_to_pages_converter.py corpus.txt -o analyse/ \
    --format annotated --lemmas
```

### Pour l'édition critique

```bash
# Format diplomatique avec métadonnées complètes
python3 corpus_to_pages_converter.py corpus.txt -o edition/ \
    --format diplomatic
```

### Traitement de masse

```bash
# Convertir toute une bibliothèque
python3 corpus_to_pages_converter.py -d /bibliotheque/corpus/ -o /output/ \
    --format clean --pattern "*.txt"
```

---

## 🔍 Aide en ligne

```bash
# Afficher l'aide complète
python3 corpus_to_pages_converter.py --help
```

---

## 🐛 Dépannage

### Le script ne trouve pas les fichiers

```bash
# Vérifier les chemins
ls -lh mon_corpus.txt

# Utiliser des chemins absolus
python3 corpus_to_pages_converter.py /chemin/absolu/corpus.txt -o /sortie/
```

### Erreur "End of statement expected"

C'est une erreur de l'IDE, pas du script Python. Le script est syntaxiquement valide. Essayez :
- Redémarrer votre IDE
- Exécuter directement le script dans le terminal

### Logs de conversion

Consultez le fichier `conversion.log` dans le dossier de sortie pour les détails :

```bash
tail -f output/conversion.log
```

---

## 📝 Format du corpus vertical

Le script attend un format corpus vertical standard :

```xml
<doc folio="folio_1r.xml" page_number="1" running_title="Titre" ...>
<s>
mot1    POS1    lemme1
mot2    POS2    lemme2
.       PUN     .
</s>
<s>
...
</s>
</doc>
```

---

## 🤝 Contribution

Pour signaler un bug ou proposer une amélioration, contactez le développeur.

---

## 📜 Licence

Script développé pour le traitement de corpus HyperBase.
