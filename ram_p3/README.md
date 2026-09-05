# ram_p3/ — Campagne P3 : la condition de §7 et le mur de compilation

## Question

§7 du papier conditionne l'utilité du durcissement (H4) à un régime où
l'autorité du repli est marginale devant le temps-avant-violation :
r = τ_armement / τ_violation proche de 1. En P2, r ≈ 0,3. P3 pousse le
seul levier autorisé — le délai d'armement du repli — vers r = 1, tout le
reste figé (graines, bornes de plante, marges, seuils, grille σ, cycles,
et la validation à la compilation sur le modèle nominal 10 Ah).

## Ce que le pilote a trouvé (resultats_pilote_p3.json)

Pilote de puissance, bras B seul, N = 30, exécuté **avant** figeage du
critère : B reste à **zéro violation** sur toute la bande compilable, et
au-delà de τ_armement = 195 s (r = 0,4875) **le jeu de contraintes est
refusé à la compilation** (RA-FUN-005 : depuis la frontière de garde,
l'action la plus défavorable persistée pendant l'armement ne doit
franchir aucun seuil brut — vérifié sur le modèle nominal).

Le régime où l'autorité du repli serait marginale n'est pas un régime
difficile à survivre : c'est un régime **non déployable par construction**.

## P3.1 (config_p3_1.json — figée, committée avant exécution)

Trois r couvrant la bande compilable — 0,35 / 0,425 / 0,475 (collé au mur) —
N = 300, quatre bras A, B, C, D, grille σ inchangée. Critère en deux
clauses (puissance, succès) : texte dans la config. But documentaire :
si B reste à zéro à r = 0,475 avec N = 300, le mur n'est pas un artefact
statistique de N = 30 (borne de Wilson ≈ 1,3 %).

Exécution : `.github/workflows/p3.yml` (déclenchement manuel, un job par
point r), puis fusion :

    python3 ram_p3/executer_p3_1.py --fusionne ram_p3/config_p3_1.json \
        ram_p3/resultats_p3_1.json ram_p3/partiel_r*.json

Non-régression : le bras A (aucun jeu compilé, indépendant de r) doit
reproduire le bras A de P2.3 bit à bit à chaque point.

## Fichiers

- `config_pilote_p3.json`, `pilote_p3.py`, `resultats_pilote_p3.json` —
  le pilote de puissance (avant figeage) ;
- `config_p3_1.json` — la configuration figée de P3.1 ;
- `executer_p3_1.py` — l'exécuteur parallèle (et la fusion) ;
- `partiel_r*.json`, `resultats_p3_1.json` — les résultats (ajoutés après
  exécution, par la CI puis par fusion locale).
