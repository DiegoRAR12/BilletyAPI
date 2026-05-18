from fastapi import FastAPI, Request
from typing import Optional
import uvicorn

from dao import Conexion, UsuarioDAO, CategoriaDAO, PlaneacionDAO, MovimientoDAO
from models import (
    Salida,
    UsuarioRegistro, UsuarioLogin, UsuarioSalida, LoginSalida, UsuarioCambiarRol,
    CategoriaCrear, CategoriaEditar, CategoriasCreadaSalida, CategoriasSalida,
    MovimientoRegistrar, MovimientoEditar, MovimientoCancelar,
    MovimientoRegistradoSalida, MovimientoDetalleSalida, MovimientosSalida,
    PlaneacionCrear, PlaneacionEditar,
    PlaneacionCreadaSalida, PlaneacionDetalleSalida, PlaneacionesSalida,
)

app = FastAPI()

# Conexión a MySQL
@app.on_event("startup")
def startup():
    app.cn = Conexion()

@app.on_event("shutdown")
def shutdown():
    app.cn.cerrar()

# RECURSO 1: USUARIOS - Base URL: /usuarios

@app.post(
"/usuarios/registrar",tags=["Usuarios"],summary="Registrar nuevo usuario",response_model=Salida)
async def registrar_usuario(request: Request, datos: UsuarioRegistro):
    dao = UsuarioDAO(request.app.cn)
    return dao.registrar(datos)


@app.post("/usuarios/login",tags=["Usuarios"],summary="Login de usuario",response_model=LoginSalida | Salida)
async def login(request: Request, datos: UsuarioLogin):
    dao = UsuarioDAO(request.app.cn)
    return dao.login(datos)


@app.get("/usuarios/{id_usuario}",tags=["Usuarios"],summary="Consultar usuario por ID",response_model=UsuarioSalida | Salida)
async def consultar_usuario(request: Request, id_usuario: int):
    dao = UsuarioDAO(request.app.cn)
    return dao.consultar_por_id(id_usuario)


@app.patch("/usuarios/{id_usuario}/desactivar",tags=["Usuarios"],summary="Desactivar cuenta de usuario",response_model=Salida)
async def desactivar_usuario(request: Request, id_usuario: int):
    dao = UsuarioDAO(request.app.cn)
    return dao.desactivar(id_usuario)


@app.patch("/usuarios/{id_usuario}/activar",tags=["Usuarios"],summary="Activar cuenta de usuario",response_model=Salida)
async def activar_usuario(request: Request, id_usuario: int):
    dao = UsuarioDAO(request.app.cn)
    return dao.activar(id_usuario)


@app.patch("/usuarios/{id_usuario}/rol",tags=["Usuarios"],summary="Cambiar rol de usuario (admin | usuario)",response_model=Salida)
async def cambiar_rol(request: Request, id_usuario: int, datos: UsuarioCambiarRol):
    dao = UsuarioDAO(request.app.cn)
    return dao.cambiar_rol(id_usuario, datos)

# RECURSO 2: CATEGORÍAS - Base URL: /categorias
@app.post("/categorias/crear",tags=["Categorías"],summary="Crear categoría",response_model=CategoriasCreadaSalida | Salida)
async def crear_categoria(request: Request, datos: CategoriaCrear):
    dao = CategoriaDAO(request.app.cn)
    return dao.crear(datos)

@app.put("/categorias/{id_categoria}/editar",tags=["Categorías"],summary="Editar nombre y/o descripción de categoría",response_model=Salida)
async def editar_categoria(request: Request, id_categoria: int, datos: CategoriaEditar):
    dao = CategoriaDAO(request.app.cn)
    return dao.editar(id_categoria, datos)


@app.patch("/categorias/{id_categoria}/desactivar",tags=["Categorías"],summary="Desactivar categoría (no elimina)",response_model=Salida)
async def desactivar_categoria(request: Request, id_categoria: int):
    dao = CategoriaDAO(request.app.cn)
    return dao.desactivar(id_categoria)

@app.patch("/categorias/{id_categoria}/reactivar", tags=["Categorías"],
    summary="Reactivar categoría", response_model=Salida)
async def reactivar_categoria(request: Request, id_categoria: int):
    dao = CategoriaDAO(request.app.cn)
    return dao.reactivar(id_categoria)


@app.get("/categorias/{id_usuario}",tags=["Categorías"],summary="Consultar todas las categorías de un usuario",response_model=CategoriasSalida)
async def consultar_categorias_usuario(request: Request, id_usuario: int):
    dao = CategoriaDAO(request.app.cn)
    return dao.consultar_por_usuario(id_usuario)


@app.get("/categorias/{id_usuario}/estado/{estado}",tags=["Categorías"],summary="Consultar categorías por estado (true=activas, false=inactivas)",response_model=CategoriasSalida)
async def consultar_categorias_estado(request: Request, id_usuario: int, estado: bool):
    dao = CategoriaDAO(request.app.cn)
    return dao.consultar_por_estado(id_usuario, estado)

# RECURSO 3: MOVIMIENTOS - Base URL: /movimientos
@app.post(
    "/movimientos/registrar",
    tags=["Movimientos"],
    summary="Registrar nuevo movimiento (ingreso o gasto)",
    response_model= MovimientoRegistradoSalida | Salida )
async def registrar_movimiento(request: Request, datos: MovimientoRegistrar):
    dao = MovimientoDAO(request.app.cn)
    return dao.registrar(datos)

@app.put("/movimientos/editar/{id_movimiento}", tags=["Movimientos"], summary="Editar un movimiento activo", response_model=Salida)
async def editar_movimiento(request: Request, id_movimiento: int, datos: MovimientoEditar):
    dao = MovimientoDAO(request.app.cn)
    return dao.editar(id_movimiento, datos)

@app.patch("/movimientos/cancelar/{id_movimiento}",tags=["Movimientos"],summary="Cancelar un movimiento (no elimina)",response_model=Salida)
async def cancelar_movimiento(request: Request, id_movimiento: int, datos: MovimientoCancelar = MovimientoCancelar()):
    dao = MovimientoDAO(request.app.cn)
    return dao.cancelar(id_movimiento, datos)

@app.get("/movimientos/{id_movimiento}",tags=["Movimientos"],summary="Consultar movimiento por ID",response_model=MovimientoDetalleSalida | Salida)
async def consultar_movimiento(request: Request, id_movimiento: int):
    dao = MovimientoDAO(request.app.cn)
    return dao.consultar_por_id(id_movimiento)

@app.get(
    "/movimientos/{id_usuario}/tipo/{tipo_movimiento}", tags=["Movimientos"],
    summary="Consultar movimientos por usuario y tipo (ingreso|gasto)", response_model=MovimientosSalida)
async def consultar_por_tipo(request: Request, id_usuario: int, tipo_movimiento: str):
    dao = MovimientoDAO(request.app.cn)
    return dao.consultar_por_tipo(id_usuario, tipo_movimiento)

@app.get("/movimientos/{id_usuario}/mes/{mes}/anio/{anio}", tags=["Movimientos"],
    summary="Consultar movimientos por mes y año", response_model=MovimientosSalida)
async def consultar_por_mes(request: Request, id_usuario: int, mes: int, anio: int):
    dao = MovimientoDAO(request.app.cn)
    return dao.consultar_por_mes(id_usuario, mes, anio)

@app.get( "/movimientos/{id_usuario}/categoria/{id_categoria}", tags=["Movimientos"],
    summary="Consultar movimientos por categoría", response_model=MovimientosSalida )
async def consultar_por_categoria(request: Request, id_usuario: int, id_categoria: int):
    dao = MovimientoDAO(request.app.cn)
    return dao.consultar_por_categoria(id_usuario, id_categoria)

@app.get("/movimientos/{id_usuario}/pago/{tipo_pago}", tags=["Movimientos"],
    summary="Consultar movimientos por tipo de pago", response_model=MovimientosSalida)
async def consultar_por_tipo_pago(request: Request, id_usuario: int, tipo_pago: str):
    dao = MovimientoDAO(request.app.cn)
    return dao.consultar_por_tipo_pago(id_usuario, tipo_pago)

#RECURSO 4: PLANEACIÓN FINANCIERA MENSUAL - Base URL: /planeacion

@app.post("/planeacion/crear", tags=["Planeación"],
    summary="Crear planeación financiera mensual", response_model=PlaneacionCreadaSalida | Salida)
async def crear_planeacion(request: Request, datos: PlaneacionCrear):
    dao = PlaneacionDAO(request.app.cn)
    return dao.crear(datos)

@app.get("/planeacion/{id_planeacion}", tags=["Planeación"],
    summary="Consultar planeación por ID", response_model=PlaneacionDetalleSalida | Salida)
async def consultar_planeacion(request: Request, id_planeacion: int):
    dao = PlaneacionDAO(request.app.cn)
    return dao.consultar_por_id(id_planeacion)

@app.get("/planeacion/{id_usuario}/historial", tags=["Planeación"],
    summary="Historial de planeaciones del usuario (?anio=2025 opcional)", response_model=PlaneacionesSalida )
async def historial_planeaciones(request: Request, id_usuario: int, anio: Optional[int] = None):
    dao = PlaneacionDAO(request.app.cn)
    return dao.consultar_historial(id_usuario, anio)

@app.get( "/planeacion/{id_usuario}/mes/{mes}/anio/{anio}", tags=["Planeación"],
    summary="Consultar planeación por mes y año", response_model=PlaneacionDetalleSalida | Salida)
async def consultar_planeacion_mes(request: Request, id_usuario: int, mes: int, anio: int):
    dao = PlaneacionDAO(request.app.cn)
    return dao.consultar_por_mes_anio(id_usuario, mes, anio)

@app.put( "/planeacion/{id_planeacion}/editar", tags=["Planeación"],
    summary="Editar ingreso_estimado o meta_ahorro de una planeación", response_model=Salida)
async def editar_planeacion(request: Request, id_planeacion: int, datos: PlaneacionEditar):
    dao = PlaneacionDAO(request.app.cn)
    return dao.editar(id_planeacion, datos)

# INICIO DEL ENTORNO VIRTUAL
if __name__ == '__main__':
   uvicorn.run("main:app",reload=True)
