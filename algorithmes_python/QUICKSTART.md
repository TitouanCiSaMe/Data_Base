# Guide de démarrage rapide - XMLCorpusProcessor

## ⚡ Installation en 5 minutes

### Étape 1 : Installer TreeTagger

```bash
# Créer le dossier TreeTagger
mkdir -p ~/treetagger && cd ~/treetagger

# Télécharger TreeTagger (Linux)
wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.4.tar.gz
tar -xzf tree-tagger-linux-3.2.4.tar.gz

# Télécharger les paramètres pour le Latin
wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/latin-par-linux-3.2.bin.gz
gunzip latin-par-linux-3.2.bin.gz

# Ajouter au PATH
echo 'export PATH="$HOME/treetagger/bin:$HOME/treetagger/cmd:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Vérifier l'installation
tree-tagger --version
```

### Étape 2 : Installer les dépendances Python

```bash
pip install treetaggerwrapper
```

### Étape 3 : Télécharger le code

```bash
cd ~/projets
git clone <url-du-depot>
cd algorithmes_python
```

---

## 🚀 Premier traitement en 3 lignes

### Script minimal

Créez `mon_premier_corpus.py` :

```python
from xml_corpus_processor import XMLCorpusProcessor, ProcessingConfig

config = ProcessingConfig(
    input_folder="/chemin/vers/mes/fichiers/xml",
    output_file="/chemin/vers/sortie/corpus.txt",
    language='la'  # Latin
)

processor = XMLCorpusProcessor(config)
processor.process_corpus()
```

### Exécution

```bash
python mon_premier_corpus.py
```

**C'est tout !** Votre corpus lemmatisé est prêt dans `corpus.txt`

---

## 📂 Structure de vos fichiers XML

Vos fichiers XML doivent avoir cette structure (PAGE XML) :

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PcGts>
    <Page>
        <TextRegion custom='structure {type:MainZone;}'>
            <TextLine>
                <TextEquiv>
                    <Unicode>Votre texte ici</Unicode>
                </TextEquiv>
            </TextLine>
        </TextRegion>
    </Page>
</PcGts>
```

---

## 📝 Exemples courants

### Exemple 1 : Corpus avec métadonnées

```python
from xml_corpus_processor import XMLCorpusProcessor, ProcessingConfig

config = ProcessingConfig(
    input_folder="/data/manuscripts/tractatus",
    output_file="/output/corpus.txt",
    language='la',
    metadata={
        "title": "Mon corpus",
        "author": "Anonyme",
        "date": "1100-1150"
    }
)

processor = XMLCorpusProcessor(config)
processor.process_corpus()
```

### Exemple 2 : Commencer à une page spécifique

```python
config = ProcessingConfig(
    input_folder="/data/xml",
    output_file="/output/corpus.txt",
    starting_page_number=361  # Commence à la page 361
)

processor = XMLCorpusProcessor(config)
processor.process_corpus()
```

### Exemple 3 : Exclure les pages vides

```python
config = ProcessingConfig(
    input_folder="/data/xml",
    output_file="/output/corpus.txt",
    include_empty_folios=False  # Ignorer les pages vides
)

processor = XMLCorpusProcessor(config)
processor.process_corpus()
```

### Exemple 4 : Texte en français

```python
config = ProcessingConfig(
    input_folder="/data/francais",
    output_file="/output/corpus_fr.txt",
    language='fr'  # Français au lieu de Latin
)

processor = XMLCorpusProcessor(config)
processor.process_corpus()
```

---

## 📊 Format de sortie

Le fichier généré contient un corpus vertical annoté :

```xml
<doc folio="manuscrit_0001.xml" page_number="1" title="Mon corpus">
<s>
Dominus	NOM	dominus
est	V	sum
</s>
</doc>
```

Chaque ligne : `FORME\tPOS\tLEMME`

---

## 🎯 Utiliser le fichier de configuration interactive

Pour explorer différentes configurations :

```bash
python config_example.py
```

Menu interactif avec 10 exemples prêts à l'emploi !

---

## ✅ Vérifier que tout fonctionne

### Test 1 : Vérifier TreeTagger

```bash
tree-tagger --version
```

Si erreur : TreeTagger n'est pas dans le PATH

### Test 2 : Vérifier Python

```python
import treetaggerwrapper
print("✓ TreeTagger wrapper installé")
```

### Test 3 : Lancer les tests unitaires

```bash
python test_xml_corpus_processor.py
```

---

## 🔧 Langues supportées par TreeTagger

Installez les paramètres pour d'autres langues :

```bash
cd ~/treetagger

# Français
wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/french-par-linux-3.2.bin.gz
gunzip french-par-linux-3.2.bin.gz

# Allemand
wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/german-par-linux-3.2.bin.gz
gunzip german-par-linux-3.2.bin.gz

# Anglais
wget https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/english-par-linux-3.2.bin.gz
gunzip english-par-linux-3.2.bin.gz
```

Puis dans votre code :

```python
config = ProcessingConfig(
    input_folder="/data/xml",
    output_file="/output/corpus.txt",
    language='fr'  # ou 'de', 'en', etc.
)
```

---

## 📚 Prochaines étapes

1. **Lire la documentation complète** : `XML_CORPUS_README.md`
2. **Tester différentes configurations** : `python config_example.py`
3. **Adapter à votre projet** : Modifier les métadonnées, chemins, etc.
4. **Optimiser pour gros corpus** : Voir section "Performances" du README

---

## 🆘 Problèmes courants

### "Aucun fichier XML trouvé"

```python
import os
print(os.listdir("/votre/dossier"))  # Vérifier le contenu
```

Vérifiez que :
- Le chemin est correct
- Les fichiers ont l'extension `.xml`
- Vous avez les permissions de lecture

### "TreeTagger not found"

```bash
export PATH="$HOME/treetagger/bin:$HOME/treetagger/cmd:$PATH"
```

Vérifiez :
```bash
which tree-tagger
ls ~/treetagger/bin/
```

### "Caractères bizarres dans le résultat"

Vos XML doivent être en UTF-8 :

```bash
file -i votre_fichier.xml
# Doit afficher : charset=utf-8
```

Convertir si nécessaire :
```bash
iconv -f ISO-8859-1 -t UTF-8 input.xml > output.xml
```

---

## 💡 Astuces

### Traiter un petit échantillon d'abord

```bash
# Copier seulement 10 fichiers pour tester
mkdir /tmp/test_corpus
cp /votre/dossier/xml/*.xml /tmp/test_corpus/ | head -n 10

# Traiter l'échantillon
python votre_script.py
```

### Activer le mode debug

```python
import logging

config = ProcessingConfig(
    input_folder="/data/xml",
    output_file="/output/corpus.txt",
    log_level=logging.DEBUG  # Détails complets
)
```

### Sauvegarder les logs

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('traitement.log'),
        logging.StreamHandler()
    ]
)
```

---

## 🎓 Tutoriel complet pas à pas

### Scénario : Traiter un manuscrit latin

**1. Préparer vos données**

```bash
# Structure recommandée
/home/user/
├── corpus_project/
│   ├── input/
│   │   ├── page_001.xml
│   │   ├── page_002.xml
│   │   └── ...
│   └── output/
└── scripts/
    └── process_manuscript.py
```

**2. Créer le script**

`scripts/process_manuscript.py` :

```python
from xml_corpus_processor import XMLCorpusProcessor, ProcessingConfig
import logging

# Activer le logging
logging.basicConfig(level=logging.INFO)

# Configuration
config = ProcessingConfig(
    input_folder="/home/user/corpus_project/input",
    output_file="/home/user/corpus_project/output/corpus_final.txt",
    language='la',
    metadata={
        "title": "Mon manuscrit théologique",
        "author": "Anonyme",
        "date": "XIIe siècle",
        "type": "Théologie"
    },
    starting_page_number=1
)

# Traitement
print("Début du traitement...")
processor = XMLCorpusProcessor(config)
processor.process_corpus()
print("✓ Traitement terminé !")
```

**3. Exécuter**

```bash
cd /home/user/scripts
python process_manuscript.py
```

**4. Vérifier le résultat**

```bash
# Afficher les premières lignes
head -n 50 /home/user/corpus_project/output/corpus_final.txt

# Compter les documents
grep -c "<doc" /home/user/corpus_project/output/corpus_final.txt

# Compter les phrases
grep -c "<s>" /home/user/corpus_project/output/corpus_final.txt
```

---

## 🔗 Liens utiles

- **Documentation complète** : `XML_CORPUS_README.md`
- **Exemples de configuration** : `config_example.py`
- **Tests unitaires** : `test_xml_corpus_processor.py`
- **TreeTagger** : https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/

---

**Vous êtes prêt !** 🎉

Pour plus de détails, consultez `XML_CORPUS_README.md`
