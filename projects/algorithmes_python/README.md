# 🐍 Algorithmes Python - Collection d'outils et scripts

Bienvenue dans la collection d'outils Python pour le traitement de corpus, l'extraction de manuscrits et l'analyse de données.

---

## 📁 Structure du projet

```
algorithmes_python/
│
├── 📚 xml_corpus/                    # Module XMLCorpusProcessor
│   ├── __init__.py
│   ├── xml_corpus_processor.py       # Processeur de corpus XML avec TreeTagger
│   ├── config_example.py             # 10 exemples de configuration
│   └── requirements.txt              # Dépendances du module
│
├── 🏗️ core/                          # Modules principaux
│   ├── base.py                       # Classes de base
│   ├── extractors.py                 # Extracteurs de données
│   ├── processors.py                 # Processeurs de données
│   ├── pipeline.py                   # Pipeline de traitement
│   └── writers.py                    # Écrivains de fichiers
│
├── 🛠️ utils/                         # Utilitaires
│   ├── async_downloader.py           # Téléchargement asynchrone
│   ├── error_handler.py              # Gestion d'erreurs
│   ├── fuzzy_matcher.py              # Correspondance floue
│   ├── progress.py                   # Barres de progression
│   └── text_processing.py            # Traitement de texte
│
├── 📜 scripts/                        # Scripts exécutables
│   ├── download_images.py            # Téléchargement d'images
│   ├── corpus_to_pages_converter.py  # Conversion corpus → pages
│   └── README_corpus_converter.md    # Documentation du convertisseur
│
├── 🧪 tests/                          # Tests unitaires et benchmarks
│   ├── test_xml_corpus_processor.py  # Tests XMLCorpusProcessor
│   └── benchmark_template.py         # Template de benchmark
│
├── 📖 docs/                           # Documentation
│   ├── xml_corpus/                   # Documentation XMLCorpusProcessor
│   │   ├── README.md                 # Documentation complète
│   │   ├── INDEX.md                  # Index de navigation
│   │   ├── QUICKSTART.md             # Guide démarrage rapide
│   │   └── CHANGELOG.md              # Historique des versions
│   ├── GUIDE_UTILISATION.md          # Guide général
│   └── TEMPLATE_ANALYSE.md           # Template d'analyse
│
├── 🗄️ original/                      # Code original/legacy
│   ├── Extract_manuscrit.py
│   ├── extract_manuscrit_tuile.py
│   └── exemple_tri.py
│
├── README.md                          # Ce fichier
└── requirements.txt                   # Dépendances globales du projet
```

---

## 🎯 Modules principaux

### 1. XMLCorpusProcessor 📚

**Traitement automatique de corpus XML avec lemmatisation TreeTagger.**

- Extraction de texte depuis XML (format PAGE)
- Gestion intelligente des mots coupés avec trait d'union
- Lemmatisation automatique avec TreeTagger
- Support multilingue (Latin, Français, Allemand, etc.)
- Gestion des métadonnées et numérotation flexible

**Documentation** : [`docs/xml_corpus/`](docs/xml_corpus/)

**Démarrage rapide** :
```bash
cd xml_corpus
pip install -r requirements.txt
python config_example.py  # Menu interactif avec exemples
```

**Utilisation** :
```python
from xml_corpus import XMLCorpusProcessor, ProcessingConfig

config = ProcessingConfig(
    input_folder="/path/to/xml",
    output_file="/path/to/output.txt",
    language='la'
)

processor = XMLCorpusProcessor(config)
processor.process_corpus()
```

---

### 2. Core Modules 🏗️

**Bibliothèque de modules pour extraction et traitement de données.**

- **base.py** : Classes abstraites et interfaces de base
- **extractors.py** : Extracteurs de données (XML, images, etc.)
- **processors.py** : Processeurs de transformation
- **pipeline.py** : Pipeline de traitement modulaire
- **writers.py** : Écrivains vers différents formats

**Utilisation** :
```python
from core.pipeline import Pipeline
from core.extractors import XMLExtractor
from core.processors import TextProcessor

pipeline = Pipeline()
pipeline.add_step(XMLExtractor())
pipeline.add_step(TextProcessor())
pipeline.run(input_data)
```

---

### 3. Utilities 🛠️

**Collection d'utilitaires réutilisables.**

- **async_downloader** : Téléchargement parallèle avec retry
- **error_handler** : Décorateurs de gestion d'erreurs
- **fuzzy_matcher** : Matching flou de chaînes
- **progress** : Barres de progression customisables
- **text_processing** : Fonctions de traitement de texte

**Utilisation** :
```python
from utils.async_downloader import AsyncDownloader
from utils.progress import ProgressBar

downloader = AsyncDownloader(max_concurrent=10)
downloader.download_batch(urls)
```

---

### 4. Scripts 📜

**Scripts exécutables pour tâches courantes.**

- **download_images.py** : Téléchargement massif d'images
- **corpus_to_pages_converter.py** : Conversion format corpus

**Utilisation** :
```bash
python scripts/download_images.py --input urls.txt --output images/
python scripts/corpus_to_pages_converter.py --input corpus.txt --output pages/
```

---

## 🚀 Installation

### Installation complète

```bash
# Cloner le dépôt
git clone <url-du-depot>
cd algorithmes_python

# Installer les dépendances globales
pip install -r requirements.txt

# Pour XMLCorpusProcessor (nécessite TreeTagger)
cd xml_corpus
pip install -r requirements.txt
```

### Installation TreeTagger (pour XMLCorpusProcessor)

```bash
# Télécharger et installer TreeTagger
mkdir -p ~/treetagger && cd ~/treetagger
wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.4.tar.gz
tar -xzf tree-tagger-linux-3.2.4.tar.gz

# Télécharger les paramètres Latin
wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/latin-par-linux-3.2.bin.gz
gunzip latin-par-linux-3.2.bin.gz

# Ajouter au PATH
echo 'export PATH="$HOME/treetagger/bin:$HOME/treetagger/cmd:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Guide complet** : [`docs/xml_corpus/QUICKSTART.md`](docs/xml_corpus/QUICKSTART.md)

---

## 📖 Documentation

### Documentation générale

- **Guide d'utilisation** : [`docs/GUIDE_UTILISATION.md`](docs/GUIDE_UTILISATION.md)
- **Template d'analyse** : [`docs/TEMPLATE_ANALYSE.md`](docs/TEMPLATE_ANALYSE.md)

### Documentation XMLCorpusProcessor

- **📍 Point d'entrée** : [`docs/xml_corpus/INDEX.md`](docs/xml_corpus/INDEX.md)
- **📚 Documentation complète** : [`docs/xml_corpus/README.md`](docs/xml_corpus/README.md)
- **🚀 Démarrage rapide** : [`docs/xml_corpus/QUICKSTART.md`](docs/xml_corpus/QUICKSTART.md)
- **📜 Changelog** : [`docs/xml_corpus/CHANGELOG.md`](docs/xml_corpus/CHANGELOG.md)

### Documentation scripts

- **Convertisseur corpus** : [`scripts/README_corpus_converter.md`](scripts/README_corpus_converter.md)

---

## 🧪 Tests

### Exécuter les tests

```bash
# Tests XMLCorpusProcessor
python tests/test_xml_corpus_processor.py

# Avec pytest (si installé)
pytest tests/ -v

# Avec couverture
pytest tests/ --cov=. --cov-report=html
```

### Benchmarks

```bash
# Utiliser le template de benchmark
cp tests/benchmark_template.py tests/benchmark_mon_module.py
# Éditer et exécuter
python tests/benchmark_mon_module.py
```

---

## 💡 Exemples d'utilisation

### Exemple 1 : Traiter un corpus XML

```bash
cd xml_corpus
python config_example.py
# Choisir l'exemple 2 : "Manuscrit latin avec métadonnées"
```

### Exemple 2 : Pipeline de traitement

```python
from core.pipeline import Pipeline
from core.extractors import XMLExtractor
from core.processors import TextCleaner
from core.writers import JSONWriter

# Créer le pipeline
pipeline = Pipeline()
pipeline.add_step(XMLExtractor(source_folder="data/xml"))
pipeline.add_step(TextCleaner())
pipeline.add_step(JSONWriter(output_file="result.json"))

# Exécuter
pipeline.run()
```

### Exemple 3 : Téléchargement asynchrone

```python
from utils.async_downloader import AsyncDownloader

urls = [
    "https://example.com/image1.jpg",
    "https://example.com/image2.jpg",
    # ...
]

downloader = AsyncDownloader(max_concurrent=10, retry=3)
downloader.download_batch(urls, output_dir="downloads/")
```

---

## 🔧 Développement

### Structure recommandée pour ajouter un module

```python
# mon_module/
# ├── __init__.py
# ├── mon_module.py
# ├── config_example.py
# └── requirements.txt

# docs/mon_module/
# ├── README.md
# ├── QUICKSTART.md
# └── CHANGELOG.md

# tests/
# └── test_mon_module.py
```

### Guidelines de code

- **PEP 8** : Suivre les conventions Python
- **Type hints** : Ajouter des annotations de types
- **Docstrings** : Google Style pour toutes les fonctions/classes
- **Tests** : Ajouter des tests unitaires pour nouveau code
- **Documentation** : Documenter les fonctionnalités

---

## 🤝 Contribution

### Comment contribuer

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/amelioration`)
3. Commit les changements (`git commit -m 'Ajout fonctionnalité X'`)
4. Push vers la branche (`git push origin feature/amelioration`)
5. Ouvrir une Pull Request

### Standards de code

- Passer les tests existants
- Ajouter des tests pour nouvelles fonctionnalités
- Mettre à jour la documentation
- Suivre le style de code existant

---

## 📊 Statistiques du projet

| Composant | Fichiers | Lignes | Tests |
|-----------|----------|--------|-------|
| xml_corpus | 4 | ~700 | 40+ |
| core | 6 | ~800 | - |
| utils | 6 | ~600 | - |
| scripts | 3 | ~400 | - |
| tests | 2 | ~500 | - |
| docs | 7 | ~3500 | - |
| **Total** | **28** | **~6500** | **40+** |

---

## 📝 Licence

MIT License - Voir le fichier LICENSE pour plus de détails.

---

## 👤 Auteur

**TitouanCiSaMe**

Pour questions, suggestions ou bugs :
- Ouvrir une issue sur GitHub
- Consulter la documentation dans `docs/`

---

## 🔗 Ressources externes

- **TreeTagger** : https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/
- **PAGE XML** : https://www.primaresearch.org/tools/PAGELibraries
- **Python PEP 8** : https://pep8.org/

---

## 🎯 Prochaines étapes

**Pour commencer** :
1. 📖 Lire la documentation appropriée dans `docs/`
2. 🚀 Tester un exemple avec `xml_corpus/config_example.py`
3. 🧪 Exécuter les tests avec `python tests/test_xml_corpus_processor.py`
4. 💻 Adapter à votre projet

**Pour développer** :
1. 📚 Consulter la structure des modules existants
2. 🛠️ Utiliser les utilitaires dans `utils/`
3. 🔧 Suivre les guidelines de développement
4. ✅ Ajouter des tests

---

**Bon codage !** 🐍✨
