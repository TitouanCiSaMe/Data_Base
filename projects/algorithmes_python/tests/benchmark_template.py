"""
Template pour les tests de performance
Ce script compare les performances entre l'original et l'optimisé
"""

import time
import tracemalloc
from typing import Callable, Any


def benchmark(func: Callable, *args, iterations: int = 1000, **kwargs) -> dict:
    """
    Benchmark une fonction et retourne les métriques de performance

    Args:
        func: Fonction à tester
        iterations: Nombre d'itérations pour la moyenne
        *args, **kwargs: Arguments à passer à la fonction

    Returns:
        dict avec les métriques (temps, mémoire)
    """
    # Mesure du temps
    start_time = time.perf_counter()

    # Mesure de la mémoire
    tracemalloc.start()

    for _ in range(iterations):
        result = func(*args, **kwargs)

    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "temps_total": (end_time - start_time) * 1000,  # en ms
        "temps_moyen": ((end_time - start_time) / iterations) * 1000,  # en ms
        "memoire_actuelle": current / 1024,  # en KB
        "memoire_pic": peak / 1024,  # en KB
        "iterations": iterations
    }


def comparer_performances(func_original: Callable, func_optimise: Callable,
                         test_data: Any, iterations: int = 1000):
    """
    Compare les performances entre deux versions d'un algorithme
    """
    print("=" * 60)
    print("COMPARAISON DE PERFORMANCES")
    print("=" * 60)

    print("\n🔵 Version originale...")
    perf_original = benchmark(func_original, test_data, iterations=iterations)

    print("🟢 Version optimisée...")
    perf_optimise = benchmark(func_optimise, test_data, iterations=iterations)

    print("\n" + "=" * 60)
    print("RÉSULTATS")
    print("=" * 60)

    print(f"\n⏱️  TEMPS D'EXÉCUTION")
    print(f"   Original  : {perf_original['temps_moyen']:.4f} ms/iteration")
    print(f"   Optimisé  : {perf_optimise['temps_moyen']:.4f} ms/iteration")

    gain_temps = ((perf_original['temps_moyen'] - perf_optimise['temps_moyen'])
                  / perf_original['temps_moyen'] * 100)
    print(f"   Gain      : {gain_temps:+.2f}%")

    print(f"\n💾 MÉMOIRE (pic)")
    print(f"   Original  : {perf_original['memoire_pic']:.2f} KB")
    print(f"   Optimisé  : {perf_optimise['memoire_pic']:.2f} KB")

    gain_memoire = ((perf_original['memoire_pic'] - perf_optimise['memoire_pic'])
                    / perf_original['memoire_pic'] * 100)
    print(f"   Gain      : {gain_memoire:+.2f}%")

    print("\n" + "=" * 60)


# Exemple d'utilisation
if __name__ == "__main__":
    # Exemple avec une fonction simple
    def version_originale(n):
        return sum([i**2 for i in range(n)])

    def version_optimisee(n):
        return sum(i**2 for i in range(n))

    comparer_performances(version_originale, version_optimisee, 10000, iterations=100)
