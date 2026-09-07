# empreintes/ — octets d'archive, pour vérification uniquement

Ces fichiers sont les octets exacts ayant produit les résultats publiés (P2.1, P2.2, P2.3). Ils existent pour la **vérification** des empreintes (`verifier_empreintes.py`, à la racine du dépôt), **pas pour l'exécution** : les chemins absolus de l'environnement de calcul d'origine y figurent tels quels. Pour rejouer la campagne, utilisez les copies de `ram_p0/` et `ram_p2/`, qui résolvent leurs chemins relativement au dépôt.

Conséquence attendue : un rejeu avec `ram_p2/` produit des `empreintes_code` identiques pour les quatre modules du moniteur (`moniteur.py`, `filtre.py`, `trace.py`, `contraintes.py` — jamais modifiés) mais différentes pour `campagne_p2.py` et `executer_p2_3.py` (seuls les chemins ont été relativisés). C'est précisément pour cela que la vérification pointe sur ce répertoire et non sur la copie exécutable.

## Pilote P2.1 (version trois bras de campagne_p2.py) — absent, motif écrit

P2.1 est la campagne pré-enregistrée qui porte la falsification de l'hypothèse H4 ; son pilote mérite donc une mention explicite.

Le fichier `campagne_p2.py` de P2.1 a été **édité en place** pour devenir la version quatre bras (P2.2), et l'environnement d'exécution d'origine (bac à sable éphémère, voir le README racine) n'en conserve aucune copie. Le fichier est donc matériellement perdu ; il n'est pas exclu du dépôt par choix. Ce qui survit :

- son empreinte SHA-256 tronquée, `0dad3d6d5bfe9f55`, embarquée dans `ram_p2/resultats_p2_1.json` ;
- la version quatre bras présente dans ce répertoire (empreinte `c5b0d30bdbeea612`), qui la **remplace** (*superseded*) et est conservée ici pour vérification uniquement.

La différence P2.1 → P2.2 est l'ajout du bras D. Chaque bras tire son aléa de graines propres (`graine_plante + i`, `graine_bruit + i`, un générateur neuf par bras) : rejouer la configuration P2.1 avec la version quatre bras reproduit les bras A, B et C de `resultats_p2_1.json` run par run, le bras D étant purement additif. `verifier_empreintes.py` affiche la ligne P2.1 comme attendue, avec ce motif.

## Copies rejouables (chemins relativisés)

P3, puis les rejeux P2.2/P2.3 de septembre 2026, exécutent les **copies rejouables** de `campagne_p2.py` et `executer_p2_3.py` (chemins relativisés, `ram_p2/`), dont les octets diffèrent donc des archives d'origine à chemins absolus — la sémantique de simulation est inchangée, prouvée par non-régression bit à bit (bras A de P3.1 == bras A de P2.3, 6300/6300 champs identiques ; pilote P3 à r = 0,3 == bras B de P2.3, 90/90 champs identiques). Les octets exacts de ces copies sont archivés ici :

- `campagne_p2_rejeu.py` — empreinte `6eb48963d9281c1b`, celle qu'embarquent les résultats rejoués (P2.2, P2.3, P3) sous la clé `campagne_p2.py` ;
- `executer_p2_3_rejeu.py` — empreinte `f2d35118c7bc15b1`, celle qu'embarquent les résultats P2.2/P2.3 rejoués sous la clé `executer_p2_3.py`.

Le vérificateur fait correspondre ces empreintes avec la mention « copie rejouable ». Les archives `campagne_p2.py` et `executer_p2_3.py` de ce répertoire restent les **octets d'origine à chemins absolus**, ceux qui ont produit les résultats P2.2/P2.3 d'avant la correction — conservés pour la provenance, ils ne correspondent plus à aucun fichier de résultats publié.

## P3 (pilote et campagne P3.1)

- `pilote_p3.py` — le pilote de puissance (écrit d'emblée à chemins relatifs : octets d'exécution = octets d'archive) ;
- `executer_p3_1.py` — l'exécuteur de P3.1 (ajouté après exécution, octets inchangés depuis le figeage de la config).

## pre_correction/ — octets d'avant la correction de septembre 2026

Une relecture du code a trouvé deux défauts, corrigés puis rejoués (note complète dans le README racine) : l'off-by-one temporel de RA-FUN-004 (`k <= pas_armement` persistait l'action un pas de trop) et la projection sous `u_min` (bug latent, jamais atteint en campagne). P2.2, P2.3, le pilote P3 et P3.1 ont été rejoués avec le code corrigé, configurations strictement inchangées : les archives principales de `moniteur.py` et `filtre.py` sont donc les octets **corrigés**.

P2.1, campagne historique déjà supplantée par P2.2, n'a pas été rejouée. Les octets pré-correction ayant produit ses résultats sont conservés ici :

- `pre_correction/moniteur.py` — empreinte `7f9937f834597201` ;
- `pre_correction/filtre.py` — empreinte `9bf5cb4253077fe0`.

Le vérificateur fait correspondre les empreintes `moniteur.py` / `filtre.py` de `resultats_p2_1.json` à ces octets, avec la mention « pré-correction, archivé ». `trace.py` et `contraintes.py` n'ont pas été touchés par la correction : leur archive principale vaut pour toutes les campagnes, P2.1 incluse.
