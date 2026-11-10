import csv
import io
from datetime import datetime, date
from pathlib import Path

import mysql.connector
from flask import Flask, Response, render_template, request, redirect, url_for, send_file

app = Flask(__name__)

# Configuración de límites y restricciones de subida
TAMANO_MAXIMO_ARCHIVO = 512 * 1024  # 512 KB

EXTENSIONES_PERMITIDAS = {".pdf", ".doc", ".docx"}
TIPOS_DOCUMENTO = {"dui", "antecedentes", "carnet_junta"}

# Conexión centralizada a MySQL (XAMPP - Puerto 3306)
def conectar():
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="",
        database="hospital"
    )

# Función auxiliar para mostrar errores de subida con un botón de regreso amigable
def responder_error_subida(empleado_id, mensaje_error, codigo_estado=400):
    html_error = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>Error de Subida</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f8f9fa;
                margin: 0;
                padding: 40px;
            }}
            .container-error {{
                max-width: 600px;
                margin: 0 auto;
                padding: 30px;
                background-color: #ffffff;
                border-left: 5px solid #dc3545;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                border-radius: 6px;
            }}
            h2 {{
                color: #dc3545;
                margin-top: 0;
            }}
            p {{
                color: #333333;
                font-size: 16px;
            }}
            .btn-regresar {{
                display: inline-block;
                margin-top: 20px;
                padding: 10px 20px;
                background-color: #0d6efd;
                color: #ffffff;
                text-decoration: none;
                border-radius: 4px;
                font-weight: bold;
            }}
            .btn-regresar:hover {{
                background-color: #0b5ed7;
            }}
        </style>
    </head>
    <body>
        <div class="container-error">
            <h2>Error al procesar el archivo</h2>
            <p>{mensaje_error}</p>
            <a href="{url_for('listar_archivos_empleado', empleado_id=empleado_id)}" class="btn-regresar">
                &larr; Volver a la lista de archivos
            </a>
        </div>
    </body>
    </html>
    """
    return Response(html_error, status=codigo_estado, mimetype="text/html")

@app.route("/empleados")
def listar_empleados():
    busqueda = request.args.get("buscar", "").strip()
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    try:
        consulta = """
            SELECT e.id, e.nombre, e.dui, e.perfil, d.estado_dui, d.observaciones
            FROM empleados AS e
            LEFT JOIN documentos AS d ON e.id = d.empleado_id
            WHERE e.nombre LIKE %s OR e.dui LIKE %s
            ORDER BY e.id
        """
        parametro = f"%{busqueda}%"
        cursor.execute(consulta, (parametro, parametro))
        empleados = cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()
    return render_template("empleados.html", empleados=empleados, busqueda=busqueda)

@app.route("/empleados/nuevo", methods=["GET", "POST"])
def registrar_empleado():
    mensaje = None
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        dui = request.form.get("dui", "").strip()
        perfil = request.form.get("perfil", "").strip()
        estado_dui = request.form.get("estado_dui", "pendiente")
        observaciones = request.form.get("observaciones", "").strip()
        
        if not nombre or not dui or not perfil:
            mensaje = "Por favor, completa todos los campos obligatorios."
        else:
            conexion = conectar()
            cursor = conexion.cursor(dictionary=True)
            try:
                cursor.execute("SELECT id FROM empleados WHERE dui = %s", (dui,))
                if cursor.fetchone():
                    mensaje = "Error: El número de DUI ingresado ya se encuentra registrado."
                else:
                    cursor.execute(
                        "INSERT INTO empleados (nombre, dui, perfil) VALUES (%s, %s, %s)",
                        (nombre, dui, perfil)
                    )
                    empleado_id = cursor.lastrowid
                    cursor.execute(
                        "INSERT INTO documentos (empleado_id, estado_dui, observaciones) VALUES (%s, %s, %s)",
                        (empleado_id, estado_dui, observaciones)
                    )
                    conexion.commit()
                    return redirect(url_for("listar_empleados"))
            except Exception as e:
                conexion.rollback()
                mensaje = f"Error al procesar el registro: {e}"
            finally:
                cursor.close()
                conexion.close()
    return render_template("nuevo.html", mensaje=mensaje)

@app.route("/empleados/editar/<int:id>", methods=["GET", "POST"])
def editar_empleado(id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    error = ""
    
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        dui = request.form.get("dui", "").strip()
        perfil = request.form.get("perfil", "").strip()
        estado_dui = request.form.get("estado_dui", "pendiente")
        observaciones = request.form.get("observaciones", "").strip()
        
        if not nombre or not dui or not perfil:
            error = "Por favor, completa todos los campos obligatorios."
        else:
            try:
                cursor.execute(
                    "UPDATE empleados SET nombre = %s, dui = %s, perfil = %s WHERE id = %s",
                    (nombre, dui, perfil, id)
                )
                
                cursor.execute("SELECT id FROM documentos WHERE empleado_id = %s", (id,))
                if cursor.fetchone():
                    cursor.execute(
                        "UPDATE documentos SET estado_dui = %s, observaciones = %s WHERE empleado_id = %s",
                        (estado_dui, observaciones, id)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO documentos (empleado_id, estado_dui, observaciones) VALUES (%s, %s, %s)",
                        (id, estado_dui, observaciones)
                    )
                conexion.commit()
                return redirect(url_for("listar_empleados"))
            except Exception as e:
                conexion.rollback()
                error = f"Error al actualizar el registro: {e}"
                
    cursor.execute("""
        SELECT e.id, e.nombre, e.dui, e.perfil, d.estado_dui, d.observaciones
        FROM empleados e
        LEFT JOIN documentos d ON e.id = d.empleado_id
        WHERE e.id = %s
    """, (id,))
    empleado = cursor.fetchone()
    cursor.close()
    conexion.close()
    
    if not empleado:
        return "Empleado no encontrado", 404
        
    return render_template("editar.html", empleado=empleado, error=error)

@app.route("/empleados/eliminar/<int:id>", methods=["POST"])
def eliminar_empleado(id):
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("DELETE FROM empleados WHERE id = %s", (id,))
        conexion.commit()
    except Exception as e:
        conexion.rollback()
    finally:
        cursor.close()
        conexion.close()
    return redirect(url_for("listar_empleados"))

@app.route("/empleados/detalle/<int:id>")
def detalle_empleado(id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.id, e.nombre, e.dui, e.perfil, d.estado_dui, d.observaciones
        FROM empleados e
        LEFT JOIN documentos d ON e.id = d.empleado_id
        WHERE e.id = %s
    """, (id,))
    empleado = cursor.fetchone()
    cursor.close()
    conexion.close()
    
    if not empleado:
        return "Empleado no encontrado", 404
        
    return render_template("detalle.html", empleado=empleado)

def calcular_estado_archivo(version, max_version, fecha_vencimiento):
    if version < max_version:
        return "Obsoleto"
    elif fecha_vencimiento and fecha_vencimiento < date.today():
        return "Vencido"
    else:
        return "Vigente"

@app.route("/resumen")
def resumen():
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT e.id, e.nombre, e.perfil, d.estado_dui, d.observaciones
            FROM empleados AS e
            LEFT JOIN documentos AS d ON e.id = d.empleado_id
            ORDER BY e.id
        """)
        registros = cursor.fetchall()

        cursor.execute("""
            SELECT empleado_id, tipo_documento, version, fecha_vencimiento 
            FROM archivos
        """)
        todos_archivos = cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()

    total = len(registros)
    validados = 0
    pendientes = 0
    rechazados = 0
    sin_registro = 0
    por_perfil = {}
    requieren_atencion = []

    for r in registros:
        if r["estado_dui"] == "validado":
            validados += 1
        elif r["estado_dui"] == "pendiente":
            pendientes += 1
            requieren_atencion.append(r)
        elif r["estado_dui"] == "rechazado":
            rechazados += 1
            requieren_atencion.append(r)
        else:
            sin_registro += 1
            requieren_atencion.append(r)

        perfil = r["perfil"]
        por_perfil[perfil] = por_perfil.get(perfil, 0) + 1

    max_versiones_map = {}
    for a in todos_archivos:
        key = (a["empleado_id"], a["tipo_documento"])
        max_versiones_map[key] = max(max_versiones_map.get(key, 0), a["version"])

    conteo_archivos_estado = {"Vigente": 0, "Vencido": 0, "Obsoleto": 0}
    for a in todos_archivos:
        max_v = max_versiones_map.get((a["empleado_id"], a["tipo_documento"]), 1)
        estado_calc = calcular_estado_archivo(a["version"], max_v, a["fecha_vencimiento"])
        conteo_archivos_estado[estado_calc] += 1

    completos = validados
    incompletos = total - completos

    def porcentaje(parte):
        if total == 0:
            return 0
        return round(parte * 100 / total, 1)

    pct_completos = porcentaje(completos)
    pct_incompletos = porcentaje(incompletos)

    if total == 0:
        nivel = "vacio"
        alerta = "Todavia no hay empleados registrados."
    elif pct_completos >= 75:
        nivel = "alto"
        alerta = "La mayoria de los expedientes esta completa."
    elif pct_completos >= 40:
        nivel = "medio"
        alerta = "Hay una cantidad importante de expedientes por revisar."
    else:
        nivel = "bajo"
        alerta = "Menos de la mitad de los expedientes esta completa."

    return render_template(
        "resumen.html",
        total=total,
        validados=validados,
        pendientes=pendientes,
        rechazados=rechazados,
        sin_registro=sin_registro,
        completos=completos,
        incompletos=incompletos,
        pct_completos=pct_completos,
        pct_incompletos=pct_incompletos,
        pct_validados=porcentaje(validados),
        pct_pendientes=porcentaje(pendientes),
        pct_rechazados=porcentaje(rechazados),
        pct_sin_registro=porcentaje(sin_registro),
        nivel=nivel,
        alerta=alerta,
        por_perfil=por_perfil,
        requieren_atencion=requieren_atencion,
        conteo_archivos_estado=conteo_archivos_estado
    )

@app.route("/empleados/exportar")
def exportar_csv():
    busqueda = request.args.get("buscar", "").strip()
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT e.id, e.nombre, e.dui, e.perfil, d.estado_dui, d.observaciones
            FROM empleados AS e
            LEFT JOIN documentos AS d ON e.id = d.empleado_id
            WHERE e.nombre LIKE %s OR e.dui LIKE %s
            ORDER BY e.id
        """, (f"%{busqueda}%", f"%{busqueda}%"))
        filas = cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()

    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(["ID", "Nombre", "DUI", "Perfil", "Estado DUI", "Observaciones"])
    for f in filas:
        escritor.writerow([
            f["id"], f["nombre"], f["dui"], f["perfil"],
            f["estado_dui"] or "sin registro",
            f["observaciones"] or "",
        ])

    nombre_archivo = "empleados_" + datetime.now().strftime("%Y%m%d_%H%M") + ".csv"
    return Response(
        "\ufeff" + salida.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=" + nombre_archivo},
    )

@app.route("/empleados/<int:empleado_id>/archivos/subir", methods=["POST"])
def subir_archivo(empleado_id):
    archivo = request.files.get("archivo")
    if archivo is None or not archivo.filename or not archivo.filename.strip():
        return responder_error_subida(empleado_id, "Seleccione un archivo PDF o Word válido.", 400)

    nombre_original = archivo.filename.strip()
    if len(nombre_original) > 255 or "/" in nombre_original or "\\" in nombre_original:
        return responder_error_subida(empleado_id, "El nombre del archivo no es válido.", 400)

    extension = Path(nombre_original).suffix.lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        return responder_error_subida(empleado_id, "Solo se permiten archivos .pdf, .doc y .docx.", 400)

    contenido = archivo.stream.read(TAMANO_MAXIMO_ARCHIVO + 1)
    if not contenido:
        return responder_error_subida(empleado_id, "El archivo está vacío.", 400)
    if len(contenido) > TAMANO_MAXIMO_ARCHIVO:
        return responder_error_subida(empleado_id, "El archivo supera el tamaño máximo permitido de 512 KB.", 413)

    tipo_documento = request.form.get("tipo_documento", "").strip().lower()
    if tipo_documento not in TIPOS_DOCUMENTO:
        return responder_error_subida(empleado_id, "Tipo de documento no permitido.", 400)

    fecha_texto = request.form.get("fecha_vencimiento", "").strip()
    fecha_vencimiento = None
    if tipo_documento == "dui" and not fecha_texto:
        return responder_error_subida(empleado_id, "La fecha de vencimiento es obligatoria para el DUI.", 400)
    if fecha_texto:
        try:
            fecha_vencimiento = date.fromisoformat(fecha_texto)
        except ValueError:
            return responder_error_subida(empleado_id, "La fecha debe tener formato AAAA-MM-DD.", 400)

    conexion = None
    cursor = None
    try:
        conexion = conectar()
        cursor = conexion.cursor()

        cursor.execute(
            "SELECT id FROM empleados WHERE id = %s FOR UPDATE",
            (empleado_id,)
        )
        if cursor.fetchone() is None:
            conexion.rollback()
            return responder_error_subida(empleado_id, "El empleado no existe.", 404)

        cursor.execute(
            """SELECT COALESCE(MAX(version), 0) FROM archivos
               WHERE empleado_id = %s AND tipo_documento = %s""",
            (empleado_id, tipo_documento)
        )
        nueva_version = cursor.fetchone()[0] + 1

        cursor.execute(
            """INSERT INTO archivos
               (empleado_id, tipo_documento, nombre_original, contenido, version, fecha_vencimiento)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (empleado_id, tipo_documento, nombre_original, contenido, nueva_version, fecha_vencimiento)
        )

        cursor.execute("SELECT id FROM documentos WHERE empleado_id = %s", (empleado_id,))
        doc_existe = cursor.fetchone()

        if doc_existe:
            if tipo_documento == "dui":
                cursor.execute("UPDATE documentos SET estado_dui = 'validado' WHERE empleado_id = %s", (empleado_id,))
            elif tipo_documento == "antecedentes":
                cursor.execute("UPDATE documentos SET estado_antecedentes = 'validado' WHERE empleado_id = %s", (empleado_id,))
            elif tipo_documento == "carnet_junta":
                cursor.execute("UPDATE documentos SET estado_carnet = 'validado' WHERE empleado_id = %s", (empleado_id,))
        else:
            est_dui = 'validado' if tipo_documento == 'dui' else 'pendiente'
            est_ant = 'validado' if tipo_documento == 'antecedentes' else 'pendiente'
            est_car = 'validado' if tipo_documento == 'carnet_junta' else 'pendiente'
            cursor.execute("""
                INSERT INTO documentos (empleado_id, estado_dui, estado_antecedentes, estado_carnet)
                VALUES (%s, %s, %s, %s)
            """, (empleado_id, est_dui, est_ant, est_car))

        conexion.commit()

        return redirect(url_for('listar_archivos_empleado', empleado_id=empleado_id))

    except mysql.connector.Error:
        if conexion is not None:
            conexion.rollback()
            app.logger.exception("Error al guardar el archivo en MySQL")
        return responder_error_subida(empleado_id, "No se pudo guardar el archivo debido a un error en la base de datos.", 500)

    finally:
        if cursor is not None:
            cursor.close()
        if conexion is not None and conexion.is_connected():
            conexion.close()

@app.route("/empleados/<int:empleado_id>/archivos")
def listar_archivos_empleado(empleado_id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, nombre, dui FROM empleados WHERE id = %s", (empleado_id,))
        empleado = cursor.fetchone()
        if not empleado:
            return "Empleado no encontrado", 404

        cursor.execute("""
            SELECT estado_dui, estado_antecedentes, estado_carnet, observaciones 
            FROM documentos WHERE empleado_id = %s
        """, (empleado_id,))
        documentos_info = cursor.fetchone() or {
            "estado_dui": "pendiente", 
            "estado_antecedentes": "pendiente", 
            "estado_carnet": "pendiente", 
            "observaciones": ""
        }

        cursor.execute("""
            SELECT id, empleado_id, tipo_documento, nombre_original, version, fecha_vencimiento, fecha_subida
            FROM archivos
            WHERE empleado_id = %s
            ORDER BY tipo_documento, version DESC
        """, (empleado_id,))
        archivos = cursor.fetchall()

        cursor.execute("""
            SELECT tipo_documento, MAX(version) as max_v
            FROM archivos
            WHERE empleado_id = %s
            GROUP BY tipo_documento
        """, (empleado_id,))
        max_versiones = {row["tipo_documento"]: row["max_v"] for row in cursor.fetchall()}

        for arch in archivos:
            max_v = max_versiones.get(arch["tipo_documento"], 1)
            arch["estado_calculado"] = calcular_estado_archivo(
                arch["version"], max_v, arch["fecha_vencimiento"]
            )

    finally:
        cursor.close()
        conexion.close()

    return render_template("archivos_empleado.html", empleado=empleado, archivos=archivos, documentos_info=documentos_info)

@app.route("/archivos/descargar/<int:archivo_id>")
def descargar_archivo(archivo_id):
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT nombre_original, contenido 
            FROM archivos 
            WHERE id = %s
        """, (archivo_id,))
        archivo = cursor.fetchone()

        if not archivo or not archivo["contenido"]:
            return "Archivo no encontrado", 404

        nombre_original = archivo["nombre_original"]
        contenido_binario = archivo["contenido"]

    finally:
        cursor.close()
        conexion.close()

    return send_file(
        io.BytesIO(contenido_binario),
        as_attachment=True,
        download_name=nombre_original
    )

if __name__ == "__main__":
    app.run(debug=True)
