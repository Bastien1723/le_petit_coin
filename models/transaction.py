"""
Auteurs : Coralie Paillard, Spartalioglou Bastien
Transaction : enregistrement d'un échange entre acheteur et vendeur.
"""

from datetime import datetime
from models.bien import Bien
from models.utilisateur import Acheteur, Vendeur


class Transaction:
    """
    Représente une transaction finalisée sur le marché.

    Attributes:
        id (int)            : Identifiant unique auto-incrémenté
        bien (Bien)         : Le bien échangé
        vendeur (Vendeur)   : Le vendeur
        acheteur (Acheteur) : L'acheteur
        prix_final (float)  : Prix de vente effectif
        date (datetime)     : Horodatage de la transaction
    """

    _compteur = 0  # Compteur de classe partagé entre toutes les instances

    def __init__(self, bien: Bien, vendeur: Vendeur,
                 acheteur: Acheteur, prix_final: float):
        Transaction._compteur += 1
        self.id = Transaction._compteur
        self.bien = bien
        self.vendeur = vendeur
        self.acheteur = acheteur
        self.prix_final = prix_final
        self.date = datetime.now()

    # ── Propriétés ────────────────────────────────────────────────────────────

    @property
    def reduction_obtenue(self) -> float:
        """Économie réalisée par rapport au prix affiché."""
        return self.bien.prix_souhaite - self.prix_final

    @property
    def pourcentage_reduction(self) -> float:
        """Pourcentage d'économie réalisée."""
        if self.bien.prix_souhaite == 0:
            return 0.0
        return (self.reduction_obtenue / self.bien.prix_souhaite) * 100

    # ── Sérialisation ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Convertit la transaction en dictionnaire pour la sauvegarde JSON."""
        return {
            "id": self.id,
            "bien_nom": self.bien.nom,
            "vendeur": self.vendeur.nom,
            "acheteur": self.acheteur.nom,
            "prix_final": self.prix_final,
            "date": self.date.isoformat(),
        }

    # ── Méthodes spéciales ────────────────────────────────────────────────────

    def __str__(self) -> str:
        return (
            f"Transaction #{self.id} : {self.bien.nom} "
            f"({self.vendeur.nom} → {self.acheteur.nom}) "
            f"pour {self.prix_final}€ "
            f"le {self.date.strftime('%d/%m/%Y %H:%M')}"
        )
