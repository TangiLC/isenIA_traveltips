from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import jwt
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()


class Security:
    """Gestion centralisée des tokens JWT et dépendances FastAPI"""

    SECRET = os.getenv("JWT_SECRET", "dev-secret-key-change-in-prod")
    ALGORITHM = os.getenv("JWT_ALG", "HS256")
    EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MIN", "300"))

    security_scheme = HTTPBearer()

    @classmethod
    def create_token(
        cls, claims: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """Génère un token JWT signé"""
        now = datetime.now(timezone.utc)
        exp = now + (expires_delta or timedelta(minutes=cls.EXPIRE_MINUTES))
        payload = {**claims, "iat": int(now.timestamp()), "exp": int(exp.timestamp())}
        return jwt.encode(payload, cls.SECRET, algorithm=cls.ALGORITHM)

    @classmethod
    def verify_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """Vérifie et décode un token JWT"""
        try:
            return jwt.decode(token, cls.SECRET, algorithms=[cls.ALGORITHM])
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None

    @classmethod
    def secured_route(
        cls, credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
    ) -> Dict[str, Any]:
        """Dépendance FastAPI à injecter dans les routes"""
        token = credentials.credentials
        payload = cls.verify_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide ou expiré",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash + salt du mot de passe en utilisant bcrypt"""
        salt = bcrypt.gensalt(rounds=8)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Vérifie un mot de passe brut contre son hash"""
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
