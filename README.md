Gestión de Empleados y Documentos

Descripción del proyecto

Este proyecto consiste en la creación de una base de datos en MySQL para gestionar empleados de un hospital y llevar el control del estado de validación de sus documentos de identidad (DUI).

La base de datos permite registrar empleados, asignarles un perfil laboral y almacenar observaciones relacionadas con la revisión de sus documentos.

Tecnologías utilizadas

MySQL: Sistema de gestión de bases de datos.

SQL: Lenguaje utilizado para crear las tablas, insertar datos y consultar información.

InnoDB: Motor de almacenamiento que permite establecer relaciones entre tablas y mantener la integridad referencial.

UTF-8 (utf8mb4): Codificación que permite almacenar caracteres especiales.

Estructura de la base de datos

La base de datos se llama hospital y contiene dos tablas principales:

1. Tabla empleados

Almacena la información de los empleados registrados en el hospital.

Campo

Tipo de dato

Descripción

id

INT

Identificador único autoincremental del empleado.

nombre

VARCHAR(100)

Nombre completo del empleado.

dui

VARCHAR(10)

Número de DUI, obligatorio y único.

perfil

ENUM

Perfil laboral del empleado.

Los perfiles permitidos son:

medico

administrativo

enfermeria

El campo dui tiene una restricción UNIQUE, que evita registrar dos empleados con el mismo número de DUI.

2. Tabla documentos

Almacena el estado de validación del DUI y las observaciones correspondientes a cada empleado.

Campo

Tipo de dato

Descripción

id

INT

Identificador único del registro documental.

empleado_id

INT

Identificador del empleado al que pertenece el registro.

estado_dui

ENUM

Estado de validación del documento.

observaciones

VARCHAR(255)

Comentarios sobre la revisión del documento.

Los estados permitidos son:

pendiente: El documento está pendiente de revisión.

validado: El documento ha sido revisado y validado.

rechazado: El documento requiere correcciones.

Por defecto, el estado del DUI es pendiente cuando no se especifica otro valor.

Relación entre las tablas

La tabla documentos se relaciona con la tabla empleados mediante el campo empleado_id, que funciona como clave foránea y referencia al campo id de la tabla empleados.

La restricción ON DELETE CASCADE permite que, al eliminar un empleado, también se eliminen automáticamente sus registros documentales relacionados.

Datos de prueba

El script inserta cinco empleados ficticios con diferentes perfiles laborales y crea un registro documental para cada uno.

Empleado

Perfil

Estado del DUI

Ana Martinez

Médico

Validado

Carlos Rivera

Enfermería

Pendiente

Maria Lopez

Administrativo

Validado

Jose Hernandez

Médico

Rechazado

Sofia Garcia

Enfermería

Pendiente

Las observaciones se utilizan para indicar si el documento fue revisado, si está pendiente de verificación o si requiere correcciones.

El comando INSERT IGNORE evita insertar un empleado cuando existe un conflicto con una restricción de la tabla, como un DUI duplicado.

Para los documentos, se utiliza una consulta con INNER JOIN para relacionar cada DUI con su empleado correspondiente. Además, WHERE NOT EXISTS evita crear otro registro documental si el empleado ya tiene uno.

Consulta final de comprobación

El script ejecuta una consulta que combina las tablas empleados y documentos mediante un LEFT JOIN.

Esta consulta muestra:

El identificador del empleado.

Su nombre.

Su DUI.

Su perfil laboral.

El estado de validación de su DUI.

Los resultados se ordenan por el identificador del empleado mediante ORDER BY e.id.

El uso de LEFT JOIN permite mostrar todos los empleados, incluso si alguno todavía no tiene un registro en la tabla documentos.

Cómo ejecutar el archivo

Abre MySQL Workbench o un cliente compatible con MySQL.

Abre el archivo crear_bd.sql.

Ejecuta el script completo.

Comprueba que la base de datos hospital y las tablas empleados y documentos se hayan creado correctamente.

Revisa los resultados de la consulta final para verificar los registros insertados.