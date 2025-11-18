# 🚀 Guide d'utilisation - Téléchargeur d'images rapide (Mac)

Guide pour utiliser le script de téléchargement parallèle d'images IIIF sur macOS.

## 📋 Prérequis

- **macOS** (toutes versions récentes)
- **Python 3.7+** (probablement déjà installé sur Mac)
- **Terminal** (l'application native de macOS)

---

## 🔧 Installation

### 1. Vérifier Python

Ouvrez le Terminal et vérifiez que Python est installé :

```bash
python3 --version
```

Vous devriez voir quelque chose comme `Python 3.x.x`. Si Python n'est pas installé :

```bash
# Installer Python avec Homebrew
brew install python3
```

### 2. Naviguer vers le dossier du projet

```bash
cd /chemin/vers/Data_Base/algorithmes_python
```

**Exemple** :
```bash
cd ~/Documents/Data_Base/algorithmes_python
```

### 3. Créer un environnement virtuel (recommandé)

```bash
# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement virtuel
source venv/bin/activate
```

Votre terminal devrait maintenant afficher `(venv)` au début de la ligne.

### 4. Installer les dépendances

```bash
pip install aiohttp aiofiles tqdm requests
```

**Détails des packages** :
- `aiohttp` : Pour le téléchargement asynchrone
- `aiofiles` : Pour l'écriture asynchrone de fichiers
- `tqdm` : Pour la barre de progression
- `requests` : Pour les requêtes HTTP

---

## ⚙️ Configuration

Éditez le fichier `scripts/download_images.py` avec votre éditeur préféré :

```bash
# Avec nano (éditeur simple)
nano scripts/download_images.py

# Ou avec VSCode
code scripts/download_images.py
```

Modifiez la section **CONFIGURATION** (lignes 146-158) :

```python
# =============================================
# CONFIGURATION - Modifiez ces valeurs
# =============================================

MANIFEST_PATH = "/Users/votre_nom/Downloads/manifest.json"
OUTPUT_DIR = "/Users/votre_nom/Downloads/Latin_18108"
URLS_OUTPUT = "/Users/votre_nom/Downloads/urls_to_download.txt"

# Paramètres de téléchargement
MAX_CONCURRENT = 10  # Augmentez pour plus de vitesse (ex: 50)
RATE_LIMIT_DELAY = 0.1  # Délai entre chaque téléchargement (secondes)
SKIP_EXISTING = True  # Skip les fichiers déjà téléchargés
FILENAME_TEMPLATE = "Latin_18108_{index}.jpg"
```

**💡 Astuce macOS** : Pour obtenir le chemin complet d'un fichier/dossier :
1. Glissez-déposez le fichier dans le Terminal
2. Le chemin complet s'affichera automatiquement

---

## 🚀 Utilisation

### Lancer le téléchargement

```bash
python3 scripts/download_images.py
```

### Exemple de sortie

```
==============================================================
📥 TÉLÉCHARGEMENT D'IMAGES DEPUIS MANIFEST
==============================================================
Manifest       : /Users/titouan/Downloads/manifest.json
Dossier sortie : /Users/titouan/Downloads/Latin_18108
Parallélisme   : 10 téléchargements simultanés
Skip existants : Oui
==============================================================

📋 Extraction des URLs depuis le manifest...
   → 1523 IDs trouvés
   → 487 URLs .jpg
   → URLs sauvegardées dans urls_to_download.txt

📥 Téléchargement de 487 images...

Downloading: 100%|████████████| 487/487 [03:15<00:00, 2.49file/s]

==============================================================
📊 RÉSUMÉ DES TÉLÉCHARGEMENTS
==============================================================
Total de fichiers    : 487
✓ Réussis            : 485
✗ Échoués            : 2
⊘ Ignorés (existants): 0
Taille totale        : 125.3 MB
Taux de réussite     : 99.6%
==============================================================

✅ Téléchargement terminé avec succès!
```

---

## ⚡ Optimisation de la vitesse

### Configuration par défaut (prudente)
```python
MAX_CONCURRENT = 10
RATE_LIMIT_DELAY = 0.1
```
➡️ **Vitesse** : ~487 images en 3-5 minutes

### Configuration rapide
```python
MAX_CONCURRENT = 50
RATE_LIMIT_DELAY = 0.0
```
➡️ **Vitesse** : ~487 images en 1-2 minutes

### Configuration ultra-rapide (attention au serveur !)
```python
MAX_CONCURRENT = 100
RATE_LIMIT_DELAY = 0.0
```
➡️ **Vitesse** : ~487 images en 30-60 secondes

**⚠️ Attention** : Une vitesse trop élevée peut :
- Surcharger le serveur distant
- Entraîner un blocage temporaire de votre IP
- Causer plus d'échecs de téléchargement

**Recommandation** : Commencez avec 10-20 et augmentez progressivement.

---

## 🔄 Cas d'utilisation

### 1. Téléchargement complet d'un manuscrit

```bash
python3 scripts/download_images.py
```

### 2. Reprise après interruption

Si le téléchargement est interrompu (Ctrl+C, fermeture du Mac, etc.), relancez simplement :

```bash
python3 scripts/download_images.py
```

**Avantage** : Le script skip automatiquement les images déjà téléchargées !

### 3. Télécharger plusieurs manuscrits

Créez une copie du script pour chaque manuscrit :

```bash
# Copier le script
cp scripts/download_images.py scripts/download_latin_18108.py
cp scripts/download_images.py scripts/download_grec_1234.py

# Modifiez chaque script avec ses propres chemins
nano scripts/download_latin_18108.py
nano scripts/download_grec_1234.py

# Lancez-les séparément
python3 scripts/download_latin_18108.py
python3 scripts/download_grec_1234.py
```

### 4. Utilisation avancée (en Python)

Si vous voulez utiliser le script dans votre propre code :

```python
from scripts.download_images import download_images_from_manifest

stats = download_images_from_manifest(
    manifest_path="/Users/vous/manifest.json",
    output_dir="/Users/vous/output",
    max_concurrent=50,
    rate_limit_delay=0.1,
    skip_existing=True,
    filename_template="page_{index:04d}.jpg"
)

print(f"Téléchargées : {stats['succeeded']}")
print(f"Échouées : {stats['failed']}")
```

---

## 🛠️ Dépannage

### ❌ "Module not found: aiohttp"

**Solution** :
```bash
source venv/bin/activate  # Assurez-vous que l'environnement virtuel est activé
pip install aiohttp aiofiles tqdm requests
```

### ❌ "Permission denied"

**Solution** : Vérifiez les permissions du dossier de sortie :
```bash
chmod +w /Users/vous/Downloads/Latin_18108
```

### ❌ "Manifest non trouvé"

**Solution** : Vérifiez le chemin du manifest :
```bash
# Afficher le chemin actuel
pwd

# Lister les fichiers
ls -la
```

Utilisez le **chemin absolu complet** : `/Users/votre_nom/Downloads/manifest.json`

### ❌ Trop d'échecs de téléchargement

**Solution** : Réduisez la vitesse de téléchargement :
```python
MAX_CONCURRENT = 5
RATE_LIMIT_DELAY = 1.0
```

### ❌ "Event loop is already running"

**Solution** : Relancez le script. C'est un bug connu avec Jupyter/IPython.

---

## 📊 Comparaison avec download_manuscript.py

| Aspect | download_manuscript.py | download_images.py |
|--------|------------------------|-------------------|
| **Vitesse** | ⏱️ Lent (séquentiel) | ⚡ Rapide (parallèle) |
| **Temps pour 487 images** | ~16 minutes (2s/image) | ~3 minutes (10 concurrent) |
| **Complexité** | ✅ Simple | ⚙️ Plus complexe |
| **Dépendances** | requests, tqdm | aiohttp, aiofiles, tqdm |
| **Utilisation** | Script autonome | Nécessite le framework |

**Recommandation** :
- 📘 **Pour débuter** : `download_manuscript.py` (plus simple)
- 🚀 **Pour la vitesse** : `download_images.py` (50-100x plus rapide)

---

## 🧹 Désactivation de l'environnement virtuel

Quand vous avez terminé :

```bash
deactivate
```

---

## 📝 Structure du projet

```
algorithmes_python/
├── scripts/
│   └── download_images.py         ← Le script à lancer
├── utils/
│   └── async_downloader.py        ← Module de téléchargement
├── core/
│   └── ...                         ← Framework Pipeline
└── venv/                           ← Environnement virtuel (à créer)
```

---

## 💡 Astuces macOS

### Raccourci clavier Terminal
- **Cmd+T** : Nouvel onglet
- **Ctrl+C** : Arrêter le script
- **Cmd+K** : Effacer l'écran

### Surveiller l'utilisation réseau
```bash
# Ouvrir le Moniteur d'activité
open -a "Activity Monitor"
```
Allez dans l'onglet "Réseau" pour voir la vitesse de téléchargement en temps réel.

### Libérer de l'espace disque
```bash
# Vérifier l'espace disponible
df -h

# Taille du dossier de sortie
du -sh /Users/vous/Downloads/Latin_18108
```

---

## 🆘 Support

En cas de problème :
1. Vérifiez que l'environnement virtuel est activé (`(venv)` visible)
2. Vérifiez que toutes les dépendances sont installées : `pip list`
3. Vérifiez les chemins (utilisez **chemins absolus** commençant par `/Users/...`)
4. Consultez le fichier de log dans le dossier de sortie

---

**✨ Bon téléchargement !**
