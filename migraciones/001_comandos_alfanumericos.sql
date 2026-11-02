
-- MIGRACION 001: CODIGOS ALFANUMERICOS
-- Base de datos destino: vehiculo_iot (AWS RDS)
-- Requiere respaldo previo y ventana de mantenimiento.
-- NO EJECUTAR HASTA VALIDAR EL PLAN DE MIGRACION.

USE vehiculo_iot;

-- 1. Actualizar el tipo de dato
ALTER TABLE comandos
    MODIFY COLUMN codigo VARCHAR(20) NOT NULL;

-- Conservar el SQL_MODE original de los procedimientos
SET @sql_mode_original = @@SESSION.sql_mode;

SET SESSION sql_mode =
'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- 2. Actualizar sp_crear_comando
DROP PROCEDURE IF EXISTS sp_crear_comando;

DELIMITER $$

CREATE PROCEDURE sp_crear_comando(
    IN p_id_vehiculo INT,
    IN p_nombre VARCHAR(60),
    IN p_codigo VARCHAR(20),
    IN p_descripcion VARCHAR(255)
)
BEGIN
    INSERT INTO comandos (
        id_vehiculo, nombre, codigo, descripcion
    )
    VALUES (
        p_id_vehiculo, p_nombre, p_codigo, p_descripcion
    );

    SELECT LAST_INSERT_ID() AS id_comando;
END$$

DELIMITER ;

-- 3. Actualizar sp_actualizar_comando
DROP PROCEDURE IF EXISTS sp_actualizar_comando;

DELIMITER $$

CREATE PROCEDURE sp_actualizar_comando(
    IN p_id_comando INT,
    IN p_nombre VARCHAR(60),
    IN p_codigo VARCHAR(20),
    IN p_descripcion VARCHAR(255),
    IN p_activo BOOLEAN
)
BEGIN
    UPDATE comandos
    SET nombre = p_nombre,
        codigo = p_codigo,
        descripcion = p_descripcion,
        activo = p_activo
    WHERE id_comando = p_id_comando;
END$$

DELIMITER ;

SET SESSION sql_mode = 'IGNORE_SPACE,NO_ENGINE_SUBSTITUTION';

-- 4. Actualizar sp_registrar_comando
DROP PROCEDURE IF EXISTS sp_registrar_comando;

DELIMITER $$

CREATE PROCEDURE sp_registrar_comando(
    IN p_id_vehiculo INT,
    IN p_nombre VARCHAR(60),
    IN p_descripcion VARCHAR(255),
    IN p_codigo VARCHAR(20)
)
BEGIN
    INSERT INTO comandos (
        id_vehiculo, nombre, descripcion, codigo
    )
    VALUES (
        p_id_vehiculo, p_nombre, p_descripcion, p_codigo
    );
END$$

DELIMITER ;

-- Restaurar la configuracion original de la sesion
SET SESSION sql_mode = @sql_mode_original;
