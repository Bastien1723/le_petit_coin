"""
Auteurs : Coralie Paillard, Spartalioglou Bastien
Bien : objet mis en vente sur le marché.
"""

from models.categorie import Categorie


class Bien:
    """
    Représente un bien mis en vente.

    Attributes:
        nom (str)               : Nom du bien
        categorie (Categorie)   : Catégorie du bien (composition)
        etat (str)              : État parmi ETATS_VALIDES
        prix_souhaite (float)   : Prix demandé par le vendeur
        prix_min (float)        : Prix plancher (offre minimum acceptée)
        description (str)       : Description libre
        vendeur                 : Référence au Vendeur (définie à la mise en vente)
    """

    ETATS_VALIDES = ["Neuf", "Très bon état", "Bon état", "Occasion", "À réparer"]

    def __init__(self, nom: str, categorie: Categorie, etat: str,
                 prix_souhaite: float, prix_min: float, description: str = ""):

        # Validations
        if prix_min > prix_souhaite:
            raise ValueError("Le prix minimum ne peut pas dépasser le prix souhaité.")
        if prix_souhaite < 0 or prix_min < 0:
            raise ValueError("Les prix doivent être positifs.")
        if etat not in self.ETATS_VALIDES:
            raise ValueError(f"État invalide. Choix possibles : {self.ETATS_VALIDES}")

        self.nom = nom
        self.categorie = categorie
        self.etat = etat
        self.prix_souhaite = prix_souhaite
        self.prix_min = prix_min
        self.description = description
        self.vendeur = None
        self._est_vendu = False

    # ── Propriétés ────────────────────────────────────────────────────────────

    @property
    def est_vendu(self) -> bool:
        return self._est_vendu

    @property
    def marge_negociation(self) -> float:
        """Écart en euros entre prix demandé et prix minimum."""
        return self.prix_souhaite - self.prix_min

    @property
    def pourcentage_negociation(self) -> float:
        """Pourcentage de réduction possible."""
        if self.prix_souhaite == 0:
            return 0.0
        return (self.marge_negociation / self.prix_souhaite) * 100

    # ── Méthodes ──────────────────────────────────────────────────────────────

    def calculer_score_opportunite(self) -> float:
        """
        Score d'opportunité = marge_negociation × coefficient_rarete.
        Plus le score est élevé, meilleure est l'affaire.
        """
        return self.marge_negociation * self.categorie.coefficient_rarete

    def accepter_offre(self, prix_propose: float) -> bool:
        """Retourne True si l'offre est >= au prix minimum."""
        return prix_propose >= self.prix_min

    def marquer_vendu(self) -> None:
        """Marque définitivement le bien comme vendu."""
        self._est_vendu = True

    # ── Méthodes spéciales ────────────────────────────────────────────────────

    def __str__(self) -> str:
        statut = " [VENDU]" if self._est_vendu else ""
        return (f"{self.nom} - {self.prix_souhaite}€"
                f" ({self.etat}) [{self.categorie.nom}]{statut}")

    def __repr__(self) -> str:
        return f"Bien('{self.nom}', {self.prix_souhaite}€, min={self.prix_min}€)"
