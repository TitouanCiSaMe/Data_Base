# Index des Diagrammes de Flux - Pipeline de Traitement de Manuscrits

## 📋 Vue d'ensemble

Ce répertoire contient une suite complète de diagrammes Mermaid documentant le pipeline de traitement des manuscrits et éditions, de l'acquisition à la production finale du corpus du Décret de Gratien.

## 🗂️ Structure des Diagrammes

### 1. Diagrammes Simplifiés

#### 📌 [flowchart-simple.mmd](./flowchart-simple.mmd)
**Niveau de détail:** ⭐ (Très haut niveau)
**Usage recommandé:** Présentation générale, vue d'ensemble rapide

**Description:** Diagramme ultra-simplifié montrant les 5 grandes étapes du pipeline :
- Acquisition de données
- Traitement eScriptorium
- Nettoyage post-traitement
- Enrichissement Décret de Gratien
- Données finales

**Idéal pour:**
- Présentations exécutives
- Introduction au projet
- Vue globale en un coup d'œil

---

#### 📌 [flowchart-overview.mmd](./flowchart-overview.mmd)
**Niveau de détail:** ⭐⭐ (Haut niveau)
**Usage recommandé:** Vue d'ensemble technique, architecture générale

**Description:** Vue d'ensemble montrant les 5 modules principaux + module Décret de Gratien avec leurs connexions :
- MODULE 1 : Récupération de manuscrits
- MODULE 2 : Méthodes de téléchargement
- MODULE 3 : Récupération d'éditions
- MODULE 4 : Traitement eScriptorium
- MODULE 5 : Nettoyage et finalisation
- MODULE SPÉCIAL : Décret de Gratien

**Idéal pour:**
- Comprendre l'architecture globale
- Identifier les flux de données
- Planifier le travail par module

---

### 2. Diagrammes Détaillés par Module

#### 📌 [flowchart-module1.mmd](./flowchart-module1.mmd)
**MODULE 1 - Récupération de manuscrits**
**Niveau de détail:** ⭐⭐⭐⭐ (Très détaillé)

**Contenu:**
- Processus d'achat (manuscrits déjà numérisés vs à numériser)
- Processus de scraping web (IIIF, PDF, méthodes complexes)
- Point de convergence : numérisation haute qualité (TIF, 300-600 DPI)
- Annotations sur les coûts et la légalité

**Idéal pour:**
- Comprendre les sources d'acquisition
- Planifier l'acquisition de nouveaux manuscrits
- Évaluer les coûts et méthodes

---

#### 📌 [flowchart-module2.mmd](./flowchart-module2.mmd)
**MODULE 2 - Méthodes de téléchargement**
**Niveau de détail:** ⭐⭐⭐⭐⭐ (Exhaustif)

**Contenu:**
- Méthode IIIF (algorithme Manuscrit_Downloader)
- Méthode PDF direct
- Méthodes complexes :
  - Manuelle (page par page)
  - Hexadécimale (algorithme British_Library)
  - Tuiles (algorithme perdu, reconstruction)
- Comparaison qualité (de ⭐ à ⭐⭐⭐⭐⭐)
- Convergence vers Seafile

**Idéal pour:**
- Choisir la méthode de téléchargement appropriée
- Comprendre les algorithmes utilisés
- Optimiser la qualité des images

---

#### 📌 [flowchart-module3.mmd](./flowchart-module3.mmd)
**MODULE 3 - Récupération d'éditions**
**Niveau de détail:** ⭐⭐⭐⭐ (Très détaillé)

**Contenu:**
- Sources d'acquisition (libre, informelle, prêt, achat)
- Processus de numérisation BNU
- Catégorisation temporelle (15e-20e, jamais sorties, 20e-21e)
- Statuts de droit (libre, secret, restreint)
- Statistiques de répartition

**Idéal pour:**
- Gérer l'acquisition d'éditions
- Comprendre les enjeux de droits d'auteur
- Planifier avec la BNU

---

#### 📌 [flowchart-module4.mmd](./flowchart-module4.mmd)
**MODULE 4 - Traitement eScriptorium**
**Niveau de détail:** ⭐⭐⭐⭐⭐ (Exhaustif)

**Contenu:**
- Workflow Éditions vs Manuscrits
- Processus de segmentation :
  - Segmentation manuelle (50-100 pages)
  - Réutilisation de modèles
  - Entraînement HPC
  - Application et validation
- Processus de transcription :
  - Transcription manuelle (100-200 lignes)
  - Réutilisation de modèles
  - Entraînement HPC
  - Application et validation
- Détail HPC (upload, fine-tuning, export)
- Métriques CER (0.1-2% éditions, 4-8% manuscrits)

**Idéal pour:**
- Comprendre le workflow eScriptorium
- Planifier l'entraînement de modèles
- Optimiser la qualité de transcription

---

#### 📌 [flowchart-module5.mmd](./flowchart-module5.mmd)
**MODULE 5 - Nettoyage Post-eScriptorium**
**Niveau de détail:** ⭐⭐⭐⭐ (Très détaillé)

**Contenu:**
- Import et stockage Seafile
- Distinction layouts (1, 2 ou 4 régions Main)
- Types de regex :
  - Communes (normalisation espaces, ponctuation, etc.)
  - Spécifiques (abbréviations latines, numérotation, etc.)
- Processus de vérification
- Outils utilisés (Python, lxml, etc.)
- Statistiques (70% simple page, 25% deux pages, 5% quatre pages)

**Idéal pour:**
- Développer des scripts de nettoyage
- Comprendre les types de regex nécessaires
- Gérer les différents layouts

---

#### 📌 [flowchart-decret-gratien.mmd](./flowchart-decret-gratien.mmd)
**MODULE SPÉCIAL - Décret de Gratien**
**Niveau de détail:** ⭐⭐⭐⭐⭐ (Exhaustif)

**Contenu:**
- Branche Allégations :
  - Ochoa et Diez (source)
  - Extraction algorithmique
  - Ajout d'ID uniques
  - Production Allégations.csv
- Branche Friedberg & Münchener :
  - Fusion des sources
  - Extraction des canons
  - Structuration hiérarchique (Parties, Distinctions, Causae, Quaestiones)
  - Enrichissement avec ID
- Statistiques (~4000 canons, ~3800 allégations)
- Outils (Python, BeautifulSoup, Pandas, lxml)

**Idéal pour:**
- Comprendre l'enrichissement spécifique au Décret
- Planifier l'extraction des allégations
- Structurer le corpus final

---

### 3. Diagramme Complet Amélioré

#### 📌 [flowchart-complete-improved.mmd](./flowchart-complete-improved.mmd)
**Pipeline Complet - Version Améliorée**
**Niveau de détail:** ⭐⭐⭐ (Détaillé mais compact)

**Description:** Version complète optimisée intégrant tous les modules dans un seul diagramme :
- Améliorations par rapport à l'original :
  - ✅ Utilisation de formes de décision ({} au lieu de [])
  - ✅ Réduction de la duplication (workflow HPC généralisé)
  - ✅ Meilleure organisation visuelle
  - ✅ Annotations clés intégrées
  - ✅ Légende et statistiques globales
- Métriques globales (durée, volume, taux automatisation)

**Idéal pour:**
- Vue complète mais lisible
- Documentation technique
- Formation des nouveaux membres de l'équipe

---

## 🎨 Convention de Styles et Couleurs

### Formes
- **Rectangles arrondis `([...])`** : Points d'entrée/sortie
- **Losanges `{...}`** : Décisions / Points de choix
- **Rectangles `[...]`** : Processus / Actions
- **Sous-graphes** : Regroupements logiques de processus

### Couleurs par Type
- 🟢 **Vert** : Points de début/fin, résultats finaux
- 🟡 **Jaune** : Décisions, choix, points de convergence
- 🔵 **Bleu** : Acquisition, téléchargement, stockage cloud
- 🟠 **Orange** : Téléchargement, HPC, entraînement
- 🟣 **Violet** : Nettoyage, traitement, segmentation/transcription
- 🔴 **Rouge/Rose** : Décret de Gratien, éléments spéciaux
- ⚪ **Gris** : Notes, annotations, légendes

### Icônes Utilisées
- 📥 Import / Téléchargement
- 📤 Export / Sortie
- 💰 Achat
- 🌐 Web / Internet
- ☁️ Cloud / Stockage
- ⚙️ Algorithme / Traitement automatique
- ✍️ Intervention manuelle
- 🎓 Entraînement ML / HPC
- ✅ Validation / Vérification
- 🔧 Outils / Regex
- 📊 Données / Statistiques
- 🗂️ Structure / Organisation
- ⚖️ Décret de Gratien
- 📖 Éditions
- 📜 Manuscrits

---

## 🚀 Comment Utiliser Ces Diagrammes

### Pour Visualiser
1. **GitHub / GitLab** : Les fichiers `.mmd` sont automatiquement rendus
2. **VSCode** : Installer l'extension "Markdown Preview Mermaid Support"
3. **En ligne** : Copier le contenu dans [mermaid.live](https://mermaid.live/)
4. **Documentation** : Intégrer dans Markdown avec ` ```mermaid `

### Pour Modifier
1. Ouvrir le fichier `.mmd` dans un éditeur de texte
2. Modifier la syntaxe Mermaid
3. Visualiser en temps réel avec mermaid.live ou extension VSCode
4. Respecter les conventions de style établies

### Pour Présenter
- **Présentation générale** → Commencer par `flowchart-simple.mmd`
- **Présentation technique** → Utiliser `flowchart-overview.mmd`
- **Formation détaillée** → Parcourir les modules 1 à 5 séquentiellement
- **Documentation complète** → Utiliser `flowchart-complete-improved.mmd`

---

## 📊 Comparaison : Original vs Amélioré

| Aspect | Version Originale | Version Améliorée |
|--------|------------------|------------------|
| **Nombre de nœuds** | ~200+ | ~80-100 |
| **Lisibilité** | ⭐⭐ | ⭐⭐⭐⭐ |
| **Duplication** | Élevée (4x HPC) | Minimale (générique) |
| **Décisions visuelles** | Rectangles | Losanges (shapes) |
| **Organisation** | Linéaire | Modulaire |
| **Annotations** | Peu | Nombreuses |
| **Navigation** | Difficile | Facile (multiple fichiers) |

---

## 🔄 Améliorations Apportées

### 1. Réduction de la Complexité
- Suppression des répétitions (workflow HPC générique)
- Regroupement logique dans des sous-graphes
- Simplification des connexions

### 2. Amélioration Visuelle
- Utilisation de formes de décision (`{}`)
- Code couleur cohérent
- Icônes pour différencier les opérations
- Légendes intégrées

### 3. Modularité
- Séparation en fichiers par module
- Navigation facilitée via l'index
- Niveaux de détail progressifs

### 4. Documentation Enrichie
- Annotations sur les nœuds importants
- Statistiques et métriques
- Notes explicatives intégrées

---

## 📚 Références

### Documentation Technique
- [Syntaxe Mermaid](https://mermaid.js.org/intro/)
- [eScriptorium](https://escriptorium.readthedocs.io/)
- [IIIF Protocol](https://iiif.io/)
- [PageXML Format](https://github.com/PRImA-Research-Lab/PAGE-XML)

### Outils Mentionnés
- **Manuscrit_Downloader** : Algorithme IIIF
- **British_Library** : Algorithme hexadécimal
- **Seafile** : Cloud universitaire
- **HPC** : High Performance Computing (GPU)

---

## 🤝 Contribution

Pour proposer des améliorations :
1. Créer une branche de modification
2. Modifier les fichiers `.mmd` concernés
3. Tester la visualisation
4. Mettre à jour cet index si nécessaire
5. Soumettre une pull request

---

## 📝 Notes de Version

### Version 2.0 - Décembre 2024
- ✅ Création de 9 diagrammes modulaires
- ✅ Version améliorée complète
- ✅ Documentation index complète
- ✅ Conventions de style établies
- ✅ Réduction de 50% de la complexité

### Version 1.0 - Original
- Diagramme unique monolithique
- ~200+ nœuds
- Duplication importante

---

## 📞 Support

Pour toute question sur les diagrammes ou le pipeline :
- Consulter la documentation technique des modules
- Référer aux README spécifiques de chaque sous-projet
- Contacter l'équipe de développement

---

**Dernière mise à jour :** Décembre 2024
**Mainteneur :** Équipe Data_Base
