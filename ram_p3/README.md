# ram_p3/ — Campagne P3 : la condition de §7 et le mur de compilation

## Question

§7 du papier conditionne l'utilité du durcissement (H4) à un régime où
l'autorité du repli est marginale devant le temps-avant-violation :
r = τ_armement / τ_violation proche de 1. Deux τ_violation sont à
distinguer (papier v4, §5.4) : le **τ_violation nominal**, mesuré sur le
modèle nominal du moniteur (C_BATT = 10 Ah, I_BASE = 0,5 A, u = 3 A,
marge 0,02, éclipse) — 205,8 s —, qui fixe l'échelle du **r_nominal**
(0,58 en P2, τ = 120 s) ; et le **τ_violation,plant** de chaque plante
Monte-Carlo (C_BATT ∈ [5 ; 9] Ah, I_BASE ∈ [0,45 ; 0,60] A), de 100,9 à
185,6 s, d'où un r_plant qui peut dépasser 1 (voir « Sensibilité »
ci-dessous). P3 pousse le seul levier autorisé — le délai d'armement du
repli — vers r = 1, tout le reste figé (graines, bornes de plante,
marges, seuils, grille σ, cycles, et la validation à la compilation sur
le modèle nominal 10 Ah). Note : les configurations figées indexent la
grille sur la constante de référence τ_violation = 400 s (estimation
d'alors) ; les valeurs rapportées dans le papier utilisent 205,8 s et
s'appellent le **r_nominal corrigé**, à ne pas confondre avec les
étiquettes historiques de la campagne.

## Ce que le pilote a trouvé (resultats_pilote_p3.json)

Pilote de puissance, bras B seul, N = 30, exécuté **avant** figeage du
critère : B reste à **zéro violation** sur toute la bande compilable, et
au-delà de τ_armement = 195 s (r ≈ 0,95 en unités physiques ; 0,4875 sur
la constante de référence 400 s de la config) **le jeu de contraintes
est refusé à la compilation** (RA-FUN-005 : depuis la frontière de
garde, l'action la plus défavorable persistée pendant l'armement ne doit
franchir aucun seuil brut — vérifié sur le modèle nominal).

Le régime où l'autorité du repli serait marginale n'est pas un régime
difficile à survivre : c'est un régime **non déployable dans le cadre
déclaré** — le mur dépend du modèle nominal (C_BATT = 10 Ah), des bornes
d'action déclarées (u_max = 3 A), des marges de sécurité et du jeu de
contraintes ; ce n'est pas une impossibilité physique générale.

## P3.1 (config_p3_1.json — figée, committée avant exécution)

Trois points couvrant la bande compilable — τ_armement = 140 / 170 /
190 s, soit r = 0,68 / 0,83 / 0,92 en unités physiques (0,35 / 0,425 /
0,475 — collé au mur — sur la constante de référence 400 s de la config
figée) — N = 300, quatre bras A, B, C, D, grille σ inchangée. Critère en
deux clauses (puissance, succès) : texte dans la config. But
documentaire : si B reste à zéro à r = 0,92 avec N = 300, le mur n'est
pas un artefact statistique de N = 30 (borne de Wilson ≈ 1,3 %).

Exécution : `.github/workflows/p3.yml` (déclenchement manuel, un job par
point r), puis fusion :

    python3 ram_p3/executer_p3_1.py --fusionne ram_p3/config_p3_1.json \
        ram_p3/resultats_p3_1.json ram_p3/partiel_r*.json

Non-régression : le bras A (aucun jeu compilé, indépendant de r) doit
reproduire le bras A de P2.3 bit à bit à chaque point.

## Sensibilité : le r physique des plantes (analyse_sensibilite_r.py)

Analyse rétrospective, **sans rejeu ni modification de données** : les
paramètres de plante de chaque run sont régénérés par le tirage
déterministe de la config figée (graine_plante + i), et
τ_violation,plant = 0,02 × C_BATT / (I_BASE + 3) × 3600 s (même
convention que le nominal : frontière de garde, u = 3 A, éclipse).
Résultats dans `resultats_sensibilite_r.json` :

- τ_violation,plant : **100,9 à 185,6 s** (nominal : 205,8 s) ;
- r_plant > 1,05 : 50 runs/300 dès P2 (τ = 120 s), 292 runs/300 au point
  τ = 190 s (r_plant jusqu'à 1,88) ;
- le bras B reste à **zéro violation observée** dans toutes les
  sous-populations (r < 1, r ≈ 1, r > 1), y compris le décile des
  r_plant les plus élevés (où le bras A viole dans 14 runs/30) ;
- l'ordre des coûts B < D < C est inchangé partout.

Exécution : `python3 ram_p3/analyse_sensibilite_r.py` (régénère
`resultats_sensibilite_r.json`).

## Fichiers

- `config_pilote_p3.json`, `pilote_p3.py`, `resultats_pilote_p3.json` —
  le pilote de puissance (avant figeage) ;
- `config_p3_1.json` — la configuration figée de P3.1 ;
- `executer_p3_1.py` — l'exécuteur parallèle (et la fusion) ;
- `partiel_r*.json`, `resultats_p3_1.json` — les résultats (ajoutés après
  exécution, par la CI puis par fusion locale) ;
- `analyse_sensibilite_r.py`, `resultats_sensibilite_r.json` — l'analyse
  de sensibilité rétrospective du r physique des plantes (v4).
