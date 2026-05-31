# =============================================================================
# security.py — Billety API
# Autenticación HTTP Basic + Autorización por roles
# Patrón igual al usado en EventosDB con el profesor
# =============================================================================

from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import Depends, HTTPException, status
from dao import Conexion, UsuarioDAO
from models import Usuario

security = HTTPBasic()

def getUser(credenciales: HTTPBasicCredentials = Depends(security)):
    """
    Verifica las credenciales del usuario contra la BD.
    Conecta con billety_admin para leer la tabla usuarios.
    Retorna el objeto Usuario si las credenciales son válidas.
    """
    # Conexión temporal con billety_admin para verificar credenciales
    cn = Conexion("billety_admin", "Admin.Billety123")
    usuarioDAO = UsuarioDAO(cn)
    usuario = usuarioDAO.autenticar(credenciales.username, credenciales.password)
    cn.cerrar()

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas o cuenta inactiva.",
            headers={"WWW-Authenticate": "Basic"},
        )
    return usuario


class RoleChecker:
    """
    Dependencia reutilizable para verificar el rol del usuario autenticado.
    Uso: roles = RoleChecker(["admin", "usuario"])
         @app.get("/ruta", ...)
         async def endpoint(user: Usuario = Depends(roles)):
    """
    def __init__(self, roles: list):
        self.roles_permitidos = roles

    def __call__(self, user: Usuario = Depends(getUser)):
        if user is None or user.rol not in self.roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sin autorización."
            )
        return user
