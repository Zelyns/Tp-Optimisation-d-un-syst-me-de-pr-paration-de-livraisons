"""Mesures de performance : python benchmark.py [--rapide]

Pour chaque taille n, mesure :
- l'ajout de n colis (table de hachage) ;
- la recherche par identifiant : table de hachage vs parcours linéaire ;
- les tris : tri fusion (poids, valeur), dénombrement (priorité), et sorted()
  (Timsort natif) comme point de comparaison ;
- la préparation d'un camion : réduction + programmation dynamique, comparée
  au glouton (temps et qualité) ;
- la mémoire occupée par la collection (tracemalloc).
"""
from __future__ import annotations

import gc
import random
import sys
import time
import tracemalloc

import donnees
from chargement import preparer_camion
from entrepot import Entrepot

TAILLES = (100, 1_000, 10_000, 100_000)
CAPACITES = (100, 1_000)
NB_RECHERCHES = 1_000
NB_RECHERCHES_LINEAIRES = 100


def chrono(f, *args, repetitions: int = 1):
    """Meilleur temps sur `repetitions` exécutions (limite le bruit), en secondes.
    Le ramasse-miettes est suspendu pendant la mesure, comme le fait `timeit`."""
    meilleur, res = float("inf"), None
    gc.disable()
    try:
        for _ in range(repetitions):
            t = time.perf_counter()
            res = f(*args)
            meilleur = min(meilleur, time.perf_counter() - t)
    finally:
        gc.enable()
    return meilleur, res


def construire(colis):
    e = Entrepot()
    for c in colis:
        e.ajouter(c)
    return e


def main(tailles=TAILLES) -> None:
    lignes_base, lignes_camion = [], []
    for n in tailles:
        colis = donnees.generer(n, graine=n)
        rep = 3

        t_ajout, e = chrono(construire, colis, repetitions=rep)

        tracemalloc.start()
        copie = construire(donnees.generer(n, graine=n))  # colis + index + agrégats
        memoire = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()
        del copie

        rnd = random.Random(0)
        ids = [rnd.randint(1, n) for _ in range(NB_RECHERCHES)]
        t_hash, _ = chrono(lambda: [e.rechercher(i) for i in ids], repetitions=rep)
        ids_lin = ids[:NB_RECHERCHES_LINEAIRES]
        t_lin, _ = chrono(lambda: [e.rechercher_lineaire(i) for i in ids_lin])

        def trier(critere):
            e._vues.clear()  # on mesure le tri, pas le cache
            return e.trie_par(critere)

        t_poids, _ = chrono(trier, "poids", repetitions=rep)
        t_prio, _ = chrono(trier, "priorite", repetitions=rep)
        t_natif, _ = chrono(lambda: sorted(colis, key=lambda c: c.poids), repetitions=rep)
        e.trie_par("poids")
        t_cache, _ = chrono(e.trie_par, "poids")

        lignes_base.append((
            n,
            f"{t_ajout * 1e3:.1f}",
            f"{t_hash / NB_RECHERCHES * 1e6:.2f}",
            f"{t_lin / NB_RECHERCHES_LINEAIRES * 1e6:.1f}",
            f"{t_poids * 1e3:.1f}",
            f"{t_prio * 1e3:.1f}",
            f"{t_natif * 1e3:.1f}",
            f"{t_cache * 1e6:.1f}",
            f"{memoire / 2**20:.2f}",
        ))

        for capacite in CAPACITES:
            pd = preparer_camion(colis, capacite)
            gl = preparer_camion(colis, capacite, forcer_glouton=True)
            pdp = preparer_camion(colis, capacite, alpha=1.0)
            ecart = 100 * (pd.valeur_totale - gl.valeur_totale) / pd.valeur_totale
            lignes_camion.append((
                n, capacite, pd.nb_candidats,
                f"{pd.duree * 1e3:.1f}", f"{pd.valeur_totale:.2f}",
                f"{gl.duree * 1e3:.1f}", f"{gl.valeur_totale:.2f}", f"{ecart:.3f}",
                f"{pdp.duree * 1e3:.1f}",
            ))
        print(f"n = {n} terminé", file=sys.stderr)

    tableau("Collection (temps)", (
        "n", "ajout n colis (ms)", "recherche hachage (µs)", "recherche linéaire (µs)",
        "tri fusion poids (ms)", "dénombrement priorité (ms)", "sorted() natif (ms)",
        "vue en cache (µs)", "mémoire totale (Mo)"), lignes_base)
    tableau("Préparation du camion", (
        "n", "capacité (kg)", "candidats après réduction", "PD (ms)", "valeur PD",
        "glouton (ms)", "valeur glouton", "perte glouton (%)", "PD avec priorité (ms)"),
        lignes_camion)


def tableau(titre, entetes, lignes) -> None:
    print(f"\n### {titre}\n")
    print("| " + " | ".join(entetes) + " |")
    print("|" + "---|" * len(entetes))
    for l in lignes:
        print("| " + " | ".join(str(x) for x in l) + " |")


if __name__ == "__main__":
    main(TAILLES[:3] if "--rapide" in sys.argv else TAILLES)
