"""Stockage et organisation de la collection de colis."""
from __future__ import annotations

from collections import Counter

from colis import PRIORITE_MAX, PRIORITE_MIN, Colis
from tri import tri_denombrement, tri_fusion

CRITERES = ("poids", "valeur", "priorite", "destination")


class Entrepot:
    """Collection de colis indexée par identifiant.

    Structures :
    - `_par_id` : table de hachage (dict) id -> Colis. Python conserve l'ordre
      d'insertion, elle sert donc aussi de liste « dans l'ordre d'arrivée ».
    - `_par_destination` : index secondaire destination -> {id: Colis}.
    - `_vues` : cache des listes triées, invalidé à chaque modification.
    - agrégats (poids, valeur, compteurs) tenus à jour à chaque ajout/suppression,
      pour que les statistiques ne reparcourent pas toute la collection.
    """

    def __init__(self) -> None:
        self._par_id: dict[int, Colis] = {}
        self._par_destination: dict[str, dict[int, Colis]] = {}
        self._vues: dict[tuple[str, bool], list[Colis]] = {}
        self._poids_total = 0
        self._valeur_totale = 0.0
        self._par_priorite: Counter[int] = Counter()

    # ------------------------------------------------------------ modification
    def ajouter(self, colis: Colis) -> None:
        """O(1) en moyenne (insertion dans deux tables de hachage)."""
        if colis.id in self._par_id:
            raise ValueError(f"un colis avec l'identifiant {colis.id} existe déjà")
        self._par_id[colis.id] = colis
        self._par_destination.setdefault(colis.destination, {})[colis.id] = colis
        self._poids_total += colis.poids
        self._valeur_totale += colis.valeur
        self._par_priorite[colis.priorite] += 1
        self._vues.clear()

    def supprimer(self, identifiant: int) -> Colis | None:
        """O(1) en moyenne."""
        colis = self._par_id.pop(identifiant, None)
        if colis is None:
            return None
        meme_dest = self._par_destination[colis.destination]
        del meme_dest[identifiant]
        if not meme_dest:
            del self._par_destination[colis.destination]
        self._poids_total -= colis.poids
        self._valeur_totale -= colis.valeur
        self._par_priorite[colis.priorite] -= 1
        self._vues.clear()
        return colis

    def vider(self) -> None:
        self.__init__()

    def prochain_id(self) -> int:
        return max(self._par_id, default=100) + 1

    # ------------------------------------------------------------- consultation
    def __len__(self) -> int:
        return len(self._par_id)

    def __contains__(self, identifiant: int) -> bool:
        return identifiant in self._par_id

    def tous(self) -> list[Colis]:
        """Colis dans l'ordre d'ajout. O(n)."""
        return list(self._par_id.values())

    def rechercher(self, identifiant: int) -> Colis | None:
        """Recherche par identifiant dans la table de hachage : O(1) en moyenne."""
        return self._par_id.get(identifiant)

    def rechercher_lineaire(self, identifiant: int) -> Colis | None:
        """Recherche séquentielle O(n) — gardée uniquement pour la comparaison
        dans benchmark.py."""
        for c in self._par_id.values():
            if c.id == identifiant:
                return c
        return None

    def par_destination(self, destination: str) -> list[Colis]:
        """O(k) avec k le nombre de colis pour cette destination."""
        return list(self._par_destination.get(destination.strip(), {}).values())

    def destinations(self) -> list[str]:
        return sorted(self._par_destination)

    def trie_par(self, critere: str, decroissant: bool = False) -> list[Colis]:
        """Liste triée selon un critère.

        - priorité : tri par dénombrement, O(n) (seulement 5 valeurs possibles) ;
        - poids, valeur, destination : tri fusion, O(n log n).
        Le résultat est mis en cache : un deuxième affichage sans ajout entre-temps
        coûte O(1). Le cache coûte O(n) mémoire par vue demandée.
        """
        if critere not in CRITERES:
            raise ValueError(f"critère inconnu : {critere}")
        vue = self._vues.get((critere, decroissant))
        if vue is None:
            colis = self.tous()
            if critere == "priorite":
                vue = tri_denombrement(colis, lambda c: c.priorite,
                                       PRIORITE_MIN, PRIORITE_MAX, decroissant)
            else:
                vue = tri_fusion(colis, lambda c: getattr(c, critere), decroissant)
            self._vues[(critere, decroissant)] = vue
        return vue

    def statistiques(self) -> dict:
        """O(d) avec d le nombre de destinations, grâce aux agrégats maintenus."""
        n = len(self)
        return {
            "nombre": n,
            "poids_total": self._poids_total,
            "valeur_totale": self._valeur_totale,
            "poids_moyen": self._poids_total / n if n else 0,
            "valeur_moyenne": self._valeur_totale / n if n else 0,
            "par_priorite": {p: self._par_priorite[p]
                             for p in range(PRIORITE_MAX, PRIORITE_MIN - 1, -1)},
            "par_destination": {d: len(ids) for d, ids in
                                sorted(self._par_destination.items(),
                                       key=lambda kv: -len(kv[1]))},
        }
