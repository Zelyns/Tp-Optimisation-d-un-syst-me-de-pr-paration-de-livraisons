"""Interface en ligne de commande : python main.py"""
from __future__ import annotations

import time

import donnees
from chargement import Chargement, preparer_camion
from colis import ENTETE, PRIORITE_MAX, PRIORITE_MIN, Colis
from entrepot import Entrepot
from tri import tri_fusion

LIGNES_PAR_DEFAUT = 20

MENU = """
===== GESTION DES LIVRAISONS =====  ({n} colis)
1. Afficher les colis
2. Ajouter un colis
3. Rechercher un colis
4. Organiser les colis (poids / valeur / priorité / destination)
5. Préparer un camion
6. Afficher le chargement
7. Afficher les statistiques
8. Données (générer / importer / exporter / exemple)
9. Supprimer un colis
0. Quitter"""


# ------------------------------------------------------------ saisies
def lire_entier(invite: str, mini: int | None = None, maxi: int | None = None,
                defaut: int | None = None) -> int:
    while True:
        brut = input(invite).strip()
        if not brut and defaut is not None:
            return defaut
        try:
            v = int(brut)
        except ValueError:
            print("  -> entier attendu.")
            continue
        if (mini is not None and v < mini) or (maxi is not None and v > maxi):
            print(f"  -> valeur attendue entre {mini} et {maxi}.")
            continue
        return v


def lire_reel(invite: str, mini: float = 0.0, defaut: float | None = None) -> float:
    while True:
        brut = input(invite).strip().replace(",", ".")
        if not brut and defaut is not None:
            return defaut
        try:
            v = float(brut)
        except ValueError:
            print("  -> nombre attendu.")
            continue
        if v < mini:
            print(f"  -> valeur attendue >= {mini}.")
            continue
        return v


def afficher_liste(colis: list[Colis], limite: int | None = LIGNES_PAR_DEFAUT) -> None:
    if not colis:
        print("  (aucun colis)")
        return
    print(ENTETE)
    print("-" * len(ENTETE))
    for c in colis[:limite] if limite else colis:
        print(c.ligne())
    if limite and len(colis) > limite:
        print(f"  ... et {len(colis) - limite} autres colis")


def demander_limite(n: int) -> int | None:
    if n <= LIGNES_PAR_DEFAUT:
        return None
    k = lire_entier(f"Nombre de colis à afficher (0 = tous, Entrée = {LIGNES_PAR_DEFAUT}) : ",
                    mini=0, defaut=LIGNES_PAR_DEFAUT)
    return k or None


# ------------------------------------------------------------ actions
def action_afficher(e: Entrepot, _etat: dict) -> None:
    afficher_liste(e.tous(), demander_limite(len(e)))


def action_ajouter(e: Entrepot, _etat: dict) -> None:
    ident = lire_entier(f"Identifiant (Entrée = {e.prochain_id()}) : ", mini=0,
                        defaut=e.prochain_id())
    if ident in e:
        print("  -> cet identifiant existe déjà.")
        return
    poids = lire_entier("Poids (kg, entier) : ", mini=1)
    valeur = lire_reel("Valeur (€) : ")
    priorite = lire_entier(f"Priorité ({PRIORITE_MIN} = faible ... {PRIORITE_MAX} = urgente) : ",
                           PRIORITE_MIN, PRIORITE_MAX)
    destination = ""
    while not destination:
        destination = input("Destination : ").strip()
    e.ajouter(Colis(ident, poids, valeur, priorite, destination))
    print(f"  -> colis {ident} ajouté.")


def action_rechercher(e: Entrepot, _etat: dict) -> None:
    print("1. Par identifiant   2. Par destination")
    if lire_entier("Choix : ", 1, 2) == 1:
        ident = lire_entier("Identifiant : ")
        t = time.perf_counter()
        c = e.rechercher(ident)
        dt = (time.perf_counter() - t) * 1e6
        afficher_liste([c] if c else [])
        print(f"  (recherche en {dt:.1f} µs dans la table de hachage)")
    else:
        print("Destinations :", ", ".join(e.destinations()) or "aucune")
        res = e.par_destination(input("Destination : "))
        afficher_liste(res, demander_limite(len(res)))


def action_organiser(e: Entrepot, _etat: dict) -> None:
    print("Trier par : 1. Poids  2. Valeur  3. Priorité  4. Destination")
    critere = ("poids", "valeur", "priorite", "destination")[lire_entier("Choix : ", 1, 4) - 1]
    decroissant = lire_entier("Ordre : 1. Croissant  2. Décroissant : ", 1, 2) == 2
    t = time.perf_counter()
    vue = e.trie_par(critere, decroissant)
    dt = (time.perf_counter() - t) * 1e3
    afficher_liste(vue, demander_limite(len(vue)))
    algo = "dénombrement O(n)" if critere == "priorite" else "tri fusion O(n log n)"
    print(f"  (tri en {dt:.2f} ms — {algo}, résultat mis en cache)")


def action_camion(e: Entrepot, etat: dict) -> None:
    if not len(e):
        print("  -> aucun colis à charger.")
        return
    capacite = lire_entier(f"Capacité du camion en kg (Entrée = {etat['capacite']}) : ",
                           mini=1, defaut=etat["capacite"])
    etat["capacite"] = capacite
    print("Règle de sélection :")
    print("  1. Maximiser la valeur")
    print("  2. Maximiser la valeur pondérée par la priorité")
    if lire_entier("Choix : ", 1, 2) == 2:
        alpha = lire_reel("Poids de la priorité alpha (0 = ignorée, Entrée = 1) : ", defaut=1.0)
    else:
        alpha = None
    ch = preparer_camion(e.tous(), capacite, alpha)
    etat["chargement"] = ch
    resume_chargement(ch)


def resume_chargement(ch: Chargement) -> None:
    print(f"\nCamion de {ch.capacite} kg — règle : {ch.regle}")
    print(f"Méthode : {ch.methode} ({'solution optimale' if ch.optimal else 'solution approchée'})")
    print(f"Colis chargés    : {len(ch.colis)}  (sur {ch.nb_candidats} candidats après filtrage)")
    print(f"Poids total      : {ch.poids_total} / {ch.capacite} kg "
          f"({100 * ch.poids_total / ch.capacite:.1f} %)")
    print(f"Valeur totale    : {ch.valeur_totale:.2f} €")
    if ch.regle != "valeur":
        print(f"Score total      : {ch.score_total:.2f}")
    print(f"Temps de calcul  : {ch.duree * 1e3:.1f} ms")


def action_afficher_chargement(_e: Entrepot, etat: dict) -> None:
    ch: Chargement | None = etat["chargement"]
    if ch is None:
        print("  -> aucun camion préparé (option 5).")
        return
    resume_chargement(ch)
    print("\nOrdre de chargement conseillé (par destination puis priorité) :")
    # tri par destination puis priorité décroissante : clé composée, tri fusion stable
    ordre = tri_fusion(ch.colis, lambda c: (c.destination, -c.priorite))
    afficher_liste(ordre, demander_limite(len(ordre)))


def action_statistiques(e: Entrepot, etat: dict) -> None:
    s = e.statistiques()
    print(f"Nombre de colis : {s['nombre']}")
    print(f"Poids total     : {s['poids_total']} kg   (moyenne {s['poids_moyen']:.2f} kg)")
    print(f"Valeur totale   : {s['valeur_totale']:.2f} €  (moyenne {s['valeur_moyenne']:.2f} €)")
    print("Par priorité    : " + ", ".join(f"P{p}: {k}" for p, k in s["par_priorite"].items()))
    print("Par destination : " + ", ".join(f"{d}: {k}" for d, k in s["par_destination"].items()))
    ch = etat["chargement"]
    if ch is not None and s["valeur_totale"]:
        print(f"Dernier camion  : {len(ch.colis)} colis, "
              f"{100 * ch.valeur_totale / s['valeur_totale']:.1f} % de la valeur totale du stock")


def action_donnees(e: Entrepot, etat: dict) -> None:
    print("1. Générer des colis aléatoires  2. Importer un CSV  3. Exporter en CSV  "
          "4. Recharger l'exemple de l'énoncé  5. Exemple camion (A, B, C, D)")
    choix = lire_entier("Choix : ", 1, 5)
    try:
        if choix == 1:
            n = lire_entier("Nombre de colis (ex. 100, 1000, 10000, 100000) : ", mini=1)
            if lire_entier("1. Remplacer  2. Ajouter aux colis existants : ", 1, 2) == 1:
                e.vider()
            t = time.perf_counter()
            for c in donnees.generer(n, premier_id=e.prochain_id()):
                e.ajouter(c)
            print(f"  -> {n} colis ajoutés en {(time.perf_counter() - t) * 1e3:.0f} ms.")
        elif choix == 2:
            colis = donnees.lire_csv(input("Chemin du fichier CSV : ").strip())
            e.vider()
            for c in colis:
                e.ajouter(c)
            print(f"  -> {len(colis)} colis importés.")
        elif choix == 3:
            chemin = input("Chemin du fichier à créer : ").strip()
            donnees.ecrire_csv(chemin, e.tous())
            print(f"  -> {len(e)} colis exportés dans {chemin}.")
        else:
            e.vider()
            for c in donnees.EXEMPLE if choix == 4 else donnees.EXEMPLE_CAMION:
                e.ajouter(Colis(c.id, c.poids, c.valeur, c.priorite, c.destination))
            print(f"  -> {len(e)} colis chargés.")
        etat["chargement"] = None
    except (OSError, ValueError, KeyError) as err:
        print(f"  -> erreur : {err}")


def action_supprimer(e: Entrepot, etat: dict) -> None:
    c = e.supprimer(lire_entier("Identifiant du colis à supprimer : "))
    print(f"  -> colis {c.id} supprimé." if c else "  -> identifiant introuvable.")
    if c:
        etat["chargement"] = None


ACTIONS = {
    1: action_afficher, 2: action_ajouter, 3: action_rechercher, 4: action_organiser,
    5: action_camion, 6: action_afficher_chargement, 7: action_statistiques,
    8: action_donnees, 9: action_supprimer,
}


def main() -> None:
    entrepot = Entrepot()
    for c in donnees.EXEMPLE:
        entrepot.ajouter(c)
    etat = {"chargement": None, "capacite": 50}
    while True:
        print(MENU.format(n=len(entrepot)))
        choix = lire_entier("Choix : ", 0, 9)
        if choix == 0:
            print("Au revoir.")
            return
        print()
        try:
            ACTIONS[choix](entrepot, etat)
        except ValueError as err:
            print(f"  -> erreur : {err}")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nAu revoir.")
