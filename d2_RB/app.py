import csv
import io
from datetime import datetime

import mysql.connector
from flask import Flask, Response, render_template, request, redirect, url_for

app = Flask(__name__)

# Conexión centralizada a MySQL (XAMPP - Puerto 3306)
def conectar():
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="",
        database="hospital"
    )

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

# MEJORA INDIVIDUAL
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

# RESUMEN ESTADISTICO (Rodrigo Burgos)
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

    # Un solo recorrido: clasifica cada expediente y va sumando los contadores
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

    # Completo = DUI validado. Todo lo demas cuenta como incompleto.
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
    )

# MEJORA INDIVIDUAL (Rodrigo Burgos): exportar el listado a CSV
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
    # El BOM al inicio hace que Excel abra bien las tildes
    return Response(
        "\ufeff" + salida.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=" + nombre_archivo},
    )

if __name__ == "__main__":
    app.run(debug=True)