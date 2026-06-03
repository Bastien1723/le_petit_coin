"""
Auteurs : Coralie Paillard, Spartalioglou Bastien
Tests unitaires — Figure imposée : ≥ 4 méthodes testées, ≥ 2 cas par méthode.

Lancement :
    python -m pytest tests/ -v
    python -m unittest discover tests -v
"""

import unittest
import sys
from pathlib import Path

# Permet d'importer les modules depuis la racine du projet
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.categorie import Categorie
from models.bien import Bien
from models.utilisateur import Acheteur, Vendeur
from models.transaction import Transaction
from services.recursion import (
    calculer_valeur_totale_recursive,
    filtrer_biens_recursive,
    rechercher_dans_categories_recursive,
)
from services.optimisation import (
    trouver_meilleure_affaire,
    trouver_bons_plans,
    optimiser_panier,
)


# ══════════════════════════════════════════════════════════════════════════════
# 1. CATEGORIE
# ══════════════════════════════════════════════════════════════════════════════

class TestCategorie(unittest.TestCase):
    """Tests pour la classe Categorie."""

    def setUp(self):
        self.parent = Categorie("Électronique", 1.2)
        self.enfant = Categorie("Téléphones", 1.0, self.parent)
        self.petit_enfant = Categorie("Apple", 1.3, self.enfant)

    def test_creation_sans_parent(self):
        """Cas 1 : Catégorie sans parent."""
        cat = Categorie("Sport", 1.0)
        self.assertEqual(cat.nom, "Sport")
        self.assertEqual(cat.coefficient_rarete, 1.0)
        self.assertIsNone(cat.parent)

    def test_creation_avec_parent(self):
        """Cas 2 : Catégorie avec parent — composition bidirectionnelle."""
        self.assertEqual(self.enfant.parent, self.parent)
        self.assertIn(self.enfant, self.parent.sous_categories)

    def test_chemin_complet_profond(self):
        """Cas 1 : Chemin hiérarchique sur 3 niveaux."""
        self.assertEqual(
            self.petit_enfant.chemin_complet(),
            "Électronique > Téléphones > Apple"
        )

    def test_chemin_complet_racine(self):
        """Cas 2 : Une catégorie racine retourne simplement son nom."""
        self.assertEqual(self.parent.chemin_complet(), "Électronique")

    def test_est_descendant_vrai(self):
        """Cas 1 : Descendance directe et indirecte."""
        self.assertTrue(self.petit_enfant.est_descendant_de(self.parent))
        self.assertTrue(self.petit_enfant.est_descendant_de(self.enfant))

    def test_est_descendant_faux(self):
        """Cas 2 : Un parent n'est pas descendant de son enfant."""
        self.assertFalse(self.parent.est_descendant_de(self.enfant))


# ══════════════════════════════════════════════════════════════════════════════
# 2. BIEN
# ══════════════════════════════════════════════════════════════════════════════

class TestBien(unittest.TestCase):
    """Tests pour la classe Bien."""

    def setUp(self):
        self.cat = Categorie("Électronique", 1.5)
        self.bien = Bien("iPhone 14", self.cat, "Bon état", 800, 600)

    def test_creation_valide(self):
        """Cas 1 : Création correcte avec attributs bien initialisés."""
        self.assertEqual(self.bien.nom, "iPhone 14")
        self.assertEqual(self.bien.prix_souhaite, 800)
        self.assertEqual(self.bien.prix_min, 600)
        self.assertFalse(self.bien.est_vendu)

    def test_creation_prix_invalide(self):
        """Cas 2 : ValueError si prix_min > prix_souhaite."""
        with self.assertRaises(ValueError):
            Bien("Test", self.cat, "Neuf", 100, 200)

    def test_marge_negociation(self):
        """Cas 1 : Marge = prix_souhaite - prix_min."""
        self.assertEqual(self.bien.marge_negociation, 200)

    def test_pourcentage_negociation(self):
        """Cas 2 : Pourcentage = (200 / 800) × 100 = 25 %."""
        self.assertEqual(self.bien.pourcentage_negociation, 25.0)

    def test_score_opportunite(self):
        """Cas 1 : Score = marge × coef = 200 × 1.5 = 300."""
        self.assertEqual(self.bien.calculer_score_opportunite(), 300)

    def test_accepter_offre(self):
        """Cas 2 : Accepte si offre ≥ prix_min, refuse sinon."""
        self.assertTrue(self.bien.accepter_offre(600))
        self.assertTrue(self.bien.accepter_offre(800))
        self.assertFalse(self.bien.accepter_offre(599))


# ══════════════════════════════════════════════════════════════════════════════
# 3. ACHETEUR
# ══════════════════════════════════════════════════════════════════════════════

class TestAcheteur(unittest.TestCase):
    """Tests pour la classe Acheteur."""

    def setUp(self):
        self.acheteur = Acheteur("Alice", 500)
        self.vendeur = Vendeur("Bob", 100)
        self.cat = Categorie("Sport", 1.0)
        self.bien = Bien("Vélo", self.cat, "Occasion", 400, 300)
        self.vendeur.mettre_en_vente(self.bien)

    def test_peut_negocier_succes(self):
        """Cas 1 : Prix ≤ budget + 10 % → True (400 ≤ 550)."""
        self.assertTrue(self.acheteur.peut_negocier(self.bien))

    def test_peut_negocier_echec(self):
        """Cas 2 : Prix > budget + 10 % → False (400 > 330)."""
        self.acheteur.budget = 300
        bien_cher = Bien("VTT Pro", self.cat, "Neuf", 400, 350)
        self.assertFalse(self.acheteur.peut_negocier(bien_cher))

    def test_acheter_succes(self):
        """Cas 1 : Argent transféré, bien attribué à l'acheteur."""
        resultat = self.acheteur.acheter_bien(self.bien)
        self.assertTrue(resultat)
        self.assertEqual(self.acheteur.budget, 100)   # 500 - 400
        self.assertEqual(self.vendeur.budget, 500)    # 100 + 400
        self.assertIn(self.bien, self.acheteur.biens_possedes)

    def test_acheter_echec_budget(self):
        """Cas 2 : Budget < prix_min → refus, argent inchangé."""
        self.acheteur.budget = 250   # offre = 250 < prix_min = 300
        resultat = self.acheteur.acheter_bien(self.bien)
        self.assertFalse(resultat)
        self.assertEqual(self.vendeur.budget, 100)    # inchangé


# ══════════════════════════════════════════════════════════════════════════════
# 4. VENDEUR
# ══════════════════════════════════════════════════════════════════════════════

class TestVendeur(unittest.TestCase):
    """Tests pour la classe Vendeur."""

    def setUp(self):
        self.vendeur = Vendeur("Charlie", 200)
        self.cat = Categorie("Électroménager", 0.9)
        self.bien = Bien("Lave-linge", self.cat, "Bon état", 300, 200)

    def test_mettre_en_vente_vendeur(self):
        """Cas 1 : Le vendeur est bien associé au bien."""
        self.vendeur.mettre_en_vente(self.bien)
        self.assertEqual(self.bien.vendeur, self.vendeur)
        self.assertIn(self.bien, self.vendeur.biens_en_vente)

    def test_mettre_en_vente_possession(self):
        """Cas 2 : Le bien est aussi dans biens_possedes du vendeur."""
        self.vendeur.mettre_en_vente(self.bien)
        self.assertIn(self.bien, self.vendeur.biens_possedes)

    def test_recevoir_paiement(self):
        """Cas 1 : Le budget augmente du montant reçu."""
        self.vendeur.recevoir_paiement(150)
        self.assertEqual(self.vendeur.budget, 350)

    def test_finaliser_vente(self):
        """Cas 2 : Le bien est retiré des listes et marqué vendu."""
        self.vendeur.mettre_en_vente(self.bien)
        self.vendeur.finaliser_vente(self.bien)
        self.assertNotIn(self.bien, self.vendeur.biens_en_vente)
        self.assertTrue(self.bien.est_vendu)


# ══════════════════════════════════════════════════════════════════════════════
# 5. FONCTIONS RÉCURSIVES
# ══════════════════════════════════════════════════════════════════════════════

class TestRecursion(unittest.TestCase):
    """Tests pour les fonctions récursives (figure imposée)."""

    def setUp(self):
        self.cat = Categorie("Test", 1.0)
        # Prix : 100, 200, 300, 400, 500
        self.biens = [
            Bien(f"Objet {i}", self.cat, "Neuf", (i + 1) * 100, i * 100)
            for i in range(5)
        ]

    def test_valeur_totale_normale(self):
        """Cas 1 : Somme correcte = 100+200+300+400+500 = 1500."""
        self.assertEqual(calculer_valeur_totale_recursive(self.biens), 1500)

    def test_valeur_totale_vide(self):
        """Cas 2 : Liste vide → 0."""
        self.assertEqual(calculer_valeur_totale_recursive([]), 0)

    def test_filtrer_biens_avec_resultats(self):
        """Cas 1 : Filtre prix ≤ 300 → 3 biens (100, 200, 300)."""
        resultats = filtrer_biens_recursive(self.biens, 300)
        self.assertEqual(len(resultats), 3)

    def test_filtrer_biens_sans_resultat(self):
        """Cas 2 : Filtre prix ≤ 50 → liste vide."""
        resultats = filtrer_biens_recursive(self.biens, 50)
        self.assertEqual(len(resultats), 0)

    def test_rechercher_categorie_trouvee(self):
        """Cas 1 : Catégorie trouvée dans l'arborescence."""
        parent = Categorie("Véhicules", 1.0)
        enfant = Categorie("Voitures", 1.0, parent)
        resultat = rechercher_dans_categories_recursive(parent, "Voitures")
        self.assertEqual(resultat, enfant)

    def test_rechercher_categorie_absente(self):
        """Cas 2 : Catégorie absente → None."""
        cat = Categorie("Mode", 1.0)
        resultat = rechercher_dans_categories_recursive(cat, "Inexistant")
        self.assertIsNone(resultat)


# ══════════════════════════════════════════════════════════════════════════════
# 6. OPTIMISATION
# ══════════════════════════════════════════════════════════════════════════════

class TestOptimisation(unittest.TestCase):
    """Tests pour les algorithmes d'optimisation (figure imposée)."""

    def setUp(self):
        self.cat_std = Categorie("Standard", 1.0)
        self.cat_rare = Categorie("Rare", 3.0)

        self.bien_std  = Bien("Objet standard", self.cat_std,  "Neuf", 100,  80)
        self.bien_rare = Bien("Objet rare",     self.cat_rare, "Neuf", 150, 100)
        self.bien_cher = Bien("Objet cher",     self.cat_std,  "Neuf", 1000, 900)

        self.catalogue = [self.bien_std, self.bien_rare, self.bien_cher]

    def test_meilleure_affaire_budget_large(self):
        """
        Cas 1 : Parmi les biens accessibles, choisit le score max.
        bien_rare → marge=50, coef=3 → score=150 (le plus élevé accessible)
        """
        meilleur = trouver_meilleure_affaire(self.catalogue, 500)
        self.assertEqual(meilleur, self.bien_rare)

    def test_meilleure_affaire_budget_limite(self):
        """Cas 2 : Budget 90 → seul bien_std accessible (prix_min=80)."""
        meilleur = trouver_meilleure_affaire(self.catalogue, 90)
        self.assertEqual(meilleur, self.bien_std)

    def test_bons_plans_seuil(self):
        """
        Cas 1 : Seuil 20 % → bien_rare (33%) et bien_std (20%) inclus,
                              bien_cher (10%) exclu.
        """
        bons = trouver_bons_plans(self.catalogue, seuil_reduction=20.0)
        self.assertIn(self.bien_rare, bons)
        self.assertIn(self.bien_std, bons)
        self.assertNotIn(self.bien_cher, bons)

    def test_bons_plans_seuil_trop_haut(self):
        """Cas 2 : Seuil 50 % → aucun bien ne correspond."""
        bons = trouver_bons_plans(self.catalogue, seuil_reduction=50.0)
        self.assertEqual(len(bons), 0)


# ══════════════════════════════════════════════════════════════════════════════
# 7. FAVORIS
# ══════════════════════════════════════════════════════════════════════════════

class TestFavoris(unittest.TestCase):
    """Tests pour la gestion des favoris."""

    def setUp(self):
        self.acheteur = Acheteur("Test", 1000)
        self.cat = Categorie("Test", 1.0)
        self.bien = Bien("Objet", self.cat, "Neuf", 100, 80)

    def test_ajouter_favori(self):
        """Cas 1 : Ajout réussi → True, bien présent dans favoris."""
        resultat = self.acheteur.ajouter_favori(self.bien)
        self.assertTrue(resultat)
        self.assertIn(self.bien, self.acheteur.favoris)

    def test_ajouter_favori_doublon(self):
        """Cas 2 : Doublon refusé → False, 1 seul exemplaire dans favoris."""
        self.acheteur.ajouter_favori(self.bien)
        resultat = self.acheteur.ajouter_favori(self.bien)
        self.assertFalse(resultat)
        self.assertEqual(len(self.acheteur.favoris), 1)


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
