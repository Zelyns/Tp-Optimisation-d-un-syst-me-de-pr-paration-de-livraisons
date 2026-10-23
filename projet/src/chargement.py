"""Préparation du chargement d'un camion : problème du sac à dos 0/1.

Stratégie principale (exacte) :
  1. pré-filtrage sans perte d'optimalité (voir `reduire_candidats`) ;
  2. programmation dynamique sur la capacité, O(n' x W) ;
  3. reconstruction de la solution grâce à une table de décisions (1 octet / case).

Stratégie de repli (approchée) : glouton sur le ratio score/poids, utilisé
uniquement si la table de la programmation dynamique devient trop grande.
"""
from __future__ import annotations

import heapq
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Iterable

from colis import PRIORITE_MAX, PRIORITE_MIN, Colis
from tri import tri_fusion

# Au-delà de ce nombre de cases (n' x W), la table de décisions dépasserait
# ~200 Mo : on bascule sur l'heuristique gloutonne et on le signale.
LIMITE_CASES_PD = 200_000_000


# ------------------------------------------------------------------ score
def score_valeur(colis: Colis) -> float:
    """Partie 2 : on maximise la valeur seule."""
    return colis.valeur


def score_priorite(alpha: float = 1.0) -> Callable[[Colis], float]:
    """Partie 3 : valeur pondérée par la priorité.

        score = valeur x (1 + alpha x (priorité - 1) / 4)

    - priorité 1 : x 1 (valeur brute) ; priorité 5 : x (1 + alpha).
    - alpha = 0 revient à ignorer la priorité, alpha = 1 (défaut) signifie
      qu'un colis de priorité 5 « vaut » deux fois sa valeur marchande.
    - Le poids n'entre pas dans le score : il reste la contrainte du problème,
      et la programmation dynamique arbitre elle-même entre score et poids.
    """
    if alpha < 0:
        raise ValueError("alpha doit être positif ou nul")
    etendue = PRIORITE_MAX - PRIORITE_MIN

    def score(colis: Colis) -> float:
        return colis.valeur * (1 + alpha * (colis.priorite - PRIORITE_MIN) / etendue)

    return score


# ------------------------------------------------------------- résultat
@dataclass
class Chargement:
    capacite: int
    colis: list[Colis]
    methode: str
    optimal: bool
    score_total: float
    nb_candidats: int = 0
    duree: float = 0.0
    regle: str = "valeur"
    poids_total: int = field(init=False)
    valeur_totale: float = field(init=False)

    def __post_init__(self) -> None:
        self.poids_total = sum(c.poids for c in self.colis)
        self.valeur_totale = sum(c.valeur for c in self.colis)


# ------------------------------------------------------------ algorithmes
def reduire_candidats(colis: Iterable[Colis], capacite: int,
                      score: Callable[[Colis], float]) -> list[Colis]:
    """Élimine des colis qui ne peuvent figurer dans AUCUNE solution optimale.

    1. Un colis plus lourd que la capacité ne rentre jamais.
    2. Un colis de score nul n'apporte rien.
    3. Pour un poids w donné, au plus floor(W / w) colis de ce poids tiennent
       dans le camion. Seuls les floor(W / w) meilleurs scores de ce poids sont
       utiles : si une solution contient un colis de poids w hors de ce
       « top », un colis du top est forcément inutilisé et l'échanger ne
       change pas le poids et n'abaisse pas le score (argument d'échange).

    Après réduction il reste au plus sum_{w=1..W} W/w ≈ W·ln(W) colis,
    QUEL QUE SOIT n : avec W = 1000, au plus ~7 500 colis au lieu de 100 000.
    Temps O(n log W) (tas de taille bornée par groupe), espace O(n).
    """
    groupes: dict[int, list[Colis]] = defaultdict(list)
    for c in colis:
        if c.poids <= capacite and score(c) > 0:
            groupes[c.poids].append(c)
    candidats: list[Colis] = []
    for poids, groupe in groupes.items():
        k = capacite // poids
        if len(groupe) > k:
            groupe = heapq.nlargest(k, groupe, key=score)
        candidats.extend(groupe)
    return candidats


def sac_a_dos_dynamique(colis: list[Colis], capacite: int,
                        score: Callable[[Colis], float]) -> tuple[list[Colis], float]:
    """Sac à dos 0/1 exact par programmation dynamique.

    meilleur[c] = meilleur score atteignable avec une charge <= c en utilisant
    les colis déjà traités. Pour chaque colis (w, s), de façon à ne l'utiliser
    qu'une fois, on calcule la nouvelle ligne à partir de l'ancienne :
        meilleur'[c] = max(meilleur[c], meilleur[c - w] + s)     pour c >= w

    Temps  : O(n x W).
    Espace : O(W) pour les scores + O(n x W) octets pour les décisions
             (nécessaires pour savoir QUELS colis charger, pas seulement le score).
    """
    meilleur = [0.0] * (capacite + 1)
    decisions: list[bytearray] = []  # decisions[i][c - w_i] = 1 si colis i pris à charge c

    for c in colis:
        w, s = c.poids, score(c)
        # compréhensions sur des tranches : ~3x plus rapide qu'une boucle indexée
        # en Python, et on lit l'ancienne ligne -> chaque colis pris au plus une fois.
        sans = meilleur[w:]
        avec = [m + s for m in meilleur[:capacite + 1 - w]]
        pris = [a > b for a, b in zip(avec, sans)]
        meilleur[w:] = [a if p else b for a, b, p in zip(avec, sans, pris)]
        decisions.append(bytearray(pris))

    # reconstruction : on remonte les colis du dernier au premier
    choisis: list[Colis] = []
    reste = capacite
    for i in range(len(colis) - 1, -1, -1):
        w = colis[i].poids
        if reste >= w and decisions[i][reste - w]:
            choisis.append(colis[i])
            reste -= w
    choisis.reverse()
    return choisis, meilleur[capacite]


def sac_a_dos_glouton(colis: list[Colis], capacite: int,
                      score: Callable[[Colis], float]) -> tuple[list[Colis], float]:
    """Heuristique gloutonne : on charge par ratio score/poids décroissant.

    On compare ensuite avec le meilleur colis seul, ce qui garantit au moins
    50 % de l'optimum (sinon le glouton peut être arbitrairement mauvais).
    Temps O(n log n), espace O(n). Pas toujours optimale.
    """
    ordre = tri_fusion(colis, lambda c: score(c) / c.poids, decroissant=True)
    choisis, charge, total = [], 0, 0.0
    for c in ordre:
        if charge + c.poids <= capacite:
            choisis.append(c)
            charge += c.poids
            total += score(c)
    seul = max((c for c in colis if c.poids <= capacite), key=score, default=None)
    if seul is not None and score(seul) > total:
        return [seul], score(seul)
    return choisis, total


def preparer_camion(colis: Iterable[Colis], capacite: int, alpha: float | None = None,
                    forcer_glouton: bool = False) -> Chargement:
    """Point d'entrée : alpha=None -> valeur seule, sinon valeur pondérée par la priorité."""
    if capacite <= 0:
        raise ValueError("la capacité doit être un entier strictement positif")
    score = score_valeur if alpha is None else score_priorite(alpha)
    regle = "valeur" if alpha is None else f"valeur x priorité (alpha = {alpha:g})"

    debut = time.perf_counter()
    candidats = reduire_candidats(colis, capacite, score)
    if forcer_glouton or len(candidats) * capacite > LIMITE_CASES_PD:
        choisis, total = sac_a_dos_glouton(candidats, capacite, score)
        methode, optimal = "glouton (ratio score/poids)", False
    else:
        choisis, total = sac_a_dos_dynamique(candidats, capacite, score)
        methode, optimal = "programmation dynamique", True
    duree = time.perf_counter() - debut

    return Chargement(capacite, choisis, methode, optimal, total,
                      nb_candidats=len(candidats), duree=duree, regle=regle)
