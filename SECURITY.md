# Sécurité

## Signaler une faille

Merci de ne pas ouvrir d'issue publique. Utilisez le signalement privé de GitHub :
onglet **Security** → **Report a vulnerability**. Une réponse est donnée dans les meilleurs délais.

## Périmètre

- **Labo** (`backend/`, `lab-ui/`) : outil uniquement local, qui écoute sur 127.0.0.1 et n'est
  jamais déployé. Il refuse les noms d'hôte inattendus et les requêtes modifiantes venant
  d'une autre origine que son interface.
- **Site public** (`site/`) : site statique sur GitHub Pages, sans serveur ni formulaire.
- **Clés d'API** : uniquement dans `.env`, ignoré par Git ; jamais renvoyées par l'API.
- **Partie privée du jeu de test** : jamais versionnée (`data/test/private/`).

## Contrôles automatiques

| Contrôle | Où |
|---|---|
| Recherche de secrets dans tout l'historique (gitleaks) | CI et hook pre-commit |
| Aucun `.env` ni test privé suivi par Git | CI |
| Failles connues des dépendances (npm audit, pip-audit) | CI, à chaque push |
| Analyse statique du code (CodeQL) | à chaque push et chaque semaine |
| Mises à jour de sécurité des dépendances | Dependabot |
