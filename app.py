import mysql.connector
from flask import Flask, render_template, request

app = Flask(__name__)

# Conexion base de datos
def conectar():
    return mysql.connector.connect(host="localhost", user="root", password="", database="hospital")

# Muestra los empleados con sus documentos y permite buscarlos
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
        parametro = "%" + busqueda + "%"
        cursor.execute(consulta, (parametro, parametro))
        empleados = cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()
    return render_template("empleados.html", empleados=empleados, busqueda=busqueda)

if __name__ == "__main__":
    app.run(debug=True)