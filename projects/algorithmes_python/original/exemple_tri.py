"""
Exemple d'algorithme à analyser
Placez vos algorithmes dans ce dossier avec une structure similaire
"""

def tri_bulles(liste):
    """
    Algorithme de tri à bulles
    À analyser et optimiser
    """
    n = len(liste)
    for i in range(n):
        for j in range(0, n - i - 1):
            if liste[j] > liste[j + 1]:
                liste[j], liste[j + 1] = liste[j + 1], liste[j]
    return liste


if __name__ == "__main__":
    # Test simple
    test = [64, 34, 25, 12, 22, 11, 90]
    print(f"Liste originale : {test}")
    print(f"Liste triée : {tri_bulles(test.copy())}")
