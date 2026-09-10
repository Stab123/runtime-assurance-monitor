# P4B — AUDIT D'IMPLÉMENTATION v0.2

**Réponse à l'audit externe de pré-exécution — verdict initial : NOT READY**
Date : 2026-09-10 21:44:14 UTC — Portée : implémentation seule, aucun résultat scientifique.

Ce document complète `P4B_IMPLEMENTATION_AUDIT_v0.1.md` (inchangé). Il traite
les 7 points du mandat de correction, dans l'ordre.

---

## 1. Bloqueur B-01 — `invalides` non initialisée (`combiner_sensibilite`)

**Constat de l'auditeur : confirmé.** Dans la version reproduite par le PDF
`P4B_CODE_SOURCE_Phase4.pdf`, `combiner_sensibilite()` contenait :

```python
    degradations = []
    for nom, vv in verdicts_variantes.items():
        ...
        if vv is None:
            invalides.append(nom)      # NameError : jamais initialisée
        ...
    elif not invalides and verdicts_variantes:   # NameError idem
```

**Correction mécanique appliquée — strictement celle prescrite :**

```python
    degradations = []
    invalides = []
```

Aucune autre ligne de `combiner_sensibilite` n'est modifiée. Aucune logique
scientifique n'est modifiée nulle part.

## 2. Bloqueur B-02 — asymétrie `labels_ocv_moins` (`combiner_sensibilites_ocv`)

**Constat de l'auditeur : confirmé** sur la version du PDF :
`labels_ocv_plus` était gardé par `is not None`, `labels_ocv_moins` était
envoyé inconditionnellement à `_verdict_variante()`.

**Correction — comportement déterministe et symétrique, règle gelée
inchangée** (None = variante non exécutée, analysée comme absente) :

```python
    variantes: dict[str, dict | None] = {}
    if labels_ocv_plus is not None:
        variantes["ocv_plus"] = _verdict_variante(
            labels_ocv_plus, n_invalid_plus, fraction_flag)
    if labels_ocv_moins is not None:
        variantes["ocv_moins"] = _verdict_variante(
            labels_ocv_moins, n_invalid_moins, fraction_flag)
    return combiner_sensibilite(verdict_principal, variantes, "OCV")
```

## 3. Tests requis — ajoutés et maintenus

Fichier `ram_p4b/tests/test_sensibilites_p4b.py` (SHA256 `ba571c31…`).
Labels et comptages 100 % synthétiques.

| # | Test requis | Test | Statut |
|---|---|---|---|
| 1 | variante OCV+ invalide | `test_variante_ocv_plus_invalide` | OK |
| 2 | variante OCV- invalide | `test_variante_invalide_n_invalide_pas_le_principal` (maintenu) | OK |
| 3 | deux variantes invalides | `test_deux_variantes_invalides` | OK |
| 4 | `labels_ocv_plus=None` | `test_labels_ocv_plus_none` | OK |
| 5 | `labels_ocv_moins=None` | `test_labels_ocv_moins_none` | OK |
| 6 | aucune variante disponible | `test_aucune_variante_disponible` | OK |
| 7 | V4 principal intact, annotation seule | `test_v4_intact_si_sensibilite_invalide_annotation_seule` | OK |

Le test 7 vérifie explicitement : code `V4` inchangé (jamais `V4-SENS`),
`b_star` non effacé, verdict inchangé, annotation « analyse invalide »
présente — une sensibilité techniquement invalide ne dégrade rien.

## 4. Suite synthétique relancée

- `python3 -m unittest discover -s ram_p4b/tests -p "test_*_p4b.py" -v`
  → **115/115 OK** (109 tests v0.1 + 6 nouveaux), exécutée 2026-09-10 21:44:08 UTC.
- `python3 ram_p4b/verifier_implementation_p4b.py` → **V-1…V-8 tous OK**,
  code de sortie 0, exécuté 2026-09-10 21:44:14 UTC.
- Sorties complètes : `P4B_TEST_REPORT_v0.2.txt`.

## 5. Résolution explicite de la divergence source/rapport (point 5)

**Question de l'auditeur :** le rapport v0.1 indique
`test_variante_invalide_n_invalide_pas_le_principal = OK`, alors que le
source reproduit dans le PDF ne peut pas passer ce test.

**Réponse : les deux faits sont vrais, et la faute est documentaire, pas
expérimentale.**

Chronologie horodatée (2026-09-11, UTC+8) :

| Heure | Événement |
|---|---|
| ~04:0x | Assemblage de l'instantané HTML du code source, **en cours de passe finale de corrections** |
| 04:07–04:26 | Passe finale de corrections Phase 4 (dont `invalides = []` + garde symétrique, 04:09:14) |
| 04:31:47 | Suite 109/109 OK + `P4B_TEST_REPORT_v0.1.txt` — **code corrigé testé** |
| 04:41:38 | Conversion du PDF **depuis l'instantané HTML figé, sans ré-assemblage** |

Preuves :

1. **La version du PDF échoue.** Reconstruction mécanique de la version
   reproduite dans le PDF (retrait des deux corrections, dans une copie
   jetable) puis exécution du même test → `NameError: name 'invalides' is
   not defined`, `FAILED (errors=1)`. La lecture de l'auditeur est exacte.
2. **La version testée en v0.1 passe.** Le code effectivement testé à
   04:31 (SHA256 `8da44e09…`, identique au code testé ici en v0.2) contient
   déjà la correction ; le test passe. Le « ok » du rapport v0.1 est
   véridique — avec la version buguée, ce test ne peut pas être « ok »,
   il est `ERROR` ; or le rapport v0.1 ne contient aucune erreur.
3. **Portée réelle du défaut : le PDF est obsolète pour 14 fichiers sur
   17**, pas seulement `sensibilites_p4b.py`. Comparaison jeton par jeton
   du texte extrait du PDF contre chaque fichier (détecteur conservatif :
   une divergence détectée est certaine) — divergents : `modele_p4b`,
   `campagne_p4b`, `analyse_p4b`, `controles_p4b`, `sensibilites_p4b`,
   `verifier_implementation_p4b`, et 8 fichiers de tests ; fidèles :
   `schemas_p4b`, `graines_p4b`, `test_graines_p4b`.

**Cause racine :** défaut de processus en Phase 4 — l'instantané HTML a
été figé avant la fin de la passe de corrections, puis converti en PDF
10 minutes après le rapport de tests sans ré-assemblage ni contrôle de
liaison de contenu. Le PDF livré ne reproduisait donc pas le code testé.

**Mesures correctives :**

- M1. Le PDF est régénéré depuis le code SHA256-vérifié de la présente
  v0.2 (`P4B_CODE_SOURCE_Phase4_v0.2.pdf`) ; l'ancien PDF est conservé
  tel quel comme pièce de l'audit (append-only) mais **ne doit plus être
  utilisé comme référence de code**.
- M2. Règle procédurale permanente : tout futur document « code source »
  est assemblé et converti de façon atomique, puis sa correspondance avec
  les fichiers est vérifiée jeton par jeton avant livraison.
  **Appliquée au présent PDF v0.2 : liaison de contenu vérifiée —
  17/17 fichiers reproduits fidèlement** (comparaison jeton par jeton
  du texte extrait du PDF contre les sources SHA256 du §6).

## 6. SHA256 du code réellement testé

| Fichier | SHA256 |
|---|---|
| `ram_p4b/modele_p4b.py` | `1b37222b03cabff891beab8e31c686fbdff4d8c5f7885fc095a5cfe2a88fb3e9` |
| `ram_p4b/campagne_p4b.py` | `4609162cff1e241cf13c6d5927047ea6bafbf9729ea956c0ee150637d3520286` |
| `ram_p4b/analyse_p4b.py` | `9ee1135030db5a34c28ae9452388c0dc039e4f954b081bfc7612152bc7edb915` |
| `ram_p4b/controles_p4b.py` | `de1f570e9085803b0b5f3611888e6ed67a7dad004e4ad4469a2886848c2f6cda` |
| `ram_p4b/sensibilites_p4b.py` | `8da44e090ed9aa0e15d7be8aeb83b052c3bc04a4ec8e3197765f551589f33239` |
| `ram_p4b/schemas_p4b.py` | `e67e4ec6d28da960fbfd28eb86a484b822a7a761023f3742b1fc2e380786c57e` |
| `ram_p4b/graines_p4b.py` | `956a8ac1f34afda0961dbd6781f25b9abafa9b0d9b36806d28853ee8df1d6215` |
| `ram_p4b/verifier_implementation_p4b.py` | `1804b9929cbcf4a2589bab81a7c3c4d2bf43fbc1e4047d70e8655e2a5945306f` |
| `ram_p4b/tests/test_modele_p4b.py` | `a2b0cf85f353f4675580bea65679808ee1c210a0f51b64a78ac7408e65f2ed6d` |
| `ram_p4b/tests/test_campagne_toy_p4b.py` | `eed9f5f9753bfa298c549458428f70b08e013003a766891c03ba667427a34962` |
| `ram_p4b/tests/test_analyse_p4b.py` | `f609f7da8ac5dd117a07c9fc643fcdce831a4699ab46dc124d9208ffe4976a16` |
| `ram_p4b/tests/test_controles_p4b.py` | `736604b49489131a8f2e764aa3484e1415ad94cc61c30342b37af93f2368138a` |
| `ram_p4b/tests/test_sensibilites_p4b.py` | `ba571c311ac80b0218821659fb719d737356ab69e3a6cd8f24ac4ee7e6a045f1` |
| `ram_p4b/tests/test_schemas_p4b.py` | `958d4bb4180936709c10bcfc2770114180d4b340cc41b3504391aa57931b47f4` |
| `ram_p4b/tests/test_tables_p4b.py` | `63abf4a6db749ed33cb9ce9238e3a2d830e0ec554534a5c0f64506b58a1ee39b` |
| `ram_p4b/tests/test_graines_p4b.py` | `f6e61045d9258c127916cc224e910bac2c7bc6f5cf28dc3c02706aed4cfa20bd` |
| `ram_p4b/tests/test_gel_p4b.py` | `790fee291dc67b1be0d8d98e31add1bb7774221c79257295668c05ed85794d0a` |

`sensibilites_p4b.py` : `8da44e09…` — **identique à la v0.1** : la
correction était déjà dans le code testé en v0.1 ; le bloqueur n'existait
que dans le PDF (voir §5). Seul changement de la v0.2 : ajout de 6 tests
(`test_sensibilites_p4b.py`, `ba571c31…`).

## 7. Confirmations de portée

- Aucun bloc réel du design exécuté ; aucune graine scientifique P4b ;
  aucune campagne ; aucun résultat (taux, frontière, verdict) produit.
- Aucun fichier gelé modifié (V-1 : 18 empreintes gelées vérifiées OK) ;
  v1.4.1, P4a, P2, P3, design, graines, tables, protocole : intacts.
- Les 37 exigences A-01…A-37 de l'audit v0.1 restent CONFORME (logique
  inchangée ; seuls des tests sont ajoutés).
- **STOP** après correction et tests. Aucun commit/push avant la revue
  externe de la v0.2.

---

*IMPLEMENTATION STATUS: READY FOR PRE-EXECUTION AUDIT (v0.2) — sous
réserve de la revue externe du présent document.*
