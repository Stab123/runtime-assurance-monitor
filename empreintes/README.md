# empreintes/ — octets d'archive, pour vérification uniquement

Ces fichiers sont les octets exacts ayant produit les résultats publiés (P2.1, P2.2, P2.3). Ils existent pour la **vérification** des empreintes (`verifier_empreintes.py`, à la racine du dépôt), **pas pour l'exécution** : les chemins absolus de l'environnement de calcul d'origine y figurent tels quels. Pour rejouer la campagne, utilisez les copies de `ram_p0/` et `ram_p2/`, qui résolvent leurs chemins relativement au dépôt.

Conséquence attendue : un rejeu avec `ram_p2/` produit des `empreintes_code` identiques pour les quatre modules du moniteur (`moniteur.py`, `filtre.py`, `trace.py`, `contraintes.py` — jamais modifiés) mais différentes pour `campagne_p2.py` et `executer_p2_3.py` (seuls les chemins ont été relativisés). C'est précisément pour cela que la vérification pointe sur ce répertoire et non sur la copie exécutable.

## Pilote P2.1 (version trois bras de campagne_p2.py) — absent, motif écrit

P2.1 est la campagne pré-enregistrée qui porte la falsification de l'hypothèse H4 ; son pilote mérite donc une mention explicite.

Le fichier `campagne_p2.py` de P2.1 a été **édité en place** pour devenir la version quatre bras (P2.2), et l'environnement d'exécution d'origine (bac à sable éphémère, voir le README racine) n'en conserve aucune copie. Le fichier est donc matériellement perdu ; il n'est pas exclu du dépôt par choix. Ce qui survit :

- son empreinte SHA-256 tronquée, `0dad3d6d5bfe9f55`, embarquée dans `ram_p2/resultats_p2_1.json` ;
- la version quatre bras présente dans ce répertoire (empreinte `c5b0d30bdbeea612`), qui la **remplace** (*superseded*) et est conservée ici pour vérification uniquement.

La différence P2.1 → P2.2 est l'ajout du bras D. Chaque bras tire son aléa de graines propres (`graine_plante + i`, `graine_bruit + i`, un générateur neuf par bras) : rejouer la configuration P2.1 avec la version quatre bras reproduit les bras A, B et C de `resultats_p2_1.json` run par run, le bras D étant purement additif. `verifier_empreintes.py` affiche la ligne P2.1 comme attendue, avec ce motif.
