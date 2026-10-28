# Sources des données d'amélioration (phase 2)

Chaque corpus utilisé pour le few-shot, le RAG ou le fine-tuning est listé ici avec sa licence **vérifiée**. Vérification faite le 28/10/2026 : le fichier ou la page de licence a été ouvert ; les points non confirmés sont signalés comme tels.

## Sources utilisées par les pipelines

| Source | Téléchargement | Contenu | Licence | Usage dans le projet |
|---|---|---|---|---|
| **Tatoeba** (via OPUS, build v2026-07-08) | `object.pouta.csc.fi/OPUS-Tatoeba/v2026-07-08/moses/fr-kab.txt.zip` | 93 908 paires français–kabyle | **CC BY 2.0 FR**, certaines phrases CC0 ([conditions](https://tatoeba.org/fr/terms_of_use)) | few-shot, RAG, fine-tuning |
| **Common Voice** : phrases kabyles | `github.com/common-voice/common-voice` → `server/data/kab/*.txt` | ≈ 180 000 phrases monolingues | **CC0** (domaine public, d'après le README du dépôt) | corpus monolingue (`mono_kab.txt`) |
| **NLLB v1** (OPUS), en option `--with-nllb` | `object.pouta.csc.fi/OPUS-NLLB/v1/moses/fr-kab.txt.zip` | ≈ 1 million de paires, alignées automatiquement (LASER3) | **ODC-By 1.0**, plus les conditions des sources d'origine (Common Crawl) | désactivé par défaut : données bruitées, n'utiliser que les meilleures paires |

**Attribution Tatoeba.** Les phrases proviennent de Tatoeba (<https://tatoeba.org>), dont les contributeurs sont listés sur le site. Elles sont réutilisées sous licence CC BY 2.0 FR.

## Sources identifiées, non intégrées pour l'instant

| Source | Licence | Remarque |
|---|---|---|
| Wikipédia en kabyle (`dumps.wikimedia.org/kabwiki`) | CC BY-SA 4.0 | ≈ 7 200 articles ; nécessite une extraction du wikitexte |
| PanLex (`cointegrated/panlex-meanings`, Hugging Face) | CC0 (étiquette Hugging Face) | meilleur lexique ouvert français–kabyle repéré, à joindre par identifiant de sens |
| Wiktionnaire français, traductions en kabyle | CC BY-SA 4.0 | ≈ 860 pages, petit mais propre |
| `Imsidag-community/kabyle-corpus-*` (Hugging Face) | CC BY-SA 4.0 | corpus monolingues |
| `abdelhaqueidali/Kabyle-Latin-to-Tifinagh-Parallel-Corpus` | CC BY 2.0 | utile pour l'écriture tifinagh |
| Mozilla-I10n (OPUS) | MPL-2.0 (non confirmé) | chaînes d'interface logicielle |

## Exclues

| Source | Raison |
|---|---|
| **FLORES+ / SIB-200** (`kab_Latn`) | Jeux d'**évaluation** de référence : à n'utiliser qu'en évaluation externe, jamais pour l'entraînement |
| Dictionnaire Dallet et autres dictionnaires publiés | Protégés par le droit d'auteur |
| `taqbaylit/timucuha-kabyle-tales`, `goldfish-models/fish-food` | Licence non commerciale (NC) |
| Dépôts sans licence explicite (`Sifal/Kabyle-French`, `FrancophonIA/Kabyle-French-pairs`…) | Licence inconnue ; souvent des copies de Tatoeba ou NLLB |

## Règle de non-contamination

Aucune phrase présente dans `data/test/` (publique ou privée) ne peut figurer dans ces données, ni exactement ni presque (similarité ≥ 0,8). `pipelines/prepare.py` les retire. `pipelines/check_contamination.py` le vérifie, et la CI le contrôle à chaque push. Le labo refuse aussi de lancer une variante few-shot ou RAG dont les données recoupent le jeu de test.
