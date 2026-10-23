"""Définition d'un colis."""
from __future__ import annotations

from dataclasses import dataclass

PRIORITE_MIN = 1  # priorité la plus faible
PRIORITE_MAX = 5  # priorité la plus forte (colis le plus urgent)


@dataclass(slots=True)
class Colis:
    """Un colis à livrer.

    `slots=True` supprime le dictionnaire interne de chaque instance :
    environ 2 à 3 fois moins de mémoire par colis, ce qui compte avec
    100 000 colis ou plus.

    Le poids est un entier (kg) : c'est ce qui permet la programmation
    dynamique sur la capacité du camion (voir chargement.py).
    """

    id: int
    poids: int
    valeur: float
    priorite: int
    destination: str

    def __post_init__(self) -> None:
        if self.poids <= 0:
            raise ValueError("le poids doit être un entier strictement positif")
        if self.valeur < 0:
            raise ValueError("la valeur ne peut pas être négative")
        if not PRIORITE_MIN <= self.priorite <= PRIORITE_MAX:
            raise ValueError(f"la priorité doit être comprise entre {PRIORITE_MIN} et {PRIORITE_MAX}")
        self.destination = self.destination.strip()
        if not self.destination:
            raise ValueError("la destination est obligatoire")

    def ligne(self) -> str:
        return (f"{self.id:>8} | {self.poids:>6} kg | {self.valeur:>9.2f} € | "
                f"{self.priorite:^8} | {self.destination}")


ENTETE = f"{'ID':>8} | {'Poids':>9} | {'Valeur':>11} | Priorité | Destination"
