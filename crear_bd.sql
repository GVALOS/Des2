
-- ==================================================
-- PROYECTO: GESTION DE EMPLEADOS Y DOCUMENTOS
-- Archivo: crear_bd.sql
-- ==================================================

-- 1. CREAR LA BASE DE DATOS

CREATE DATABASE IF NOT EXISTS hospital
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE hospital;


-- 2. TABLA PRINCIPAL: EMPLEADOS

CREATE TABLE IF NOT EXISTS empleados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    dui VARCHAR(10) NOT NULL UNIQUE,
    perfil ENUM(
        'medico',
        'administrativo',
        'enfermeria'
    ) NOT NULL
) ENGINE=InnoDB;


-- 3. TABLA RELACIONADA: DOCUMENTOS

CREATE TABLE IF NOT EXISTS documentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empleado_id INT NOT NULL,
    estado_dui ENUM(
        'pendiente',
        'validado',
        'rechazado'
    ) NOT NULL DEFAULT 'pendiente',
    observaciones VARCHAR(255),

    CONSTRAINT fk_documentos_empleados
        FOREIGN KEY (empleado_id)
        REFERENCES empleados(id)
        ON DELETE CASCADE
) ENGINE=InnoDB;


-- 4. INSERTAR CINCO EMPLEADOS DE PRUEBA
-- Los datos son ficticios.

INSERT IGNORE INTO empleados (nombre, dui, perfil)
VALUES
    ('Ana Martinez', '00000001-0', 'medico'),
    ('Carlos Rivera', '00000002-0', 'enfermeria'),
    ('Maria Lopez', '00000003-0', 'administrativo'),
    ('Jose Hernandez', '00000004-0', 'medico'),
    ('Sofia Garcia', '00000005-0', 'enfermeria');


-- 5. INSERTAR UN REGISTRO DOCUMENTAL POR EMPLEADO
-- Se identifica a cada empleado mediante su DUI
-- para no depender de que sus ID comiencen en 1.

INSERT INTO documentos
    (empleado_id, estado_dui, observaciones)
SELECT
    e.id,
    datos.estado_dui,
    datos.observaciones
FROM empleados AS e
INNER JOIN (
    SELECT '00000001-0' AS dui,
           'validado' AS estado_dui,
           'DUI revisado' AS observaciones

    UNION ALL

    SELECT '00000002-0', 'pendiente',
           'Pendiente de verificacion'

    UNION ALL

    SELECT '00000003-0', 'validado',
           'Documentacion completa'

    UNION ALL

    SELECT '00000004-0', 'rechazado',
           'Requiere correccion'

    UNION ALL

    SELECT '00000005-0', 'pendiente',
           'Pendiente de revision'
) AS datos ON e.dui = datos.dui

WHERE NOT EXISTS (
    SELECT 1
    FROM documentos AS d
    WHERE d.empleado_id = e.id
);


-- 6. CONSULTA FINAL DE COMPROBACION

SELECT
    e.id,
    e.nombre,
    e.dui,
    e.perfil,
    d.estado_dui
FROM empleados AS e
LEFT JOIN documentos AS d
    ON e.id = d.empleado_id
ORDER BY e.id;