from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class Salida(BaseModel):
    codigo: int
    mensaje: str

# RECURSO 1: USUARIOS
# --- ENTRADA ---
class UsuarioRegistro(BaseModel):
    """Datos que manda el cliente para registrarse. El sistema asigna id_usuario."""
    nombre:   str      = Field(..., min_length=1, description="Nombre no puede estar vacío")
    correo:   EmailStr = Field(..., description="Formato válido usuario@dominio.com")
    password: str      = Field(..., min_length=8, description="Mínimo 8 caracteres")

class UsuarioLogin(BaseModel):
    """Credenciales para autenticarse."""
    correo:   EmailStr
    password: str

class UsuarioCambiarRol(BaseModel):
    """Solo permite cambiar entre 'admin' y 'usuario'."""
    rol: str = Field(..., pattern="^(admin|usuario)$", description="'admin' o 'usuario'")

# --- SALIDA ---
class UsuarioSalida(BaseModel):
    """Datos que se retornan al consultar un usuario. Nunca incluye password."""
    id_usuario: int
    nombre:     str
    correo:     str
    estatus:    bool
    rol:        str

class LoginSalida(BaseModel):
    """Login exitoso."""
    codigo:     int
    id_usuario: int
    nombre:     str
    estatus:    bool
    rol:        str

class Usuario(BaseModel):
    id_usuario: int
    nombre:     str
    correo:     str
    password:   str   # hash SHA-256, nunca se expone en salida
    estatus:    bool  # True=activo — sistema asigna True al registrarse
    rol:        str   # 'admin' | 'usuario' — sistema asigna 'usuario' al registrarse


# RECURSO 2: CATEGORÍAS
# --- ENTRADA ---
class CategoriaCrear(BaseModel):
    """Datos para crear categoría. El sistema asigna id_categoria y estado=True."""
    id_usuario:  int           = Field(..., gt=0)
    nombre:      str           = Field(..., min_length=1, description="Nombre no puede estar vacío")
    descripcion: Optional[str] = None

class CategoriaEditar(BaseModel):
    """Ambos campos opcionales: se actualiza solo lo que se manda."""
    nombre:      Optional[str] = Field(None, min_length=1)
    descripcion: Optional[str] = None

# --- SALIDA ---
class CategoriaSalida(BaseModel):
    """Representación de una categoría en respuestas."""
    id_categoria: int
    nombre:       str
    descripcion:  Optional[str]
    estado:       bool

class CategoriasCreadaSalida(Salida):
    """Respuesta al crear categoría, incluye el id generado."""
    id_categoria: int

class CategoriasSalida(Salida):
    """Respuesta con lista de categorías."""
    categorias: Optional[List[CategoriaSalida]] = None

# --- INTERNO ---
class Categoria(BaseModel):
    id_categoria: int
    id_usuario:   int
    nombre:       str
    descripcion:  Optional[str]
    estado:       bool