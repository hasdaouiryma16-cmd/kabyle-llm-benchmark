# Métriques

## Note humaine (métrique principale)

- Moyenne des notes de 0 à 3, également exprimée en % (note / 3 × 100).
- **Intervalle de confiance à 95 %** par bootstrap : 1 000 rééchantillonnages des tests notés avec remise, puis percentiles 2,5 et 97,5. C'est simple, sans hypothèse de normalité, et honnête sur les petits échantillons.

## chrF++ (métrique automatique principale)

- F-score sur les n-grammes de **caractères** (jusqu'à 6), complété par les n-grammes de mots (jusqu'à 2, le « ++ »). Implémentation : `sacrebleu` (`CHRF(word_order=2)`).
- **Pourquoi pour le kabyle.** C'est une langue à morphologie riche (affixes, états, clitiques) et à orthographe variable. Une erreur sur un affixe coûte peu en caractères alors qu'elle annule un mot entier en BLEU. chrF++ est la métrique de référence pour les langues peu dotées (FLORES-200, AmericasNLP).
- **Plusieurs références.** Le score retenu est le meilleur obtenu contre l'une des références.
- **Nettoyage minimal de la sortie.** Seuls les espaces et les guillemets englobants (« … ») sont retirés. Le contenu n'est jamais modifié.

## BLEU (secondaire)

Fourni pour la comparabilité avec la littérature : BLEU de phrase de `sacrebleu`, avec `effective_order`. Peu fiable sur des phrases courtes, il n'est jamais utilisé pour classer les modèles.

## Pourquoi pas COMET ?

COMET s'appuie sur XLM-R, dont le pré-entraînement couvre mal le kabyle. Ses scores seraient peu fiables, voire trompeurs. C'est une limite assumée.

## Langue et écriture de la réponse

1. **Écriture dominante** (déterministe) : proportion de lettres latines, tifinagh (U+2D30–U+2D7F) ou arabes.
2. **Langue détectée** :
   - **GlotLID** (fastText, plus de 1 600 langues dont `kab`) s'il est installé (voir [`lab.md`](lab.md)) ;
   - sinon, une **heuristique prudente** : écriture arabe → arabe, mots outils français → français. Elle **ne déclare jamais** qu'une réponse est en kabyle.
3. **`lang_ok`** : la réponse est-elle dans la langue et l'écriture attendues ? La valeur `null` signifie « impossible de trancher ». Seuls les cas tranchés entrent dans le taux de « bonne langue », et leur nombre est affiché.

## Gains d'une variante

Pour les tests notés à la fois pour la variante et son modèle de base :

- gain en points = % moyen après − % moyen avant ;
- gain relatif = gain en points / % moyen avant × 100 ;
- intervalle de confiance à 95 % : bootstrap sur les différences appariées.

Ces calculs sont aussi faits par catégorie, et pour chrF++.

## Corrélation note humaine / chrF++

La note humaine et chrF++ sont tous deux exportés pour chaque réponse. Leur corrélation, à calculer quand le jeu sera complet, indique dans quelle mesure chrF++ peut servir d'indicateur rapide pour le kabyle.
