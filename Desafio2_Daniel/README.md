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