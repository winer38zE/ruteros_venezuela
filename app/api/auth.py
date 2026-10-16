import os
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from jose import jwt
from pydantic import BaseModel

# La clave por defecto se mantiene para no invalidar sesiones ya emitidas.
# En producción defina JWT_SECRET_KEY en el entorno del servidor.
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "tu_super_clave_secreta_aqui_no_la_compartas")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # El token dura 1 semana para los ruteros


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    empresa_id: Optional[str] = None
    rol: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        pwd = plain_password.encode("utf-8")
        digest = (
            hashed_password.encode("utf-8")
            if isinstance(hashed_password, str)
            else hashed_password
        )
        return bcrypt.checkpw(pwd, digest)
    except (ValueError, TypeError):
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    # Aquí es donde inyectamos el empresa_id y el rol en el token
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
