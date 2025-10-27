from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas.country_dto import CountryCreate, CountryUpdate, CountryResponse
from services.country_service import CountryService

# from repositories.country_repository import CountryRepository
# from connexion.mysql_connect import MySQLConnection
from security.security import Security

router = APIRouter(prefix="/api/countries", tags=["Countries"])


@router.get(
    "/by_id/{alpha2}",
    response_model=CountryResponse,
    summary="Récupère un pays par son code ISO alpha-2",
    description="Récupère toutes les informations d'un pays (données de base + relations) selon son code ISO 3166-1 alpha-2",
    responses={
        200: {"description": "Pays récupéré avec succès"},
        404: {"description": "Aucun pays trouvé"},
        422: {"description": "Format des données incompatible"},
        500: {"description": "Erreur serveur"},
    },
)
def get_country_by_id(alpha2: str):
    """
    Récupère un pays par son code ISO alpha-2 (ex: 'fr', 'us', 'jp')
    Retourne toutes les informations enrichies : langues complètes, monnaies, électricité, frontières, villes principales
    """
    try:
        return CountryService.get_by_alpha2(alpha2)
    except ValueError as e:
        # Déterminer status code selon le message
        if "2 caractères" in str(e):
            status_code = 400
        else:
            status_code = 404
        raise HTTPException(status_code=status_code, detail=str(e))


@router.get(
    "/by_name/{name}",
    response_model=List[CountryResponse],
    summary="Recherche des pays par nom",
    description="Recherche dans name_en, name_fr et name_local (insensible à la casse et aux accents)",
    responses={
        200: {"description": "Liste de pays récupérée avec succès"},
        404: {"description": "Aucun pays trouvé avec ce nom"},
        422: {
            "description": "Format des données incompatible -Nom trop court (<4 caractères)"
        },
        500: {"description": "Erreur serveur"},
    },
)
def get_countries_by_name(name: str):
    """
    Recherche des pays par nom (tolérant aux accents et à la casse)
    Exemples: 'france', 'côte ivoire', 'japan', 'allemagne'
    """
    try:
        return CountryService.get_by_name(name)
    except ValueError as e:
        # Déterminer status code selon le message
        if "4 caractères" in str(e):
            status_code = 422
        else:
            status_code = 404
        raise HTTPException(status_code=status_code, detail=str(e))


@router.get(
    "/",
    response_model=List[CountryResponse],
    summary="Lister tous les pays",
    description="Lister tous les pays de la base avec pagination (sans relations pour performance)",
    responses={
        200: {"description": "Liste récupérée avec succès"},
        422: {"description": "Format des données incompatible"},
        500: {"description": "Erreur serveur"},
    },
)
def get_countries(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)):
    """
    Liste tous les pays avec pagination
    Note: Pour avoir les relations complètes, utiliser /by_id/{alpha2}
    """
    return CountryService.get_all(skip, limit)


@router.post(
    "/",
    response_model=CountryResponse,
    summary="Ajouter un pays",
    description="Ajouter un nouveau pays avec toutes ses relations (langues, monnaies, frontières, électricité)",
    responses={
        201: {"description": "Pays ajouté avec succès"},
        400: {"description": "Un pays existe déjà avec ce code ISO"},
        403: {"description": "Accès interdit (route sécurisée par JWT)"},
        422: {"description": "Format des données incompatible"},
        500: {"description": "Erreur serveur"},
    },
)
def create_country(country: CountryCreate, _=Depends(Security.secured_route)):
    """
    Crée un nouveau pays avec ses relations
    Nécessite une authentification JWT (admin)
    """
    try:
        return CountryService.create(country.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@router.put(
    "/{alpha2}",
    response_model=CountryResponse,
    summary="Modifier un pays",
    description="Modifier les données d'un pays existant (données de base et/ou relations)",
    responses={
        200: {"description": "Pays modifié avec succès"},
        403: {"description": "Accès interdit (route sécurisée par JWT)"},
        404: {"description": "Pays non trouvé"},
        422: {"description": "Format des données incompatible"},
        500: {"description": "Erreur serveur"},
    },
)
def update_country(
    alpha2: str, country: CountryUpdate, _=Depends(Security.secured_route)
):
    """
    Met à jour un pays existant
    Les relations sont remplacées si fournies (pas de merge)
    Nécessite une authentification JWT (admin)
    """
    try:
        return CountryService.update(alpha2, country.model_dump(exclude_unset=True))
    except ValueError as e:
        # Déterminer status code selon le message
        if "2 caractères" in str(e):
            status_code = 400
        else:
            status_code = 404
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@router.delete(
    "/{alpha2}",
    response_model=dict,
    summary="Supprimer un pays",
    description="Supprime un pays et toutes ses relations (cascade)",
    responses={
        200: {"description": "Pays supprimé avec succès"},
        403: {"description": "Accès interdit (route sécurisée par JWT)"},
        404: {"description": "Pays non trouvé"},
        500: {"description": "Erreur serveur"},
    },
)
def delete_country(alpha2: str, _=Depends(Security.secured_route)):
    """
    Supprime un pays et toutes ses relations
    Nécessite une authentification JWT (admin)
    """
    try:
        existing = CountryService.delete(alpha2)

        return {
            "message": f"Pays '{alpha2}' supprimé avec succès",
            "deleted_country": existing["name_en"],
        }
    except ValueError as e:
        # Déterminer status code selon le message
        if "2 caractères" in str(e):
            status_code = 400
        elif "non trouvé" in str(e):
            status_code = 404
        else:
            status_code = 500
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")
