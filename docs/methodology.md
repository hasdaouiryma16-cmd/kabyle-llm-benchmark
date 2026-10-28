# Méthodologie

## 1. Jeu de test

- **Autrice unique, locutrice native.** Les références en kabyle (traductions, textes de compréhension, réponses culturelles, transcriptions tifinagh) sont toutes écrites à la main. L'IA n'a fourni que la structure, les catégories et les consignes en français ([`data/prompts/guided_fr.yaml`](../data/prompts/guided_fr.yaml)).
- **Plusieurs références par test** quand plusieurs formulations ou orthographes sont acceptables. chrF++ prend la meilleure correspondance.
- **Statuts.** Seuls les tests au statut `ready` (complets et validés) entrent dans le benchmark.
- **Partie privée (≈ 20 %).** Elle n'est jamais publiée, pour garder une mesure non contaminée même si le jeu public finit dans l'entraînement de futurs modèles.
- **Versionnement.** Le fichier JSONL est versionné dans Git. Le manifeste contient une version sémantique, l'empreinte SHA-256 des tests évalués et une chaîne canari. Voir [`testset-format.md`](testset-format.md).

## 2. Interrogation des modèles

- **Même message pour tous.** La consigne du test est envoyée telle quelle, précédée du texte de compréhension s'il y en a un, sans consigne système. Les consignes de traduction précisent « réponds uniquement par la traduction », pour ne pas pénaliser un modèle bavard sur les métriques automatiques.
- **Paramètres.** La température est à 0 partout où l'API l'accepte. Les exceptions sont documentées dans `backend/config/models.yaml` :
  - les modèles Claude actuels n'acceptent plus `temperature`, et leur niveau d'effort est fixé explicitement ;
  - le raisonnement de Qwen3.5 est désactivé pour obtenir une réponse directe.

  Les paramètres réels sont enregistrés avec chaque réponse.
- **Pas de repli automatique.** Si un modèle refuse de répondre, le refus est enregistré tel quel. Aucun autre modèle ne répond à sa place.
- **Copie figée.** Chaque exécution enregistre une copie des tests au moment du run et l'empreinte du jeu. Une modification ultérieure d'un test ne change pas l'interprétation des réponses déjà obtenues.
- **Robustesse.**
  - Les appels en erreur temporaire (429, 5xx, réseau) sont relancés avec une attente exponentielle.
  - Une exécution interrompue reprend sans rejouer les réponses déjà obtenues.
  - Un plafond de coût arrête l'exécution si nécessaire.

## 3. Notation

### Humaine, à l'aveugle (note de référence)

| Note | Signification |
|---|---|
| 0 | Faux, hors sujet, incompréhensible ou dans une autre langue |
| 1 | Partiellement correct, erreurs importantes |
| 2 | Correct sur le fond, erreurs mineures (orthographe, tournure) |
| 3 | Correct et naturel |

Les réponses sont tirées au hasard, toutes exécutions et tous modèles confondus. L'interface ne reçoit ni le modèle, ni le fournisseur, ni les scores automatiques, pour éviter tout biais d'ancrage. Le modèle n'est révélé qu'après la note, sur demande.

### Automatique (indicateurs)

chrF++, BLEU, écriture dominante et langue détectée. Voir [`metrics.md`](metrics.md).

## 4. Analyse des erreurs

Chaque réponse notée peut recevoir une ou plusieurs étiquettes :

| Étiquette | Exemple de situation |
|---|---|
| Mauvaise langue | répond en français ou en anglais |
| Confusion avec l'arabe | mots ou écriture arabes |
| Autre langue berbère | formes chleuhes, rifaines, touarègues… |
| Mots inventés | formes qui n'existent pas en kabyle |
| Orthographe / transcription | ɛ, ɣ, ḥ… manquants ou erronés |
| Grammaire / conjugaison | accords, états, aspects |
| Contresens | sens erroné |
| Trop littéral | calque du français |
| Incomplet | réponse tronquée |
| Mauvaise écriture | latin au lieu de tifinagh, ou l'inverse |
| Refus | non-réponse |

Les distributions d'étiquettes par modèle alimentent l'analyse de la phase 3.

## 5. Comparaison avant/après (phase 3)

Une variante (few-shot, RAG, fine-tunée) est déclarée avec son modèle de base. Le gain est calculé **uniquement sur les tests notés pour les deux modèles** (comparaison appariée), en points de pourcentage et en pourcentage relatif, avec un intervalle de confiance bootstrap sur les différences. Les deux modèles doivent avoir été évalués sur le même jeu de test (même empreinte).
