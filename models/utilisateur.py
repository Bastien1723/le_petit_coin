"""
Auteurs : Coralie Paillard, Spartalioglou Bastien
Utilisateur / Acheteur / Vendeur : héritage depuis une classe abstraite.
"""

from abc import ABC, abstractmethod
from models.bien import Bien


class Utilisateur(ABC):
    """
    Classe abstraite — base commune pour Acheteur et Vendeur.

    Attributes:
        nom (str)               : Nom de l'utilisateur
        budget (float)          : Argent disponible
        biens_possedes (list)   : Biens actuellement détenus
        favoris (list)          : Biens mis en favoris
    """

    def __init__(self, nom: str, budget: float):
        if budget < 0:
            raise ValueError("Le budget ne peut pas être négatif.")
        self.nom = nom
        self.budget = budget
        self.biens_possedes: list[Bien] = []
        self.favoris: list[Bien] = []

    # ── Méthodes communes ─────────────────────────────────────────────────────

    def ajouter_favori(self, bien: Bien) -> bool:
        """Ajoute un bien aux favoris. Retourne False si déjà présent."""
        if bien not in self.favoris:
            self.favoris.append(bien)
            return True
        return False

    def retirer_favori(self, bien: Bien) -> bool:
        """Retire un bien des favoris. Retourne False si absent."""
        if bien in self.favoris:
            self.favoris.remove(bien)
            return True
        return False

    # ── Méthode abstraite ─────────────────────────────────────────────────────

    @abstractmethod
    def type_utilisateur(self) -> str:
        """Chaque sous-classe retourne son type sous forme de chaîne."""
        pass

    # ── Méthodes spéciales ────────────────────────────────────────────────────

    def __str__(self) -> str:
        return f"{self.nom} ({self.type_utilisateur()}) - Budget : {self.budget}€"


# ══════════════════════════════════════════════════════════════════════════════


class Vendeur(Utilisateur):
    """
    Peut mettre des biens en vente et recevoir des paiements.
    """

    def __init__(self, nom: str, budget: float = 0):
        super().__init__(nom, budget)
        self.biens_en_vente: list[Bien] = []

    def type_utilisateur(self) -> str:
        return "Vendeur"

    def mettre_en_vente(self, bien: Bien) -> None:
        """Associe ce vendeur au bien et l'ajoute à sa liste de vente."""
        bien.vendeur = self
        if bien not in self.biens_en_vente:
            self.biens_en_vente.append(bien)
        if bien not in self.biens_possedes:
            self.biens_possedes.append(bien)

    def retirer_de_la_vente(self, bien: Bien) -> bool:
        """Retire un bien de la liste en vente sans le marquer vendu."""
        if bien in self.biens_en_vente:
            self.biens_en_vente.remove(bien)
            return True
        return False

    def recevoir_paiement(self, montant: float) -> None:
        """Crédite le budget du vendeur après une vente."""
        self.budget += montant

    def finaliser_vente(self, bien: Bien) -> None:
        """Retire le bien des listes du vendeur et le marque comme vendu."""
        if bien in self.biens_en_vente:
            self.biens_en_vente.remove(bien)
        if bien in self.biens_possedes:
            self.biens_possedes.remove(bien)
        bien.marquer_vendu()


# ══════════════════════════════════════════════════════════════════════════════


class Acheteur(Utilisateur):
    """
    Peut acheter des biens et utiliser l'assistant d'optimisation.
    """

    MARGE_NEGOCIATION = 0.10  # 10 % au-dessus du budget autorisé pour négocier

    def __init__(self, nom: str, budget: float):
        super().__init__(nom, budget)
        self.historique_achats: list[Bien] = []

    def type_utilisateur(self) -> str:
        return "Acheteur"

    @property
    def budget_max_negociation(self) -> float:
        """Budget + 10 % : plafond pour pouvoir négocier."""
        return self.budget * (1 + self.MARGE_NEGOCIATION)

    def peut_negocier(self, bien: Bien) -> bool:
        """True si le prix souhaité est ≤ budget + 10 %."""
        return bien.prix_souhaite <= self.budget_max_negociation

    def peut_acheter(self, bien: Bien) -> bool:
        """True si le budget couvre directement le prix souhaité."""
        return self.budget >= bien.prix_souhaite

    def calculer_offre(self, bien: Bien) -> float:
        """L'offre est le minimum entre le budget et le prix demandé."""
        return min(self.budget, bien.prix_souhaite)

    def acheter_bien(self, bien: Bien) -> bool:
        """
        Tente d'acheter un bien.

        Returns:
            True  → transaction réussie (argent transféré, bien attribué)
            False → échec (bien déjà vendu, pas de vendeur, offre refusée)
        """
        if bien.est_vendu:
            print(f"✗ {bien.nom} a déjà été vendu.")
            return False

        if bien.vendeur is None:
            print(f"✗ {bien.nom} n'est pas en vente.")
            return False

        offre = self.calculer_offre(bien)

        if not bien.accepter_offre(offre):
            print(f"✗ Offre de {offre}€ refusée (minimum accepté : {bien.prix_min}€)")
            return False

        # ── Transaction réussie ──
        self.budget -= offre
        bien.vendeur.recevoir_paiement(offre)
        bien.vendeur.finaliser_vente(bien)

        self.biens_possedes.append(bien)
        self.historique_achats.append(bien)

        # On retire le bien des favoris si c'était le cas
        if bien in self.favoris:
            self.favoris.remove(bien)

        print(f"✓ {self.nom} a acheté {bien.nom} pour {offre}€")
        return True

    def conseiller_meilleur_achat(self, catalogue: list[Bien]):
        """
        Figure imposée : Algorithme d'optimisation.
        Retourne le bien avec le meilleur score d'opportunité
        parmi ceux que l'acheteur peut réellement payer.
        """
        accessibles = [
            b for b in catalogue
            if not b.est_vendu
            and self.peut_negocier(b)
            and b.accepter_offre(self.budget)
        ]

        if not accessibles:
            return None

        return max(accessibles, key=lambda b: b.calculer_score_opportunite())
