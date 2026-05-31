-- =============================================================================
-- Billety DB — Política de Seguridad
-- Script: billety_seguridad.sql
-- MySQL 8.0
-- Ejecutar DESPUÉS de haber ejecutado billety_db.sql
-- =============================================================================

USE billety_db;

-- =============================================================================
-- PASO 1: CREAR USUARIOS DE MYSQL POR ROL
-- Se crean dos usuarios correspondientes a los roles del sistema:
--   billety_admin   → acceso total (rol admin en la aplicación)
--   billety_usuario → acceso restringido sin DELETE (rol usuario en la app)
-- =============================================================================

-- !! IMPORTANTE: Cambia las contraseñas antes de ejecutar en producción !!

CREATE USER IF NOT EXISTS 'billety_admin'@'localhost'
    IDENTIFIED BY 'Admin.Billety123';

CREATE USER IF NOT EXISTS 'billety_usuario'@'localhost'
    IDENTIFIED BY 'Usuario.Billety123';


-- =============================================================================
-- PASO 2: ASIGNAR PRIVILEGIOS — ROL: admin
-- Acceso completo (SELECT, INSERT, UPDATE, DELETE) en todas las tablas
-- =============================================================================

GRANT SELECT, INSERT, UPDATE, DELETE
    ON billety_db.usuarios
    TO 'billety_admin'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
    ON billety_db.categorias
    TO 'billety_admin'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
    ON billety_db.movimientos
    TO 'billety_admin'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE
    ON billety_db.planeacion_mensual
    TO 'billety_admin'@'localhost';

-- Acceso de lectura a todas las vistas
GRANT SELECT ON billety_db.vista_usuarios_activos     TO 'billety_admin'@'localhost';
GRANT SELECT ON billety_db.vista_categorias_activas   TO 'billety_admin'@'localhost';
GRANT SELECT ON billety_db.vista_movimientos_activos  TO 'billety_admin'@'localhost';
GRANT SELECT ON billety_db.vista_resumen_mensual      TO 'billety_admin'@'localhost';


-- =============================================================================
-- PASO 3: ASIGNAR PRIVILEGIOS — ROL: usuario
-- Acceso restringido (SELECT, INSERT, UPDATE) — sin DELETE en ninguna tabla
-- Las bajas son lógicas: estatus = false / 'cancelado'
-- =============================================================================

GRANT SELECT, INSERT, UPDATE
    ON billety_db.usuarios
    TO 'billety_usuario'@'localhost';

GRANT SELECT, INSERT, UPDATE
    ON billety_db.categorias
    TO 'billety_usuario'@'localhost';

GRANT SELECT, INSERT, UPDATE
    ON billety_db.movimientos
    TO 'billety_usuario'@'localhost';

GRANT SELECT, INSERT, UPDATE
    ON billety_db.planeacion_mensual
    TO 'billety_usuario'@'localhost';

-- Acceso de lectura a las vistas
GRANT SELECT ON billety_db.vista_usuarios_activos     TO 'billety_usuario'@'localhost';
GRANT SELECT ON billety_db.vista_categorias_activas   TO 'billety_usuario'@'localhost';
GRANT SELECT ON billety_db.vista_movimientos_activos  TO 'billety_usuario'@'localhost';
GRANT SELECT ON billety_db.vista_resumen_mensual      TO 'billety_usuario'@'localhost';


-- =============================================================================
-- PASO 4: APLICAR PRIVILEGIOS
-- =============================================================================

FLUSH PRIVILEGES;


-- =============================================================================
-- VERIFICACIÓN
-- Confirmar que los usuarios y sus privilegios quedaron correctos
-- =============================================================================

-- Ver usuarios creados
SELECT user, host FROM mysql.user
WHERE user IN ('billety_admin', 'billety_usuario');

-- Ver privilegios de billety_admin
SHOW GRANTS FOR 'billety_admin'@'localhost';

-- Ver privilegios de billety_usuario
SHOW GRANTS FOR 'billety_usuario'@'localhost';
