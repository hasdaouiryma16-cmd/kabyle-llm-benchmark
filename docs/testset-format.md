# Format du jeu de tests

## Fichiers

| Fichier | Contenu | Dans Git ? |
|---|---|---|
| `data/test/kab-bench.v1.jsonl` | Tests publics, un objet JSON par ligne | Oui |
| `data/test/private/kab-bench.v1.private.jsonl` | Tests privés (~20 %) | **Non** (ignoré) |
| `data/test/MANIFEST.json` | Version, empreintes, chaîne canari, comptes | Oui |

Encodage UTF-8 sans BOM, fins de ligne LF, texte normalisé **Unicode NFC**.

Le JSONL est la **source de vérité**. La base SQLite du labo en est une copie de travail :
- « Enregistrer dans le dépôt » (`POST /api/testset/save-to-repo`) écrit les fichiers et le manifeste ;
- « Recharger depuis le dépôt » (`POST /api/testset/load-from-repo`) reconstruit la base.

⚠️ La partie privée n'existe que sur ta machine. Pense à la sauvegarder ailleurs (clé USB, stockage chiffré).

## Champs

| Champ | Type | Obligatoire | Description |
|---|---|---|---|
| `id` | texte | généré si absent | Minuscules, chiffres, tirets. Ex. `tr-fr-kab-0001` |
| `category` | énum | oui | `translation_fr_kab`, `translation_kab_fr`, `comprehension`, `culture`, `writing`, `conversation` |
| `subcategory` | texte | non | Thème libre : famille, nature, nombres… |
| `script` | énum | défaut `latin` | `latin` ou `tifinagh` |
| `prompt` | texte | oui | Consigne envoyée telle quelle au modèle |
| `source_text` | texte | pour les traductions | Texte à traduire |
| `context` | texte | pour la compréhension | Court texte kabyle sur lequel porte la question |
| `references` | liste de textes | pour la notation auto | Une ou plusieurs réponses de référence acceptables |
| `grading` | énum | défaut `auto+human` | `auto`, `human`, `auto+human` |
| `expected_lang` | texte | défaut `kab` | Langue attendue de la réponse (`kab`, `fr`) |
| `difficulty` | 1 à 3 | défaut 1 | Niveau de difficulté |
| `split` | énum | défaut `public` | `public` ou `private` |
| `status` | énum | défaut `draft` | `draft` (exclu du benchmark) ou `ready` |
| `source` | texte | défaut `author` | Origine du test |
| `author` | texte | non | Autrice de la référence |
| `notes` | texte | non | Remarques libres (n'affectent pas l'empreinte) |
| `created_at`, `updated_at` | date ISO 8601 UTC | automatique | |

## Règles de validation (statut `ready`)

Un test ne peut passer en `ready` que s'il est complet :
- notation `auto` ou `auto+human` → au moins une référence ;
- traduction → `source_text` renseigné ;
- compréhension → `context` renseigné.

Un brouillon (`draft`) peut être incomplet.

## Empreinte du benchmark

`content_hash` = SHA-256 des tests `ready`, triés par identifiant, limités aux champs réellement évalués
(`id`, `category`, `script`, `prompt`, `source_text`, `context`, `references`, `grading`, `expected_lang`).
Modifier une note ou une date ne change pas l'empreinte ; modifier une référence la change.
Chaque exécution de benchmark enregistrera cette empreinte : deux scores ne sont comparables que s'ils
partagent la même.

## Chaîne canari

Le manifeste contient un GUID unique (`canary`), généré une fois puis conservé. Si un futur modèle est
capable de le restituer, c'est qu'il a été entraîné sur ce jeu de test.

## Import / export

- **JSONL** : format natif.
- **JSON** : `{"items": [...]}` ou une liste.
- **CSV** : une colonne par champ ; `references` contient une liste JSON (ex. `["réf 1", "réf 2"]`).
  L'export ajoute un BOM UTF-8 pour qu'Excel affiche correctement ɛ, ɣ, ḥ et le tifinagh.

L'import est **tout ou rien** : si une seule ligne est invalide, rien n'est écrit et le rapport liste
chaque erreur avec son numéro de ligne. Un test dont l'`id` existe déjà est mis à jour.
