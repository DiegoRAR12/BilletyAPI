from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn
from starlette import status
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from dao import Conexion, UsuarioDAO, CategoriaDAO, PlaneacionDAO, MovimientoDAO
from security import getUser, RoleChecker
from models import (
    Salida, Usuario,
    UsuarioRegistro, UsuarioLogin, UsuarioSalida, LoginSalida, UsuarioCambiarRol,
    CategoriaCrear, CategoriaEditar, CategoriasCreadaSalida, CategoriasSalida,
    MovimientoRegistrar, MovimientoEditar, MovimientoCancelar,
    MovimientoRegistradoSalida, MovimientoDetalleSalida, MovimientosSalida,
    PlaneacionCrear, PlaneacionEditar,
    PlaneacionCreadaSalida, PlaneacionDetalleSalida, PlaneacionesSalida,
)

def _rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Respuesta personalizada en español cuando se supera el límite de solicitudes."""
    return JSONResponse(
        status_code=429,
        content={
            "codigo": 429,
            "mensaje": "Demasiadas solicitudes. Has superado el límite permitido. Intenta de nuevo en un momento."
        }
    )

# =============================================================================
# RATE LIMITING — límite de solicitudes por dirección IP
# =============================================================================
limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

# =============================================================================
# ROLES DISPONIBLES
# =============================================================================
roles_admin         = RoleChecker(["admin"])
roles_admin_usuario = RoleChecker(["admin", "usuario"])


# =============================================================================
# HELPER — Conexión MySQL según rol del usuario autenticado
# =============================================================================
def get_cn(user: Usuario) -> Conexion:
    """Conecta a MySQL con billety_admin o billety_usuario según el rol."""
    if user.rol == "admin":
        return Conexion("billety_admin", "Admin.Billety123")
    return Conexion("billety_usuario", "Usuario.Billety123")


# =============================================================================
# HELPER — Validación de ownership
# Verifica que un usuario solo acceda a sus propios recursos.
# El admin puede acceder a cualquier recurso.
# =============================================================================
def verificar_propiedad(user: Usuario, id_usuario: int):
    if user.rol != "admin" and user.id_usuario != id_usuario:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sin autorización. Solo puedes acceder a tus propios datos."
        )


# =============================================================================
# CICLO DE VIDA
# =============================================================================
@app.on_event("startup")
def startup():
    app.cn = Conexion("billety_admin", "Admin.Billety123")

@app.on_event("shutdown")
def shutdown():
    app.cn.cerrar()


# =============================================================================
# RECURSO 1: USUARIOS — /usuarios
# =============================================================================

# ── Endpoints PÚBLICOS (sin autenticación) ────────────────────────────────────
@app.post("/usuarios/registrar", tags=["Usuarios"],
    summary="Registrar nuevo usuario", response_model=Salida)
@limiter.limit("5/minute")
async def registrar_usuario(request: Request, datos: UsuarioRegistro):
    # Público: cualquiera puede registrarse
    cn = Conexion("billety_usuario", "Usuario.Billety123")
    dao = UsuarioDAO(cn)
    return dao.registrar(datos)


@app.post("/usuarios/login", tags=["Usuarios"],
    summary="Login de usuario", response_model=LoginSalida | Salida)
@limiter.limit("10/minute")
async def login(request: Request, datos: UsuarioLogin):
    # Público: cualquiera puede hacer login
    cn = Conexion("billety_usuario", "Usuario.Billety123")
    dao = UsuarioDAO(cn)
    return dao.login(datos)


# ── Endpoints PROTEGIDOS ──────────────────────────────────────────────────────
@app.get("/usuarios/{id_usuario}", tags=["Usuarios"],
    summary="Consultar usuario por ID", response_model=UsuarioSalida | Salida)
@limiter.limit("60/minute")
async def consultar_usuario(request: Request, id_usuario: int,
                            user: Usuario = Depends(roles_admin_usuario)):
    # Ownership: usuario solo puede ver su propio perfil
    verificar_propiedad(user, id_usuario)
    cn = get_cn(user)
    dao = UsuarioDAO(cn)
    resultado = dao.consultar_por_id(id_usuario)
    if isinstance(resultado, Salida):
        return JSONResponse(status_code=resultado.codigo, content=resultado.model_dump())
    return resultado


@app.patch("/usuarios/{id_usuario}/desactivar", tags=["Usuarios"],
    summary="Desactivar cuenta de usuario", response_model=Salida)
@limiter.limit("30/minute")
async def desactivar_usuario(request: Request, id_usuario: int,
                             user: Usuario = Depends(roles_admin_usuario)):
    # Ownership: usuario solo puede desactivar su propia cuenta
    verificar_propiedad(user, id_usuario)
    cn = get_cn(user)
    dao = UsuarioDAO(cn)
    return dao.desactivar(id_usuario)


@app.patch("/usuarios/{id_usuario}/activar", tags=["Usuarios"],
    summary="Activar cuenta de usuario (solo admin)", response_model=Salida)
@limiter.limit("30/minute")
async def activar_usuario(request: Request, id_usuario: int,
                          user: Usuario = Depends(roles_admin)):
    # Solo admin puede activar cuentas
    cn = get_cn(user)
    dao = UsuarioDAO(cn)
    return dao.activar(id_usuario)


@app.patch("/usuarios/{id_usuario}/rol", tags=["Usuarios"],
    summary="Cambiar rol de usuario (solo admin)", response_model=Salida)
@limiter.limit("30/minute")
async def cambiar_rol(request: Request, id_usuario: int, datos: UsuarioCambiarRol,
                      user: Usuario = Depends(roles_admin)):
    # Solo admin puede cambiar roles
    cn = get_cn(user)
    dao = UsuarioDAO(cn)
    return dao.cambiar_rol(id_usuario, datos)


# =============================================================================
# RECURSO 2: CATEGORÍAS — /categorias
# =============================================================================

@app.post("/categorias/crear", tags=["Categorías"],
    summary="Crear categoría", response_model=CategoriasCreadaSalida | Salida)
@limiter.limit("30/minute")
async def crear_categoria(request: Request, datos: CategoriaCrear,
                          user: Usuario = Depends(roles_admin_usuario)):
    # Ownership: usuario solo puede crear categorías para sí mismo
    verificar_propiedad(user, datos.id_usuario)
    cn = get_cn(user)
    dao = CategoriaDAO(cn)
    return dao.crear(datos)


@app.put("/categorias/{id_categoria}/editar", tags=["Categorías"],
    summary="Editar nombre y/o descripción de categoría", response_model=Salida)
@limiter.limit("30/minute")
async def editar_categoria(request: Request, id_categoria: int, datos: CategoriaEditar,
                           user: Usuario = Depends(roles_admin_usuario)):
    cn = get_cn(user)
    dao = CategoriaDAO(cn)
    return dao.editar(id_categoria, datos)


@app.patch("/categorias/{id_categoria}/desactivar", tags=["Categorías"],
    summary="Desactivar categoría (no elimina)", response_model=Salida)
@limiter.limit("30/minute")
async def desactivar_categoria(request: Request, id_categoria: int,
                               user: Usuario = Depends(roles_admin_usuario)):
    cn = get_cn(user)
    dao = CategoriaDAO(cn)
    return dao.desactivar(id_categoria)


@app.patch("/categorias/{id_categoria}/reactivar", tags=["Categorías"],
    summary="Reactivar categoría", response_model=Salida)
@limiter.limit("30/minute")
async def reactivar_categoria(request: Request, id_categoria: int,
                              user: Usuario = Depends(roles_admin_usuario)):
    cn = get_cn(user)
    dao = CategoriaDAO(cn)
    return dao.reactivar(id_categoria)


@app.get("/categorias/{id_usuario}", tags=["Categorías"],
    summary="Consultar todas las categorías de un usuario", response_model=CategoriasSalida)
@limiter.limit("60/minute")
async def consultar_categorias_usuario(request: Request, id_usuario: int,
                                       user: Usuario = Depends(roles_admin_usuario)):
    # Ownership: usuario solo puede ver sus propias categorías
    verificar_propiedad(user, id_usuario)
    cn = get_cn(user)
    dao = CategoriaDAO(cn)
    return dao.consultar_por_usuario(id_usuario)


@app.get("/categorias/{id_usuario}/estado/{estado}", tags=["Categorías"],
    summary="Consultar categorías por estado (true=activas, false=inactivas)",
    response_model=CategoriasSalida)
@limiter.limit("60/minute")
async def consultar_categorias_estado(request: Request, id_usuario: int, estado: bool,
                                      user: Usuario = Depends(roles_admin_usuario)):
    # Ownership: usuario solo puede filtrar sus propias categorías
    verificar_propiedad(user, id_usuario)
    cn = get_cn(user)
    dao = CategoriaDAO(cn)
    return dao.consultar_por_estado(id_usuario, estado)


# =============================================================================
# RECURSO 3: MOVIMIENTOS — /movimientos
# =============================================================================

@app.post("/movimientos/registrar", tags=["Movimientos"],
    summary="Registrar nuevo movimiento (ingreso o gasto)",
    response_model=MovimientoRegistradoSalida | Salida)
@limiter.limit("30/minute")
async def registrar_movimiento(request: Request, datos: MovimientoRegistrar,
                               user: Usuario = Depends(roles_admin_usuario)):
    # Ownership: usuario solo puede registrar movimientos para sí mismo
    verificar_propiedad(user, datos.id_usuario)
    cn = get_cn(user)
    dao = MovimientoDAO(cn)
    return dao.registrar(datos)


@app.put("/movimientos/editar/{id_movimiento}", tags=["Movimientos"],
    summary="Editar un movimiento activo", response_model=Salida)
@limiter.limit("30/minute")
async def editar_movimiento(request: Request, id_movimiento: int, datos: MovimientoEditar,
                            user: Usuario = Depends(roles_admin_usuario)):
    cn = get_cn(user)
    dao = MovimientoDAO(cn)
    return dao.editar(id_movimiento, datos)


@app.patch("/movimientos/cancelar/{id_movimiento}", tags=["Movimientos"],
    summary="Cancelar un movimiento (no elimina)", response_model=Salida)
@limiter.limit("30/minute")
async def cancelar_movimiento(request: Request, id_movimiento: int,
                              datos: MovimientoCancelar = MovimientoCancelar(),
                              user: Usuario = Depends(roles_admin_usuario)):
    cn = get_cn(user)
    dao = MovimientoDAO(cn)
    return dao.cancelar(id_movimiento, datos)


@app.get("/movimientos/{id_movimiento}", tags=["Movimientos"],
    summary="Consultar movimiento por ID", response_model=MovimientoDetalleSalida | Salida)
@limiter.limit("60/minute")
async def consultar_movimiento(request: Request, id_movimiento: int,
                               user: Usuario = Depends(roles_admin_usuario)):
    cn = get_cn(user)
    dao = MovimientoDAO(cn)
    return dao.consultar_por_id(id_movimiento)


@app.get("/movimientos/{id_usuario}/tipo/{tipo_movimiento}", tags=["Movimientos"],
    summary="Consultar movimientos por usuario y tipo (ingreso|gasto)",
    response_model=MovimientosSalida)
@limiter.limit("60/minute")
async def consultar_por_tipo(request: Request, id_usuario: int, tipo_movimiento: str,
                             user: Usuario = Depends(roles_admin_usuario)):
    verificar_propiedad(user, id_usuario)
    cn = get_cn(user)
    dao = MovimientoDAO(cn)
    return dao.consultar_por_tipo(id_usuario, tipo_movimiento)


@app.get("/movimientos/{id_usuario}/mes/{mes}/anio/{anio}", tags=["Movimientos"],
    summary="Consultar movimientos por mes y año", response_model=MovimientosSalida)
@limiter.limit("60/minute")
async def consultar_por_mes(request: Request, id_usuario: int, mes: int, anio: int,
                            user: Usuario = Depends(roles_admin_usuario)):
    verificar_propiedad(user, id_usuario)
    cn = get_cn(user)
    dao = MovimientoDAO(cn)
    return dao.consultar_por_mes(id_usuario, mes, anio)


@app.get("/movimientos/{id_usuario}/categoria/{id_categoria}", tags=["Movimientos"],
    summary="Consultar movimientos por categoría", response_model=MovimientosSalida)
@limiter.limit("60/minute")
async def consultar_por_categoria(request: Request, id_usuario: int, id_categoria: int,
                                  user: Usuario = Depends(roles_admin_usuario)):
    verificar_propiedad(user, id_usuario)
    cn = get_cn(user)
    dao = MovimientoDAO(cn)
    return dao.consultar_por_categoria(id_usuario, id_categoria)


@app.get("/movimientos/{id_usuario}/pago/{tipo_pago}", tags=["Movimientos"],
    summary="Consultar movimientos por tipo de pago", response_model=MovimientosSalida)
@limiter.limit("60/minute")
async def consultar_por_tipo_pago(request: Request, id_usuario: int, tipo_pago: str,
                                  user: Usuario = Depends(roles_admin_usuario)):
    verificar_propiedad(user, id_usuario)
    cn = get_cn(user)
    dao = MovimientoDAO(cn)
    return dao.consultar_por_tipo_pago(id_usuario, tipo_pago)


# =============================================================================
# RECURSO 4: PLANEACIÓN FINANCIERA MENSUAL — /planeacion
# =============================================================================

@app.post("/planeacion/crear", tags=["Planeación"],
    summary="Crear planeación financiera mensual",
    response_model=PlaneacionCreadaSalida | Salida)
@limiter.limit("30/minute")
async def crear_planeacion(request: Request, datos: PlaneacionCrear,
                           user: Usuario = Depends(roles_admin_usuario)):
    # Ownership: usuario solo puede crear planeaciones para sí mismo
    verificar_propiedad(user, datos.id_usuario)
    cn = get_cn(user)
    dao = PlaneacionDAO(cn)
    resultado = dao.crear(datos)
    return JSONResponse(status_code=resultado.codigo, content=resultado.model_dump())


@app.get("/planeacion/{id_planeacion}", tags=["Planeación"],
    summary="Consultar planeación por ID", response_model=PlaneacionDetalleSalida | Salida)
@limiter.limit("60/minute")
async def consultar_planeacion(request: Request, id_planeacion: int,
                               user: Usuario = Depends(roles_admin_usuario)):
    cn = get_cn(user)
    dao = PlaneacionDAO(cn)
    return dao.consultar_por_id(id_planeacion)


@app.get("/planeacion/{id_usuario}/historial", tags=["Planeación"],
    summary="Historial de planeaciones del usuario (?anio= opcional)",
    response_model=PlaneacionesSalida)
@limiter.limit("60/minute")
async def historial_planeaciones(request: Request, id_usuario: int,
                                 anio: Optional[int] = None,
                                 user: Usuario = Depends(roles_admin_usuario)):
    verificar_propiedad(user, id_usuario)
    cn = get_cn(user)
    dao = PlaneacionDAO(cn)
    return dao.consultar_historial(id_usuario, anio)


@app.get("/planeacion/{id_usuario}/mes/{mes}/anio/{anio}", tags=["Planeación"],
    summary="Consultar planeación por mes y año",
    response_model=PlaneacionDetalleSalida | Salida)
@limiter.limit("60/minute")
async def consultar_planeacion_mes(request: Request, id_usuario: int, mes: int, anio: int,
                                   user: Usuario = Depends(roles_admin_usuario)):
    verificar_propiedad(user, id_usuario)
    cn = get_cn(user)
    dao = PlaneacionDAO(cn)
    return dao.consultar_por_mes_anio(id_usuario, mes, anio)


@app.put("/planeacion/{id_planeacion}/editar", tags=["Planeación"],
    summary="Editar ingreso_estimado o meta_ahorro de una planeación",
    response_model=Salida)
@limiter.limit("30/minute")
async def editar_planeacion(request: Request, id_planeacion: int, datos: PlaneacionEditar,
                            user: Usuario = Depends(roles_admin_usuario)):
    cn = get_cn(user)
    dao = PlaneacionDAO(cn)
    return dao.editar(id_planeacion, datos)


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================
if __name__ == '__main__':
    uvicorn.run("main:app", reload=True)