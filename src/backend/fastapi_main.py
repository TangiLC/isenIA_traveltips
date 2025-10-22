from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import langue_routeur, currency_routeur, ville_routeur, electricity_router


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
app.include_router(langue_routeur.router)
app.include_router(currency_routeur.router)
app.include_router(electricity_router.router)
app.include_router(ville_routeur.router)


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


# Point d'entrée pour uvicorn
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "fastapi_main:app", host="0.0.0.0", port=8000, reload=True  # Mode développement
    )
