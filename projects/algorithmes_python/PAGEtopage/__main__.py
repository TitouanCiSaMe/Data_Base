"""
Point d'entrée pour l'exécution en tant que module

Usage:
    python -m PAGEtopage <commande> [options]
"""

from .cli import main
import sys

if __name__ == "__main__":
    sys.exit(main())
