"""Package services."""

from .stockage import GestionnaireStockage
from .recherche import MoteurRecherche
from .optimisation import trouver_meilleure_affaire, trouver_bons_plans, optimiser_panier
from .recursion import calculer_valeur_totale_recursive