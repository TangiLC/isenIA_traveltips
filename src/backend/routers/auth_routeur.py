# auth_routeur.py
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query, Path
from pydantic import BaseModel, Field
from security.security import Security
from models.auth import UserIn, UserPatch, UserOut, TokenResponse, LoginIn
from repositories.auth_repository import AuthRepository

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
        claims = {"sub": "test-user", "role": "user", "scope": "test"}
        token = Security.create_token(claims)
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
    row = AuthRepository.get_by_name(credentials.pseudo)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides"
        )

    stored_hash = row["password"]
    if not Security.verify_password(credentials.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides"
        )

    claims = {
        "sub": str(row["id"]),
        "pseudo": row["pseudo"],
        "role": row["role"],
    }
    token = Security.create_token(claims)

    user_out = UserOut(id=int(row["id"]), pseudo=row["pseudo"], role=row["role"])
    return TokenResponse(access_token=token, user=user_out)


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
    row = AuthRepository.get_by_name(pseudo)
    if not row:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return UserOut(**AuthRepository.row_to_user_out(row))


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

    existing = AuthRepository.get_by_name(data.pseudo)
    if existing:
        raise HTTPException(status_code=409, detail="Pseudo déjà utilisé")

    hashed_password = Security.hash_password(data.password)
    new_id = AuthRepository.create(data.pseudo, hashed_password, data.role.value)
    row = AuthRepository.get_by_id(new_id)
    return UserOut(**AuthRepository.row_to_user_out(row))


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
    current = AuthRepository.get_by_id(id)
    if not current:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    if data.password is not None:
        hashed_password = Security.hash_password(data.password)
    else:
        hashed_password = current["password"]

    truePartialUpdate = AuthRepository.update_partial(
        id,
        pseudo=None if data.pseudo is None else data.pseudo,
        password=None if data.password is None else hashed_password,
        role=None if data.role is None else data.role.value,
    )

    if not truePartialUpdate:
        return UserOut(**AuthRepository.row_to_user_out(current))
    row = AuthRepository.get_by_id(id)
    return UserOut(**AuthRepository.row_to_user_out(row))


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
    current = AuthRepository.get_by_id(id)
    if not current:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    AuthRepository.delete(id)
    return None
