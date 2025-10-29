# auth_routeur.py
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query, Path
from services.auth_service import AuthService
from security.security import Security
from models.auth import UserIn, UserPatch, UserOut, TokenResponse, LoginIn

# from repositories.auth_repository import AuthOrm

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.get(
    "/test_token",
    response_model=TokenResponse,
    summary="Générer un token JWT de test",
    description="Génère un token JWT basique sans authentification -Mode dev MVP !!!-",
    responses={
        200: {"description": "Token généré", "model": TokenResponse},
        403: {"description": "Accès refusé"},
        500: {"description": "Erreur interne du serveur"},
    },
)
def get_test_token():
    try:
        token = AuthService.generate_test_token()
        return TokenResponse(access_token=token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur génération token: {str(e)}",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Obtenir un token JWT (login)",
    description="Processus d'authentification avec pseudo et password",
    responses={
        200: {"description": "Token généré", "model": TokenResponse},
        403: {"description": "Accès refusé"},
        404: {"description": "Utilisateur introuvable"},
        500: {"description": "Erreur interne du serveur"},
    },
)
def login(credentials: LoginIn):
    try:
        token, user_data = AuthService.login(credentials.pseudo, credentials.password)
        user_out = UserOut(**user_data)
        return TokenResponse(access_token=token, user=user_out)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.get(
    "/user/by_name",
    response_model=UserOut,
    summary="Récupérer un utilisateur par son pseudo",
    description="Récupération des données utilisateur avec le pseudo",
    responses={
        200: {"description": "Utilisateur trouvé"},
        403: {"description": "Accès refusé"},
        404: {"description": "Utilisateur introuvable"},
        500: {"description": "Erreur interne du serveur"},
    },
)
def get_user_by_name(
    pseudo: str = Query(..., min_length=1, max_length=255),
    _=Depends(Security.secured_route),
):
    try:
        user_data = AuthService.get_by_name(pseudo)
        return UserOut(**user_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put(
    "/user",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un utilisateur",
    description="Crée un utilisateur avec pseudo/password/role",
    responses={
        200: {"description": "Utilisateur créé"},
        403: {"description": "Accès refusé"},
        404: {"description": "Utilisateur introuvable"},
        500: {"description": "Erreur interne du serveur"},
    },
)
def create_user(
    data: UserIn,
    _=Depends(Security.secured_route),
):

    try:
        user_data = AuthService.create(data.pseudo, data.password, data.role.value)
        return UserOut(**user_data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.patch(
    "/user/{id}",
    response_model=UserOut,
    summary="Mettre à jour partiellement un utilisateur",
    description="Mise à jour partiel d'un utilisateur (pseudo, password, role)",
    responses={
        200: {"description": "Utilisateur mis à jour"},
        403: {"description": "Accès refusé"},
        404: {"description": "Utilisateur introuvable"},
        500: {"description": "Erreur interne du serveur"},
    },
)
def patch_user(
    id: int = Path(..., ge=1),
    data: UserPatch = ...,
    _=Depends(Security.secured_route),
):
    try:
        user_data = AuthService.update_partial(
            id,
            pseudo=data.pseudo,
            password=data.password,
            role=None if data.role is None else data.role.value,
        )
        return UserOut(**user_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/user/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un utilisateur",
    description="Suppression définitive d'utilisateur avec id",
    responses={
        200: {"description": "Suppression validée"},
        403: {"description": "Accès refusé"},
        404: {"description": "Utilisateur introuvable"},
        500: {"description": "Erreur interne du serveur"},
    },
)
def delete_user(
    id: int = Path(..., ge=1),
    _=Depends(Security.secured_route),
):
    try:
        AuthService.delete(id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
