-- Crear DB --
CREATE DATABASE billety_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE billety_db;

-- =========== CREAR TABLAS ============= --
-- ── Usuarios ── --
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario  INT           NOT NULL AUTO_INCREMENT,
    nombre      VARCHAR(150)  NOT NULL,
    correo      VARCHAR(255)  NOT NULL,
    password    VARCHAR(255)  NOT NULL,
    estatus     BOOLEAN       NOT NULL DEFAULT TRUE,
    rol         VARCHAR(10)   NOT NULL DEFAULT 'usuario',
    PRIMARY KEY (id_usuario),
    UNIQUE KEY uk_correo (correo)
);
 
-- ── Categorías ─── --
CREATE TABLE IF NOT EXISTS categorias (
    id_categoria INT          NOT NULL AUTO_INCREMENT,
    id_usuario   INT          NOT NULL,
    nombre       VARCHAR(150) NOT NULL,
    descripcion  VARCHAR(300)     NULL,
    estado       BOOLEAN      NOT NULL DEFAULT TRUE,
    PRIMARY KEY (id_categoria),
    CONSTRAINT fk_cat_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuarios (id_usuario)
);
 
-- ── Planeación Mensual ── --
CREATE TABLE IF NOT EXISTS planeacion_mensual (
    id_planeacion    INT            NOT NULL AUTO_INCREMENT,
    id_usuario       INT            NOT NULL,
    mes              INT            NOT NULL,
    anio             INT            NOT NULL,
    ingreso_estimado DECIMAL(10,2)  NOT NULL DEFAULT 0.00,
    ingreso_real     DECIMAL(10,2)  NOT NULL DEFAULT 0.00,
    gasto_total      DECIMAL(10,2)  NOT NULL DEFAULT 0.00,
    meta_ahorro      DECIMAL(10,2)  NOT NULL DEFAULT 0.00,
    ahorro_real      DECIMAL(10,2)  NOT NULL DEFAULT 0.00,
    PRIMARY KEY (id_planeacion),
    CONSTRAINT fk_plan_usuario FOREIGN KEY (id_usuario)
        REFERENCES usuarios (id_usuario)
);
 
-- ── Movimientos ─── --
CREATE TABLE IF NOT EXISTS movimientos (
    id_movimiento   INT           NOT NULL AUTO_INCREMENT,
    id_usuario      INT           NOT NULL,
    id_categoria    INT           NOT NULL,
    id_planeacion   INT           NOT NULL,
    monto           DECIMAL(10,2) NOT NULL,
    tipo_movimiento VARCHAR(10)   NOT NULL,
    fecha           DATETIME      NOT NULL,
    descripcion     VARCHAR(300)      NULL,
    tipo_pago       VARCHAR(20)   NOT NULL,
    estatus         VARCHAR(15)   NOT NULL DEFAULT 'activo',
    PRIMARY KEY (id_movimiento),
    CONSTRAINT fk_mov_usuario    FOREIGN KEY (id_usuario)
        REFERENCES usuarios (id_usuario),
    CONSTRAINT fk_mov_categoria  FOREIGN KEY (id_categoria)
        REFERENCES categorias (id_categoria),
    CONSTRAINT fk_mov_planeacion FOREIGN KEY (id_planeacion)
        REFERENCES planeacion_mensual (id_planeacion)
);

-- =========== RESTRICCIONES (CHECKS) ============= --
-- Validación de Reglas de negocio de la BD --
ALTER TABLE usuarios
    ADD CONSTRAINT chk_rol
        CHECK (rol IN ('admin', 'usuario'));
 
ALTER TABLE planeacion_mensual
    ADD CONSTRAINT chk_mes
        CHECK (mes BETWEEN 1 AND 12),
    ADD CONSTRAINT chk_anio
        CHECK (anio > 0),
    ADD CONSTRAINT chk_ingreso_estimado
        CHECK (ingreso_estimado >= 0),
    ADD CONSTRAINT chk_meta_ahorro
        CHECK (meta_ahorro >= 0);
 
-- Unicidad: un usuario no puede tener dos planeaciones del mismo mes y año
ALTER TABLE planeacion_mensual
    ADD CONSTRAINT uk_usuario_mes_anio
        UNIQUE (id_usuario, mes, anio);
 
ALTER TABLE movimientos
    ADD CONSTRAINT chk_monto
        CHECK (monto > 0),
    ADD CONSTRAINT chk_tipo_movimiento
        CHECK (tipo_movimiento IN ('ingreso', 'gasto')),
    ADD CONSTRAINT chk_tipo_pago
        CHECK (tipo_pago IN ('efectivo', 'tarjeta_debito', 'tarjeta_credito')),
    ADD CONSTRAINT chk_estatus_mov
        CHECK (estatus IN ('activo', 'cancelado'));

-- =========== VISTAS ============= --
-- ── Vista: resumen financiero por usuario y mes ──
CREATE OR REPLACE VIEW vista_resumen_mensual AS
SELECT
    u.id_usuario,
    u.nombre                        AS usuario,
    p.mes,
    p.anio,
    p.ingreso_estimado,
    p.ingreso_real,
    p.gasto_total,
    p.meta_ahorro,
    p.ahorro_real,
    CASE
        WHEN p.meta_ahorro = 0 THEN NULL
        ELSE ROUND((p.ahorro_real / p.meta_ahorro) * 100, 2)
    END                             AS porcentaje_meta_cumplida
FROM planeacion_mensual p
JOIN usuarios u ON u.id_usuario = p.id_usuario;
 
-- ── Vista: movimientos activos con detalle ────────────────────────────────────
CREATE OR REPLACE VIEW vista_movimientos_activos AS
SELECT
    m.id_movimiento,
    u.nombre                        AS usuario,
    c.nombre                        AS categoria,
    m.monto,
    m.tipo_movimiento,
    m.fecha,
    m.descripcion,
    m.tipo_pago,
    m.estatus,
    p.mes,
    p.anio
FROM movimientos m
JOIN usuarios           u ON u.id_usuario    = m.id_usuario
JOIN categorias         c ON c.id_categoria  = m.id_categoria
JOIN planeacion_mensual p ON p.id_planeacion = m.id_planeacion
WHERE m.estatus = 'activo';
 
-- ── Vista: categorías activas por usuario ─────────────────────────────────────
CREATE OR REPLACE VIEW vista_categorias_activas AS
SELECT
    c.id_categoria,
    c.id_usuario,
    u.nombre    AS usuario,
    c.nombre    AS categoria,
    c.descripcion
FROM categorias c
JOIN usuarios u ON u.id_usuario = c.id_usuario
WHERE c.estado = TRUE;
 
-- ── Vista: usuarios activos ───────────────────────────────────────────────────
-- Lista de usuarios que pueden iniciar sesión (sin exponer password)
CREATE OR REPLACE VIEW vista_usuarios_activos AS
SELECT
    id_usuario,
    nombre,
    correo,
    rol
FROM usuarios
WHERE estatus = TRUE;

-- =========== CREAR ADMINISTRADOR ============= --
INSERT INTO usuarios (nombre, correo, password, estatus, rol)
VALUES (
    'Diego Ramirez',
    'daccram12@gmail.com',
    SHA2('papoisql', 256),
    TRUE,
    'admin'
);

-- Confirmar que las tablas se crearon correctamente
SHOW TABLES;
 
-- Confirmar que el admin quedó registrado
SELECT id_usuario, nombre, correo, estatus, rol FROM usuarios;