
CREATE DATABASE IF NOT EXISTS hospital_tarea3
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE hospital_tarea3;

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(50) NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol ENUM('admin', 'consulta') NOT NULL DEFAULT 'consulta',
    activo TINYINT(1) NOT NULL DEFAULT 1,
    fecha_creacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_usuarios_usuario UNIQUE (usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS empleados (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    dui VARCHAR(10) NOT NULL,
    perfil ENUM('medico', 'administrativo', 'enfermeria') NOT NULL,
    observaciones VARCHAR(255) NULL,
    fecha_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_empleados_dui UNIQUE (dui)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS tipos_documento (
    codigo VARCHAR(30) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255) NULL,
    requiere_vencimiento TINYINT(1) NOT NULL DEFAULT 0,
    activo TINYINT(1) NOT NULL DEFAULT 1,
    orden INT NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS requisitos_perfil (
    perfil ENUM('medico', 'administrativo', 'enfermeria') NOT NULL,
    tipo_codigo VARCHAR(30) NOT NULL,
    PRIMARY KEY (perfil, tipo_codigo),
    CONSTRAINT fk_requisitos_tipo
        FOREIGN KEY (tipo_codigo) REFERENCES tipos_documento (codigo)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS estado_documentos (
    empleado_id INT NOT NULL,
    tipo_codigo VARCHAR(30) NOT NULL,
    estado ENUM('pendiente', 'en_revision', 'validado', 'rechazado') NOT NULL DEFAULT 'pendiente',
    observacion VARCHAR(255) NULL,
    actualizado_por INT NULL,
    fecha_actualizacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (empleado_id, tipo_codigo),
    CONSTRAINT fk_estado_empleado
        FOREIGN KEY (empleado_id) REFERENCES empleados (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_estado_tipo
        FOREIGN KEY (tipo_codigo) REFERENCES tipos_documento (codigo),
    CONSTRAINT fk_estado_usuario
        FOREIGN KEY (actualizado_por) REFERENCES usuarios (id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS archivos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empleado_id INT NOT NULL,
    tipo_codigo VARCHAR(30) NOT NULL,
    nombre_original VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    tamano_bytes INT UNSIGNED NOT NULL,
    contenido LONGBLOB NOT NULL,
    version INT UNSIGNED NOT NULL,
    fecha_vencimiento DATE NULL,
    fecha_subida DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    subido_por INT NULL,
    CONSTRAINT fk_archivos_empleado
        FOREIGN KEY (empleado_id) REFERENCES empleados (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_archivos_tipo
        FOREIGN KEY (tipo_codigo) REFERENCES tipos_documento (codigo),
    CONSTRAINT fk_archivos_usuario
        FOREIGN KEY (subido_por) REFERENCES usuarios (id)
        ON DELETE SET NULL,
    CONSTRAINT uq_archivos_empleado_tipo_version
        UNIQUE (empleado_id, tipo_codigo, version),
    CONSTRAINT chk_archivos_version CHECK (version >= 1),
    CONSTRAINT chk_archivos_dui_vencimiento
        CHECK (tipo_codigo <> 'dui' OR fecha_vencimiento IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS bitacora (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NULL,
    accion VARCHAR(40) NOT NULL,
    detalle VARCHAR(500) NOT NULL,
    fecha DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_bitacora_usuario
        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO usuarios (id, usuario, nombre, password_hash, rol) VALUES
    (1, 'admin', 'Administrador RR. HH.', 'pbkdf2:sha256:600000$Y7FBe3vcdpbO1sM5$1a56c1e0886fff8be038456b155ec76cdee83dc4cd5aed5462a64bfc0d108cfd', 'admin'),
    (2, 'consulta', 'Usuario de Consulta', 'pbkdf2:sha256:600000$aIlGUxfHPkJvaGhB$1591369d37d767f454a81d811780b4ae0d1d6216028b9d1e2ef0d5215028c3aa', 'consulta');

INSERT INTO tipos_documento (codigo, nombre, descripcion, requiere_vencimiento, orden) VALUES
    ('dui', 'DUI', 'Documento Único de Identidad, ambos lados (también funciona como NIT).', 1, 1),
    ('partida_nacimiento', 'Partida de nacimiento', 'Certificación reciente emitida por el registro familiar de la alcaldía.', 0, 2),
    ('fotografia', 'Fotografía', 'Fotografía reciente tamaño cédula, fondo blanco.', 0, 3),
    ('antecedentes', 'Antecedentes penales', 'Constancia de antecedentes penales vigente.', 1, 4),
    ('solvencia_pnc', 'Solvencia de la PNC', 'Constancia de antecedentes policiales emitida por la Policía Nacional Civil.', 1, 5),
    ('curriculum', 'Currículum vitae', 'Hoja de vida actualizada, de lo más reciente a lo más antiguo.', 0, 6),
    ('titulo_academico', 'Título y atestados académicos', 'Título universitario, técnico o de bachillerato según el puesto, y diplomas.', 0, 7),
    ('incorporacion_titulo', 'Incorporación de título extranjero', 'Solo si estudió fuera de El Salvador (incorporación ante MINEDUCYT).', 0, 8),
    ('titulo_especialidad', 'Título de especialidad', 'Especialidad o subespecialidad médica (si aplica).', 0, 9),
    ('servicio_social', 'Constancia de servicio social', 'Constancia de haber cumplido el año social.', 0, 10),
    ('referencias_laborales', 'Referencias laborales (2)', 'Dos cartas de referencia laboral firmadas y recientes.', 0, 11),
    ('referencias_personales', 'Referencias personales (2)', 'Dos cartas de referencia personal firmadas y recientes.', 0, 12),
    ('constancias_laborales', 'Constancias de servicio laboral', 'Constancias de trabajos anteriores con fechas y cargo (si aplica).', 0, 13),
    ('carnet_junta', 'Carnet de Junta de Vigilancia', 'JVPM para médicos / JVPE para enfermería.', 1, 14),
    ('solvencia_junta', 'Solvencia de anualidad de la Junta', 'Comprobante de pago de la anualidad de la Junta de Vigilancia.', 1, 15),
    ('soporte_vital', 'Certificación en soporte vital (BLS/ACLS)', 'Curso de reanimación cardiopulmonar vigente (si aplica).', 1, 16),
    ('certificado_salud', 'Certificado de salud', 'Certificado médico / exámenes de ingreso.', 1, 17),
    ('esquema_vacunacion', 'Esquema de vacunación', 'Hepatitis B, tétanos, influenza, entre otras.', 0, 18),
    ('afiliacion_isss', 'Tarjeta de afiliación ISSS', 'Carné o boleta de inscripción al Seguro Social.', 0, 19),
    ('afiliacion_afp', 'Constancia de AFP (NUP)', 'Carné o constancia con el Número Único Previsional.', 0, 20),
    ('cuenta_bancaria', 'Constancia de cuenta bancaria', 'Para el depósito del salario (opcional).', 0, 21),
    ('licencia_conducir', 'Licencia de conducir', 'Solo para puestos que conducen vehículos.', 1, 22);

INSERT INTO requisitos_perfil (perfil, tipo_codigo) VALUES
    ('medico', 'dui'), ('medico', 'partida_nacimiento'), ('medico', 'fotografia'),
    ('medico', 'antecedentes'), ('medico', 'solvencia_pnc'), ('medico', 'curriculum'),
    ('medico', 'titulo_academico'), ('medico', 'referencias_laborales'), ('medico', 'referencias_personales'),
    ('medico', 'certificado_salud'), ('medico', 'afiliacion_isss'), ('medico', 'afiliacion_afp'),
    ('medico', 'servicio_social'), ('medico', 'carnet_junta'), ('medico', 'solvencia_junta'),
    ('medico', 'esquema_vacunacion'),
    ('enfermeria', 'dui'), ('enfermeria', 'partida_nacimiento'), ('enfermeria', 'fotografia'),
    ('enfermeria', 'antecedentes'), ('enfermeria', 'solvencia_pnc'), ('enfermeria', 'curriculum'),
    ('enfermeria', 'titulo_academico'), ('enfermeria', 'referencias_laborales'), ('enfermeria', 'referencias_personales'),
    ('enfermeria', 'certificado_salud'), ('enfermeria', 'afiliacion_isss'), ('enfermeria', 'afiliacion_afp'),
    ('enfermeria', 'carnet_junta'), ('enfermeria', 'solvencia_junta'), ('enfermeria', 'esquema_vacunacion'),
    ('administrativo', 'dui'), ('administrativo', 'partida_nacimiento'), ('administrativo', 'fotografia'),
    ('administrativo', 'antecedentes'), ('administrativo', 'solvencia_pnc'), ('administrativo', 'curriculum'),
    ('administrativo', 'titulo_academico'), ('administrativo', 'referencias_laborales'), ('administrativo', 'referencias_personales'),
    ('administrativo', 'certificado_salud'), ('administrativo', 'afiliacion_isss'), ('administrativo', 'afiliacion_afp');

INSERT INTO empleados (id, nombre, dui, perfil, observaciones, fecha_registro) VALUES
    (1, 'Ana Lucía Martínez', '01234567-8', 'medico', NULL, '2026-08-03 08:30:00'),
    (2, 'Carlos Eduardo Ramírez', '02345678-9', 'enfermeria', 'Falta entregar todos los documentos.', '2026-08-10 10:15:00'),
    (3, 'María Fernanda López', '03456789-0', 'administrativo', 'DUI ilegible, volver a subirlo.', '2026-08-21 14:00:00'),
    (4, 'José Roberto Hernández', '04567890-1', 'enfermeria', 'Carnet con fecha incorrecta.', '2026-09-02 09:45:00'),
    (5, 'Sofía Alejandra Méndez', '05678901-2', 'medico', NULL, '2026-09-15 11:20:00'),
    (6, 'Luis Alberto Castillo', '06789012-3', 'administrativo', 'Expediente completo.', '2026-10-01 08:00:00'),
    (7, 'Gabriela Beatriz Flores', '07890123-4', 'enfermeria', NULL, '2026-10-20 13:30:00'),
    (8, 'Ricardo Antonio Portillo', '08901234-5', 'medico', 'Pendiente título de especialidad.', '2026-11-05 16:10:00');

SET @pdf = X'255044462D312E340A312030206F626A0A3C3C202F54797065202F436174616C6F67202F5061676573203220302052203E3E0A656E646F626A0A322030206F626A0A3C3C202F54797065202F5061676573202F4B696473205B33203020525D202F436F756E742031203E3E0A656E646F626A0A332030206F626A0A3C3C202F54797065202F50616765202F506172656E74203220302052202F4D65646961426F78205B30203020363132203739325D202F5265736F7572636573203C3C202F466F6E74203C3C202F4631203520302052203E3E203E3E202F436F6E74656E7473203420302052203E3E0A656E646F626A0A342030206F626A0A3C3C202F4C656E67746820313232203E3E0A73747265616D0A4254202F4631203230205466203732203730302054642028486F73706974616C20646520446961676E6F737469636F2920546A2030202D3330205464202F46312031342054662028446F63756D656E746F20646520707275656261202D20457870656469656E746573204469676974616C65732920546A2045540A656E6473747265616D0A656E646F626A0A352030206F626A0A3C3C202F54797065202F466F6E74202F53756274797065202F5479706531202F42617365466F6E74202F48656C766574696361203E3E0A656E646F626A0A787265660A3020360A303030303030303030302036353533352066200A30303030303030303039203030303030206E200A30303030303030303538203030303030206E200A30303030303030313135203030303030206E200A30303030303030323431203030303030206E200A30303030303030343134203030303030206E200A747261696C65720A3C3C202F53697A652036202F526F6F74203120302052203E3E0A7374617274787265660A3438340A2525454F460A';

INSERT INTO archivos
    (empleado_id, tipo_codigo, nombre_original, mime_type, tamano_bytes, contenido, version, fecha_vencimiento, fecha_subida, subido_por) VALUES
    (1, 'dui', 'dui_ana_martinez.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, '2031-02-15', '2026-08-04 09:00:00', 1),
    (1, 'antecedentes', 'antecedentes_ana.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, '2027-01-20', '2026-08-04 09:05:00', 1),
    (1, 'carnet_junta', 'jvpm_ana_martinez.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, '2026-12-01', '2026-08-05 10:00:00', 1),
    (1, 'curriculum', 'cv_ana_martinez.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, NULL, '2026-08-05 10:10:00', 1),
    (1, 'titulo_academico', 'titulo_doctorado_ana.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, NULL, '2026-08-05 10:20:00', 1),
    (3, 'dui', 'dui_maria_lopez.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, '2029-08-01', '2026-08-22 08:40:00', 1),
    (3, 'antecedentes', 'antecedentes_maria.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, '2027-02-10', '2026-08-22 08:45:00', 1),
    (4, 'dui', 'dui_jose_hernandez.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, '2030-04-04', '2026-09-03 09:00:00', 1),
    (4, 'carnet_junta', 'jvpe_jose_2025.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, '2025-06-30', '2026-09-03 09:10:00', 1),
    (4, 'carnet_junta', 'jvpe_jose_2026.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 2, '2026-09-30', '2026-09-20 15:00:00', 1),
    (5, 'dui', 'dui_sofia_mendez.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, '2026-10-01', '2026-09-16 08:00:00', 1),
    (6, 'dui', 'dui_luis_castillo.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, '2032-01-01', '2026-10-01 09:00:00', 1),
    (6, 'partida_nacimiento', 'partida_luis.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, NULL, '2026-10-01 09:05:00', 1),
    (6, 'antecedentes', 'antecedentes_luis.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, '2027-05-01', '2026-10-01 09:10:00', 1),
    (6, 'solvencia_pnc', 'solvencia_pnc_luis.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, '2027-04-15', '2026-10-01 09:15:00', 1),
    (6, 'curriculum', 'cv_luis_castillo.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, NULL, '2026-10-01 09:20:00', 1),
    (6, 'titulo_academico', 'titulo_luis.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, NULL, '2026-10-01 09:25:00', 1),
    (6, 'certificado_salud', 'certificado_salud_luis.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, '2027-08-01', '2026-10-01 09:30:00', 1),
    (6, 'afiliacion_isss', 'isss_luis.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, NULL, '2026-10-01 09:35:00', 1),
    (6, 'afiliacion_afp', 'afp_luis.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, NULL, '2026-10-01 09:40:00', 1),
    (6, 'fotografia', 'foto_luis.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, NULL, '2026-10-01 09:45:00', 1),
    (6, 'referencias_laborales', 'ref_laborales_luis.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, NULL, '2026-10-01 09:50:00', 1),
    (6, 'referencias_personales', 'ref_personales_luis.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, NULL, '2026-10-01 09:55:00', 1),
    (7, 'curriculum', 'cv_gabriela_flores.pdf', 'application/pdf', LENGTH(@pdf), @pdf, 1, NULL, '2026-10-21 10:00:00', 1);

INSERT INTO estado_documentos (empleado_id, tipo_codigo, estado, observacion, actualizado_por) VALUES
    (1, 'dui', 'validado', NULL, 1),
    (1, 'antecedentes', 'validado', NULL, 1),
    (1, 'carnet_junta', 'en_revision', NULL, NULL),
    (1, 'curriculum', 'validado', NULL, 1),
    (1, 'titulo_academico', 'validado', NULL, 1),
    (3, 'dui', 'rechazado', 'DUI ilegible, volver a subirlo.', 1),
    (3, 'antecedentes', 'validado', NULL, 1),
    (4, 'dui', 'validado', NULL, 1),
    (4, 'carnet_junta', 'rechazado', 'Carnet con fecha incorrecta.', 1),
    (5, 'dui', 'validado', NULL, 1),
    (6, 'dui', 'validado', NULL, 1),
    (6, 'partida_nacimiento', 'validado', NULL, 1),
    (6, 'antecedentes', 'validado', NULL, 1),
    (6, 'solvencia_pnc', 'validado', NULL, 1),
    (6, 'curriculum', 'validado', NULL, 1),
    (6, 'titulo_academico', 'validado', NULL, 1),
    (6, 'certificado_salud', 'validado', NULL, 1),
    (6, 'afiliacion_isss', 'validado', NULL, 1),
    (6, 'afiliacion_afp', 'validado', NULL, 1),
    (6, 'fotografia', 'validado', NULL, 1),
    (6, 'referencias_laborales', 'validado', NULL, 1),
    (6, 'referencias_personales', 'validado', NULL, 1),
    (7, 'curriculum', 'en_revision', NULL, NULL);
