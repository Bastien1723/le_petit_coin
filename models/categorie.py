"""
Auteurs : Coralie Paillard, Spartalioglou Bastien
Catégorie : structure hiérarchique des catégories de biens (composition).
"""


class Categorie:
    """
    Représente une catégorie de bien avec ses sous-catégories.

    Attributes:
        nom (str)                       : Nom de la catégorie
        coefficient_rarete (float)      : Multiplie la marge → score d'opportunité
        parent (Categorie | None)       : Catégorie parente
        sous_categories (list)          : Sous-catégories directes
    """

    def __init__(self, nom: str, coefficient_rarete: float = 1.0, parent=None):
        self.nom = nom
        self.coefficient_rarete = coefficient_rarete
        self.parent = parent
        self.sous_categories = []

        # On s'ajoute automatiquement aux sous-catégories du parent
        if parent:
            parent.ajouter_sous_categorie(self)

    # ── Méthodes ──────────────────────────────────────────────────────────────

    def ajouter_sous_categorie(self, categorie) -> None:
        """Ajoute une sous-catégorie (évite les doublons)."""
        if categorie not in self.sous_categories:
            self.sous_categories.append(categorie)
            categorie.parent = self

    def chemin_complet(self) -> str:
        """Retourne le chemin hiérarchique : 'Véhicules > Voitures > Peugeot'."""
        if self.parent:
            return f"{self.parent.chemin_complet()} > {self.nom}"
        return self.nom

    def est_descendant_de(self, categorie) -> bool:
        """Vérifie si cette catégorie est une sous-catégorie (directe ou indirecte)."""
        if self.parent is None:
            return False
        if self.parent == categorie:
            return True
        return self.parent.est_descendant_de(categorie)

    # ── Méthodes spéciales ────────────────────────────────────────────────────

    def __str__(self) -> str:
        return f"{self.nom} (rareté: {self.coefficient_rarete})"

    def __repr__(self) -> str:
        return f"Categorie('{self.nom}', {self.coefficient_rarete})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Categorie):
            return False
        return self.nom.lower() == other.nom.lower()

    def __hash__(self) -> int:
        return hash(self.nom.lower())
