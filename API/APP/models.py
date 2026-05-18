from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
from decimal import Decimal

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

# RECURSO 3: MOVIMIENTOS
# --- ENTRADA ---
class MovimientoRegistrar(BaseModel):
    id_usuario:      int            = Field(..., gt=0)
    id_categoria:    int            = Field(..., gt=0)
    monto:           Decimal        = Field(..., gt=0, description="Debe ser mayor a 0")
    tipo_movimiento: str            = Field(..., pattern="^(ingreso|gasto)$")
    fecha:           datetime       = Field(..., description="No puede ser futura")
    descripcion:     Optional[str]  = None
    tipo_pago:       str            = Field(..., pattern="^(efectivo|tarjeta_debito|tarjeta_credito)$")

    from pydantic import model_validator
    @model_validator(mode='after')
    def validar_fecha_no_futura(self):
        fecha = self.fecha
        if fecha.tzinfo is not None:
            if fecha > datetime.now(timezone.utc):
                raise ValueError("La fecha del movimiento no puede ser futura")
        else:
            if fecha > datetime.now():
                raise ValueError("La fecha del movimiento no puede ser futura")
        return self

class MovimientoEditar(BaseModel):
    id_categoria:    Optional[int]     = Field(None, gt=0)
    monto:           Optional[Decimal] = Field(None, gt=0)
    tipo_movimiento: Optional[str]     = Field(None, pattern="^(ingreso|gasto)$")
    descripcion:     Optional[str]     = None
    tipo_pago:       Optional[str]     = Field(None, pattern="^(efectivo|tarjeta_debito|tarjeta_credito)$")

class MovimientoCancelar(BaseModel):
    motivo: Optional[str] = None

# --- SALIDA ---
class MovimientoSalida(BaseModel):
    id_movimiento:   int
    id_usuario:      int
    id_categoria:    int
    id_planeacion:   int
    monto:           Decimal
    tipo_movimiento: str
    fecha:           datetime
    descripcion:     Optional[str]
    tipo_pago:       str
    estatus:         str

class MovimientoRegistradoSalida(Salida):
    id_movimiento: int

class MovimientoDetalleSalida(Salida):
    movimiento: Optional[MovimientoSalida] = None

class MovimientosSalida(Salida):
    movimientos: Optional[List[MovimientoSalida]] = None

# --- INTERNO ---
class Movimiento(BaseModel):
    id_movimiento:   int
    id_usuario:      int
    id_categoria:    int
    id_planeacion:   int
    monto:           Decimal
    tipo_movimiento: str
    fecha:           datetime
    descripcion:     Optional[str]
    tipo_pago:       str
    estatus:         str  # 'activo' | 'cancelado'

# RECURSO 4: PLANEACIÓN FINANCIERA MENSUAL
# --- ENTRADA ---
class PlaneacionCrear(BaseModel):
    id_usuario:       int            = Field(..., gt=0)
    mes:              int            = Field(..., ge=1, le=12)
    anio:             int            = Field(..., gt=0)
    ingreso_estimado: Optional[Decimal] = Field(None, gt=0)
    meta_ahorro:      Optional[Decimal] = Field(None, ge=0)

class PlaneacionEditar(BaseModel):
    ingreso_estimado: Optional[Decimal] = Field(None, gt=0)
    meta_ahorro:      Optional[Decimal] = Field(None, ge=0)

# --- SALIDA ---
class PlaneacionSalida(BaseModel):
    id_planeacion:    int
    id_usuario:       int
    mes:              int
    anio:             int
    ingreso_estimado: Decimal
    ingreso_real:     Decimal
    gasto_total:      Decimal
    meta_ahorro:      Decimal
    ahorro_real:      Decimal

class PlaneacionCreadaSalida(Salida):
    id_planeacion: int

class PlaneacionDetalleSalida(Salida):
    planeacion: Optional[PlaneacionSalida] = None

class PlaneacionesSalida(Salida):
    planeaciones: Optional[List[PlaneacionSalida]] = None

# --- INTERNO ---
class Planeacion(BaseModel):
    id_planeacion:    int
    id_usuario:       int
    mes:              int
    anio:             int
    ingreso_estimado: Decimal
    ingreso_real:     Decimal
    gasto_total:      Decimal
    meta_ahorro:      Decimal
    ahorro_real:      Decimal
