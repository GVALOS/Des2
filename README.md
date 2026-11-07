
# Módulo de Base de Datos y Estructura Relacional - Expedientes Digitales

Este módulo define la persistencia de datos relacional para el sistema de **Expedientes Digitales del Hospital de Diagnóstico**, construido con MySQL / MariaDB (compatible con XAMPP). Soporta la gestión de empleados, el estado de sus documentos administrativos y médicos, y el almacenamiento binario de archivos (`LONGBLOB`) con soporte para control de versiones y eliminación en cascada.

---

## Instrucciones de Configuración desde Cero

Para inicializar o restablecer la base de datos en tu entorno local:

1. Asegúrate de tener encendido **Apache** y **MySQL** desde el panel de control de XAMPP.
2. Abre tu navegador y accede a **phpMyAdmin** (`http://localhost/phpmyadmin/`).
3. Ve a la pestaña **Importar**.
4. Selecciona el archivo **`crear_bd.sql`** ubicado en el repositorio.
5. Haz clic en **Continuar** para ejecutar el script. Esto creará la base de datos `hospital`, establecerá la codificación `utf8mb4` y cargará las tablas junto con los datos de prueba iniciales.

**Importante:** El script contiene instrucciones `DROP TABLE`, por lo que volver a importarlo eliminará los registros existentes de esas tablas.

> **Nota sobre el tamaño de archivos:** MySQL limita el tamaño de los paquetes mediante `max_allowed_packet`, cuyo valor depende de la configuración del servidor. Si necesitas archivos más pesados, puedes configurar `max_allowed_packet=16M` en `my.ini` de XAMPP y reiniciar MySQL. También debes aumentar el límite establecido en Flask.

---

## Estructura del Esquema Relacional

La base de datos consta de tres tablas relacionadas mediante llaves foráneas (`FOREIGN KEY`) con borrado en cascada (`ON DELETE CASCADE`).

### 1. Tabla `empleados`

Almacena la información general del personal del hospital.

| Campo | Tipo de dato | Restricciones | Descripción |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | `AUTO_INCREMENT`, `PRIMARY KEY` | Identificador único del empleado. |
| `nombre` | `VARCHAR(100)` | `NOT NULL` | Nombre completo del empleado. |
| `dui` | `VARCHAR(10)` | `NOT NULL`, `UNIQUE` | Documento Único de Identidad. |
| `perfil` | `ENUM` | `NOT NULL` | Rol: `medico`, `administrativo` o `enfermeria`. |

### 2. Tabla `documentos`

Controla el estado de validación de los documentos requeridos por cada empleado.

| Campo | Tipo de dato | Restricciones | Descripción |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | `AUTO_INCREMENT`, `PRIMARY KEY` | Identificador único del registro. |
| `empleado_id` | `INT` | `FOREIGN KEY`, `NOT NULL` | Relación con `empleados`, con borrado en cascada. |
| `estado_dui` | `ENUM` | `DEFAULT 'pendiente'` | Estado: `pendiente`, `validado` o `rechazado`. |
| `estado_antecedentes` | `ENUM` | `DEFAULT 'pendiente'` | Estado de antecedentes. |
| `estado_carnet` | `ENUM` | `DEFAULT 'pendiente'` | Estado del carnet institucional. |
| `observaciones` | `VARCHAR(255)` | `NULL` | Comentarios sobre los documentos. |

### 3. Tabla `archivos` (Gestión de Binarios y Versionado)

Almacena archivos PDF y Word en MySQL, conservando sus versiones anteriores.

| Campo | Tipo de dato | Restricciones | Descripción |
| :--- | :--- | :--- | :--- |
| `id` | `INT` | `AUTO_INCREMENT`, `PRIMARY KEY` | Identificador único del archivo. |
| `empleado_id` | `INT` | `FOREIGN KEY`, `NOT NULL` | Relación con `empleados`, con borrado en cascada. |
| `tipo_documento` | `ENUM` | `NOT NULL` | `dui`, `antecedentes` o `carnet`. |
| `nombre_original` | `VARCHAR(255)` | `NOT NULL` | Nombre original del archivo. |
| `contenido` | `LONGBLOB` | `NOT NULL` | Contenido binario del documento. |
| `version` | `INT UNSIGNED` | `NOT NULL` | Número de versión, iniciando en 1. |
| `fecha_vencimiento` | `DATE` | `NULL` | Fecha de vencimiento, obligatoria para DUI. |
| `fecha_subida` | `DATETIME` | `DEFAULT CURRENT_TIMESTAMP` | Fecha y hora de subida. |

---

## Reglas de Integridad y Restricciones

- **Borrado en cascada (`ON DELETE CASCADE`):** Al eliminar un empleado, se eliminan automáticamente sus registros relacionados en `documentos` y `archivos`.
- **Versionado único (`uq_archivos_empleado_tipo_version`):** Impide duplicar una combinación de empleado, tipo de documento y número de versión.
- **Control de versiones (`chk_archivos_version`):** Garantiza que `version >= 1`.
- **Vencimiento obligatorio del DUI (`chk_archivos_dui_vencimiento`):** Exige que los archivos de tipo `dui` tengan una fecha de vencimiento.

---

## Backend de Subida de Archivos (Integrante 2)

Se implementó en `app.py` la ruta `POST /empleados/<int:empleado_id>/archivos/subir`, utilizando `request.files` para recibir archivos PDF y Word.

El formulario debe utilizar `method="POST"` y `enctype="multipart/form-data"` para enviar los documentos correctamente.

### Validación de Archivos

Antes de guardar, el sistema verifica:

- Que se haya seleccionado un archivo.
- Que la extensión sea `.pdf`, `.doc` o `.docx`, sin distinguir mayúsculas.
- Que el archivo no esté vacío ni supere **512 KB**.
- Que el tipo de documento sea `dui`, `antecedentes` o `carnet`.
- Que los archivos DUI incluyan una fecha de vencimiento válida.

Los archivos que cumplen las validaciones se almacenan en la columna `contenido` de tipo `LONGBLOB` de MySQL.

### Versionado Automático

Se utiliza `SELECT COALESCE(MAX(version), 0)` para obtener la última versión registrada según el empleado y el tipo de documento.

La nueva versión se calcula sumando 1 al resultado, iniciando en 1 cuando no existen versiones anteriores.

Cada documento se guarda mediante `INSERT INTO`, conservando los registros y las versiones anteriores.

### Manejo de Errores

El backend utiliza consultas SQL parametrizadas, `commit()`, `rollback()` y cierre de conexiones mediante `finally`.

También devuelve mensajes de error HTTP:

- `400`: archivo o datos inválidos.
- `404`: empleado inexistente.
- `413`: tamaño máximo excedido.
- `500`: error al almacenar el archivo en MySQL.

Estas validaciones permiten evitar el almacenamiento de archivos inválidos y revertir operaciones fallidas.
