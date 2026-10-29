# Textes de communication (brouillons)

Brouillons pour LinkedIn et le portfolio. Les `{{…}}` sont à remplacer **uniquement** par des valeurs lues dans l'onglet Résultats du labo ou sur le site public, après les vraies exécutions et notations. Ne rien publier tant qu'un `{{…}}` reste.

Visuels associés : `docker compose run --rm api python -m scripts.visuals.generate` → `data/results/public/visuals/`.

## Portfolio — description courte

**FR.** Benchmark open source qui mesure la maîtrise du kabyle (taqbaylit) par les grands modèles de langage, avec des réponses de référence écrites par une personne de langue maternelle kabyle et une notation humaine à l'aveugle. Laboratoire local (FastAPI, SQLite, React/TypeScript) pour exécuter les modèles, noter et analyser ; amélioration d'un petit modèle open source par few-shot, RAG et QLoRA, avec une séparation vérifiable entre données de test et données d'entraînement ; site de résultats bilingue publié par GitHub Actions.

**EN.** Open-source benchmark measuring how well large language models handle Kabyle (Taqbaylit), with reference answers written by a native Kabyle speaker and blind human grading. Local lab (FastAPI, SQLite, React/TypeScript) to run models, grade and analyze; a small open-source model improved with few-shot, RAG and QLoRA, with a verifiable split between test and training data; bilingual results site deployed by GitHub Actions.

**Stack :** Python, FastAPI, SQLModel, Alembic, asyncio, sacrebleu, numpy · React 19, TypeScript, Vite, Tailwind, Recharts · Astro · Docker Compose · GitHub Actions, GitHub Pages, gitleaks · Ollama, Unsloth (QLoRA).

## Post LinkedIn — FR

> Les grands modèles de langage parlent-ils kabyle ? J'ai voulu le mesurer plutôt que le supposer.
>
> J'ai construit un benchmark open source : {{NB_TESTS}} tests en six catégories (traduction dans les deux sens, compréhension, culture, écriture en latin et en tifinagh, conversation), dont toutes les réponses de référence sont écrites par moi, locutrice/locuteur natif.
>
> {{NB_MODELES}} modèles évalués, {{NB_REPONSES_NOTEES}} réponses notées à l'aveugle (je ne savais pas quel modèle avait répondu).
>
> Résultats :
> • Meilleur modèle : {{MEILLEUR_MODELE}}, {{SCORE_MEILLEUR}} % (IC 95 % : {{IC_MEILLEUR}})
> • Erreur la plus fréquente : {{ERREUR_PRINCIPALE}}
> • {{CONSTAT_MARQUANT}}
>
> Puis j'ai essayé d'améliorer un petit modèle open source ({{PETIT_MODELE}}) :
> • few-shot : {{GAIN_FEWSHOT}} points
> • RAG : {{GAIN_RAG}} points
> • fine-tuning QLoRA : {{GAIN_LORA}} points
> Gains mesurés sur les mêmes tests, jamais utilisés pour l'entraînement (contrôle de contamination automatique).
>
> Tout est ouvert : code, méthodologie, jeu de test public, résultats.
> 🔗 https://hasdaouiryma16-cmd.github.io/kabyle-llm-benchmark/
>
> #Kabyle #Taqbaylit #LLM #NLP #LanguesMinoritaires #OpenSource

*(Adapter « locutrice/locuteur natif » à votre choix avant publication.)*

## LinkedIn post — EN

> Do large language models speak Kabyle? I wanted to measure it rather than assume it.
>
> I built an open-source benchmark: {{NB_TESTS}} tests across six categories (translation both ways, comprehension, culture, writing in Latin and Tifinagh script, conversation), with every reference answer written by me as a native speaker.
>
> {{NB_MODELES}} models evaluated, {{NB_REPONSES_NOTEES}} responses graded blind (I didn't know which model had answered).
>
> Results:
> • Best model: {{MEILLEUR_MODELE}}, {{SCORE_MEILLEUR}}% (95% CI: {{IC_MEILLEUR}})
> • Most frequent error: {{ERREUR_PRINCIPALE}}
> • {{CONSTAT_MARQUANT}}
>
> Then I tried to improve a small open-source model ({{PETIT_MODELE}}):
> • few-shot: {{GAIN_FEWSHOT}} points
> • RAG: {{GAIN_RAG}} points
> • QLoRA fine-tuning: {{GAIN_LORA}} points
> Gains measured on the same tests, never used for training (automatic contamination check).
>
> Everything is open: code, methodology, public test set, results.
> 🔗 https://hasdaouiryma16-cmd.github.io/kabyle-llm-benchmark/
>
> #Kabyle #Taqbaylit #LLM #NLP #LowResourceLanguages #OpenSource

## Où trouver chaque valeur

| Champ | Source |
|---|---|
| `NB_TESTS` | site, section Méthode (« éléments du jeu de test ») ou `MANIFEST.json` |
| `NB_MODELES`, `NB_REPONSES_NOTEES` | onglet Résultats du labo (classement, colonne « notées ») |
| `MEILLEUR_MODELE`, `SCORE_MEILLEUR`, `IC_MEILLEUR` | première ligne du classement |
| `ERREUR_PRINCIPALE` | graphique « Analyse des erreurs » |
| `GAIN_*` | section « Gains » (points de %, comparaison appariée) |
| `CONSTAT_MARQUANT` | votre propre lecture des résultats |
