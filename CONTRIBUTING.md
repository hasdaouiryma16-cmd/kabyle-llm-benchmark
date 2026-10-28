# Contribuer

Merci de votre intérêt ! Quelques règles non négociables :

1. **Aucun texte kabyle généré par IA** dans `data/test/`. Les références sont écrites par des locuteurs natifs.
2. **Aucun score inventé ou retouché.** Les résultats sont exportés par le labo, pas écrits à la main.
3. **Séparation test / entraînement.** Ne copiez jamais une phrase de `data/test/` vers `data/train/`,
   un prompt few-shot ou un index RAG. La CI le vérifie.
4. **Aucun secret.** Les clés API vont dans `.env` (ignoré par Git). Installez les hooks :
   `pip install pre-commit && pre-commit install`.

Pour ajouter un modèle, voir `docs/add-a-model.md` (disponible à l'étape 3).
