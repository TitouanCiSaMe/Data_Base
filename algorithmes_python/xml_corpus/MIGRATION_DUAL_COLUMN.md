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
