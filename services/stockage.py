"""
Auteurs : Coralie Paillard, Spartalioglou Bastien
Figure imposée : Stockage de données (fichiers JSON).
Sauvegarde et chargement de l'état complet du marché.
"""

import json
from pathlib import Path
from models.categorie import Categorie
from models.bien import Bien
from models.utilisateur import Acheteur, Vendeur, Utilisateur
from models.transaction import Transaction


class GestionnaireStockage:
    """
    Gère la persistance des données via des fichiers JSON.

    Attributes:
        chemin_fichier (Path) : Chemin vers le fichier de sauvegarde
    """

    def __init__(self, chemin_fichier: str = "data/sauvegarde.json"):
        self.chemin_fichier = Path(chemin_fichier)
        # Crée automatiquement le dossier data/ s'il n'existe pas
        self.chemin_fichier.parent.mkdir(parents=True, exist_ok=True)

    # ── Sauvegarde ────────────────────────────────────────────────────────────

    def sauvegarder(self, catalogue: list, utilisateurs: list,
                    transactions: list = None) -> bool:
        """
        Sauvegarde l'état complet du marché dans le fichier JSON.

        Returns:
            True si la sauvegarde a réussi, False sinon.
        """
        donnees = {
            "biens": [self._bien_to_dict(b) for b in catalogue],
            "utilisateurs": [self._utilisateur_to_dict(u) for u in utilisateurs],
            "transactions": [t.to_dict() for t in (transactions or [])],
        }
        try:
            with open(self.chemin_fichier, "w", encoding="utf-8") as f:
                json.dump(donnees, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Erreur de sauvegarde : {e}")
            return False

    # ── Chargement ────────────────────────────────────────────────────────────

    def charger(self) -> tuple:
        """
        Charge les données depuis le fichier JSON.

        Returns:
            Tuple (catalogue, utilisateurs, transactions_dict)
            Retourne ([], [], []) si le fichier est absent ou corrompu.
        """
        if not self.chemin_fichier.exists():
            return [], [], []

        try:
            with open(self.chemin_fichier, "r", encoding="utf-8") as f:
                donnees = json.load(f)

            utilisateurs = self._charger_utilisateurs(donnees.get("utilisateurs", []))
            catalogue = self._charger_biens(donnees.get("biens", []), utilisateurs)
            transactions = donnees.get("transactions", [])

            return catalogue, utilisateurs, transactions

        except (IOError, json.JSONDecodeError) as e:
            print(f"Erreur de chargement : {e}")
            return [], [], []

    # ── Sérialisation privée ──────────────────────────────────────────────────

    def _bien_to_dict(self, bien: Bien) -> dict:
        return {
            "nom": bien.nom,
            "categorie_nom": bien.categorie.nom,
            "categorie_coef": bien.categorie.coefficient_rarete,
            "etat": bien.etat,
            "prix_souhaite": bien.prix_souhaite,
            "prix_min": bien.prix_min,
            "description": bien.description,
            "vendeur_nom": bien.vendeur.nom if bien.vendeur else None,
            "est_vendu": bien.est_vendu,
        }

    def _utilisateur_to_dict(self, utilisateur: Utilisateur) -> dict:
        data = {
            "nom": utilisateur.nom,
            "budget": utilisateur.budget,
            "type": utilisateur.type_utilisateur(),
            "favoris": [b.nom for b in utilisateur.favoris],
        }
        if isinstance(utilisateur, Vendeur):
            data["biens_en_vente"] = [b.nom for b in utilisateur.biens_en_vente]
        elif isinstance(utilisateur, Acheteur):
            data["historique_achats"] = [b.nom for b in utilisateur.historique_achats]
        return data

    # ── Désérialisation privée ────────────────────────────────────────────────

    def _charger_utilisateurs(self, donnees: list) -> list:
        utilisateurs = []
        for u in donnees:
            if u["type"] == "Acheteur":
                utilisateurs.append(Acheteur(u["nom"], u["budget"]))
            else:
                utilisateurs.append(Vendeur(u["nom"], u["budget"]))
        return utilisateurs

    def _charger_biens(self, donnees: list, utilisateurs: list) -> list:
        catalogue = []
        vendeurs = {u.nom: u for u in utilisateurs if isinstance(u, Vendeur)}

        for b in donnees:
            cat = Categorie(b["categorie_nom"], b.get("categorie_coef", 1.0))
            bien = Bien(
                b["nom"], cat, b["etat"],
                b["prix_souhaite"], b["prix_min"],
                b.get("description", ""),
            )
            # Rattacher au vendeur si celui-ci existe
            vendeur_nom = b.get("vendeur_nom")
            if vendeur_nom and vendeur_nom in vendeurs:
                vendeurs[vendeur_nom].mettre_en_vente(bien)

            if not b.get("est_vendu", False):
                catalogue.append(bien)

        return catalogue
