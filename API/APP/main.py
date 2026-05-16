# =============================================================================
# main.py — Billety API
# Capa de presentación: endpoints REST + ciclo de vida de la conexión
# =============================================================================

from fastapi import FastAPI, Request

from dao import Conexion, UsuarioDAO, CategoriaDAO
from models import (
    Salida,
    UsuarioRegistro, UsuarioLogin, UsuarioSalida, LoginSalida, UsuarioCambiarRol,
    CategoriaCrear, CategoriaEditar, CategoriasCreadaSalida, CategoriasSalida,
)

app = FastAPI(
    title="Billety API",
    description="API REST para finanzas personales — Arquitectura de Servicios",
    version="1.0.0"
)

# =============================================================================
# Conexión a MySQL
# =============================================================================

@app.on_event("startup")
def startup():
    app.cn = Conexion()

@app.on_event("shutdown")
def shutdown():
    app.cn.cerrar()

# =============================================================================
# RECURSO 1: USUARIOS
# Base URL: /usuarios
# =============================================================================

@app.post(
"/usuarios/registrar",
    tags=["Usuarios"],
    summary="Registrar nuevo usuario",
    response_model=Salida
)
async def registrar_usuario(request: Request, datos: UsuarioRegistro):
    dao = UsuarioDAO(request.app.cn)
    return dao.registrar(datos)


@app.post(
    "/usuarios/login",
    tags=["Usuarios"],
    summary="Login de usuario",
    response_model=LoginSalida | Salida
)
async def login(request: Request, datos: UsuarioLogin):
    dao = UsuarioDAO(request.app.cn)
    return dao.login(datos)


@app.get(
    "/usuarios/{id_usuario}",
    tags=["Usuarios"],
    summary="Consultar usuario por ID",
    response_model=UsuarioSalida | Salida
)
async def consultar_usuario(request: Request, id_usuario: int):
    dao = UsuarioDAO(request.app.cn)
    return dao.consultar_por_id(id_usuario)


@app.patch(
    "/usuarios/{id_usuario}/desactivar",
    tags=["Usuarios"],
    summary="Desactivar cuenta de usuario",
    response_model=Salida
)
async def desactivar_usuario(request: Request, id_usuario: int):
    dao = UsuarioDAO(request.app.cn)
    return dao.desactivar(id_usuario)


@app.patch(
    "/usuarios/{id_usuario}/activar",
    tags=["Usuarios"],
    summary="Activar cuenta de usuario",
    response_model=Salida
)
async def activar_usuario(request: Request, id_usuario: int):
    dao = UsuarioDAO(request.app.cn)
    return dao.activar(id_usuario)


@app.patch(
    "/usuarios/{id_usuario}/rol",
    tags=["Usuarios"],
    summary="Cambiar rol de usuario (admin | usuario)",
    response_model=Salida
)
async def cambiar_rol(request: Request, id_usuario: int, datos: UsuarioCambiarRol):
    dao = UsuarioDAO(request.app.cn)
    return dao.cambiar_rol(id_usuario, datos)

# RECURSO 2: CATEGORÍAS
# Base URL: /categorias
@app.post(
    "/categorias/crear",
    tags=["Categorías"],
    summary="Crear categoría",
    response_model=CategoriasCreadaSalida | Salida
)
async def crear_categoria(request: Request, datos: CategoriaCrear):
    dao = CategoriaDAO(request.app.cn)
    return dao.crear(datos)


@app.put(
    "/categorias/{id_categoria}/editar",
    tags=["Categorías"],
    summary="Editar nombre y/o descripción de categoría",
    response_model=Salida
)
async def editar_categoria(request: Request, id_categoria: int, datos: CategoriaEditar):
    dao = CategoriaDAO(request.app.cn)
    return dao.editar(id_categoria, datos)


@app.patch(
    "/categorias/{id_categoria}/desactivar",
    tags=["Categorías"],
    summary="Desactivar categoría (no elimina)",
    response_model=Salida
)
async def desactivar_categoria(request: Request, id_categoria: int):
    dao = CategoriaDAO(request.app.cn)
    return dao.desactivar(id_categoria)


@app.get(
    "/categorias/{id_usuario}",
    tags=["Categorías"],
    summary="Consultar todas las categorías de un usuario",
    response_model=CategoriasSalida
)
async def consultar_categorias_usuario(request: Request, id_usuario: int):
    dao = CategoriaDAO(request.app.cn)
    return dao.consultar_por_usuario(id_usuario)


@app.get(
    "/categorias/{id_usuario}/estado/{estado}",
    tags=["Categorías"],
    summary="Consultar categorías por estado (true=activas, false=inactivas)",
    response_model=CategoriasSalida
)
async def consultar_categorias_estado(request: Request, id_usuario: int, estado: bool):
    dao = CategoriaDAO(request.app.cn)
    return dao.consultar_por_estado(id_usuario, estado)

# INICIO DEL ENTORNO VIRTUAL
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)