### MOPSI

Projet MOdéliser Programmer SImuler (MOPSI) de 2ème année à l'ENPC.

Nous avons travaillé sur le piaulage des admissibles au coucours Mines-Ponts au sein de la résidence de l'ENPC. Nous avons modélisé ce problème comme un problème d'optimisation linéaire en nombres entiers. Nous avons eu recours à deux approches :
* Résolution exacte à l'aide d'un solveur (Gurobi). Cette approche est limitée aux instances de petite taille.
* Résolution approchée avec une heuristique simple : découpage en sous-problèmes, résolution de chacun d'eux avec le solveur, puis amélioration de la solution obtenue par recherche locale.

Cette solution est utilisée par le [KI Clubinfo](https://github.com/KIClubinfo) pour réaliser le piaulage des admissibles chaque année.
