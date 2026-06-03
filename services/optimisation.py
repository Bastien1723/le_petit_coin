"""
Auteurs : Coralie Paillard, Spartalioglou Bastien
Figure imposée : Algorithmes d'optimisation.
"""

from models.bien import Bien


def trouver_meilleure_affaire(catalogue: list, budget: float):
    """
    Trouve la meilleure affaire accessible dans le catalogue.

    Critère : maximiser le score d'opportunité (marge × coefficient_rareté)
    Contrainte : prix_min ≤ budget

    Args:
        catalogue : Liste de Bien disponibles
        budget    : Budget maximum de l'acheteur

    Returns:
        Le meilleur Bien ou None si aucun n'est accessible
    """
    accessibles = [
        b for b in catalogue
        if not b.est_vendu and b.prix_min <= budget
    ]

    if not accessibles:
        return None

    return max(accessibles, key=lambda b: b.calculer_score_opportunite())


def trouver_bons_plans(catalogue: list, seuil_reduction: float = 20.0) -> list:
    """
    Identifie les bons plans : biens avec une marge de négociation ≥ seuil.

    Args:
        catalogue        : Liste de Bien disponibles
        seuil_reduction  : Pourcentage minimum de réduction possible (défaut 20%)

    Returns:
        Liste triée par score d'opportunité décroissant
    """
    bons_plans = [
        b for b in catalogue
        if not b.est_vendu and b.pourcentage_negociation >= seuil_reduction
    ]

    # Figure imposée : utilisation d'une fonction Lambda pour le tri
    bons_plans.sort(key=lambda b: b.calculer_score_opportunite(), reverse=True)
    return bons_plans


def optimiser_panier(catalogue: list, budget: float,
                     max_articles: int = 5) -> tuple:
    """
    Algorithme GLOUTON pour optimiser un panier d'achats.

    Stratégie : trier par ratio (score / prix_min) décroissant,
                puis sélectionner les biens tant que le budget le permet.

    Args:
        catalogue    : Liste de Bien disponibles
        budget       : Budget total disponible
        max_articles : Nombre maximum d'articles (défaut 5)

    Returns:
        Tuple (liste des biens sélectionnés, coût total)
    """
    accessibles = [
        b for b in catalogue
        if not b.est_vendu and b.prix_min <= budget
    ]

    # Tri par rapport qualité-prix (lambda)
    accessibles.sort(
        key=lambda b: b.calculer_score_opportunite() / max(b.prix_min, 0.01),
        reverse=True
    )

    panier = []
    cout_total = 0.0
    budget_restant = budget

    for bien in accessibles:
        if len(panier) >= max_articles:
            break
        if bien.prix_min <= budget_restant:
            panier.append(bien)
            cout_total += bien.prix_min
            budget_restant -= bien.prix_min

    return panier, cout_total


def suggerer_similaires(bien_reference: Bien, catalogue: list, limite: int = 5) -> list:
    """
    Suggère des biens similaires à un bien de référence.

    Critères : même catégorie (ou sous-catégorie) et prix dans ±30 %.

    Args:
        bien_reference : Bien de référence
        catalogue      : Catalogue complet
        limite         : Nombre maximum de suggestions

    Returns:
        Liste des biens similaires triés par proximité de prix
    """
    prix_ref = bien_reference.prix_souhaite
    marge = 0.30

    similaires = [
        b for b in catalogue
        if not b.est_vendu
        and b != bien_reference
        and (
            b.categorie == bien_reference.categorie
            or b.categorie.est_descendant_de(bien_reference.categorie)
            or bien_reference.categorie.est_descendant_de(b.categorie)
        )
        and prix_ref * (1 - marge) <= b.prix_souhaite <= prix_ref * (1 + marge)
    ]

    similaires.sort(key=lambda b: abs(b.prix_souhaite - prix_ref))
    return similaires[:limite]
