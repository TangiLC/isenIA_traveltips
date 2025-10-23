import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import (
    auth_routeur,
    langue_routeur,
    currency_routeur,
    ville_routeur,
    electricity_router,
    week_meteo_routeur,
    conversation_routeur,
    country_routeur,
)


# Création de l'application FastAPI
app = FastAPI(
    title="TravelTips API",
    description="API REST pour la gestion des données info pays",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrement des routeurs
app.include_router(auth_routeur.router)
app.include_router(country_routeur.router)
app.include_router(langue_routeur.router)
app.include_router(currency_routeur.router)
app.include_router(electricity_router.router)
app.include_router(ville_routeur.router)
app.include_router(week_meteo_routeur.router)
app.include_router(conversation_routeur.router)


@app.get("/", tags=["Root"])
def read_root():
    """
    Point d'entrée de l'API
    """
    return {
        "message": "Bienvenue sur l'API TravelTips",
        "version": "1.0.0",
        "documentation": "/docs",
        "author": "Tangi LE CADRE  /ecoleIA Brest",
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Vérification de l'état de l'API
    """
    return {"status": "healthy", "service": "TravelTips API"}


def main():
    # Pilotable par variables d’environnement
    host = os.getenv("FASTAPI_HOST", "0.0.0.0")
    port = int(os.getenv("FASTAPI_PORT", "8000"))
    reload_flag = os.getenv("FASTAPI_RELOAD", "true").lower() in {"1", "true", "yes"}
    # workers n’est utile que sans reload
    workers = int(os.getenv("FASTAPI_WORKERS", "1"))
    if reload_flag and workers != 1:
        workers = 1  # sécurité: uvicorn ne supporte pas reload + workers>1

    uvicorn.run(
        "fastapi_main:app",
        host=host,
        port=port,
        reload=reload_flag,
        workers=workers if not reload_flag else 1,
        # log_level peut aussi être lu depuis l’env si besoin
    )


if __name__ == "__main__":
    main()
