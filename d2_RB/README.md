# Expedientes Digitales del Hospital de Diagnóstico

Aplicación web hecha con Flask y MySQL para llevar el control de los expedientes de los empleados de un hospital. Permite registrar, buscar, editar y eliminar empleados, ver el estado de su DUI y sacar un resumen con porcentajes de cuántos expedientes están completos.

## Qué necesitas instalado

- Python 3.10 o más reciente
- XAMPP (solo el módulo de MySQL hace falta)
- Git

## Cómo correrlo desde cero

1. Clona el repositorio y entra a la carpeta que se crea:

```powershell
git clone https://github.com/GVALOS/D2.git
cd D2
```

2. Crea y activa un entorno virtual:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Instala las dependencias:

```powershell
pip install flask mysql-connector-python
```

4. Abre el panel de XAMPP y arranca MySQL (puerto 3306).

5. Crea la base de datos. Entra a http://localhost/phpmyadmin, ve a la pestaña **Importar** y sube el archivo `crear_bd.sql`. También puedes pegar su contenido en la pestaña **SQL**. El script crea la base `hospital`, las dos tablas y cinco empleados de ejemplo.

6. Arranca la aplicación:

```powershell
python app.py
```

7. Abre http://127.0.0.1:5000/empleados en el navegador.

La conexión está en la función `conectar()` de `app.py` y asume usuario `root` sin contraseña, que es lo que trae XAMPP por defecto. Si tu MySQL tiene otra configuración, cámbiala ahí.

## Estructura de archivos

```
.
├── app.py              rutas de Flask y conexión a MySQL
├── crear_bd.sql        script para crear la base de datos y los datos de ejemplo
├── README.md
├── static/
│   └── style.css       estilos de todas las páginas
└── templates/
    ├── empleados.html  listado y búsqueda
    ├── nuevo.html      formulario de registro
    ├── editar.html     formulario de edición
    ├── detalle.html    vista ampliada de un expediente
    └── resumen.html    estadísticas
```

Flask busca las plantillas en `templates/` y los estilos en `static/`, así que los archivos tienen que estar en esas carpetas con esos nombres.

## Rutas

| Ruta | Qué hace |
|---|---|
| `/empleados` | Lista los empleados y permite buscar por nombre o DUI |
| `/empleados/nuevo` | Registra un empleado y su documento |
| `/empleados/editar/<id>` | Edita los datos del empleado y el estado de su DUI |
| `/empleados/eliminar/<id>` | Elimina al empleado (y su documento) |
| `/empleados/detalle/<id>` | Muestra el expediente completo |
| `/resumen` | Estadísticas de los expedientes |
| `/empleados/exportar` | Descarga el listado en CSV |

## Base de datos y el JOIN

Hay dos tablas. `empleados` guarda nombre, DUI (único) y perfil. `documentos` guarda el estado del DUI y las observaciones, y apunta al empleado con la columna `empleado_id`. La llave foránea tiene `ON DELETE CASCADE`, de modo que al borrar un empleado se borra también su documento.

Para mostrar todo junto en una sola tabla usamos un `LEFT JOIN`:

```sql
SELECT e.id, e.nombre, e.dui, e.perfil, d.estado_dui, d.observaciones
FROM empleados AS e
LEFT JOIN documentos AS d ON e.id = d.empleado_id
```

Se usa `LEFT JOIN` y no `INNER JOIN` por una razón práctica: si un empleado existe pero todavía no tiene fila en `documentos`, con `INNER JOIN` desaparecería del listado. Con `LEFT JOIN` aparece igual y sus columnas de documento llegan vacías (`NULL`), que la página muestra como "Sin registro".

## Resumen y exportación

La página `/resumen` recorre todos los expedientes con un solo `for` y va sumando contadores. Un expediente cuenta como completo cuando su DUI está validado; pendiente, rechazado o sin documento cuentan como incompleto. Con esos contadores se calculan los porcentajes y se muestra un mensaje de color según el avance: verde si hay 75% o más de expedientes completos, naranja entre 40% y 75%, rojo por debajo de 40%.

El botón **Exportar a CSV** del listado descarga los empleados con las mismas columnas de la tabla. Si hay una búsqueda activa, exporta solo los resultados filtrados. El archivo se abre bien en Excel, con tildes incluidas.

## Aportes del equipo

Falta completar con los usuarios de GitHub y las tareas de cada quien antes de entregar.

| Integrante | Usuario de GitHub | Aporte |
|---|---|---|
| Daniel Brizuela | (completar) | (completar) |
| (completar) | (completar) | (completar) |
| (completar) | (completar) | (completar) |
| (completar) | (completar) | (completar) |
| Rodrigo Burgos | (completar) | Ruta `/resumen` con bucles, condicionales y contadores; hoja de estilos `static/style.css`; README; exportación a CSV |
