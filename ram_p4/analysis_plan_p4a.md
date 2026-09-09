# PLAN D'ANALYSE ET DIMENSIONNEMENT P4a

Document de justification du préenregistrement — figé au même commit. Tous
les calculs sont antérieurs à toute donnée P4a. La simulation de puissance
utilise uniquement des tirages Bernoulli théoriques à hypothèses explicitement
déclarées : aucun code dynamique P4, aucun résultat P4.

## 1. Intervalle de Wilson et cas zéro événement

IC de Wilson 95 % bilatéral (z = 1.959963985130054) :

    centre = (p̂ + z²/2N) / (1 + z²/N)
    demi-largeur = z·√(p̂(1−p̂)/N + z²/4N²) / (1 + z²/N)

Pour k = 0 événement : U = z²/(N + z²).
- N = 500 → U = 3.841/503.841 = **0.0076 < εS = 0.01** : S déclarable.
- N = 200 → U = 0.0188 > εS : une réplication S est impossible à N = 200 —
  raison pour laquelle RESEED est un test de direction/effet, pas une
  réplication de classes.

## 2. Puissance de classification (N = 500/niveau)

**F** : le plus petit compte dont la borne inf Wilson dépasse εF = 0.05 est
x = 35 (p̂ = 0.070 ; IC [0.0508 ; 0.0958]). Puissance P(X ≥ 35) :

| p vrai | 0.05 | 0.06 | 0.08 | 0.10 | 0.15 |
|---|---|---|---|---|---|
| P(déclarer F) | 0.03 | 0.20 | 0.82 | 0.99 | 1.00 |

Zone p ∈ ]0.05 ; 0.08[ → classification T assumée et déclarée.

**S** : S exige 0 événement (U = 0.0076 < εS ; 1 événement → borne sup
0.0111 > εS). P(X = 0) : p = 0 → 1.00 ; p = 0.001 → 0.61 ; p = 0.002 → 0.37 ;
p = 0.005 → 0.08. Un niveau à p vrai ∈ ]0 ; εS[ peut donc tomber en T —
classification correcte au sens où T est une catégorie réelle, jamais F.

## 3. Simulation de dimensionnement (hypothèses déclarées)

Modèle théorique : p(b) logistique ; 5 niveaux positifs ; 500 blocs ;
dépendance CRN par copule gaussienne ρ = 0.5 ; ajustement isotonique + règles
de plateau ; bootstrap 200 répliques par blocs ; 150 répétitions.

- **Scénario MILIEU** (b\* ≈ 0.05) : puissance du test de tendance
  (logistique, SE cluster-robust, unilatéral α = 0.05) = **1.00** ;
  largeur IC(b\*) : moyenne 0.0104, q90 = **0.0145** ; b\* défini dans 100 %
  des cas.
- **Scénario BORD** (b\* ≈ 0.09) : puissance = **1.00** ; largeur moyenne
  0.0085, q90 = 0.0105 ; b\* défini dans 100 % des cas.
- **Scénario SANS FRONTIÈRE** (p = 0 partout) : 0 événement à tous les
  niveaux → tous S ; P(faux F) = 0 analytiquement.

Conclusion du dimensionnement : N = 500/niveau satisfait les critères A, B, D,
E du protocole ; la largeur cible IC(b\*) ≤ 0.02 est atteinte avec marge.

## 4. N total maximal

| Composante | Runs |
|---|---|
| Principal (9 niveaux × 500 blocs) | 4500 |
| RESEED (9 niveaux × 200 blocs) | 1800 |
| DTCTRL (2 niveaux × 500 blocs, DT = 2.5 s) — amendement pré-data | 1000 |
| **Total maximal** | **7300** |

Mesure de charge (code P2 figé, b = 0, exploratoire) : ≈ 0.53 s/run à
DT = 5 s (≈ 1.06 s à DT = 2.5 s) → ≈ 90 min de calcul. Aucun ajustement de
N après observation.

**DTCTRL (amendement pré-data)** : mêmes 500 blocs et mêmes graines NOISE que
le principal ; seul DT change. Les classifications (N = 500 des deux côtés)
sont directement comparables — une discordance ne peut plus être un artefact
de résolution (0/200 → T aurait faussement contredit 0/500 → S).

**Cas non estimable (amendement pré-data)** : si tous les Y des niveaux
positifs sont identiques, la pente logistique est NON ESTIMABLE ; aucun test
de tendance n'est interprété, sans bloquer la voie B. Même traitement RESEED.

**Localisation (amendement pré-data)** : A exige b\* défini dans ≥ 95 % des
2000 répliques bootstrap, en plus de la largeur d'IC ≤ 0.02.

## 5. Analyse (script unique `analyse_p4a.py`)

Wilson → classes S/T/F par niveau ; INCONCLUSIVE si > 2 % de runs invalidés
par invariant logiciel sur le niveau ; tendance logistique cluster-robust ;
PAVA + b\* avec règles de plateau ; bootstrap 2000 par blocs (seed BOOTSTRAP) ;
RESEED : tests z d'homogénéité (Bonferroni 0.05/9) + concordance du signe de
pente ; DTCTRL : concordance de classification ; verdict global A–E
automatique. Aucune décision humaine après lecture des résultats.

## 6. Reproductibilité

Versions Python/numpy/scipy/statsmodels enregistrées à l'exécution dans les
métadonnées ; RNG `random.Random` par graine dérivée (`graines_p4.py`) ;
ordre des runs fixe (bloc puis niveau) ; parallélisation autorisée par
plages de blocs indépendantes (`--debut/--fin`), non-régression vérifiée au
pilote ; hashes SHA-256 code/config dans les métadonnées de chaque fichier de
résultats ; données brutes jamais remplacées silencieusement.
