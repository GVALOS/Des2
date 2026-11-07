# Módulo de Base de Datos y Estructura Relacional - Expedientes Digitales

Este módulo define la persistencia de datos relacional para el sistema de **Expedientes Digitales del Hospital de Diagnóstico**, construido con MySQL / MariaDB (compatible con XAMPP). Soporta la gestión de empleados, el estado de sus documentos administrativos y médicos, y el almacenamiento binario de archivos (`LONGBLOB`) con soporte completo para control de versiones y políticas de eliminación en cascada.

---

## Instrucciones de Configuración desde Cero

Para inicializar o restablecer la base de datos en tu entorno local:

1. Asegúrate de tener encendido **Apache** y **MySQL** desde el panel de control de XAMPP.
2. Abre tu navegador y accede a **phpMyAdmin** (`http://localhost/phpmyadmin/`).
3. Ve a la pestaña **Importar**.
4. Selecciona el archivo del script **`crear_bd.sql`** ubicado en la raíz del repositorio.
5. Haz clic en **Continuar** para ejecutar el script. Esto creará automáticamente la base de datos `hospital`, establecerá la codificación `utf8mb4` y cargará la estructura de tablas junto con los datos de prueba iniciales.

>**Nota importante sobre el tamaño de archivos:** El servidor MySQL por defecto limita el tamaño de los paquetes mediante la variable `max_allowed_packet` (suele venir en `1M`). Si necesitas subir archivos PDF o Word más pesados, asegúrate de modificar `max_allowed_packet=16M` (o el valor requerido) en tu archivo de configuración `my.ini` de XAMPP y reinicia el servicio de MySQL.

---

## Estructura del Esquema Relacional

La base de datos consta de tres tablas principales interrelacionadas mediante llaves foráneas (`FOREIGN KEY`) con borrado en cascada (`ON DELETE CASCADE`):

### 1. Tabla `empleados`
Almacena la información general del personal del hospital.

| Campo | Tipo de Dato | Restricciones | Descripción |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | `AUTO_INCREMENT`, `PRIMARY KEY` | Identificador único del empleado. |
| `nombre` | `VARCHAR(100)` | `NOT NULL` | Nombre completo del empleado. |
| `dui` | `VARCHAR(10)` | `NOT NULL`, `UNIQUE` | Número de Documento Único de Identidad. |
| `perfil` | `ENUM(...)` | `NOT NULL` | Rol del empleado (`medico`, `administrativo`, `enfermeria`). |

### 2. Tabla `documentos`
Controla el estatus de validación actual de los documentos requeridos por cada empleado.

| Campo | Tipo de Dato | Restricciones | Descripción |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | `AUTO_INCREMENT`, `PRIMARY KEY` | Identificador único del registro de documentos. |
| `empleado_id` | `INT` | `FOREIGN KEY` | Relación con la tabla `empleados` (Cascada en borrado). |
| `estado_dui` | `ENUM` | `DEFAULT 'pendiente'` | Estado de validación del DUI (`pendiente`, `validado`, `rechazado`). |
| `estado_antecedentes` | `ENUM` | `DEFAULT 'pendiente'` | Estado de antecedentes penales/policiales. |
| `estado_carnet` | `ENUM` | `DEFAULT 'pendiente'` | Estado del carnet institucional. |
| `observaciones` | `VARCHAR(255)` | `NULL` | Comentarios del administrador sobre los documentos. |

### 3. Tabla `archivos` (Gestión de Binarios y Versionado)
Almacena los archivos digitales subidos (PDF o Word) permitiendo conservar un historial completo de versiones sin sobrescribir los archivos anteriores.

| Campo | Tipo de Dato | Restricciones | Descripción |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | `AUTO_INCREMENT`, `PRIMARY KEY` | Identificador único del archivo almacenado. |
| `empleado_id` | `INT` | `FOREIGN KEY` | Relación con la tabla `empleados` (Cascada en borrado). |
| `tipo_documento`| `ENUM` | `NOT NULL` | Tipo de archivo (`dui`, `antecedentes`, `carnet`). |
| `nombre_original`| `VARCHAR(255)`| `NOT NULL` | Nombre con el que el usuario subió el archivo. |
| `contenido` | `LONGBLOB` | `NOT NULL` | Binario real del documento almacenado en la base de datos. |
| `version` | `INT UNSIGNED` | `NOT NULL` | Número de versión secuencial (inicia en 1). |
| `fecha_vencimiento`| `DATE` | `NULL` | Fecha límite de validez (Obligatoria para tipo `dui`). |
| `fecha_subida` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP`| Marca de tiempo exacta de la subida. |

---

##  Reglas de Integridad y Restricciones

* **Borrado en Cascada (`ON DELETE CASCADE`):** Si un registro de un empleado es eliminado de la tabla `empleados`, todas sus filas asociadas en `documentos` y todos sus archivos históricos en `archivos` se eliminan automáticamente de la base de datos, previniendo registros huérfanos.
* **Restricción de Versionado Único (`uq_archivos_empleado_tipo_version`):** Llave única compuesta por `(empleado_id, tipo_documento, version)` que garantiza que no puedan existir dos archivos del mismo tipo y con el mismo número de versión para un mismo empleado.
* **Control de Versiones (`chk_archivos_version`):** Validación a nivel de base de datos que asegura que el número de versión sea siempre mayor o igual a 1 (`version >= 1`).
* **Vencimiento Obligatorio para DUI (`chk_archivos_dui_vencimiento`):** Restricción lógica integrada mediante `CHECK` que obliga a que si el `tipo_documento` es `'dui'`, la `fecha_vencimiento` no pueda ser nula (`IS NOT NULL`).
