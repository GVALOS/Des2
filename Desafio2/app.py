import mysql.connector
from flask import Flask, render_template, request, redirect, url_for

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

if __name__ == "__main__":
    app.run(debug=True)