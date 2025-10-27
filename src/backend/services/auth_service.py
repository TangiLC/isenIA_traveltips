from typing import Dict, Any, Optional
from security.security import Security
from repositories.auth_repository import AuthRepository


class AuthService:
    """Service pour la gestion de l'authentification et des utilisateurs"""

    @staticmethod
    def generate_test_token() -> str:
        """Génère un token JWT de test

        Returns:
            Token JWT
        """
        claims = {"sub": "test-user", "role": "user", "scope": "test"}
        return Security.create_token(claims)

    @staticmethod
    def login(pseudo: str, password: str) -> tuple[str, Dict[str, Any]]:
        """Authentifie un utilisateur et génère un token

        Args:
            pseudo: Pseudo de l'utilisateur
            password: Mot de passe en clair

        Returns:
            Tuple (token, user_data)

        Raises:
            ValueError: Si identifiants invalides
        """
        row = AuthRepository.get_by_name(pseudo)
        if not row:
            raise ValueError("Identifiants invalides")

        stored_hash = row["password"]
        if not Security.verify_password(password, stored_hash):
            raise ValueError("Identifiants invalides")

        claims = {
            "sub": str(row["id"]),
            "pseudo": row["pseudo"],
            "role": row["role"],
        }
        token = Security.create_token(claims)

        user_out = AuthRepository.row_to_user_out(row)
        return token, user_out

    @staticmethod
    def get_by_name(pseudo: str) -> Dict[str, Any]:
        """Récupère un utilisateur par pseudo

        Args:
            pseudo: Pseudo de l'utilisateur

        Returns:
            Données de l'utilisateur

        Raises:
            ValueError: Si utilisateur non trouvé
        """
        row = AuthRepository.get_by_name(pseudo)
        if not row:
            raise ValueError("Utilisateur introuvable")
        return AuthRepository.row_to_user_out(row)

    @staticmethod
    def create(pseudo: str, password: str, role: str) -> Dict[str, Any]:
        """Crée un nouvel utilisateur

        Args:
            pseudo: Pseudo de l'utilisateur
            password: Mot de passe en clair
            role: Rôle de l'utilisateur

        Returns:
            Données de l'utilisateur créé

        Raises:
            ValueError: Si pseudo déjà utilisé
        """
        existing = AuthRepository.get_by_name(pseudo)
        if existing:
            raise ValueError("Pseudo déjà utilisé")

        hashed_password = Security.hash_password(password)
        new_id = AuthRepository.create(pseudo, hashed_password, role)
        row = AuthRepository.get_by_id(new_id)
        return AuthRepository.row_to_user_out(row)

    @staticmethod
    def update_partial(
        user_id: int,
        pseudo: Optional[str] = None,
        password: Optional[str] = None,
        role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Mise à jour partielle d'un utilisateur

        Args:
            user_id: ID de l'utilisateur
            pseudo: Nouveau pseudo (optionnel)
            password: Nouveau mot de passe en clair (optionnel)
            role: Nouveau rôle (optionnel)

        Returns:
            Données de l'utilisateur mis à jour

        Raises:
            ValueError: Si utilisateur non trouvé
        """
        current = AuthRepository.get_by_id(user_id)
        if not current:
            raise ValueError("Utilisateur introuvable")

        # Hash du password si fourni
        hashed_password = None
        if password is not None:
            hashed_password = Security.hash_password(password)

        # Mise à jour
        updated = AuthRepository.update_partial(
            user_id,
            pseudo=pseudo,
            password=hashed_password,
            role=role,
        )

        # Si aucune modification, retourner l'état actuel
        if not updated:
            return AuthRepository.row_to_user_out(current)

        # Récupérer et retourner l'utilisateur mis à jour
        row = AuthRepository.get_by_id(user_id)
        return AuthRepository.row_to_user_out(row)

    @staticmethod
    def delete(user_id: int) -> None:
        """Supprime un utilisateur

        Args:
            user_id: ID de l'utilisateur

        Raises:
            ValueError: Si utilisateur non trouvé
        """
        current = AuthRepository.get_by_id(user_id)
        if not current:
            raise ValueError("Utilisateur introuvable")

        AuthRepository.delete(user_id)
