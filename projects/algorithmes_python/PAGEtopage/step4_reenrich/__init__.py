"""
Étape 4: Ré-enrichissement

Permet de ré-enrichir des fichiers texte corrigés manuellement
pour régénérer le format vertical avec les nouvelles corrections.
"""

from .reenricher import ReEnricher, reenrich_from_text

__all__ = ['ReEnricher', 'reenrich_from_text']
