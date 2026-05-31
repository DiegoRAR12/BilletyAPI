from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, Numeric, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime
from decimal import Decimal
from typing import Optional
import hashlib

from models import (
    Salida,
    UsuarioRegistro, UsuarioLogin, UsuarioSalida, LoginSalida, UsuarioCambiarRol,
    CategoriaCrear, CategoriaEditar, CategoriasCreadaSalida, CategoriasSalida, CategoriaSalida,
    MovimientoRegistrar, MovimientoEditar, MovimientoCancelar,
    MovimientoRegistradoSalida, MovimientoDetalleSalida, MovimientosSalida, MovimientoSalida,
    PlaneacionCrear, PlaneacionEditar,
    PlaneacionCreadaSalida, PlaneacionDetalleSalida, PlaneacionesSalida, PlaneacionSalida,
)

# TABLAS
Base = declarative_base()
class UsuarioORM(Base):
    __tablename__ = "usuarios"
    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    nombre     = Column(String(150), nullable=False)
    correo     = Column(String(255), nullable=False, unique=True)
    password   = Column(String(255), nullable=False)
    estatus    = Column(Boolean,     nullable=False, default=True)
    rol        = Column(String(10),  nullable=False, default="usuario")

class CategoriaORM(Base):
    __tablename__ = "categorias"
    id_categoria = Column(Integer,     primary_key=True, autoincrement=True)
    id_usuario   = Column(Integer,     ForeignKey("usuarios.id_usuario"), nullable=False)
    nombre       = Column(String(150), nullable=False)
    descripcion  = Column(String(300), nullable=True)
    estado       = Column(Boolean,     nullable=False, default=True)

class PlaneacionORM(Base):
    __tablename__ = "planeacion_mensual"
    id_planeacion    = Column(Integer,      primary_key=True, autoincrement=True)
    id_usuario       = Column(Integer,      ForeignKey("usuarios.id_usuario"), nullable=False)
    mes              = Column(Integer,      nullable=False)
    anio             = Column(Integer,      nullable=False)
    ingreso_estimado = Column(Numeric(10,2),nullable=False, default=0.00)
    ingreso_real     = Column(Numeric(10,2),nullable=False, default=0.00)
    gasto_total      = Column(Numeric(10,2),nullable=False, default=0.00)
    meta_ahorro      = Column(Numeric(10,2),nullable=False, default=0.00)
    ahorro_real      = Column(Numeric(10,2),nullable=False, default=0.00)

class MovimientoORM(Base):
    __tablename__ = "movimientos"
    id_movimiento   = Column(Integer,      primary_key=True, autoincrement=True)
    id_usuario      = Column(Integer,      ForeignKey("usuarios.id_usuario"),            nullable=False)
    id_categoria    = Column(Integer,      ForeignKey("categorias.id_categoria"),         nullable=False)
    id_planeacion   = Column(Integer,      ForeignKey("planeacion_mensual.id_planeacion"),nullable=False)
    monto           = Column(Numeric(10,2),nullable=False)
    tipo_movimiento = Column(String(10),   nullable=False)
    fecha           = Column(DateTime,     nullable=False)
    descripcion     = Column(String(300),  nullable=True)
    tipo_pago       = Column(String(20),   nullable=False)
    estatus         = Column(String(15),   nullable=False, default="activo")

# CLASE Conexion
class Conexion:
    HOST = "localhost"
    PORT = 3306
    BD   = "billety_db"

    def __init__(self, user: str, password: str):
        try:
            url = f"mysql+pymysql://{user}:{password}@{self.HOST}:{self.PORT}/{self.BD}"
            self._engine = create_engine(url, echo=False, pool_pre_ping=True)
            Base.metadata.create_all(self._engine)
            self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
            print(f"✅ Conexión exitosa a MySQL como '{user}' — Billety DB")
        except Exception as e:
            print(f"❌ Error al conectar a la BD: {e}")
            raise

    def cerrar(self):
        if self._engine:
            self._engine.dispose()
            print("Conexión cerrada correctamente")

    @property
    def session(self) -> Session:
        return self._SessionLocal()

# HELPER — Hashear contraseñas
def _hashear(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

#USUARIOS
class UsuarioDAO:
    def __init__(self, conexion: Conexion):
        self.conexion = conexion

    def registrar(self, datos: UsuarioRegistro) -> Salida:
        try:
            with self.conexion.session as db:
                nuevo = UsuarioORM(
                    nombre   = datos.nombre,
                    correo   = datos.correo,
                    password = _hashear(datos.password),
                    estatus  = True,
                    rol      = "usuario"
                )
                db.add(nuevo)
                db.commit()
                return Salida(codigo=201, mensaje="Usuario registrado exitosamente")
        except IntegrityError:
            return Salida(codigo=409, mensaje="El correo ya está registrado en el sistema")
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno al registrar usuario: {e}")

    def login(self, datos: UsuarioLogin) -> LoginSalida | Salida:
        try:
            with self.conexion.session as db:
                usuario = db.query(UsuarioORM).filter(
                    UsuarioORM.correo == datos.correo
                ).first()

                if not usuario:
                    return Salida(codigo=400, mensaje="El correo no está registrado")
                if usuario.password != _hashear(datos.password):
                    return Salida(codigo=400, mensaje="Contraseña incorrecta")
                if not usuario.estatus:
                    return Salida(codigo=403, mensaje="La cuenta está desactivada")

                return LoginSalida(
                    codigo=200,
                    id_usuario=usuario.id_usuario,
                    nombre=usuario.nombre,
                    estatus=usuario.estatus,
                    rol=usuario.rol
                )
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno al iniciar sesión: {e}")

    def consultar_por_id(self, id_usuario: int) -> UsuarioSalida | Salida:
        try:
            with self.conexion.session as db:
                usuario = db.query(UsuarioORM).filter(
                    UsuarioORM.id_usuario == id_usuario
                ).first()

                if not usuario:
                    return Salida(codigo=404, mensaje="Usuario no encontrado")

                return UsuarioSalida(
                    id_usuario=usuario.id_usuario,
                    nombre=usuario.nombre,
                    correo=usuario.correo,
                    estatus=usuario.estatus,
                    rol=usuario.rol
                )
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno al consultar usuario: {e}")

    def desactivar(self, id_usuario: int) -> Salida:
        try:
            with self.conexion.session as db:
                usuario = db.query(UsuarioORM).filter(
                    UsuarioORM.id_usuario == id_usuario
                ).first()

                if not usuario:
                    return Salida(codigo=404, mensaje="Usuario no encontrado")
                if not usuario.estatus:
                    return Salida(codigo=400, mensaje="La cuenta ya está desactivada")

                usuario.estatus = False
                db.commit()
                return Salida(codigo=200, mensaje="Cuenta desactivada exitosamente")
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno al desactivar usuario: {e}")

    def reactivar(self, id_usuario: int) -> Salida:
        try:
            with self.conexion.session as db:
                usuario = db.query(UsuarioORM).filter(
                    UsuarioORM.id_usuario == id_usuario
                ).first()

                if not usuario:
                    return Salida(codigo=404, mensaje="Usuario no encontrado")
                if usuario.estatus:
                    return Salida(codigo=400, mensaje="La cuenta ya está activa")

                usuario.estatus = True
                db.commit()
                return Salida(codigo=200, mensaje="Cuenta reactivada exitosamente")
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno al reactivar usuario: {e}")

    def activar(self, id_usuario: int) -> Salida:
        try:
            with self.conexion.session as db:
                usuario = db.query(UsuarioORM).filter(
                    UsuarioORM.id_usuario == id_usuario
                ).first()

                if not usuario:
                    return Salida(codigo=404, mensaje="Usuario no encontrado")
                if usuario.estatus:
                    return Salida(codigo=400, mensaje="La cuenta ya está activa")

                usuario.estatus = True
                db.commit()
                return Salida(codigo=200, mensaje="Cuenta activada exitosamente")
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno al activar usuario: {e}")

    def cambiar_rol(self, id_usuario: int, datos: UsuarioCambiarRol) -> Salida:
        try:
            with self.conexion.session as db:
                usuario = db.query(UsuarioORM).filter(
                    UsuarioORM.id_usuario == id_usuario
                ).first()

                if not usuario:
                    return Salida(codigo=404, mensaje="Usuario no encontrado")
                if not usuario.estatus:
                    return Salida(codigo=400, mensaje="No se puede cambiar el rol de un usuario inactivo")

                usuario.rol = datos.rol
                db.commit()
                return Salida(codigo=200, mensaje=f"Rol actualizado a '{datos.rol}' exitosamente")
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno al cambiar rol: {e}")

    def autenticar(self, correo: str, password: str) -> "Usuario | None":
        """
        Verifica credenciales contra la tabla usuarios.
        Retorna el objeto Usuario si son válidas y la cuenta está activa.
        Usado por security.py en el proceso de autenticación HTTP Basic.
        """
        try:
            with self.conexion.session as db:
                usuario = db.query(UsuarioORM).filter(
                    UsuarioORM.correo  == correo,
                    UsuarioORM.password == _hashear(password),
                    UsuarioORM.estatus  == True
                ).first()

                if not usuario:
                    return None

                from models import Usuario
                return Usuario(
                    id_usuario = usuario.id_usuario,
                    nombre     = usuario.nombre,
                    correo     = usuario.correo,
                    password   = usuario.password,
                    estatus    = usuario.estatus,
                    rol        = usuario.rol
                )
        except SQLAlchemyError:
            return None

#CATEGORÍAS
class CategoriaDAO:
    def __init__(self, conexion: Conexion):
        self.conexion = conexion

    def crear(self, datos: CategoriaCrear) -> CategoriasCreadaSalida | Salida:
        try:
            with self.conexion.session as db:
                usuario = db.query(UsuarioORM).filter(
                    UsuarioORM.id_usuario == datos.id_usuario
                ).first()
                if not usuario:
                    return Salida(codigo=404, mensaje="Usuario no encontrado")

                existe = db.query(CategoriaORM).filter(
                    CategoriaORM.id_usuario == datos.id_usuario,
                    CategoriaORM.nombre    == datos.nombre
                ).first()
                if existe:
                    return Salida(codigo=409, mensaje="Ya existe una categoría con ese nombre para este usuario")

                nueva = CategoriaORM(
                    id_usuario  = datos.id_usuario,
                    nombre      = datos.nombre,
                    descripcion = datos.descripcion,
                    estado      = True
                )
                db.add(nueva)
                db.commit()
                db.refresh(nueva)

                return CategoriasCreadaSalida(
                    codigo=201,
                    mensaje="Categoría creada exitosamente",
                    id_categoria=nueva.id_categoria
                )
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno al crear categoría: {e}")

    def editar(self, id_categoria: int, datos: CategoriaEditar) -> Salida:
        try:
            with self.conexion.session as db:
                cat = db.query(CategoriaORM).filter(
                    CategoriaORM.id_categoria == id_categoria
                ).first()

                if not cat:
                    return Salida(codigo=404, mensaje="Categoría no encontrada")
                if not cat.estado:
                    return Salida(codigo=400, mensaje="No se pueden editar categorías inactivas")

                cambios = datos.model_dump(exclude_unset=True)
                if not cambios:
                    return Salida(codigo=400, mensaje="No se enviaron campos para actualizar")

                if "nombre" in cambios:
                    duplicado = db.query(CategoriaORM).filter(
                        CategoriaORM.id_usuario   == cat.id_usuario,
                        CategoriaORM.nombre       == cambios["nombre"],
                        CategoriaORM.id_categoria != id_categoria
                    ).first()
                    if duplicado:
                        return Salida(codigo=409, mensaje="Ya existe otra categoría con ese nombre")
                    cat.nombre = cambios["nombre"]

                if "descripcion" in cambios:
                    cat.descripcion = cambios["descripcion"]

                db.commit()
                return Salida(codigo=200, mensaje="Categoría actualizada exitosamente")
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno al editar categoría: {e}")

    def desactivar(self, id_categoria: int) -> Salida:
        try:
            with self.conexion.session as db:
                cat = db.query(CategoriaORM).filter(
                    CategoriaORM.id_categoria == id_categoria
                ).first()

                if not cat:
                    return Salida(codigo=404, mensaje="Categoría no encontrada")
                if not cat.estado:
                    return Salida(codigo=400, mensaje="La categoría ya está inactiva")

                cat.estado = False
                db.commit()
                return Salida(codigo=200, mensaje="Categoría desactivada exitosamente")
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno al desactivar categoría: {e}")

    def reactivar(self, id_categoria: int) -> Salida:
        try:
            with self.conexion.session as db:
                cat = db.query(CategoriaORM).filter(
                    CategoriaORM.id_categoria == id_categoria
                ).first()

                if not cat:
                    return Salida(codigo=404, mensaje="Categoría no encontrada")
                if cat.estado:
                    return Salida(codigo=400, mensaje="La categoría ya está activa")

                cat.estado = True
                db.commit()
                return Salida(codigo=200, mensaje="Categoría reactivada exitosamente")
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno al reactivar categoría: {e}")

    def consultar_por_usuario(self, id_usuario: int) -> CategoriasSalida:
        try:
            with self.conexion.session as db:
                usuario = db.query(UsuarioORM).filter(
                    UsuarioORM.id_usuario == id_usuario
                ).first()
                if not usuario:
                    return CategoriasSalida(codigo=404, mensaje="Usuario no encontrado", categorias=None)

                cats = db.query(CategoriaORM).filter(
                    CategoriaORM.id_usuario == id_usuario
                ).all()

                if not cats:
                    return CategoriasSalida(codigo=200, mensaje="El usuario no tiene categorías registradas", categorias=[])

                lista = [
                    CategoriaSalida(
                        id_categoria=c.id_categoria,
                        nombre=c.nombre,
                        descripcion=c.descripcion,
                        estado=c.estado
                    ) for c in cats
                ]
                return CategoriasSalida(codigo=200, mensaje="OK", categorias=lista)
        except SQLAlchemyError as e:
            return CategoriasSalida(codigo=500, mensaje=f"Error interno: {e}", categorias=None)

    def consultar_por_estado(self, id_usuario: int, estado: bool) -> CategoriasSalida:
        try:
            with self.conexion.session as db:
                usuario = db.query(UsuarioORM).filter(
                    UsuarioORM.id_usuario == id_usuario
                ).first()
                if not usuario:
                    return CategoriasSalida(codigo=404, mensaje="Usuario no encontrado", categorias=None)

                cats = db.query(CategoriaORM).filter(
                    CategoriaORM.id_usuario == id_usuario,
                    CategoriaORM.estado     == estado
                ).all()

                if not cats:
                    estado_texto = "activas" if estado else "inactivas"
                    return CategoriasSalida(codigo=200, mensaje=f"El usuario no tiene categorías {estado_texto}", categorias=[])

                lista = [
                    CategoriaSalida(
                        id_categoria=c.id_categoria,
                        nombre=c.nombre,
                        descripcion=c.descripcion,
                        estado=c.estado
                    ) for c in cats
                ]
                return CategoriasSalida(codigo=200, mensaje="OK", categorias=lista)
        except SQLAlchemyError as e:
            return CategoriasSalida(codigo=500, mensaje=f"Error interno: {e}", categorias=None)


# PLANEACIÓN FINANCIERA MENSUAL
class PlaneacionDAO:
    def __init__(self, conexion: Conexion):
        self.conexion = conexion

    def crear(self, datos: PlaneacionCrear) -> PlaneacionCreadaSalida | Salida:
        try:
            with self.conexion.session as db:
                usuario = db.query(UsuarioORM).filter(
                    UsuarioORM.id_usuario == datos.id_usuario
                ).first()
                if not usuario:
                    return Salida(codigo=404, mensaje="Usuario no encontrado")

                existe = db.query(PlaneacionORM).filter(
                    PlaneacionORM.id_usuario == datos.id_usuario,
                    PlaneacionORM.mes        == datos.mes,
                    PlaneacionORM.anio       == datos.anio
                ).first()
                if existe:
                    return Salida(codigo=409, mensaje="Ya existe una planeación para ese mes y año")

                nueva = PlaneacionORM(
                    id_usuario       = datos.id_usuario,
                    mes              = datos.mes,
                    anio             = datos.anio,
                    ingreso_estimado = datos.ingreso_estimado or Decimal("0.00"),
                    meta_ahorro      = datos.meta_ahorro      or Decimal("0.00"),
                    ingreso_real     = Decimal("0.00"),
                    gasto_total      = Decimal("0.00"),
                    ahorro_real      = Decimal("0.00"),
                )
                db.add(nueva)
                db.commit()
                db.refresh(nueva)
                return PlaneacionCreadaSalida(
                    codigo=201,
                    mensaje="Planeación creada exitosamente",
                    id_planeacion=nueva.id_planeacion
                )
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno al crear planeación: {e}")

    def consultar_por_id(self, id_planeacion: int) -> PlaneacionDetalleSalida | Salida:
        try:
            with self.conexion.session as db:
                p = db.query(PlaneacionORM).filter(
                    PlaneacionORM.id_planeacion == id_planeacion
                ).first()
                if not p:
                    return Salida(codigo=404, mensaje="Planeación no encontrada")
                return PlaneacionDetalleSalida(codigo=200, mensaje="OK", planeacion=self._a_salida(p))
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno: {e}")

    def consultar_historial(self, id_usuario: int, anio: Optional[int] = None) -> PlaneacionesSalida:
        try:
            with self.conexion.session as db:
                usuario = db.query(UsuarioORM).filter(
                    UsuarioORM.id_usuario == id_usuario
                ).first()
                if not usuario:
                    return PlaneacionesSalida(codigo=404, mensaje="Usuario no encontrado", planeaciones=None)

                query = db.query(PlaneacionORM).filter(PlaneacionORM.id_usuario == id_usuario)
                if anio:
                    query = query.filter(PlaneacionORM.anio == anio)
                planes = query.order_by(PlaneacionORM.anio.desc(), PlaneacionORM.mes.desc()).all()

                if not planes:
                    return PlaneacionesSalida(codigo=200, mensaje="El usuario no tiene planeaciones registradas", planeaciones=[])

                return PlaneacionesSalida(
                    codigo=200, mensaje="OK",
                    planeaciones=[self._a_salida(p) for p in planes]
                )
        except SQLAlchemyError as e:
            return PlaneacionesSalida(codigo=500, mensaje=f"Error interno: {e}", planeaciones=None)

    def consultar_por_mes_anio(self, id_usuario: int, mes: int, anio: int) -> PlaneacionDetalleSalida | Salida:
        try:
            with self.conexion.session as db:
                p = db.query(PlaneacionORM).filter(
                    PlaneacionORM.id_usuario == id_usuario,
                    PlaneacionORM.mes        == mes,
                    PlaneacionORM.anio       == anio
                ).first()
                if not p:
                    return Salida(codigo=404, mensaje="No existe planeación para ese mes y año")
                return PlaneacionDetalleSalida(codigo=200, mensaje="OK", planeacion=self._a_salida(p))
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno: {e}")

    def editar(self, id_planeacion: int, datos: PlaneacionEditar) -> Salida:
        try:
            with self.conexion.session as db:
                p = db.query(PlaneacionORM).filter(
                    PlaneacionORM.id_planeacion == id_planeacion
                ).first()
                if not p:
                    return Salida(codigo=404, mensaje="Planeación no encontrada")

                cambios = datos.model_dump(exclude_unset=True)
                if not cambios:
                    return Salida(codigo=400, mensaje="No se enviaron campos para actualizar")

                if "ingreso_estimado" in cambios:
                    p.ingreso_estimado = cambios["ingreso_estimado"]
                if "meta_ahorro" in cambios:
                    p.meta_ahorro = cambios["meta_ahorro"]

                db.commit()
                return Salida(codigo=200, mensaje="Planeación actualizada exitosamente")
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno al editar planeación: {e}")

    def _buscar_o_crear(self, db: Session, id_usuario: int, mes: int, anio: int) -> PlaneacionORM:
        p = db.query(PlaneacionORM).filter(
            PlaneacionORM.id_usuario == id_usuario,
            PlaneacionORM.mes        == mes,
            PlaneacionORM.anio       == anio
        ).first()

        if not p:
            p = PlaneacionORM(
                id_usuario       = id_usuario,
                mes              = mes,
                anio             = anio,
                ingreso_estimado = Decimal("0.00"),
                meta_ahorro      = Decimal("0.00"),
                ingreso_real     = Decimal("0.00"),
                gasto_total      = Decimal("0.00"),
                ahorro_real      = Decimal("0.00"),
            )
            db.add(p)
            db.flush()  # obtiene el id sin hacer commit todavía

        return p

    def _a_salida(self, p: PlaneacionORM) -> PlaneacionSalida:
        return PlaneacionSalida(
            id_planeacion    = p.id_planeacion,
            id_usuario       = p.id_usuario,
            mes              = p.mes,
            anio             = p.anio,
            ingreso_estimado = p.ingreso_estimado,
            ingreso_real     = p.ingreso_real,
            gasto_total      = p.gasto_total,
            meta_ahorro      = p.meta_ahorro,
            ahorro_real      = p.ahorro_real,
        )

# MOVIMIENTOS
class MovimientoDAO:
    def __init__(self, conexion: Conexion):
        self.conexion = conexion
        self._plan_dao = PlaneacionDAO(conexion)

    def registrar(self, datos: MovimientoRegistrar) -> MovimientoRegistradoSalida | Salida:
        try:
            with self.conexion.session as db:
                # Validar usuario
                usuario = db.query(UsuarioORM).filter(
                    UsuarioORM.id_usuario == datos.id_usuario
                ).first()
                if not usuario:
                    return Salida(codigo=404, mensaje="Usuario no encontrado")

                # Validar categoría: debe existir, pertenecer al usuario y estar activa
                cat = db.query(CategoriaORM).filter(
                    CategoriaORM.id_categoria == datos.id_categoria,
                    CategoriaORM.id_usuario   == datos.id_usuario,
                    CategoriaORM.estado       == True
                ).first()
                if not cat:
                    return Salida(codigo=400, mensaje="La categoría no existe, no pertenece al usuario o está inactiva")

                # Buscar o crear planeación automáticamente según mes/año de la fecha
                plan = self._plan_dao._buscar_o_crear(
                    db, datos.id_usuario, datos.fecha.month, datos.fecha.year
                )

                # Crear el movimiento
                nuevo = MovimientoORM(
                    id_usuario      = datos.id_usuario,
                    id_categoria    = datos.id_categoria,
                    id_planeacion   = plan.id_planeacion,
                    monto           = datos.monto,
                    tipo_movimiento = datos.tipo_movimiento,
                    fecha           = datos.fecha,
                    descripcion     = datos.descripcion,
                    tipo_pago       = datos.tipo_pago,
                    estatus         = "activo"
                )
                db.add(nuevo)

                # Actualizar totales en la planeación
                if datos.tipo_movimiento == "ingreso":
                    plan.ingreso_real += datos.monto
                else:
                    plan.gasto_total += datos.monto
                plan.ahorro_real = plan.ingreso_real - plan.gasto_total

                db.commit()
                db.refresh(nuevo)
                return MovimientoRegistradoSalida(
                    codigo=201,
                    mensaje="Movimiento registrado exitosamente",
                    id_movimiento=nuevo.id_movimiento
                )
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno al registrar movimiento: {e}")

    def editar(self, id_movimiento: int, datos: MovimientoEditar) -> Salida:
        try:
            with self.conexion.session as db:
                mov = db.query(MovimientoORM).filter(
                    MovimientoORM.id_movimiento == id_movimiento
                ).first()
                if not mov:
                    return Salida(codigo=404, mensaje="Movimiento no encontrado")
                if mov.estatus != "activo":
                    return Salida(codigo=400, mensaje="Solo se pueden editar movimientos activos")

                cambios = datos.model_dump(exclude_unset=True)
                if not cambios:
                    return Salida(codigo=400, mensaje="No se enviaron campos para actualizar")

                plan = db.query(PlaneacionORM).filter(
                    PlaneacionORM.id_planeacion == mov.id_planeacion
                ).first()

                tipo_anterior  = mov.tipo_movimiento
                monto_anterior = mov.monto
                tipo_nuevo     = cambios.get("tipo_movimiento", tipo_anterior)
                monto_nuevo    = cambios.get("monto", monto_anterior)

                # Revertir efecto anterior en la planeación
                if tipo_anterior == "ingreso":
                    plan.ingreso_real -= monto_anterior
                else:
                    plan.gasto_total -= monto_anterior

                # Aplicar nuevo efecto
                if tipo_nuevo == "ingreso":
                    plan.ingreso_real += monto_nuevo
                else:
                    plan.gasto_total += monto_nuevo

                plan.ahorro_real = plan.ingreso_real - plan.gasto_total

                # Aplicar cambios al movimiento
                for campo, valor in cambios.items():
                    setattr(mov, campo, valor)

                db.commit()
                return Salida(codigo=200, mensaje="Movimiento actualizado exitosamente")
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno al editar movimiento: {e}")

    def cancelar(self, id_movimiento: int, datos: MovimientoCancelar) -> Salida:
        try:
            with self.conexion.session as db:
                mov = db.query(MovimientoORM).filter(
                    MovimientoORM.id_movimiento == id_movimiento
                ).first()
                if not mov:
                    return Salida(codigo=404, mensaje="Movimiento no encontrado")
                if mov.estatus == "cancelado":
                    return Salida(codigo=400, mensaje="El movimiento ya está cancelado")

                plan = db.query(PlaneacionORM).filter(
                    PlaneacionORM.id_planeacion == mov.id_planeacion
                ).first()

                # Revertir efecto en la planeación
                if mov.tipo_movimiento == "ingreso":
                    plan.ingreso_real -= mov.monto
                else:
                    plan.gasto_total -= mov.monto
                plan.ahorro_real = plan.ingreso_real - plan.gasto_total

                mov.estatus = "cancelado"
                if datos.motivo:
                    mov.descripcion = f"[CANCELADO] {datos.motivo}"

                db.commit()
                return Salida(codigo=200, mensaje="Movimiento cancelado exitosamente")
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno al cancelar movimiento: {e}")

    def consultar_por_id(self, id_movimiento: int) -> MovimientoDetalleSalida | Salida:
        try:
            with self.conexion.session as db:
                mov = db.query(MovimientoORM).filter(
                    MovimientoORM.id_movimiento == id_movimiento
                ).first()
                if not mov:
                    return Salida(codigo=404, mensaje="Movimiento no encontrado")
                return MovimientoDetalleSalida(codigo=200, mensaje="OK", movimiento=self._a_salida(mov))
        except SQLAlchemyError as e:
            return Salida(codigo=500, mensaje=f"Error interno: {e}")

    def consultar_por_tipo(self, id_usuario: int, tipo: str) -> MovimientosSalida:
        try:
            with self.conexion.session as db:
                movs = db.query(MovimientoORM).filter(
                    MovimientoORM.id_usuario      == id_usuario,
                    MovimientoORM.tipo_movimiento == tipo,
                    MovimientoORM.estatus         != "cancelado"
                ).all()
                if not movs:
                    return MovimientosSalida(codigo=200, mensaje="No se encontraron movimientos", movimientos=[])
                return MovimientosSalida(codigo=200, mensaje="OK", movimientos=[self._a_salida(m) for m in movs])
        except SQLAlchemyError as e:
            return MovimientosSalida(codigo=500, mensaje=f"Error interno: {e}", movimientos=None)

    def consultar_por_mes(self, id_usuario: int, mes: int, anio: int) -> MovimientosSalida:
        try:
            with self.conexion.session as db:
                plan = db.query(PlaneacionORM).filter(
                    PlaneacionORM.id_usuario == id_usuario,
                    PlaneacionORM.mes        == mes,
                    PlaneacionORM.anio       == anio
                ).first()
                if not plan:
                    return MovimientosSalida(codigo=404, mensaje="No existe planeación para ese mes y año", movimientos=None)

                movs = db.query(MovimientoORM).filter(
                    MovimientoORM.id_usuario    == id_usuario,
                    MovimientoORM.id_planeacion == plan.id_planeacion,
                    MovimientoORM.estatus       != "cancelado"
                ).all()
                if not movs:
                    return MovimientosSalida(codigo=200, mensaje="No hay movimientos en ese período", movimientos=[])
                return MovimientosSalida(codigo=200, mensaje="OK", movimientos=[self._a_salida(m) for m in movs])
        except SQLAlchemyError as e:
            return MovimientosSalida(codigo=500, mensaje=f"Error interno: {e}", movimientos=None)

    def consultar_por_categoria(self, id_usuario: int, id_categoria: int) -> MovimientosSalida:
        try:
            with self.conexion.session as db:
                movs = db.query(MovimientoORM).filter(
                    MovimientoORM.id_usuario   == id_usuario,
                    MovimientoORM.id_categoria == id_categoria,
                    MovimientoORM.estatus      != "cancelado"
                ).all()
                if not movs:
                    return MovimientosSalida(codigo=200, mensaje="No se encontraron movimientos para esa categoría", movimientos=[])
                return MovimientosSalida(codigo=200, mensaje="OK", movimientos=[self._a_salida(m) for m in movs])
        except SQLAlchemyError as e:
            return MovimientosSalida(codigo=500, mensaje=f"Error interno: {e}", movimientos=None)

    def consultar_por_tipo_pago(self, id_usuario: int, tipo_pago: str) -> MovimientosSalida:
        try:
            with self.conexion.session as db:
                movs = db.query(MovimientoORM).filter(
                    MovimientoORM.id_usuario == id_usuario,
                    MovimientoORM.tipo_pago  == tipo_pago,
                    MovimientoORM.estatus    != "cancelado"
                ).all()
                if not movs:
                    return MovimientosSalida(codigo=200, mensaje="No se encontraron movimientos con ese tipo de pago", movimientos=[])
                return MovimientosSalida(codigo=200, mensaje="OK", movimientos=[self._a_salida(m) for m in movs])
        except SQLAlchemyError as e:
            return MovimientosSalida(codigo=500, mensaje=f"Error interno: {e}", movimientos=None)

    def _a_salida(self, m: MovimientoORM) -> MovimientoSalida:
        return MovimientoSalida(
            id_movimiento   = m.id_movimiento,
            id_usuario      = m.id_usuario,
            id_categoria    = m.id_categoria,
            id_planeacion   = m.id_planeacion,
            monto           = m.monto,
            tipo_movimiento = m.tipo_movimiento,
            fecha           = m.fecha,
            descripcion     = m.descripcion,
            tipo_pago       = m.tipo_pago,
            estatus         = m.estatus,
        )