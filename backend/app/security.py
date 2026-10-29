"""Protection de l'API locale contre les requêtes venues d'autres sites.

L'API n'écoute que sur 127.0.0.1, mais le navigateur peut y accéder depuis n'importe quelle
page ouverte. CORS empêche de lire les réponses, pas d'envoyer une requête « simple »
(formulaire POST) : une page malveillante pourrait lancer une exécution payante ou importer
des tests. On refuse donc :
- tout nom d'hôte inattendu (attaque par « DNS rebinding ») ;
- toute requête modifiante dont l'origine n'est pas l'interface du labo.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def add_local_only_protection(
    app: FastAPI, allowed_hosts: list[str], allowed_origins: list[str]
) -> None:
    origins = set(allowed_origins)

    @app.middleware("http")
    async def same_origin_writes(request: Request, call_next):
        if request.method not in SAFE_METHODS:
            origin = request.headers.get("origin")
            cross_site = request.headers.get("sec-fetch-site") == "cross-site"
            if (origin is not None and origin not in origins) or (origin is None and cross_site):
                return JSONResponse(
                    {"detail": "requête refusée : origine non autorisée"}, status_code=403
                )
        return await call_next(request)

    # Ajouté en dernier : s'exécute en premier
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)
