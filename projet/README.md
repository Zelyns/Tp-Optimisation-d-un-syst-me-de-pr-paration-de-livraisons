# Projet : gestion des livraisons

Programme en ligne de commande qui permet de gérer des colis (ajout, affichage, recherche, tris)
et de choisir quels colis mettre dans un camion qui a une capacité maximale.

## Langage

J'ai choisi Python, parce que le code est simple à lire et que le dictionnaire (table de hachage) est
déjà intégré au langage, ce qui est pratique pour retrouver un colis par son identifiant.
Python est plus lent que le C : j'en parle dans le rapport.

Il n'y a aucune bibliothèque à installer, il faut seulement Python 3.10 ou plus récent.

## Lancer le programme

```bash
cd src
python main.py
```

Au démarrage, il y a les 5 colis de l'exemple de l'énoncé. Avec l'option 8 du menu, on peut générer
beaucoup de colis (par exemple 100 000), importer ou exporter un fichier CSV, ou recharger l'exemple
du camion (A, B, C, D).

Autres commandes :

```bash
python tests.py       # vérifie que tout fonctionne
python benchmark.py   # mesure les temps pour 100, 1 000, 10 000 et 100 000 colis (environ 1 minute)
```

## Fichiers

```
projet/
├── src/
│   ├── colis.py        la classe Colis
│   ├── entrepot.py     la liste des colis (ajout, recherche, tris, statistiques)
│   ├── tri.py          tri fusion et tri par dénombrement
│   ├── chargement.py   choix des colis pour le camion
│   ├── donnees.py      exemples, génération aléatoire, CSV
│   ├── main.py         le menu
│   ├── tests.py        les tests
│   └── benchmark.py    les mesures de temps
├── resultats_benchmark.md
├── README.md
└── rapport.pdf
```

## En résumé

| Opération | Méthode | Temps |
|---|---|---|
| Ajouter / chercher un colis | dictionnaire (table de hachage) | O(1) en moyenne |
| Trier par poids ou par valeur | tri fusion | O(n log n) |
| Trier par priorité | tri par dénombrement (5 priorités possibles) | O(n) |
| Statistiques | compteurs mis à jour à chaque ajout | presque immédiat |
| Remplir le camion | programmation dynamique (problème du sac à dos) | O(n' × W) |

W est la capacité du camion en kg. n' est le nombre de colis qui restent après avoir enlevé ceux qui ne
peuvent pas servir, ce qui rend le calcul rapide même avec 100 000 colis.

Pour la priorité, j'utilise un score : `valeur × (1 + α × (priorité − 1) / 4)`. Avec α = 1, un colis de
priorité 5 compte pour deux fois sa valeur. Les explications sont dans le rapport.
