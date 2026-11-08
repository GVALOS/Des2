CREATE DATABASE IF NOT EXISTS hospital
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE hospital;

SET NAMES utf8mb4;

DROP TABLE IF EXISTS archivos;
DROP TABLE IF EXISTS documentos;
DROP TABLE IF EXISTS empleados;

CREATE TABLE empleados (
    id     INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    dui    VARCHAR(10)  NOT NULL,
    perfil ENUM('medico', 'administrativo', 'enfermeria') NOT NULL,
    CONSTRAINT uq_empleados_dui UNIQUE (dui)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE documentos (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    empleado_id         INT NOT NULL,
    estado_dui          ENUM('pendiente', 'validado', 'rechazado') NOT NULL DEFAULT 'pendiente',
    estado_antecedentes ENUM('pendiente', 'validado', 'rechazado') NOT NULL DEFAULT 'pendiente',
    estado_carnet       ENUM('pendiente', 'validado', 'rechazado') NOT NULL DEFAULT 'pendiente',
    observaciones       VARCHAR(255) NULL,
    CONSTRAINT fk_documentos_empleado
        FOREIGN KEY (empleado_id) REFERENCES empleados (id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE archivos (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    empleado_id       INT NOT NULL,
    tipo_documento    ENUM('dui', 'antecedentes', 'carnet') NOT NULL,
    nombre_original   VARCHAR(255) NOT NULL,
    contenido         LONGBLOB NOT NULL,
    version           INT UNSIGNED NOT NULL,
    fecha_vencimiento DATE NULL,
    fecha_subida      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_archivos_empleado
        FOREIGN KEY (empleado_id) REFERENCES empleados (id)
        ON DELETE CASCADE,
    CONSTRAINT uq_archivos_empleado_tipo_version
        UNIQUE (empleado_id, tipo_documento, version),
    CONSTRAINT chk_archivos_version CHECK (version >= 1),
    CONSTRAINT chk_archivos_dui_vencimiento
        CHECK (tipo_documento <> 'dui' OR fecha_vencimiento IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO empleados (id, nombre, dui, perfil) VALUES
    (1, 'Ana Lucía Martínez',     '01234567-8', 'medico'),
    (2, 'Carlos Eduardo Ramírez', '02345678-9', 'enfermeria'),
    (3, 'María Fernanda López',   '03456789-0', 'administrativo'),
    (4, 'José Roberto Hernández', '04567890-1', 'enfermeria'),
    (5, 'Sofía Alejandra Méndez', '05678901-2', 'medico');

INSERT INTO documentos
    (empleado_id, estado_dui, estado_antecedentes, estado_carnet, observaciones) VALUES
    (1, 'validado',  'validado',  'pendiente', NULL),
    (2, 'pendiente', 'pendiente', 'pendiente', 'Falta entregar todos los documentos.'),
    (3, 'rechazado', 'validado',  'validado',  'DUI ilegible, volver a subirlo.'),
    (4, 'validado',  'pendiente', 'rechazado', 'Carnet con fecha incorrecta.');