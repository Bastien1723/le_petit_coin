"""
Auteurs : Coralie Paillard, Spartalioglou Bastien
Serveur Flask — Interface web du simulateur de marché.

Lancement :
    python app.py
Puis ouvre : http://localhost:5000
"""

import json
from pathlib import Path
from flask import Flask, jsonify, request, render_template

from models.categorie import Categorie
from models.bien import Bien
from models.utilisateur import Acheteur, Vendeur
from models.transaction import Transaction
from services.stockage import GestionnaireStockage
from services.recherche import MoteurRecherche
from services.optimisation import trouver_meilleure_affaire, trouver_bons_plans, optimiser_panier
from services.recursion import calculer_valeur_totale_recursive

app = Flask(__name__)

# ── État global ───────────────────────────────────────────────────────────────
catalogue: list[Bien] = []
utilisateurs: list = []
transactions: list[Transaction] = []
categories: dict = {}
stockage = GestionnaireStockage("data/sauvegarde.json")


# ── Helpers ───────────────────────────────────────────────────────────────────

def bien_to_dict(b: Bien) -> dict:
    return {
        "id":           id(b),
        "nom":          b.nom,
        "categorie":    b.categorie.nom,
        "categorie_coef": b.categorie.coefficient_rarete,
        "etat":         b.etat,
        "prix":         b.prix_souhaite,
        "prixMin":      b.prix_min,
        "description":  b.description,
        "vendeur":      b.vendeur.nom if b.vendeur else None,
        "estVendu":     b.est_vendu,
        "marge":        b.marge_negociation,
        "pctNeg":       round(b.pourcentage_negociation, 1),
        "score":        round(b.calculer_score_opportunite(), 2),
    }

def user_to_dict(u) -> dict:
    base = {
        "id":     id(u),
        "nom":    u.nom,
        "budget": u.budget,
        "type":   u.type_utilisateur(),
        "favoris": [id(b) for b in u.favoris],
    }
    if isinstance(u, Vendeur):
        base["biens_en_vente"] = [id(b) for b in u.biens_en_vente]
    elif isinstance(u, Acheteur):
        base["historique"] = [id(b) for b in u.historique_achats]
    return base

def tx_to_dict(t: Transaction) -> dict:
    return {
        "id":          t.id,
        "bien":        t.bien.nom,
        "vendeur":     t.vendeur.nom,
        "acheteur":    t.acheteur.nom,
        "prix":        t.prix_final,
        "reduction":   round(t.reduction_obtenue, 2),
        "pctReduction": round(t.pourcentage_reduction, 1),
        "date":        t.date.strftime("%d/%m/%Y %H:%M"),
    }

def find_bien(obj_id: int):
    return next((b for b in catalogue if id(b) == obj_id), None)

def find_user(obj_id: int):
    return next((u for u in utilisateurs if id(u) == obj_id), None)

def get_or_create_cat(nom: str) -> Categorie:
    key = nom.lower()
    if key not in categories:
        categories[key] = Categorie(nom, 1.0)
    return categories[key]

def sauvegarder():
    stockage.sauvegarder(catalogue, utilisateurs, transactions)


# ── Initialisation ────────────────────────────────────────────────────────────

def init():
    chemin = Path("data/categories.json")
    if chemin.exists():
        with open(chemin, "r", encoding="utf-8") as f:
            data = json.load(f)
        def parcourir(d, parent=None):
            cat = Categorie(d["nom"], d.get("coefficient_rarete", 1.0), parent)
            categories[d["nom"].lower()] = cat
            for s in d.get("sous_categories", []):
                parcourir(s, cat)
        for c in data.get("categories", []):
            parcourir(c)

    saved_cat, saved_users, _ = stockage.charger()
    catalogue.extend(saved_cat)
    utilisateurs.extend(saved_users)
    print(f"✓ {len(utilisateurs)} utilisateur(s), {len(catalogue)} bien(s) chargés.")


# ══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")


# ── Catalogue ─────────────────────────────────────────────────────────────────

@app.route("/api/catalogue")
def api_catalogue():
    q       = request.args.get("q", "").strip()
    cat_nom = request.args.get("categorie", "").strip()
    pmin    = float(request.args.get("prix_min", 0))
    pmax    = float(request.args.get("prix_max", 1e9))
    etat    = request.args.get("etat", "").strip()
    tri     = request.args.get("tri", "prix")

    moteur = MoteurRecherche(catalogue)

    if q:
        biens = moteur.rechercher_par_mot_cle(q)
    elif cat_nom:
        cat = get_or_create_cat(cat_nom)
        biens = moteur.rechercher_par_categorie(cat)
    else:
        biens = [b for b in catalogue if not b.est_vendu]

    biens = [b for b in biens if pmin <= b.prix_souhaite <= pmax]
    if etat:
        biens = [b for b in biens if b.etat.lower() == etat.lower()]

    biens = moteur.trier_resultats(biens, tri, ordre_croissant=(tri not in ["opportunite", "rarete"]))
    total = calculer_valeur_totale_recursive(biens)

    return jsonify({"biens": [bien_to_dict(b) for b in biens],
                    "total": round(total, 2), "count": len(biens)})


@app.route("/api/catalogue/<int:bien_id>")
def api_bien_detail(bien_id):
    b = find_bien(bien_id)
    if not b:
        return jsonify({"error": "Introuvable"}), 404
    return jsonify(bien_to_dict(b))


# ── Bons plans & optimisation ─────────────────────────────────────────────────

@app.route("/api/bons-plans")
def api_bons_plans():
    seuil = float(request.args.get("seuil", 20.0))
    return jsonify({"biens": [bien_to_dict(b) for b in trouver_bons_plans(catalogue, seuil)]})


@app.route("/api/meilleure-affaire")
def api_meilleure_affaire():
    budget = float(request.args.get("budget", 0))
    b = trouver_meilleure_affaire(catalogue, budget)
    return jsonify({"bien": bien_to_dict(b) if b else None})


@app.route("/api/optimiser-panier")
def api_optimiser_panier():
    budget = float(request.args.get("budget", 0))
    max_a  = int(request.args.get("max", 5))
    panier, cout = optimiser_panier(catalogue, budget, max_a)
    return jsonify({"panier": [bien_to_dict(b) for b in panier], "cout_total": round(cout, 2)})


# ── Utilisateurs ──────────────────────────────────────────────────────────────

@app.route("/api/utilisateurs")
def api_utilisateurs():
    return jsonify({"utilisateurs": [user_to_dict(u) for u in utilisateurs]})


@app.route("/api/utilisateurs", methods=["POST"])
def api_creer_utilisateur():
    d = request.get_json()
    nom    = d.get("nom", "").strip()
    budget = float(d.get("budget", 0))
    type_u = d.get("type", "Acheteur")
    if not nom:
        return jsonify({"error": "Nom requis"}), 400
    u = Acheteur(nom, budget) if type_u == "Acheteur" else Vendeur(nom, budget)
    utilisateurs.append(u)
    sauvegarder()
    return jsonify({"utilisateur": user_to_dict(u)}), 201


# ── Biens ─────────────────────────────────────────────────────────────────────

@app.route("/api/biens", methods=["POST"])
def api_creer_bien():
    d = request.get_json()
    nom       = d.get("nom", "").strip()
    cat_nom   = d.get("categorie", "")
    etat      = d.get("etat", "Bon état")
    prix      = float(d.get("prix", 0))
    prix_min  = float(d.get("prixMin", 0))
    vendeur_id= int(d.get("vendeurId", 0))
    desc      = d.get("description", "")

    if not nom:
        return jsonify({"error": "Nom requis"}), 400

    vendeur = find_user(vendeur_id)
    if not vendeur or not isinstance(vendeur, Vendeur):
        return jsonify({"error": "Vendeur invalide"}), 400

    try:
        cat  = get_or_create_cat(cat_nom)
        bien = Bien(nom, cat, etat, prix, prix_min, desc)
        vendeur.mettre_en_vente(bien)
        catalogue.append(bien)
        sauvegarder()
        return jsonify({"bien": bien_to_dict(bien)}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# ── Achat ─────────────────────────────────────────────────────────────────────

@app.route("/api/acheter", methods=["POST"])
def api_acheter():
    d          = request.get_json()
    bien_id    = int(d.get("bienId", 0))
    acheteur_id= int(d.get("acheteurId", 0))

    bien     = find_bien(bien_id)
    acheteur = find_user(acheteur_id)

    if not bien:
        return jsonify({"error": "Bien introuvable"}), 404
    if not acheteur or not isinstance(acheteur, Acheteur):
        return jsonify({"error": "Acheteur invalide"}), 400

    vendeur = bien.vendeur
    offre   = acheteur.calculer_offre(bien)
    succes  = acheteur.acheter_bien(bien)

    if succes:
        if bien in catalogue:
            catalogue.remove(bien)
        t = Transaction(bien, vendeur, acheteur, offre)
        transactions.append(t)
        sauvegarder()
        return jsonify({"succes": True,
                        "message": f"{acheteur.nom} a acheté {bien.nom}",
                        "transaction": tx_to_dict(t)})
    return jsonify({"succes": False, "message": "Achat impossible"}), 400


# ── Favoris ───────────────────────────────────────────────────────────────────

@app.route("/api/favoris/<int:user_id>", methods=["POST"])
def api_toggle_favori(user_id):
    d       = request.get_json()
    bien_id = int(d.get("bienId", 0))
    user    = find_user(user_id)
    bien    = find_bien(bien_id)
    if not user or not bien:
        return jsonify({"error": "Introuvable"}), 404
    if bien in user.favoris:
        user.retirer_favori(bien)
        return jsonify({"action": "retire"})
    user.ajouter_favori(bien)
    return jsonify({"action": "ajoute"})


# ── Transactions ──────────────────────────────────────────────────────────────

@app.route("/api/transactions")
def api_transactions():
    return jsonify({"transactions": [tx_to_dict(t) for t in transactions]})


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    init()
    print("🚀 Serveur démarré → http://localhost:5000")

    """
    app.run(debug=True, port=5000)"""

import os
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
