# Ajouter un modèle

## Un modèle d'un fournisseur existant

Ajouter une entrée dans [`backend/config/models.yaml`](../backend/config/models.yaml) :

```yaml
  - key: mistral-medium          # identifiant unique dans le labo
    label: Mistral Medium        # nom affiché
    provider: mistral            # anthropic | openai | mistral | openrouter | ollama
    model: mistral-medium-latest # identifiant exact chez le fournisseur
    params: { max_tokens: 2048, temperature: 0 }  # transmis tel quel à l'API
    pricing: null                # ou { input: 0.4, output: 2.0 } en $ par million de tokens
```

- `params` est envoyé tel quel et enregistré avec chaque réponse. Utiliser les noms de paramètres de l'API concernée (par exemple `max_completion_tokens` pour certains modèles OpenAI). Pour Anthropic, `effort` est converti en `output_config.effort`. Pour Ollama, `think` passe au premier niveau de la requête.
- **Ne jamais inventer un prix** : laisser `null` si on ne le connaît pas. Le coût ne sera alors simplement pas estimé.
- Le fichier est relu au redémarrage de l'API : `docker compose restart api`.
- **N'importe quel modèle d'OpenRouter** s'ajoute avec `provider: openrouter` et son identifiant du catalogue (par exemple `meta-llama/llama-3.3-70b-instruct`).

## Une variante d'un modèle (phase 2)

```yaml
  - key: gemma4-e4b-fewshot
    label: Gemma 4 E4B + few-shot
    provider: ollama
    model: gemma4:e4b
    base: gemma4-e4b          # modèle de base, pour calculer le gain
    variant: fewshot          # fewshot | rag | finetuned
    variant_params: { k: 5, selection: similar }
    params: { temperature: 0, num_predict: 1024 }
```

## Un nouveau fournisseur

1. Dans [`backend/app/providers.py`](../backend/app/providers.py), écrire une classe avec deux méthodes :
   - `available() -> bool` : la clé est-elle présente, le service répond-il ?
   - `async chat(model, system, messages) -> ChatResult` : renvoie le texte, la raison d'arrêt et les tokens. Lever `ProviderError(message, retryable)` en cas d'erreur, avec `retryable=True` pour les erreurs 429, 5xx et réseau. Le runner applique alors la même politique de nouvelles tentatives à tous les fournisseurs.
2. Ajouter le nom dans `ProviderName` ([`registry.py`](../backend/app/registry.py)) et l'instancier dans `build_providers`.
3. Ajouter la clé éventuelle dans `config.py` et dans `.env.example`, **sans valeur**.
4. Si l'API est compatible OpenAI (`/chat/completions`), réutiliser `OpenAICompatibleProvider` avec la bonne URL de base.
5. Écrire un test avec le fournisseur `mock` (voir `backend/tests/test_runs.py`).
