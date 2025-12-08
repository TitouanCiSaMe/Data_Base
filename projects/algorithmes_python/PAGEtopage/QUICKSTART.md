# PAGEtopage - Démarrage rapide (5 minutes)

Ce guide vous permettra de traiter votre premier corpus en 5 minutes.

---

## Étape 1 : Vérifiez que Python est installé

Ouvrez un terminal et tapez :

```
python --version
```

Vous devriez voir quelque chose comme `Python 3.10.x`. Si ce n'est pas le cas, installez Python depuis https://www.python.org/downloads/

---

## Étape 2 : Installez les dépendances

```
pip install pyyaml cltk
```

---

## Étape 3 : Préparez vos fichiers

Organisez vos fichiers ainsi :

```
mon_projet/
├── xml_pages/          ← Vos fichiers XML ici
│   ├── 0001.xml
│   ├── 0002.xml
│   └── ...
└── config.yaml         ← Créez ce fichier (voir ci-dessous)
```

---

## Étape 4 : Créez le fichier config.yaml

Copiez-collez ce contenu dans un fichier `config.yaml` :

```yaml
corpus:
  edition_id: "Mon-Edition"
  title: "Mon Manuscrit"
  language: "Latin"
  author: "Auteur"

pagination:
  starting_page_number: 1

extraction:
  column_mode: single
  merge_hyphenated: true

enrichment:
  lemmatizer: cltk
  language: lat

export:
  format: clean
```

---

## Étape 5 : Lancez le traitement

Dans le terminal, naviguez vers le dossier contenant PAGEtopage, puis :

```
python -m PAGEtopage run --input ./xml_pages/ --output ./resultats/ --config config.yaml
```

---

## Étape 6 : Récupérez vos résultats

Vos fichiers sont dans le dossier `resultats/` :

- `corpus.vertical.txt` : Le corpus complet annoté
- `pages/` : Un fichier texte par page
- `texte_complet.txt` : Tout le texte en un seul fichier

---

## C'est fait !

Pour aller plus loin, consultez le fichier `README.md` pour :
- Personnaliser les métadonnées
- Changer le format de sortie
- Résoudre les problèmes courants
