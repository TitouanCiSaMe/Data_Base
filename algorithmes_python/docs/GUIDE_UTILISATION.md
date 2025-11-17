# 📖 Guide d'utilisation

## 🚀 Démarrage rapide

### 1. Installation des dépendances (optionnel)
```bash
pip install -r requirements.txt
```

### 2. Ajoutez votre algorithme
Créez un fichier `.py` dans le dossier `original/` :

```python
# original/mon_algorithme.py

def mon_algorithme(data):
    """
    Description de votre algorithme
    """
    # Votre code ici
    pass
```

### 3. Demandez l'analyse
Dites simplement à Claude :
> "Analyse et optimise mon_algorithme.py"

## 🔍 Ce que Claude fera

1. **Lecture** de votre code
2. **Analyse** complète :
   - Complexité algorithmique
   - Points forts/faibles
   - Bugs potentiels
3. **Optimisation** :
   - Création d'une version optimisée dans `optimise/`
   - Rapport détaillé dans `analyses/`
4. **Tests** :
   - Benchmark de performance
   - Comparaison avant/après

## 📊 Format des rapports

Chaque analyse génère :
- `analyses/mon_algorithme_analyse.md` - Rapport complet
- `optimise/mon_algorithme.py` - Version optimisée
- `tests/test_mon_algorithme.py` - Tests de performance

## 💡 Conseils

- **Documentez votre code** : Plus il y a de contexte, meilleure sera l'analyse
- **Cas de test** : Fournissez des exemples d'utilisation
- **Objectifs** : Précisez si vous voulez optimiser le temps, la mémoire, ou la lisibilité
- **Contraintes** : Mentionnez les contraintes spécifiques (compatibilité Python, dépendances, etc.)

## 🎯 Exemples de demandes

- "Analyse cet algorithme et optimise-le pour la vitesse"
- "Mon algo est trop lent avec de grandes données, peux-tu l'améliorer ?"
- "Compare ces deux implémentations et dis-moi laquelle est meilleure"
- "Explique-moi la complexité de cet algorithme"
- "Refactorise ce code pour le rendre plus pythonique"

## ✅ Prêt !

Le projet est configuré. Il ne reste plus qu'à ajouter vos algorithmes ! 🎉
