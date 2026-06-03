"""
Auteurs : Coralie Paillard, Spartalioglou Bastien
Point d'entrée console du Simulateur de Marché de Seconde Main.

Lancement :
    python main.py
"""

import json
from pathlib import Path

from models.categorie import Categorie
from models.bien import Bien
from models.utilisateur import Acheteur, Vendeur
from models.transaction import Transaction
from services.stockage import GestionnaireStockage
from services.recherche import MoteurRecherche
from services.optimisation import trouver_meilleure_affaire, trouver_bons_plans, optimiser_panier
from services.recursion import calculer_valeur_totale_recursive


# ── Initialisation ────────────────────────────────────────────────────────────

stockage = GestionnaireStockage("data/sauvegarde.json")
categories: dict = {}


def charger_categories():
    """Charge les catégories depuis data/categories.json."""
    chemin = Path("data/categories.json")
    if not chemin.exists():
        print("⚠ categories.json introuvable — catégories par défaut utilisées.")
        for nom in ["Véhicules", "Électronique", "Maison", "Mode", "Loisirs"]:
            categories[nom.lower()] = Categorie(nom, 1.0)
        return

    with open(chemin, "r", encoding="utf-8") as f:
        donnees = json.load(f)

    def parcourir(data, parent=None):
        cat = Categorie(data["nom"], data.get("coefficient_rarete", 1.0), parent)
        categories[data["nom"].lower()] = cat
        for sous in data.get("sous_categories", []):
            parcourir(sous, cat)

    for c in donnees.get("categories", []):
        parcourir(c)


def obtenir_categorie(nom: str) -> Categorie:
    """Récupère une catégorie existante ou en crée une générique."""
    key = nom.lower()
    if key not in categories:
        categories[key] = Categorie(nom, 1.0)
    return categories[key]


def sauvegarder(catalogue, utilisateurs, transactions):
    if stockage.sauvegarder(catalogue, utilisateurs, transactions):
        print("✓ Données sauvegardées.")


# ── Affichages ────────────────────────────────────────────────────────────────

def afficher_catalogue(catalogue):
    print(f"\n{'='*50}")
    print(f"CATALOGUE ({len(catalogue)} article(s))")
    print("=" * 50)
    if not catalogue:
        print("  Aucun article en vente.")
        return
    for i, b in enumerate(catalogue):
        print(f"  [{i}] {b.nom}")
        print(f"       Prix : {b.prix_souhaite}€  |  Plancher : {b.prix_min}€"
              f"  |  Marge : -{b.pourcentage_negociation:.0f}%")
        print(f"       État : {b.etat}  |  Catégorie : {b.categorie.nom}")
        print(f"       Vendeur : {b.vendeur.nom if b.vendeur else 'Inconnu'}")


def afficher_utilisateurs(utilisateurs):
    print(f"\n{'='*50}")
    print(f"UTILISATEURS ({len(utilisateurs)})")
    print("=" * 50)
    for u in utilisateurs:
        print(f"  • {u}")


# ── Menus ─────────────────────────────────────────────────────────────────────

def menu_creer_utilisateur(utilisateurs, catalogue, transactions):
    print("\n--- CRÉER UN UTILISATEUR ---")
    nom = input("Nom : ").strip()
    try:
        budget = float(input("Budget initial (€) : "))
    except ValueError:
        print("✗ Budget invalide."); return
    role = input("Rôle (A = Acheteur / V = Vendeur) : ").strip().upper()
    u = Acheteur(nom, budget) if role == "A" else Vendeur(nom, budget)
    utilisateurs.append(u)
    sauvegarder(catalogue, utilisateurs, transactions)
    print(f"✓ {u.type_utilisateur()} '{nom}' créé(e).")


def menu_creer_bien(utilisateurs, catalogue, transactions):
    vendeurs = [u for u in utilisateurs if isinstance(u, Vendeur)]
    if not vendeurs:
        print("✗ Créez d'abord un vendeur."); return

    print("\n--- DÉPOSER UNE ANNONCE ---")
    print("Vendeurs disponibles :")
    for i, v in enumerate(vendeurs):
        print(f"  [{i}] {v.nom}")
    try:
        idx = int(input("Choisir le vendeur : "))
        vendeur = vendeurs[idx]
    except (ValueError, IndexError):
        print("✗ Sélection invalide."); return

    nom = input("Nom du bien : ").strip()
    cat_nom = input("Catégorie : ").strip()
    print(f"États valides : {Bien.ETATS_VALIDES}")
    etat = input("État : ").strip()
    try:
        prix = float(input("Prix demandé (€) : "))
        prix_min = float(input("Prix minimum (€) : "))
    except ValueError:
        print("✗ Prix invalide."); return

    try:
        cat = obtenir_categorie(cat_nom)
        bien = Bien(nom, cat, etat, prix, prix_min)
        vendeur.mettre_en_vente(bien)
        catalogue.append(bien)
        sauvegarder(catalogue, utilisateurs, transactions)
        print(f"✓ '{nom}' mis en vente par {vendeur.nom}.")
    except ValueError as e:
        print(f"✗ Erreur : {e}")


def menu_acheter(utilisateurs, catalogue, transactions):
    acheteurs = [u for u in utilisateurs if isinstance(u, Acheteur)]
    if not acheteurs or not catalogue:
        print("✗ Il faut au moins un acheteur et un bien en vente."); return

    print("\n--- RÉALISER UN ACHAT ---")
    print("Acheteurs :")
    for i, a in enumerate(acheteurs):
        print(f"  [{i}] {a.nom} — budget : {a.budget}€")
    try:
        idx_a = int(input("Choisir l'acheteur : "))
        acheteur = acheteurs[idx_a]
    except (ValueError, IndexError):
        print("✗ Sélection invalide."); return

    afficher_catalogue(catalogue)
    try:
        idx_b = int(input("Choisir le bien (numéro) : "))
        bien = catalogue[idx_b]
    except (ValueError, IndexError):
        print("✗ Sélection invalide."); return

    vendeur = bien.vendeur
    if acheteur.acheter_bien(bien):
        t = Transaction(bien, vendeur, acheteur, acheteur.calculer_offre(bien))
        transactions.append(t)
        catalogue.remove(bien)
        sauvegarder(catalogue, utilisateurs, transactions)


def menu_bons_plans(catalogue):
    print("\n--- BONS PLANS 🔥 ---")
    try:
        seuil = float(input("Réduction minimum (%, défaut 20) : ") or "20")
    except ValueError:
        seuil = 20.0
    bons_plans = trouver_bons_plans(catalogue, seuil)
    if not bons_plans:
        print("  Aucun bon plan pour le moment."); return
    for b in bons_plans[:10]:
        print(f"  • {b.nom} — {b.prix_souhaite}€ → min {b.prix_min}€"
              f" (-{b.pourcentage_negociation:.0f}%) [score {b.calculer_score_opportunite():.1f}]")


def menu_assistant(utilisateurs, catalogue):
    acheteurs = [u for u in utilisateurs if isinstance(u, Acheteur)]
    if not acheteurs or not catalogue:
        print("✗ Il faut au moins un acheteur et des biens."); return

    print("\n--- ASSISTANT D'ACHAT INTELLIGENT 🤖 ---")
    for i, a in enumerate(acheteurs):
        print(f"  [{i}] {a.nom} — budget : {a.budget}€")
    try:
        idx = int(input("Pour quel acheteur ? "))
        acheteur = acheteurs[idx]
    except (ValueError, IndexError):
        print("✗ Sélection invalide."); return

    suggestion = acheteur.conseiller_meilleur_achat(catalogue)
    if suggestion:
        print(f"\n  ⭐ Meilleure opportunité pour {acheteur.nom} :")
        print(f"     {suggestion.nom} — {suggestion.prix_souhaite}€"
              f" (min {suggestion.prix_min}€)")
        print(f"     Score d'opportunité : {suggestion.calculer_score_opportunite():.1f}")
    else:
        print(f"  ⚠ Aucun bien accessible pour {acheteur.nom}.")

    # Optimisation du panier
    panier, cout = optimiser_panier(catalogue, acheteur.budget)
    if panier:
        print(f"\n  🛒 Panier optimisé (coût total : {cout:.2f}€) :")
        for b in panier:
            print(f"     • {b.nom} — {b.prix_min}€")


def menu_valeur_catalogue(catalogue):
    if not catalogue:
        print("⚠ Catalogue vide."); return
    # Figure imposée : appel récursif
    total = calculer_valeur_totale_recursive(catalogue)
    print(f"\n  Nombre d'articles : {len(catalogue)}")
    print(f"  Valeur totale     : {total:.2f}€")
    print(f"  Prix moyen        : {total / len(catalogue):.2f}€")


def menu_trier(catalogue):
    if not catalogue:
        print("⚠ Catalogue vide."); return
    print("\n  1. Prix croissant")
    print("  2. Prix décroissant")
    print("  3. Rareté (plus rares en premier)")
    print("  4. Opportunité (meilleures affaires)")
    choix = input("Votre choix : ").strip()

    # Figure imposée : utilisation de fonctions Lambda
    if choix == "1":
        catalogue.sort(key=lambda b: b.prix_souhaite)
        print("✓ Trié par prix croissant.")
    elif choix == "2":
        catalogue.sort(key=lambda b: b.prix_souhaite, reverse=True)
        print("✓ Trié par prix décroissant.")
    elif choix == "3":
        catalogue.sort(key=lambda b: b.categorie.coefficient_rarete, reverse=True)
        print("✓ Trié par rareté.")
    elif choix == "4":
        catalogue.sort(key=lambda b: b.calculer_score_opportunite(), reverse=True)
        print("✓ Trié par opportunité.")
    else:
        print("✗ Choix invalide."); return

    afficher_catalogue(catalogue)


def menu_recherche(catalogue):
    if not catalogue:
        print("⚠ Catalogue vide."); return
    moteur = MoteurRecherche(catalogue)
    print("\n  1. Par mot-clé")
    print("  2. Par fourchette de prix")
    print("  3. Par état")
    choix = input("Votre choix : ").strip()

    if choix == "1":
        kw = input("Mot-clé : ").strip()
        resultats = moteur.rechercher_par_mot_cle(kw)
    elif choix == "2":
        try:
            pmin = float(input("Prix min : "))
            pmax = float(input("Prix max : "))
            resultats = moteur.rechercher_par_prix(pmin, pmax)
        except ValueError:
            print("✗ Prix invalide."); return
    elif choix == "3":
        etat = input("État : ").strip()
        resultats = moteur.rechercher_par_etat(etat)
    else:
        print("✗ Choix invalide."); return

    print(f"\n  {len(resultats)} résultat(s) :")
    for b in resultats:
        print(f"    • {b}")


# ── Boucle principale ─────────────────────────────────────────────────────────

def main():
    charger_categories()
    catalogue, utilisateurs, _ = stockage.charger()
    transactions: list[Transaction] = []
    print(f"✓ {len(utilisateurs)} utilisateur(s), {len(catalogue)} bien(s) chargés.")

    while True:
        print("\n" + "=" * 50)
        print("   SIMULATEUR DE MARCHÉ — MENU PRINCIPAL")
        print("=" * 50)
        print("1.  Créer un utilisateur")
        print("2.  Déposer un bien en vente")
        print("3.  Afficher le catalogue")
        print("4.  Afficher les utilisateurs")
        print("5.  Réaliser un achat")
        print("6.  Bons plans 🔥")
        print("7.  Assistant d'achat intelligent 🤖")
        print("8.  Valeur totale du catalogue (récursif)")
        print("9.  Trier le catalogue (lambda)")
        print("10. Rechercher un bien")
        print("0.  Quitter")

        choix = input("\nVotre choix : ").strip()

        if choix == "1":
            menu_creer_utilisateur(utilisateurs, catalogue, transactions)
        elif choix == "2":
            menu_creer_bien(utilisateurs, catalogue, transactions)
        elif choix == "3":
            afficher_catalogue(catalogue)
        elif choix == "4":
            afficher_utilisateurs(utilisateurs)
        elif choix == "5":
            menu_acheter(utilisateurs, catalogue, transactions)
        elif choix == "6":
            menu_bons_plans(catalogue)
        elif choix == "7":
            menu_assistant(utilisateurs, catalogue)
        elif choix == "8":
            menu_valeur_catalogue(catalogue)
        elif choix == "9":
            menu_trier(catalogue)
        elif choix == "10":
            menu_recherche(catalogue)
        elif choix == "0":
            print("Au revoir !")
            break
        else:
            print("✗ Choix invalide.")


if __name__ == "__main__":
    main()
