"""Tests de correction : python tests.py"""
from __future__ import annotations

import random
from itertools import combinations

import donnees
from chargement import (preparer_camion, reduire_candidats, sac_a_dos_dynamique,
                        score_priorite, score_valeur)
from colis import Colis
from entrepot import Entrepot
from tri import tri_denombrement, tri_fusion


def force_brute(colis, capacite, score):
    """Énumère les 2^n sous-ensembles : référence exacte pour n petit."""
    meilleur = 0.0
    for k in range(len(colis) + 1):
        for sous in combinations(colis, k):
            if sum(c.poids for c in sous) <= capacite:
                meilleur = max(meilleur, sum(score(c) for c in sous))
    return meilleur


def test_tris():
    rnd = random.Random(1)
    for n in (0, 1, 2, 3, 7, 64, 1000):
        l = [rnd.randint(0, 20) for _ in range(n)]
        assert tri_fusion(l, lambda x: x) == sorted(l)
        assert tri_fusion(l, lambda x: x, True) == sorted(l, reverse=True)
    # stabilité : à clé égale, l'ordre d'origine est conservé
    paires = [(rnd.randint(1, 5), i) for i in range(500)]
    attendu = sorted(paires, key=lambda p: p[0])
    assert tri_fusion(paires, lambda p: p[0]) == attendu
    assert tri_denombrement(paires, lambda p: p[0], 1, 5) == attendu
    assert tri_fusion(paires, lambda p: p[0], True) == sorted(paires, key=lambda p: -p[0])


def test_entrepot():
    e = Entrepot()
    for c in donnees.EXEMPLE:
        e.ajouter(c)
    assert e.rechercher(104).destination == "Paris"
    assert e.rechercher(999) is None
    assert [c.id for c in e.trie_par("poids")] == [105, 102, 104, 101, 103]
    assert [c.id for c in e.trie_par("valeur", True)] == [103, 104, 101, 105, 102]
    assert [c.id for c in e.trie_par("priorite", True)] == [102, 104, 105, 101, 103]
    assert {c.id for c in e.par_destination("Lille")} == {102, 105}
    try:
        e.ajouter(Colis(101, 1, 1, 1, "X"))
        raise AssertionError("doublon accepté")
    except ValueError:
        pass
    e.supprimer(101)
    s = e.statistiques()
    assert s["nombre"] == 4 and s["poids_total"] == 22 and s["valeur_totale"] == 90


def test_sac_a_dos():
    # exemple de l'énoncé, capacité 13 : B + C (43 €) sans priorité, A + C avec priorité
    ex = donnees.EXEMPLE_CAMION
    assert {c.destination for c in preparer_camion(ex, 13).colis} == {"B", "C"}
    assert {c.destination for c in preparer_camion(ex, 13, alpha=1).colis} == {"A", "C"}
    assert preparer_camion(ex, 15).valeur_totale == 57  # B + C + D

    rnd = random.Random(42)
    for _ in range(300):
        n = rnd.randint(0, 12)
        colis = [Colis(i, rnd.randint(1, 15), rnd.randint(0, 50), rnd.randint(1, 5), "X")
                 for i in range(n)]
        capacite = rnd.randint(1, 40)
        for alpha in (None, 1.0, 3.0):
            score = score_valeur if alpha is None else score_priorite(alpha)
            ch = preparer_camion(colis, capacite, alpha)
            assert ch.optimal
            assert abs(ch.score_total - force_brute(colis, capacite, score)) < 1e-6
            assert ch.poids_total <= capacite
            assert abs(sum(score(c) for c in ch.colis) - ch.score_total) < 1e-6
            assert len({c.id for c in ch.colis}) == len(ch.colis)


def test_reduction_sans_perte():
    # beaucoup de colis de même poids : la réduction ne doit rien changer à l'optimum
    rnd = random.Random(7)
    colis = [Colis(i, rnd.randint(1, 5), rnd.randint(1, 100), 3, "X") for i in range(2000)]
    capacite = 20
    reduits = reduire_candidats(colis, capacite, score_valeur)
    assert len(reduits) <= sum(capacite // w for w in range(1, 6))
    _, avec = sac_a_dos_dynamique(reduits, capacite, score_valeur)
    _, sans = sac_a_dos_dynamique([c for c in colis if c.poids <= capacite], capacite, score_valeur)
    assert avec == sans


if __name__ == "__main__":
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            f()
            print(f"OK  {nom}")
    print("Tous les tests passent.")
