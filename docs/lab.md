# Utiliser le labo

## Lancer et arrêter

```bash
docker compose up -d        # API (127.0.0.1:8800) + interface (127.0.0.1:5173)
docker compose logs -f api  # journaux
docker compose down         # arrêt (les données restent)
```

Les clés API se mettent dans `.env` (copie de `.env.example`), qui n'est jamais commité. Après une modification de `.env` : `docker compose up -d --force-recreate api`.

## 1. Écrire les tests

- **Mode guidé** : 52 consignes en français, proposées une à une. Pour chacune, saisir ce qui est demandé (référence kabyle, phrase source kabyle, texte de compréhension…). <kbd>Ctrl</kbd>+<kbd>Entrée</kbd> enregistre. « Passer » met une consigne de côté.
- **Tests** : création libre, modification, filtres, import/export JSON, JSONL ou CSV (le CSV s'ouvre dans Excel avec les bons caractères).
- **Barre de caractères** : un clic insère ɛ, ɣ, ḥ, ṭ, ẓ, č, ǧ, ṛ, ṣ, ḍ… ou une lettre tifinagh à la position du curseur. La liste est modifiable dans `lab-ui/src/lib/charsets.ts`.
- **Partie privée** : cocher « Partie privée » pour environ un test sur cinq.
- **Enregistrer dans le dépôt** (onglet Tests) écrit `data/test/kab-bench.v1.jsonl`, la partie privée (ignorée par Git) et `MANIFEST.json`. Il faut ensuite commiter.

## 2. Lancer une exécution

Onglet **Exécutions**, puis **Nouvelle exécution** :

1. Choisir les modèles. Un modèle grisé n'a pas de clé API, ou Ollama ne répond pas.
2. Garder le **mode test** (2 questions par catégorie) pour une première vérification.
3. Vérifier l'**estimation** : nombre d'appels et coût pour les modèles dont le prix est connu.
4. Lancer, puis suivre la progression en direct. Une exécution interrompue peut **reprendre** : seules les réponses manquantes ou en erreur sont rejouées.

Le plafond de coût par exécution est `MAX_RUN_COST_USD` dans `.env` (5 $ par défaut).

## 3. Noter à l'aveugle

Onglet **Notation** :

- touches <kbd>0</kbd> à <kbd>3</kbd> : noter et passer à la réponse suivante ;
- lettres <kbd>A</kbd> <kbd>Z</kbd> <kbd>E</kbd>… : basculer les étiquettes d'erreur ;
- <kbd>←</kbd> : revenir à la réponse précédente ;
- « Révéler » : voir le modèle de la réponse qui vient d'être notée.

## 4. Résultats et export

Onglet **Résultats** : classement, graphiques par catégorie, gains avant/après, analyse des erreurs et exploration des réponses.

- ★ et ⚠ marquent les exemples marquants publiés sur le site. Ce n'est possible que pour les tests publics.
- **Exporter vers le site public** écrit `data/results/public/results.json`. Ensuite :

```bash
docker compose run --rm api python -m scripts.visuals.generate   # PNG LinkedIn + image de partage
git add data/results/public && git commit -m "résultats : …" && git push   # le site se met à jour
```

## Sauvegardes (important)

`backend/var/lab.db` contient les réponses des modèles et les notes. Elles ne sont **pas** reconstructibles, et ce fichier n'est pas dans Git. `data/test/private/` non plus.

```powershell
docker compose run --rm api python -m scripts.backup
```

Cette commande copie la base (de façon sûre, même pendant une exécution) et le jeu privé dans `backend/var/backups/<date>/`, en gardant les 10 dernières sauvegardes. Ce dossier reste sur la même machine : copier aussi régulièrement `backend/var/backups/` sur un support externe ou un stockage chiffré.

## Schéma de la base (migrations)

Le schéma est géré par Alembic et mis à jour automatiquement au démarrage de l'API. Après une modification de `app/models.py` ou `app/run_models.py` :

```powershell
docker compose run --rm api alembic revision --autogenerate -m "description"
```

Le test `test_migrations_match_models` échoue tant que la migration correspondante manque.

## Modèles locaux (Ollama)

1. Installer Ollama : <https://ollama.com>.
2. Télécharger les modèles : `ollama pull qwen3.5:4b`, `ollama pull gemma4:e4b`, `ollama pull bge-m3`.
   Espace disque : environ 4,6 Go pour Qwen3.5 4B et bge-m3 ensemble ; Gemma 4 E4B et Apertus 8B sont plus lourds (taille indiquée sur la page de chaque modèle Ollama). Prévoir au moins 10 Go libres et 8 Go de RAM disponibles.
3. Le conteneur joint Ollama via `host.docker.internal:11434`. Si besoin, modifier `OLLAMA_DOCKER_URL` dans `.env`.

## Détection de langue GlotLID (optionnelle, non testée dans ce dépôt)

1. Télécharger `model_v3.bin` depuis le dépôt Hugging Face `cis-lmu/glotlid` dans `backend/var/models/glotlid.bin`.
2. Installer la bibliothèque `fasttext` dans l'image (`uv add fasttext-numpy2` dans `backend/`, puis `docker compose build`).
3. `GET /api/health` indique alors `"language_detection": "glotlid"`.

## Tests automatisés

```bash
docker compose run --rm api pytest                       # backend + pipelines
docker compose run --rm api ruff check .
docker compose run --rm lab-ui npm test                  # interface
```
