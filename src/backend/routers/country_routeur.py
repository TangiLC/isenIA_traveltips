from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from schemas.country_dto import CountryCreate, CountryUpdate, CountryResponse
from repositories.country_repository import CountryRepository
from security.security import Security
from connexion.mysql_connect import MySQLConnection


router = APIRouter(prefix="/api/pays", tags=["Countries"])


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
    """Récupère un pays par son code ISO alpha-2 (ex: 'fr', 'us', 'jp')"""
    alpha2 = alpha2.lower().strip()

    if len(alpha2) != 2:
        raise HTTPException(
            status_code=400,
            detail="Le code pays doit contenir exactement 2 caractères (ISO 3166-1 alpha-2)",
        )

    country = CountryRepository.get_by_alpha2(alpha2)
    if country is None:
        raise HTTPException(status_code=404, detail=f"Pays '{alpha2}' non trouvé")

    return country


@router.get(
    "/by_name/{name}",
    response_model=List[CountryResponse],
    summary="Recherche des pays par nom",
    description="Recherche dans name_en, name_fr et name_local (insensible à la casse et aux accents)",
    responses={
        200: {"description": "Liste de pays récupérée avec succès"},
        404: {"description": "Aucun pays trouvé avec ce nom"},
        422: {"description": "Format des données incompatible"},
        500: {"description": "Erreur serveur"},
    },
)
def get_countries_by_name(name: str):
    """
    Recherche des pays par nom (tolérant aux accents et à la casse)
    Exemples: 'france', 'côte ivoire', 'japan', 'allemagne'
    """
    if not name or len(name.strip()) < 2:
        raise HTTPException(
            status_code=400, detail="Le nom doit contenir au moins 2 caractères"
        )

    countries = CountryRepository.get_by_name(name)

    if not countries:
        raise HTTPException(
            status_code=404, detail=f"Aucun pays trouvé avec le nom '{name}'"
        )

    return countries


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
    countries = CountryRepository.get_all(skip, limit)
    return countries


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
    # Normaliser le code ISO
    iso2 = country.iso3166a2.lower().strip()
    iso3 = country.iso3166a3.upper().strip()

    # Vérifier si le pays existe déjà
    existing = CountryRepository.get_by_alpha2(iso2)
    if existing:
        raise HTTPException(
            status_code=400, detail=f"Un pays avec le code '{iso2}' existe déjà"
        )

    # Insérer le pays
    CountryRepository.upsert_pays(
        iso2=iso2,
        iso3=iso3,
        name_en=country.name_en,
        name_fr=country.name_fr,
        name_local=country.name_local,
        lat=country.lat,
        lng=country.lng,
    )

    # Insérer les relations
    if country.langues:
        CountryRepository.insert_langues(iso2, country.langues)

    if country.currencies:
        CountryRepository.insert_monnaies(iso2, country.currencies)

    if country.borders:
        CountryRepository.insert_borders(iso2, country.borders)

    if country.electricity_types:
        CountryRepository.insert_electricite(
            iso2,
            country.electricity_types,
            country.voltage or "",
            country.frequency or "",
        )

    # Récupérer et retourner le pays créé
    created = CountryRepository.get_by_alpha2(iso2)
    return created


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
    iso2 = alpha2.lower().strip()

    if len(iso2) != 2:
        raise HTTPException(
            status_code=400, detail="Le code pays doit contenir exactement 2 caractères"
        )

    # Vérifier que le pays existe
    existing = CountryRepository.get_by_alpha2(iso2)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Pays '{iso2}' non trouvé")

    # Extraire les champs à mettre à jour (exclude_unset pour ne garder que les champs fournis)
    update_data = country.model_dump(exclude_unset=True)

    # Mettre à jour les données de base
    base_fields = {
        k: v
        for k, v in update_data.items()
        if k in ["iso3166a3", "name_en", "name_fr", "name_local", "lat", "lng"]
    }

    if base_fields:
        CountryRepository.update_pays(iso2, base_fields)

    # Mettre à jour les relations (suppression puis réinsertion)
    if "langues" in update_data:
        MySQLConnection.execute_update(
            "DELETE FROM Pays_Langues WHERE country_iso3166a2 = %s", (iso2,)
        )
        if update_data["langues"]:
            CountryRepository.insert_langues(iso2, update_data["langues"])

    if "currencies" in update_data:
        MySQLConnection.execute_update(
            "DELETE FROM Pays_Monnaies WHERE country_iso3166a2 = %s", (iso2,)
        )
        if update_data["currencies"]:
            CountryRepository.insert_monnaies(iso2, update_data["currencies"])

    if "borders" in update_data:
        MySQLConnection.execute_update(
            "DELETE FROM Pays_Borders WHERE country_iso3166a2 = %s OR border_iso3166a2 = %s",
            (iso2, iso2),
        )
        if update_data["borders"]:
            CountryRepository.insert_borders(iso2, update_data["borders"])

    if "electricity_types" in update_data:
        MySQLConnection.execute_update(
            "DELETE FROM Pays_Electricite WHERE country_iso3166a2 = %s", (iso2,)
        )
        if update_data["electricity_types"]:
            voltage = update_data.get("voltage", "")
            frequency = update_data.get("frequency", "")
            CountryRepository.insert_electricite(
                iso2, update_data["electricity_types"], voltage, frequency
            )

    # Récupérer et retourner le pays mis à jour
    updated = CountryRepository.get_by_alpha2(iso2)
    return updated


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
    iso2 = alpha2.lower().strip()

    if len(iso2) != 2:
        raise HTTPException(
            status_code=400, detail="Le code pays doit contenir exactement 2 caractères"
        )

    # Vérifier que le pays existe
    existing = CountryRepository.get_by_alpha2(iso2)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Pays '{iso2}' non trouvé")

    # Supprimer le pays (cascade sur les relations via ON DELETE CASCADE)
    success = CountryRepository.delete_pays(iso2)

    if not success:
        raise HTTPException(
            status_code=500, detail="Erreur lors de la suppression du pays"
        )

    return {
        "message": f"Pays '{iso2}' supprimé avec succès",
        "deleted_country": existing["name_en"],
    }
