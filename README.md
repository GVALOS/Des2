# Sistema de Expedientes Digitales: Hospital de Diagnóstico
 
## ¿Qué hace el sistema?
El sistema gestiona de forma digital los expedientes de los empleados del Hospital de Diagnóstico utilizando una base de datos relacional en MySQL. Permite registrar nuevos empleados con validaciones estrictas y control de duplicados, listar los registros unificando la información de ambas tablas mediante una consulta `JOIN`, buscar registros por texto, editar información, eliminar registros de forma segura asegurando la integridad referencial (en cascada), visualizar un reporte de detalle individual para cada expediente, generar un reporte estadístico completo (resumen) con repetición y decisión, y exportar los datos filtrados a formato CSV.
 
---
 
## ¿Cómo ejecutarlo desde cero?
 
1. **Iniciar el servidor MySQL:**
   * Abre el Panel de Control de **XAMPP** y pon en marcha el servicio **MySQL** (verificando que corra en el puerto por defecto **3306**).
 
2. **Crear la Base de Datos:**
   * Entra a **phpMyAdmin** (`http://localhost/phpmyadmin/`).
   * Importa el archivo `crear_bd.sql` incluido en el repositorio para generar la base de datos `hospital`, las tablas relacionadas y cargar los registros iniciales.
 
3. **Instalar las dependencias de Python:**
   * Abre una terminal en la carpeta del proyecto e instala los paquetes necesarios ejecutando:
     ```bash
     pip install -r requirements.txt
     ```
 
4. **Ejecutar la aplicación:**
   * Inicia el servidor Flask ejecutando:
     ```bash
     python app.py
     ```
 
5. **Abrir en el navegador:**
   * Ingresa a la siguiente URL completa para ver el sistema en funcionamiento:
     ```text
     [http://127.0.0.1:5000/empleados](http://127.0.0.1:5000/empleados)
     ```
   * O visita directamente el reporte estadístico en:
     ```text
     [http://127.0.0.1:5000/resumen](http://127.0.0.1:5000/resumen)
     ```
=======
# Gestión de Empleados y Documentos

## Descripción del proyecto

Este proyecto consiste en desarrollar un sistema web para gestionar empleados de un hospital y controlar el estado de validación de sus documentos (DUI). Utiliza MySQL para almacenar la información y Flask para mostrarla mediante una interfaz web.

## Programas utilizados

- **Python:** Desarrollo de la lógica del programa.
- **Flask:** Creación de rutas y conexión con las páginas HTML.
- **MySQL:** Almacenamiento de los datos.
- **mysql-connector-python:** Conexión entre Python y MySQL.
- **SQL:** Creación de tablas y consultas.
- **HTML:** Visualización de la información.

## Rutas del Sistema

* `/empleados`
  * **(GET):** Muestra el listado general de empleados con su respectivo estado de documento mediante un `LEFT JOIN`, e incluye la barra de búsqueda por nombre o número de DUI.

* `/empleados/nuevo`
  * **(GET y POST):** Formulario web para registrar un nuevo empleado y su documento asociado, con validación de campos obligatorios y control de duplicados de DUI.

* `/empleados/editar/<int:id>`
  * **(GET y POST):** Permite modificar los datos del empleado y su expediente documental de forma transaccional.

* `/empleados/eliminar/<int:id>`
  * **(POST):** Elimina un empleado de la base de datos y borra automáticamente sus documentos relacionados gracias a la regla `ON DELETE CASCADE`.

* `/empleados/detalle/<int:id>`
  * **(GET):** Muestra una tarjeta con la información detallada y ampliada de un expediente específico.

* `/resumen`
  * **(GET):** Ejecuta el reporte estadístico recorriendo todos los registros, clasificándolos con estructuras de decisión y mostrando contadores, porcentajes y alertas de avance.

* `/empleados/exportar`
  * **(GET):** Genera y descarga un archivo en formato CSV con el listado completo de expedientes filtrados y codificación UTF-8 con BOM compatible con Excel.

---

## Base de datos
La base de datos se denomina `hospital` (codificación `utf8mb4_unicode_ci`) y consta de dos tablas relacionadas:

### Tabla `empleados` (Tabla Principal):
* `id`: INT (Auto-incrementable, Clave Primaria)
* `nombre`: VARCHAR(100) (Obligatorio)
* `dui`: VARCHAR(10) (Obligatorio, Único para evitar duplicados)
* `perfil`: ENUM('medico', 'administrativo', 'enfermeria') (Obligatorio)

### Tabla `documentos` (Tabla Relacionada):
* `id`: INT (Auto-incrementable, Clave Primaria)
* `empleado_id`: INT (Obligatorio, Clave Foránea hacia `empleados.id` con `ON DELETE CASCADE`)
* `estado_dui`: ENUM('pendiente', 'validado', 'rechazado') (Por defecto 'pendiente')
* `observaciones`: VARCHAR(255) (Opcional)

---

## ¿Cómo funciona el resumen?
La ruta `/resumen` realiza un procesamiento analítico de los datos mediante un bucle `for` que recorre todas las filas obtenidas a través de la consulta `LEFT JOIN`. Dentro del bucle:

* Utiliza estructuras de decisión (`if` / `elif` / `else`) para clasificar el estado de cada expediente (`validado`, `pendiente`, `rechazado`, o `sin_registro`).
* Incrementa contadores numéricos independientes para cada categoría y almacena en una lista (`requieren_atencion`) aquellos expedientes que necesitan revisión o corrección.
* Agrupa los registros por perfil profesional utilizando diccionarios.
* Calcula los porcentajes globales de expedientes completos e incompletos y asigna dinámicamente un nivel de alerta visual (`alto`, `medio`, `bajo` o `vacio`) dependiendo del porcentaje de validación obtenido.

## Aportaciones:

### 1. Pedro Reyes
* **Estructura y diseño de la base de datos:** Lideró la arquitectura relacional del proyecto redactando el script SQL para la creación de la base de datos y sus dos tablas principales (`empleados` y `documentos`). Estableció la restricción de borrado en cascada (`ON DELETE CASCADE`) para garantizar la integridad referencial y prevenir registros huérfanos, incorporando también los datos iniciales de prueba.
* **Aportación personalizada:** Desarrolló el sistema de filtrado avanzado que permite segmentar el listado de expedientes de forma dinámica según el rol profesional (médicos, personal de enfermería o área administrativa).
**Mejora individual:** Desarrolló una funcionalidad para segmentar y filtrar el listado de empleados de forma dinámica según su categoría profesional (médicos, personal de enfermería o administrativos).
  

### 2. Gabriel Avalos
Implementé la conexión entre Flask y MySQL mediante la función `conectar()` y agregué las dependencias necesarias en `requirements.txt`.
Desarrollé la ruta `/empleados` utilizando `LEFT JOIN` para mostrar la información de los empleados junto con sus documentos.
Actualicé `empleados.html` para mostrar los datos de ambas tablas.
**Mejora individual:** Incorporé una búsqueda por nombre o número de DUI desde el listado de empleados. Si el campo está vacío, se muestran todos los empleados.

### 3. Pedro Valle
* **Gestión de ingresos y seguridad de formularios:** Habilitó el flujo de registro de nuevos colaboradores mediante la creación de rutas con soporte para peticiones HTTP y el diseño de la plantilla de captura. Aseguró la integridad de los datos empleando consultas parametrizadas para neutralizar cualquier riesgo de inyección SQL.
* **Aportación personalizada:** Programó la validación estricta en el servidor para bloquear el ingreso de números de DUI duplicados antes de que la información sea almacenada en la base de datos.
**Mejora individual:** Programó una validación rigurosa en el servidor para comprobar que el número de DUI ingresado no exista previamente en la base de datos, evitando registros repetidos.
  
### 4. Daniel Brizuela
* **Mantenimiento y operaciones críticas:** Diseñó los mecanismos seguros para modificar y dar de baja registros del sistema. Garantizó que las sentencias de actualización y eliminación incluyeran de forma obligatoria los filtros correspondientes, complementando la interfaz con alertas de confirmación en JavaScript para evitar borrados accidentales.
* **Aportación personalizada:** Construyó la vista de expediente detallado, ofreciendo una tarjeta informativa con la información ampliada e individual de cada empleado.
**Mejora individual:** Creó la ruta y la interfaz dedicada (`/empleados/detalle/<int:id>`) para consultar una tarjeta informativa completa y ampliada con la información específica de cada expediente.
  
### 5. Rodrigo Burgos
* **Análisis estadístico e identidad visual:** Unificó la línea gráfica de la aplicación a través de una hoja de estilos centralizada y programó la ruta de reportes analíticos utilizando estructuras de control y bucles para calcular porcentajes de avance y alertas de estado. Además, coordinó la redacción de la documentación oficial del proyecto.
* **Aportación personalizada:** Añadió la funcionalidad de exportación de datos a formato CSV con soporte de codificación UTF-8 (BOM), facilitando su apertura directa en herramientas de hoja de cálculo como Microsoft Excel.
**Mejora individual:** Incorporó la funcionalidad para descargar los expedientes filtrados en formato CSV, asegurando la codificación UTF-8 con BOM para una compatibilidad perfecta con Microsoft Excel.
