from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
import hashlib

from models import (
    Salida,
    UsuarioRegistro, UsuarioLogin, UsuarioSalida, LoginSalida, UsuarioCambiarRol,
    CategoriaCrear, CategoriaEditar, CategoriasCreadaSalida, CategoriasSalida, CategoriaSalida,
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

# CLASE Conexion
class Conexion:
    URL_BD = "mysql+pymysql://root:papoisql@localhost:3306/billety_db"

    def __init__(self):
        try:
            self._engine = create_engine(self.URL_BD, echo=False, pool_pre_ping=True)
            Base.metadata.create_all(self._engine)
            self._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
            print("✅ Conexión exitosa a MySQL — Billety DB")
        except Exception as e:
            print(f"❌ Error al conectar a la BD: {e}")
            raise

    def cerrar(self):
        if self._engine:
            self._engine.dispose()
            print("🔒 Conexión cerrada correctamente")

    @property
    def session(self) -> Session:
        return self._SessionLocal()

# HELPER — Hashear contraseñas
def _hashear(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# DAO — USUARIOS
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

# DAO — CATEGORÍAS
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