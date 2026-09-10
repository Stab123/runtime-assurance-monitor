# Annexe POST-HOC / EXPLORATOIRE — P4a

> **Statut** : analyse descriptive écrite APRÈS le verdict confirmatoire D gelé.
> Elle n'est pas préenregistrée, ne modifie ni le verdict, ni aucun seuil, ni
> aucune donnée. Script reproductible : `exploratoire_post_hoc_p4a.py`.
> Résultats machine : `exploratoire_post_hoc_p4a_resultats.json`.

## 1. Question

Le bilan confirmatoire montre un plateau : 21/500 violations à b=+0.05 et
21/500 à b=+0.10. S'agit-il des **mêmes blocs**, et qu'est-ce qui les
caractérise physiquement ?

## 2. Emboîtement — réponse : oui, exactement

- |D(+0.02)| = 7, |D(+0.05)| = 21, |D(+0.10)| = 21
- D(+0.02) ⊆ D(+0.05) = D(+0.10) : emboîtement **strict et total**
- Les 21 blocs : 7, 30, 44, 57, 70, 73, 122, 139, 153, 161, 199, 211, 219,
  224, 287, 306, 310, 318, 351, 370, 416

Sous bruit commun (CRN), un bloc qui viole à un niveau de biais viole à tous
les niveaux supérieurs : la défaillance est une propriété **du bloc**, pas du
tirage de bruit.

## 3. Signature physique des 21 blocs

Facteur discriminant principal : **marge_min à b=0**. Les 21 défaillants sont
les 21 blocs dont le creux SoC à biais nul est épinglé au garde-fou
(marge ≈ +0.0200–0.0211, rangs 0–22 sur 500 par marge croissante, deux
inversions près).

| groupe | C_BATT méd. | I_SUN méd. | I_BASE méd. | soc0 méd. | marge R2 méd. |
|---|---|---|---|---|---|
| Défaillants (21) | 7.0 Ah | 1.28 A | 0.45 A | 0.428 | 247 A·s |
| Non défaillants (479) | 9.5 Ah | 1.75 A | 0.38 A | 0.555 | 2846 A·s |

Profil : blocs énergétiquement tendus (proches de la frontière d'admissibilité
R2), batterie plus petite, SoC initial plus bas.

## 4. Mécanique du plateau (observation, pas preuve)

Chez les défaillants, la marge sous biais suit ≈ `marge(0) − b`
(ex. 0.0200 − 0.05 = −0.0300) : le biais se transmet 1:1 au creux vrai — ces
blocs « absorbent ». Mais **132 blocs** ont marge(0) < 0.10 et seuls 21
violent à +0.10 : la majorité **s'adapte** (la boucle referme, le filtre
étrangle davantage, la marge sature au lieu de décroître — ex. bloc 127 :
+0.0200 → +0.0052 → +0.0047 → +0.0047).

Le plateau 21 = 21 vient donc de la structure des blocs épinglés au garde-fou,
pas d'un effet de seuil de la grille.

## 5. Limite

Aucun séparateur univarié net ne distingue absorbants d'adaptants parmi les
épinglés (C_BATT et marge R2 plus élevés chez les adaptants, en tendance
seulement — ex. bloc 73 : 13.2 Ah, absorbant ; bloc 375 : 4.7 Ah, adaptant).
Une explication multivariée complète relèverait d'une campagne P4a.2 dédiée,
préenregistrée séparément.
