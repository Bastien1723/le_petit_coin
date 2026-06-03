"""
Auteurs : Coralie Paillard, Spartalioglou Bastien
Figure imposée : Fonctions récursives au cœur du projet.
"""

from models.bien import Bien
from models.categorie import Categorie


def calculer_valeur_totale_recursive(liste_biens: list) -> float:
    """
    Calcule la somme des prix du catalogue de manière RÉCURSIVE.

    Cas de base  : liste vide → retourne 0
    Cas récursif : prix du premier élément + valeur du reste

    Args:
        liste_biens : Liste de Bien

    Returns:
        Somme totale des prix souhaités (float)
    """
    if not liste_biens:          # Cas de base
        return 0.0
    return liste_biens[0].prix_souhaite + calculer_valeur_totale_recursive(liste_biens[1:])


def rechercher_dans_categories_recursive(categorie: Categorie, nom_recherche: str):
    """
    Recherche RÉCURSIVE d'une catégorie par nom dans l'arborescence.

    Cas de base  : le nom correspond → retourne la catégorie
    Cas récursif : cherche dans les sous-catégories

    Args:
        categorie      : Catégorie racine de la recherche
        nom_recherche  : Nom à trouver (insensible à la casse)

    Returns:
        La Categorie trouvée ou None
    """
    if categorie.nom.lower() == nom_recherche.lower():   # Cas de base
        return categorie

    for sous_cat in categorie.sous_categories:           # Cas récursif
        resultat = rechercher_dans_categories_recursive(sous_cat, nom_recherche)
        if resultat:
            return resultat

    return None


def filtrer_biens_recursive(biens: list, prix_max: float) -> list:
    """
    Filtre RÉCURSIVEMENT les biens dont le prix ≤ prix_max.

    Cas de base  : liste vide → retourne []
    Cas récursif : inclut ou non le premier élément, puis traite le reste

    Args:
        biens    : Liste de Bien à filtrer
        prix_max : Prix maximum accepté

    Returns:
        Liste filtrée
    """
    if not biens:                        # Cas de base
        return []

    premier = biens[0]
    reste = filtrer_biens_recursive(biens[1:], prix_max)

    if premier.prix_souhaite <= prix_max:
        return [premier] + reste
    return reste


def compter_biens_par_categorie_recursive(biens: list, categorie: Categorie) -> int:
    """
    Compte RÉCURSIVEMENT les biens appartenant à une catégorie
    (y compris ses sous-catégories).

    Args:
        biens      : Liste de Bien
        categorie  : Catégorie cible

    Returns:
        Nombre de biens correspondants (int)
    """
    if not biens:
        return 0

    premier = biens[0]
    compte = 1 if (
        premier.categorie == categorie
        or premier.categorie.est_descendant_de(categorie)
    ) else 0

    return compte + compter_biens_par_categorie_recursive(biens[1:], categorie)
