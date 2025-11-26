#!/usr/bin/env python3
"""
Test de PyCollatinus pour valider qu'il fonctionne correctement.
"""

import sys
sys.path.insert(0, '/tmp/collatinus-python')

print("=" * 60)
print("  TEST DE PYCOLLATINUS")
print("=" * 60)

try:
    print("\n1️⃣  Import de PyCollatinus...")
    from pycollatinus import Lemmatiseur
    print("✅ Import réussi")

    print("\n2️⃣  Initialisation du lemmatiseur...")
    print("⚠️  Cela peut prendre 10-15 secondes au premier chargement...")
    lemmatizer = Lemmatiseur()
    print("✅ Lemmatiseur initialisé")

    print("\n3️⃣  Test sur une phrase simple...")
    test_text = "abbas monachus scriptorium"
    print(f"Texte : \"{test_text}\"")

    results = lemmatizer.lemmatise_multiple(test_text)

    print(f"\n📊 Type de résultat : {type(results)}")
    print(f"📊 Nombre de résultats : {len(results)}")
    print("\n📊 Résultats :")
    print("-" * 60)

    # results est une liste de tuples (mot, analyses)
    for item in results:
        if isinstance(item, tuple) and len(item) == 2:
            word, analyses = item
            if analyses:
                print(f"✅ {word:15} → reconnu ({len(analyses)} analyse(s))")
                for analysis in analyses[:2]:  # Montrer max 2 analyses
                    if hasattr(analysis, 'lemme'):
                        print(f"     - Lemme: {analysis.lemme}")
            else:
                print(f"❌ {word:15} → NON RECONNU")
        else:
            print(f"⚠️  Format inattendu : {item}")

    print("\n" + "=" * 60)
    print("✅ PyCollatinus fonctionne correctement !")
    print("=" * 60)

except ImportError as e:
    print(f"❌ Erreur d'import : {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Erreur : {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
