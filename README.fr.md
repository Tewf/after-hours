# Projets personnels

> [Read in English](README.md)

Ce que je construis sur mon temps libre, en apprentissage automatique, calcul
formel et mathématiques appliquées. Chaque dossier est autonome, avec son propre
README et ses dépendances.

| Projet | De quoi il s'agit |
|---|---|
| [Flappy Bird à partir des pixels bruts](Flappy_Bird_CNN/) | Un réseau de politique convolutif entraîné par REINFORCE sur des images 84×84, sans aucun accès à l'état du jeu. *PyTorch, Pygame, Gymnasium* |
| [Solveur 3-SAT sur GF(2)](Groebner_Basis_SAT_Solver/) | Les clauses deviennent des polynômes ; une élimination triangulaire à la Gröbner propage, le branchement termine. Confronté à une recherche exhaustive sur 2 500 instances. *Python* |
| [Algorithmes matriciels réimplémentés de zéro](Linear_Algebra/) | Multiplication par FFT 2D, déterminant en O(n^log n), trace d'un produit sans calculer le produit, élimination de Gauss exacte sur les rationnels. *Python, NumPy* |
| [L'impôt français, modélisé](Taxes/) | Ajustements exponentiels par tranche, puis la fonction W de Lambert pour trouver le point de bascule — 62 114 € brut. *SciPy, Quarto* |
| [Algorithmes de tri en 3D](Blender_Python_Scripts/) | Tri à bulles et tri fusion animés via l'API Python de Blender. *Blender* |

## Lancer l'un d'eux

```sh
cd <dossier>
pip install -r requirements.txt
```

Le README de chaque dossier indique quoi y lancer. Les scripts Blender, eux, se
chargent dans l'espace de travail Scripting.

## Licence

[MIT](LICENSE)
