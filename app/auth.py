"""Autenticacion y control de acceso por rol.

La sesion se maneja con un JWT guardado en una cookie httponly. No se usa
almacenamiento de sesion en servidor para mantener el aplicativo simple
(coherente con el enfoque monolitico y sin dependencias extra).

Roles y permisos:
- administrador: consultar, crear, modificar, eliminar.
- digitador:     consultar, crear.
- consulta:      solo consultar.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario

SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esta-clave-por-una-generada-aleatoriamente")
ALGORITHM = "HS256"
SESSION_EXPIRE_MINUTES = int(os.getenv("SESSION_EXPIRE_MINUTES", "120"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ROLES_PERMITIDOS = ("administrador", "digitador", "consulta")

# Permisos por rol sobre las operaciones CRUD.
PERMISOS = {
    "administrador": {"consultar", "crear", "modificar", "eliminar"},
    "digitador": {"consultar", "crear"},
    "consulta": {"consultar"},
}


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verificar_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def crear_token_sesion(username: str, rol: str) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=SESSION_EXPIRE_MINUTES)
    payload = {"sub": username, "rol": rol, "exp": expira}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def leer_token_sesion(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def obtener_usuario_actual(request: Request, db: Session = Depends(get_db)) -> Optional[Usuario]:
    """Devuelve el usuario autenticado a partir de la cookie de sesion, o None."""
    token = request.cookies.get("session_token")
    if not token:
        return None

    payload = leer_token_sesion(token)
    if not payload:
        return None

    usuario = db.query(Usuario).filter(Usuario.username == payload.get("sub")).first()
    return usuario


def requerir_login(request: Request, db: Session = Depends(get_db)) -> Usuario:
    """Dependencia: exige una sesion valida. Lanza 401 si no la hay."""
    usuario = obtener_usuario_actual(request, db)
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Se requiere iniciar sesion.",
            headers={"Location": "/login"},
        )
    return usuario


def requerir_permiso(accion: str):
    """Genera una dependencia que exige que el usuario autenticado tenga el
    permiso indicado ("consultar", "crear", "modificar" o "eliminar")."""

    def dependencia(usuario: Usuario = Depends(requerir_login)) -> Usuario:
        permisos_rol = PERMISOS.get(usuario.rol, set())
        if accion not in permisos_rol:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"El rol '{usuario.rol}' no tiene permiso para '{accion}'.",
            )
        return usuario

    return dependencia
