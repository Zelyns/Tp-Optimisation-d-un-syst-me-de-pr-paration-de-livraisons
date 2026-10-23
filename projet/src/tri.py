"""Algorithmes de tri implémentés à la main.

- tri_fusion      : tri par comparaison, stable, O(n log n) dans tous les cas.
- tri_denombrement: tri sans comparaison pour des clés entières à petite
                    plage (la priorité 1..5), O(n + k).
"""
from __future__ import annotations

import operator
from typing import Callable, Sequence, TypeVar

T = TypeVar("T")


def tri_fusion(elements: Sequence[T], cle: Callable[[T], object],
               decroissant: bool = False) -> list[T]:
    """Tri fusion ascendant (bottom-up), itératif et stable.

    Temps  : O(n log n) — log2(n) passes, chacune fusionne n éléments.
    Espace : O(n) — les clés pré-calculées, un tableau d'indices et un tampon.

    Les clés sont calculées une seule fois (n appels à `cle` au lieu de
    n log n) et on trie des indices plutôt que les objets eux-mêmes.
    La version itérative évite la limite de récursion de Python.
    Stable : à clé égale, l'ordre d'origine (ordre d'ajout) est conservé.
    """
    n = len(elements)
    if n < 2:
        return list(elements)

    cles = [cle(e) for e in elements]
    # « prendre l'élément de droite » seulement s'il passe strictement devant :
    # c'est ce qui garantit la stabilité dans les deux sens de tri.
    passe_devant = operator.gt if decroissant else operator.lt

    idx = list(range(n))
    tampon = [0] * n
    largeur = 1
    while largeur < n:
        for debut in range(0, n, 2 * largeur):
            milieu = min(debut + largeur, n)
            fin = min(debut + 2 * largeur, n)
            i, j, k = debut, milieu, debut
            while i < milieu and j < fin:
                if passe_devant(cles[idx[j]], cles[idx[i]]):
                    tampon[k] = idx[j]
                    j += 1
                else:
                    tampon[k] = idx[i]
                    i += 1
                k += 1
            # une des deux moitiés est épuisée : on recopie le reste de l'autre
            reste_gauche = milieu - i
            tampon[k:k + reste_gauche] = idx[i:milieu]
            k += reste_gauche
            tampon[k:k + fin - j] = idx[j:fin]
        idx, tampon = tampon, idx
        largeur *= 2

    return [elements[i] for i in idx]


def tri_denombrement(elements: Sequence[T], cle: Callable[[T], int],
                     k_min: int, k_max: int, decroissant: bool = False) -> list[T]:
    """Tri par dénombrement (par paquets) pour des clés entières dans [k_min, k_max].

    Temps  : O(n + k) avec k = k_max - k_min + 1 (ici k = 5, donc O(n)).
    Espace : O(n + k).
    Stable : chaque paquet garde l'ordre d'arrivée.
    """
    paquets: list[list[T]] = [[] for _ in range(k_max - k_min + 1)]
    for e in elements:
        paquets[cle(e) - k_min].append(e)
    if decroissant:
        paquets.reverse()
    resultat: list[T] = []
    for p in paquets:
        resultat.extend(p)
    return resultat
