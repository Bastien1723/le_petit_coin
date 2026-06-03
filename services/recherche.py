"""
Auteurs : Coralie Paillard, Spartalioglou Bastien
Moteur de recherche : filtrage multi-critères du catalogue.
"""

from models.bien import Bien
from models.categorie import Categorie


class MoteurRecherche:
    """
    Permet de chercher et trier les biens du catalogue.

    Attributes:
        catalogue (list[Bien]) : Liste des biens sur lesquels travailler
    """

    def __init__(self, catalogue: list):
        self.catalogue = catalogue

    # ── Recherches simples ────────────────────────────────────────────────────

    def rechercher_par_mot_cle(self, mot_cle: str) -> list:
        """Retourne les biens dont le nom ou la description contient le mot-clé."""
        mot = mot_cle.lower()
        return [
            b for b in self.catalogue
            if not b.est_vendu
            and (mot in b.nom.lower() or mot in b.description.lower())
        ]

    def rechercher_par_categorie(self, categorie: Categorie,
                                  inclure_sous_categories: bool = True) -> list:
        """
        Retourne les biens d'une catégorie donnée.

        Args:
            inclure_sous_categories : Si True, inclut aussi les sous-catégories
        """
        resultats = []
        for b in self.catalogue:
            if b.est_vendu:
                continue
            if b.categorie == categorie:
                resultats.append(b)
            elif inclure_sous_categories and b.categorie.est_descendant_de(categorie):
                resultats.append(b)
        return resultats

    def rechercher_par_prix(self, prix_min: float = 0,
                             prix_max: float = float("inf")) -> list:
        """Retourne les biens dont le prix est dans la fourchette donnée."""
        return [
            b for b in self.catalogue
            if not b.est_vendu and prix_min <= b.prix_souhaite <= prix_max
        ]

    def rechercher_par_etat(self, etat: str) -> list:
        """Retourne les biens d'un état particulier (insensible à la casse)."""
        return [
            b for b in self.catalogue
            if not b.est_vendu and b.etat.lower() == etat.lower()
        ]

    # ── Recherche composée ────────────────────────────────────────────────────

    def recherche_composee(self, mot_cle: str = None, categorie: Categorie = None,
                           prix_min: float = 0, prix_max: float = float("inf"),
                           etat: str = None) -> list:
        """
        Recherche avec plusieurs critères combinés (ET logique).
        Seuls les critères non None sont appliqués.
        """
        resultats = [b for b in self.catalogue if not b.est_vendu]

        if mot_cle:
            mot = mot_cle.lower()
            resultats = [
                b for b in resultats
                if mot in b.nom.lower() or mot in b.description.lower()
            ]

        if categorie:
            resultats = [
                b for b in resultats
                if b.categorie == categorie
                or b.categorie.est_descendant_de(categorie)
            ]

        resultats = [b for b in resultats if prix_min <= b.prix_souhaite <= prix_max]

        if etat:
            resultats = [b for b in resultats if b.etat.lower() == etat.lower()]

        return resultats

    # ── Tri ───────────────────────────────────────────────────────────────────

    def trier_resultats(self, biens: list, critere: str = "prix",
                        ordre_croissant: bool = True) -> list:
        """
        Trie une liste de biens.

        Figure imposée : utilisation de fonctions Lambda.

        Args:
            critere        : "prix" | "rarete" | "opportunite" | "nom"
            ordre_croissant: True = du plus petit au plus grand
        """
        # Dictionnaire de lambdas — une par critère
        criteres = {
            "prix":        lambda b: b.prix_souhaite,
            "rarete":      lambda b: b.categorie.coefficient_rarete,
            "opportunite": lambda b: b.calculer_score_opportunite(),
            "nom":         lambda b: b.nom.lower(),
        }

        cle = criteres.get(critere, criteres["prix"])
        return sorted(biens, key=cle, reverse=not ordre_croissant)
