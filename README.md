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