# Data_Base

Dépôt principal pour le traitement et l'analyse de manuscrits latins.

## 📁 Structure du Dépôt

```
Data_Base/
├── docs/                           # 📚 Documentation centralisée
│   ├── README_DOWNLOAD_IMAGES_MAC.md
│   ├── README_MANUSCRIPT_DOWNLOADER.md
│   └── architecture/
│       └── Base_de_donnees.drawio.png
│
├── tools/                          # 🔧 Scripts utilitaires
│   └── manuscript/
│       └── download_manuscript.py
│
└── projects/                       # 🎯 Projets principaux
    ├── algorithmes_python/         # Algorithmes de traitement
    │   ├── core/                   # Modules principaux
    │   ├── scripts/                # Scripts d'exécution
    │   ├── utils/                  # Utilitaires
    │   ├── tests/                  # Tests unitaires
    │   └── docs/                   # Documentation spécifique
    │
    └── latin_analyzer/             # Analyseur de latin
        ├── src/                    # Code source
        ├── scripts/                # Scripts d'analyse
        ├── data/                   # Données (dictionnaires)
        ├── tests/                  # Tests
        └── docs/                   # Documentation
```

## 🚀 Démarrage Rapide

### Téléchargement de Manuscrits
```bash
python tools/manuscript/download_manuscript.py
```
📖 Voir [docs/README_MANUSCRIPT_DOWNLOADER.md](docs/README_MANUSCRIPT_DOWNLOADER.md)

### Algorithmes Python
```bash
cd projects/algorithmes_python
pip install -r requirements.txt
```
📖 Voir [projects/algorithmes_python/README.md](projects/algorithmes_python/README.md)

### Analyseur Latin
```bash
cd projects/latin_analyzer
./setup.sh
```
📖 Voir [projects/latin_analyzer/README.md](projects/latin_analyzer/README.md)

## 📚 Documentation

- **Architecture** : [docs/architecture/Base_de_donnees.drawio.png](docs/architecture/Base_de_donnees.drawio.png)
- **Téléchargement d'images (Mac)** : [docs/README_DOWNLOAD_IMAGES_MAC.md](docs/README_DOWNLOAD_IMAGES_MAC.md)
- **Manuscrits** : [docs/README_MANUSCRIPT_DOWNLOADER.md](docs/README_MANUSCRIPT_DOWNLOADER.md)

## 🔧 Outils Disponibles

| Outil | Description | Emplacement |
|-------|-------------|-------------|
| **download_manuscript.py** | Téléchargement de manuscrits | `tools/manuscript/` |

## 🎯 Projets

### 1. Algorithmes Python
Pipeline de traitement pour l'extraction et l'analyse de corpus de textes.

**Fonctionnalités :**
- Extraction de manuscrits
- Traitement de corpus XML
- Annotation pour SketchEngine
- Conversion de formats

### 2. Latin Analyzer
Analyseur morphologique et lexical pour textes latins médiévaux.

**Fonctionnalités :**
- Analyse morphologique avec PyCollatinus
- Recherche dans le dictionnaire Du Cange
- Export vers formats XML/TXT
- Statistiques d'analyse

## 🤝 Contribution

Les contributions sont les bienvenues ! Veuillez créer une branche pour vos modifications et soumettre une pull request.

## 📄 Licence

Voir les fichiers de licence individuels dans chaque projet.
