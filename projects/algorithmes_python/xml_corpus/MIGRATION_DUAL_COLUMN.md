# Migration vers le support dual-column

## Vue d'ensemble

Le module `XMLCorpusProcessor` a été refactorisé pour supporter deux modes de traitement :

1. **Mode `single`** (par défaut) : Un fichier XML = une page
   - Extrait le texte d'une seule `MainZone`
   - Comportement identique à la version précédente

2. **Mode `dual`** (nouveau) : Un fichier XML = deux pages
   - Extrait le texte de deux colonnes : `MainZone:column#1` et `MainZone:column#2`
   - Chaque colonne devient une page distincte dans le corpus

## Changements apportés

### 1. Nouvelles structures de données

#### `ProcessingConfig`
Ajout du paramètre `column_mode` :
```python
@dataclass
class ProcessingConfig:
    # ... paramètres existants ...
    column_mode: str = 'single'  # 'single' ou 'dual'
```

#### `PageMetadata`
Ajout du champ `column` :
```python
@dataclass
class PageMetadata:
    filename: str
    page_number: int
    running_title: str
    is_empty: bool = False
    column: Optional[str] = None  # Nouveau: 'col1', 'col2', ou None
```

### 2. Nouvelles méthodes

#### `_extract_columns(root: ET.Element) -> List[Tuple[Optional[str], List[str]]]`
Extrait les colonnes selon le mode configuré :
- Mode `single` : retourne `[(None, lignes)]`
- Mode `dual` : retourne `[("col1", lignes1), ("col2", lignes2)]`

### 3. Méthodes modifiées

#### `_process_xml_page(file_path: str)`
**Ancienne signature :**
```python
-> Tuple[Optional[int], str, List[str]]
```

**Nouvelle signature :**
```python
-> Tuple[Optional[int], str, List[Tuple[Optional[str], List[str]]]]
```

Retourne maintenant une liste de colonnes au lieu d'une simple liste de lignes.

#### `_process_all_files(xml_files: List[str])`
Gère maintenant la numérotation de page différemment selon le mode :
- Mode `single` : un fichier = un numéro de page
- Mode `dual` : un fichier = deux numéros de page (un par colonne)

#### `_format_document(metadata: PageMetadata, lines: List[str])`
Génère maintenant un identifiant de folio avec suffixe de colonne en mode dual :
- Mode `single` : `folio="fichier.xml"`
- Mode `dual` : `folio="fichier.xml-col1"`, `folio="fichier.xml-col2"`

## Guide de migration

### Code existant (rétro-compatible)

Votre code existant **continue de fonctionner** sans modification :

```python
config = ProcessingConfig(
    input_folder="/path/to/xml",
    output_file="/path/to/output.txt",
    language='la'
)
# Le mode 'single' est utilisé par défaut
processor = XMLCorpusProcessor(config)
processor.process_corpus()
```

### Nouveau code (mode dual)

Pour traiter des fichiers avec deux colonnes :

```python
config = ProcessingConfig(
    input_folder="/path/to/xml",
    output_file="/path/to/output.txt",
    language='la',
    column_mode='dual',  # Activer le mode dual
    starting_page_number=3  # Numéro de la première colonne
)

processor = XMLCorpusProcessor(config)
processor.process_corpus()
```

## Structure XML attendue

### Mode single
```xml
<TextRegion custom='structure {type:MainZone;}'>
    <TextLine>...</TextLine>
</TextRegion>
```

### Mode dual
```xml
<TextRegion custom='structure {type:MainZone:column#1;}'>
    <TextLine>...</TextLine>
</TextRegion>

<TextRegion custom='structure {type:MainZone:column#2;}'>
    <TextLine>...</TextLine>
</TextRegion>
```

## Format de sortie

### Mode single
```xml
<doc folio="fichier_0001.xml" page_number="1" ...>
    <s>
    mot1    POS1    lemme1
    mot2    POS2    lemme2
    </s>
</doc>
```

### Mode dual
```xml
<doc folio="fichier_0001.xml-col1" page_number="3" ...>
    <s>
    mot1    POS1    lemme1
    </s>
</doc>

<doc folio="fichier_0001.xml-col2" page_number="4" ...>
    <s>
    mot3    POS3    lemme3
    </s>
</doc>
```

## Gestion des colonnes vides

En mode `dual`, si une colonne est vide :
- Avec `include_empty_folios=True` (défaut) : une balise `<doc empty="true">` est créée
- Avec `include_empty_folios=False` : la page est ignorée mais le compteur continue

## Guide d'utilisation complet

### Paramètres de configuration

Le `ProcessingConfig` accepte les paramètres suivants :

#### Paramètres obligatoires

| Paramètre | Type | Description |
|-----------|------|-------------|
| `input_folder` | `str` | Chemin du dossier contenant les fichiers XML |
| `output_file` | `str` | Chemin du fichier de sortie (.txt) |

#### Paramètres optionnels

| Paramètre | Type | Défaut | Description |
|-----------|------|--------|-------------|
| `language` | `str` | `'la'` | Code langue pour TreeTagger (`'la'`, `'fr'`, `'en'`, etc.) |
| `log_level` | `int` | `logging.INFO` | Niveau de journalisation (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `metadata` | `dict` | `None` | Dictionnaire de métadonnées à inclure dans chaque document |
| `page_numbering_source` | `str` | `'filename'` | Source pour la numérotation : `'filename'` ou `'numbering_zone'` |
| `starting_page_number` | `int` | `1` | Numéro de la première page/colonne |
| `include_empty_folios` | `bool` | `True` | Inclure les folios vides avec balise `empty="true"` |
| `column_mode` | `str` | `'single'` | Mode de colonnes : `'single'` ou `'dual'` |

### Exemples d'utilisation

#### 1. Configuration minimale (mode single)

```python
from xml_corpus import XMLCorpusProcessor, ProcessingConfig

config = ProcessingConfig(
    input_folder="/chemin/vers/xml/",
    output_file="/chemin/vers/sortie.txt"
)

processor = XMLCorpusProcessor(config)
processor.process_corpus()
```

#### 2. Configuration avec métadonnées

```python
config = ProcessingConfig(
    input_folder="/chemin/vers/xml/",
    output_file="/chemin/vers/sortie.txt",
    language='la',
    metadata={
        "edition_id": "Edi-001",
        "title": "Mon manuscrit",
        "author": "Anonyme",
        "date": "XIIe siècle",
        "type": "Théologie",
        "lieu": "France"
    }
)

processor = XMLCorpusProcessor(config)
processor.process_corpus()
```

**Résultat :** Chaque document contiendra ces attributs :
```xml
<doc folio="..." page_number="..." edition_id="Edi-001" title="Mon manuscrit" ...>
```

#### 3. Mode dual avec numérotation personnalisée

```python
config = ProcessingConfig(
    input_folder="/chemin/vers/xml/",
    output_file="/chemin/vers/sortie.txt",
    language='la',
    column_mode='dual',           # Activer le mode dual
    starting_page_number=25,      # Commencer à la page 25
    metadata={
        "source": "Manuscrit XYZ",
        "type": "Droit Canonique"
    }
)

processor = XMLCorpusProcessor(config)
processor.process_corpus()
```

**Résultat :** Le premier fichier produira :
- Page 25 : colonne 1 (`fichier-col1`)
- Page 26 : colonne 2 (`fichier-col2`)
- Page 27 : colonne 1 du fichier suivant, etc.

#### 4. Numérotation depuis NumberingZone

```python
config = ProcessingConfig(
    input_folder="/chemin/vers/xml/",
    output_file="/chemin/vers/sortie.txt",
    page_numbering_source='numbering_zone',  # Utiliser les numéros du XML
    language='la'
)

processor = XMLCorpusProcessor(config)
processor.process_corpus()
```

**Usage :** Extrait les numéros de page depuis les zones `NumberingZone` du XML au lieu du nom de fichier.

#### 5. Exclure les folios vides

```python
config = ProcessingConfig(
    input_folder="/chemin/vers/xml/",
    output_file="/chemin/vers/sortie.txt",
    include_empty_folios=False,  # Ignorer les folios sans contenu
    language='la'
)

processor = XMLCorpusProcessor(config)
processor.process_corpus()
```

**Résultat :** Les pages vides ne seront pas incluses dans le fichier de sortie (mais la numérotation continue).

#### 6. Mode dual avec colonnes vides exclues

```python
config = ProcessingConfig(
    input_folder="/chemin/vers/xml/",
    output_file="/chemin/vers/sortie.txt",
    column_mode='dual',
    include_empty_folios=False,  # Exclure les colonnes vides
    starting_page_number=1
)

processor = XMLCorpusProcessor(config)
processor.process_corpus()
```

**Usage :** Utile si certaines pages ont seulement une colonne remplie.

#### 7. Mode debug avec logging détaillé

```python
import logging

config = ProcessingConfig(
    input_folder="/chemin/vers/xml/",
    output_file="/chemin/vers/sortie.txt",
    log_level=logging.DEBUG,  # Afficher tous les détails
    language='la',
    column_mode='dual'
)

processor = XMLCorpusProcessor(config)
processor.process_corpus()
```

**Résultat :** Affiche des logs détaillés sur chaque étape du traitement.

#### 8. Configuration complète (tous les paramètres)

```python
import logging

config = ProcessingConfig(
    # Obligatoires
    input_folder="/home/user/manuscripts/xml/",
    output_file="/home/user/corpus/output.txt",

    # Traitement
    language='la',
    column_mode='dual',

    # Numérotation
    page_numbering_source='filename',
    starting_page_number=101,

    # Options
    include_empty_folios=True,
    log_level=logging.INFO,

    # Métadonnées
    metadata={
        "edition_id": "Edi-42",
        "title": "Sententiae",
        "author": "Pierre Lombard",
        "language": "Latin",
        "date": "1150-1160",
        "type": "Théologie",
        "lieu": "Paris",
        "source": "MS 123"
    }
)

processor = XMLCorpusProcessor(config)
processor.process_corpus()
```

### Cas d'usage spécifiques

#### Manuscrits avec colonnes non uniformes

Si certains fichiers ont 2 colonnes et d'autres 1 seule :

**Option 1 : Mode dual avec colonnes vides**
```python
config = ProcessingConfig(
    input_folder="/chemin/vers/xml/",
    output_file="/chemin/vers/sortie.txt",
    column_mode='dual',
    include_empty_folios=True  # Les colonnes vides auront empty="true"
)
```

**Option 2 : Traiter séparément**
```python
# Traiter d'abord les fichiers à 2 colonnes
config_dual = ProcessingConfig(
    input_folder="/chemin/vers/xml/dual/",
    output_file="/chemin/vers/sortie_dual.txt",
    column_mode='dual',
    starting_page_number=1
)

# Puis les fichiers à 1 colonne
config_single = ProcessingConfig(
    input_folder="/chemin/vers/xml/single/",
    output_file="/chemin/vers/sortie_single.txt",
    column_mode='single',
    starting_page_number=201  # Continuer la numérotation
)
```

#### Extraction sans lemmatisation (debug)

Pour tester l'extraction sans TreeTagger :

```python
# Créer un mock de TreeTagger ou commenter la lemmatisation
config = ProcessingConfig(
    input_folder="/chemin/vers/xml/",
    output_file="/chemin/vers/sortie.txt",
    language='la'
)

processor = XMLCorpusProcessor(config)
# Commenter la ligne d'initialisation de TreeTagger dans process_corpus()
```

### Comparaison des modes

| Critère | Mode `single` | Mode `dual` |
|---------|---------------|-------------|
| Fichiers XML | 1 MainZone par fichier | 2 MainZones (column#1, column#2) |
| Pages générées | 1 par fichier | 2 par fichier |
| Identifiant folio | `fichier.xml` | `fichier.xml-col1`, `fichier.xml-col2` |
| Numérotation | Séquentielle (1, 2, 3...) | Séquentielle continue (1, 2, 3, 4...) |
| Cas d'usage | Textes en page simple | Manuscrits en colonnes |

## Tests

Des tests unitaires ont été ajoutés pour valider le mode dual :
- `TestDualColumnMode.test_dual_column_config`
- `TestDualColumnMode.test_extract_dual_columns`
- `TestDualColumnMode.test_extract_partial_dual_columns`
- `TestDualColumnMode.test_format_document_with_column`

Pour exécuter les tests (nécessite TreeTagger) :
```bash
cd algorithmes_python/tests
python test_xml_corpus_processor.py
```

## Exemples complets

Voir les fichiers :
- `xml_corpus/config_example.py` : exemple mode single
- `xml_corpus/config_example_dual.py` : exemple mode dual

## Avantages de la refactorisation

1. **Rétro-compatibilité** : Le code existant fonctionne sans modification
2. **Architecture unifiée** : Un seul module pour les deux cas d'usage
3. **Maintenance simplifiée** : Plus besoin de maintenir deux versions séparées
4. **Extensibilité** : Facile d'ajouter d'autres modes (triple colonnes, etc.)
5. **Tests robustes** : Tests unitaires pour les deux modes

## Support

Pour toute question ou problème, consultez :
- La documentation inline dans `xml_corpus_processor.py`
- Les exemples dans `config_example.py` et `config_example_dual.py`
- Les tests dans `tests/test_xml_corpus_processor.py`
