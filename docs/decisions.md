# Journal des décisions techniques

Chaque décision importante est notée ici avec sa justification, pour pouvoir la défendre et la réviser.

| # | Date | Décision | Justification |
|---|---|---|---|
| 1 | 2026-10-28 | SQLite (SQLModel + Alembic) plutôt que PostgreSQL | Une seule utilisatrice, faible volume ; un seul fichier, aucun service à gérer. Migration possible plus tard. |
| 2 | 2026-10-28 | Jeu de test en JSONL dans Git, normalisé Unicode NFC | Versionné, lisible en diff, citable ; NFC évite que deux graphies identiques de « ḥ », « ɛ »… soient comparées comme différentes. |
| 3 | 2026-10-28 | Code sous Apache-2.0 | Permissive, avec clause explicite sur les brevets ; bien acceptée en entreprise. |
| 4 | 2026-10-28 | Données sous CC BY 4.0 | Réutilisation maximale (recherche et industrie) avec attribution obligatoire. |
| 5 | 2026-10-28 | ~20 % du jeu de test gardés privés (`data/test/private/`, ignoré par Git) | Le jeu public finira sur le web et potentiellement dans l'entraînement de futurs modèles ; la partie privée reste une mesure propre dans le temps. |
| 6 | 2026-10-28 | chrF++ comme métrique automatique principale, BLEU en secondaire, pas de COMET | chrF++ (n-grammes de caractères) est robuste à la morphologie riche et à l'orthographe variable ; COMET s'appuie sur XLM-R qui couvre mal le kabyle. |
| 7 | 2026-10-28 | Détection de langue avec GlotLID + détection d'écriture par plages Unicode | GlotLID couvre le kabyle ; l'écriture (latin / tifinagh / arabe) se détecte de façon déterministe. |
| 8 | 2026-10-28 | Labo uniquement local (écoute sur 127.0.0.1), site public statique séparé | Les clés API ne quittent jamais la machine ; le site ne contient que des résultats exportés via une liste blanche de champs. |
| 9 | 2026-10-28 | Protection des secrets : .gitignore + hook pre-commit (gitleaks, blocage des .env) + gitleaks en CI sur tout l'historique | Défense en profondeur : une erreur à un niveau est rattrapée au suivant. |
| 10 | 2026-10-28 | Tout le labo tourne dans Docker | Smart App Control (Windows) bloque des binaires non signés (bash, libcurl de Git) ; Docker isole l'environnement et rend le labo reproductible sur n'importe quelle machine. |
| 11 | 2026-10-28 | Le JSONL du dépôt est la source de vérité, la base SQLite en est une copie reconstructible | Les tests restent lisibles, versionnés et auditables ; la base peut être supprimée et rechargée à tout moment. Alembic (migrations) sera introduit quand la base contiendra des données non reconstructibles (réponses, notations). |
| 12 | 2026-10-28 | Empreinte SHA-256 du benchmark limitée aux champs évalués | Deux scores ne sont comparables que sur un jeu identique ; une note ou une date modifiée ne doit pas casser la comparabilité. |
| 13 | 2026-10-28 | Import « tout ou rien » avec rapport ligne par ligne | Évite un jeu de tests à moitié importé, difficile à diagnostiquer. |
| 14 | 2026-10-28 | Statuts `draft` / `ready` | Permet de saisir progressivement ; seul un test complet et validé entre dans le benchmark. |
| 15 | 2026-10-28 | SDK officiel Anthropic ; API HTTP directes (httpx) pour OpenAI, Mistral, OpenRouter, Ollama | OpenAI, Mistral et OpenRouter partagent l'API « chat/completions » : une seule classe suffit. Les nouvelles tentatives sont gérées par le runner, pas par les SDK, pour une politique identique pour tous. |
| 16 | 2026-10-28 | Pas de repli automatique vers un autre modèle en cas de refus | Dans un benchmark, une réponse doit toujours provenir du modèle évalué ; un refus est une information. |
| 17 | 2026-10-28 | Température 0 quand l'API l'accepte, paramètres réels enregistrés | Les modèles Claude actuels refusent `temperature` : plutôt que masquer cet écart, il est documenté et tracé réponse par réponse. |
| 18 | 2026-10-28 | Runner asynchrone dans le processus de l'API (asyncio), lignes « pending » créées à l'avance | Pas de file de messages externe pour un outil local ; l'idempotence vient de la base (une ligne par test × modèle). |
| 19 | 2026-10-28 | Recherche vectorielle RAG avec numpy plutôt qu'une base vectorielle (LanceDB envisagé) | < 100 000 entrées : un produit matriciel suffit, sans serveur ni dépendance lourde, et reste transparent. |
| 20 | 2026-10-28 | Embeddings via Ollama (bge-m3) | Évite d'embarquer PyTorch dans l'image du labo ; même service que pour les modèles locaux. |
| 21 | 2026-10-28 | Petit modèle par défaut : Qwen3.5 4B (candidats : Gemma 4 E4B, Apertus 8B) | Apache 2.0, rapide sur T4 gratuit, bien supporté par Unsloth ; les trois bases sont mesurées avant de choisir définitivement. |
| 22 | 2026-10-28 | Données préparées non versionnées (seul STATS.json l'est), pipeline reproductible avec empreintes | Volumes importants et licences tierces ; la CI rejoue le pipeline et le contrôle de contamination. |
| 23 | 2026-10-28 | Site Astro statique, îlots React (Recharts) | HTML rapide et indexable, balises Open Graph soignées, interactivité seulement où elle sert (graphiques). |
| 24 | 2026-10-28 | Palette de graphiques validée (daltonisme), couleur liée au modèle et non au rang | Lisibilité pour tous ; un filtre ne repeint pas les séries restantes. |
| 25 | 2026-10-28 | Alembic reporté : schéma créé par `create_all` | Pas encore de données réelles ; Alembic à introduire avant toute modification de schéma une fois des notations saisies. |
| 26 | 2026-10-29 | Alembic introduit (révision 0001), appliqué au démarrage ; remplace la décision 25 | Introduit avant la saisie des premiers tests réels ; une base antérieure est marquée à 0001 puis mise à jour. Un test vérifie que migrations et modèles concordent. |
| 27 | 2026-10-29 | Accord note humaine / chrF++ mesuré par Spearman | La note humaine est ordinale (0–3) ; une corrélation de rang ne suppose pas d'écart régulier entre les notes. |
| 28 | 2026-10-29 | Sauvegarde locale par l'API de sauvegarde SQLite, rotation de 10 copies | Copie cohérente même pendant une exécution ; la copie hors machine reste à faire par l'utilisatrice ou l'utilisateur. |
| 29 | 2026-10-29 | Empreinte du jeu de test enregistrée par `prepare` et `build_rag_index` | Rend vérifiable que les données d'amélioration ont été filtrées contre la version actuelle du jeu de test ; la page Préparation signale tout décalage. |
| 30 | 2026-10-29 | Modèles OpenAI : GPT-6 Astra, GPT-6.1 Sol, GPT-6 Luna (au lieu de GPT-5) | Identifiants et prix vérifiés sur la documentation officielle le 29/10/2026 ; GPT-5 n'est plus le modèle de référence d'OpenAI. |
