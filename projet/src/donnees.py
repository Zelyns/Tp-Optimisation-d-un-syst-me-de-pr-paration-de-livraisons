"""Jeux de données : exemple de l'énoncé, génération aléatoire, import/export CSV."""
from __future__ import annotations

import csv
import random
from pathlib import Path

from colis import PRIORITE_MAX, PRIORITE_MIN, Colis

VILLES = ("Paris", "Lille", "Lyon", "Marseille", "Toulouse", "Nantes",
          "Bordeaux", "Strasbourg", "Rennes", "Nice")

EXEMPLE = [
    Colis(101, 8, 20, 2, "Paris"),
    Colis(102, 3, 10, 5, "Lille"),
    Colis(103, 12, 40, 1, "Lyon"),
    Colis(104, 5, 25, 4, "Paris"),
    Colis(105, 2, 15, 3, "Lille"),
]

# Exemple de la partie « camion » (A, B, C, D) avec les priorités de la partie 3.
EXEMPLE_CAMION = [
    Colis(1, 8, 20, 5, "A"),
    Colis(2, 6, 25, 1, "B"),
    Colis(3, 5, 18, 4, "C"),
    Colis(4, 4, 14, 3, "D"),
]


def generer(n: int, graine: int | None = None, premier_id: int = 1) -> list[Colis]:
    """n colis aléatoires (poids 1-30 kg, valeur liée au poids, priorité 1-5). O(n)."""
    rnd = random.Random(graine)
    resultat = []
    for i in range(n):
        poids = rnd.randint(1, 30)
        valeur = round(poids * rnd.uniform(1, 6) + rnd.uniform(0, 30), 2)
        resultat.append(Colis(premier_id + i, poids, valeur,
                              rnd.randint(PRIORITE_MIN, PRIORITE_MAX), rnd.choice(VILLES)))
    return resultat


COLONNES = ("ID", "Poids", "Valeur", "Priorite", "Destination")


def lire_csv(chemin: str | Path) -> list[Colis]:
    with open(chemin, newline="", encoding="utf-8") as f:
        return [Colis(int(l["ID"]), int(l["Poids"]), float(l["Valeur"]),
                      int(l["Priorite"]), l["Destination"])
                for l in csv.DictReader(f)]


def ecrire_csv(chemin: str | Path, colis: list[Colis]) -> None:
    with open(chemin, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLONNES)
        for c in colis:
            w.writerow((c.id, c.poids, c.valeur, c.priorite, c.destination))
