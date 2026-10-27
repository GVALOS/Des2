# Sistema de Expedientes Digitales: Hospital de Diagnóstico

## ¿Qué hace el sistema?
El sistema gestiona de forma digital los expedientes de los empleados del Hospital de Diagnóstico utilizando una base de datos relacional en MySQL. Permite registrar nuevos empleados con validaciones estrictas y control de duplicados, listar los registros unificando la información de ambas tablas mediante una consulta `JOIN`, buscar registros por texto, editar información, eliminar registros de forma segura asegurando la integridad referencial (en cascada), y visualizar un reporte de detalle individual para cada expediente.

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

## Estructura de la base de datos

La base de datos `hospital` contiene dos tablas:

**1. empleados:** Almacena el ID, nombre, DUI y perfil laboral. El DUI es único y los perfiles permitidos son `medico`, `administrativo` y `enfermeria`.

**2. documentos:** Contiene el ID, `empleado_id`, `estado_dui` y observaciones. Los estados permitidos son `pendiente`, `validado` y `rechazado`.

Ambas tablas se relacionan mediante la llave foránea `empleado_id`, que referencia a `empleados.id`. Se utiliza `ON DELETE CASCADE` para eliminar automáticamente los documentos relacionados cuando se elimina un empleado.

## Datos de prueba

El archivo `crear_bd.sql` inserta cinco empleados ficticios con sus respectivos documentos. Se utiliza `INSERT IGNORE` para evitar registros duplicados de empleados y `WHERE NOT EXISTS` para evitar duplicar registros documentales existentes.

## Conexión a MySQL

En `app.py` se implementó la función `conectar()` mediante `mysql-connector-python`, utilizando `localhost`, el usuario `root`, contraseña vacía y la base de datos `hospital`.

El archivo `requirements.txt` contiene las dependencias `flask` y `mysql-connector-python`.

## Consulta JOIN y listado

La ruta `/empleados` utiliza `LEFT JOIN` para relacionar las tablas `empleados` y `documentos` mediante `e.id = d.empleado_id`.

La consulta muestra el ID, nombre, DUI, perfil, estado del documento y observaciones. También permite visualizar empleados sin registros documentales asociados.

Los resultados se presentan en la plantilla `templates/empleados.html`.


## Ejecución del proyecto

1. Iniciar MySQL desde XAMPP.
2. Importar `crear_bd.sql` en phpMyAdmin.
3. Instalar las dependencias con `pip install -r requirements.txt`.
4. Ejecutar `python app.py`.
5. Abrir `http://127.0.0.1:5000/empleados` en el navegador.

## Aportaciones:
Pedro Reyes:

Gabriel Avalos:
Implementé la conexión entre Flask y MySQL mediante la función `conectar()` y agregué las dependencias necesarias en `requirements.txt`.
Desarrollé la ruta `/empleados` utilizando `LEFT JOIN` para mostrar la información de los empleados junto con sus documentos.
Actualicé `empleados.html` para mostrar los datos de ambas tablas.
**Mejora individual:** Incorporé una búsqueda por nombre o número de DUI desde el listado de empleados. Si el campo está vacío, se muestran todos los empleados.

Pedro Valle:

Daniel Brizuela:

Rodrigo Burgos: