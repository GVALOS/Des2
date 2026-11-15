"""
Expedientes Digitales del Personal - Hospital de Diagnóstico (El Salvador)
Flask + MySQL / MariaDB (XAMPP)
"""
import csv
import io
import math
import re
import secrets
import unicodedata
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from functools import wraps
from pathlib import Path
from urllib.parse import urlencode

import click
import mysql.connector
from flask import (Flask, Response, abort, flash, g, redirect, render_template,
                   request, send_file, session, url_for)
from markupsafe import Markup
from werkzeug.exceptions import HTTPException
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config.update(
    SECRET_KEY="cambia-esta-clave-por-una-frase-larga-y-secreta",
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,          # límite de toda la petición
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# Conexión a MySQL (XAMPP - puerto 3306)
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",
    "database": "hospital_tarea3",
}


TAMANO_MAXIMO_ARCHIVO = 512 * 1024  # 512 KB

FIRMAS_ARCHIVO = {
    ".pdf": b"%PDF",
    ".doc": b"\xd0\xcf\x11\xe0",
    ".docx": b"PK\x03\x04",
}
MIME_POR_EXTENSION = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
METODO_HASH = "pbkdf2:sha256:600000"
PERFILES = {"medico": "Médico", "enfermeria": "Enfermería", "administrativo": "Administrativo"}
ESTADOS_DOCUMENTO = {
    "pendiente": "Pendiente",
    "en_revision": "En revisión",
    "validado": "Validado",
    "rechazado": "Rechazado",
}
ESTADOS_ARCHIVO = {
    "vigente": "Vigente",
    "por_vencer": "Por vencer",
    "vencido": "Vencido",
    "obsoleto": "Versión anterior",
}
DIAS_POR_VENCER = 30
POR_PAGINA = 10
PATRON_DUI = re.compile(r"^\d{8}-\d$")



def conectar():
    return mysql.connector.connect(**DB_CONFIG)


@contextmanager
def cursor_bd():
    """Abre conexión y cursor; hace commit al terminar o rollback si hay error."""
    conexion = conectar()
    cursor = conexion.cursor(dictionary=True, buffered=True)
    try:
        yield cursor
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def consultar(sql, params=(), uno=False):
    with cursor_bd() as cur:
        cur.execute(sql, params)
        return cur.fetchone() if uno else cur.fetchall()


def registrar(cur, accion, detalle, usuario_id=None):
    """Guarda una acción en la bitácora."""
    if usuario_id is None and g.get("usuario"):
        usuario_id = g.usuario["id"]
    cur.execute(
        "INSERT INTO bitacora (usuario_id, accion, detalle, fecha) VALUES (%s, %s, %s, %s)",
        (usuario_id, accion, detalle[:500], datetime.now()),
    )


def normalizar(texto):
    """Minúsculas y sin tildes, para buscar 'martinez' y encontrar 'Martínez'."""
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def a_fecha(texto):
    try:
        return date.fromisoformat(texto) if texto else None
    except ValueError:
        return None


def solo_fecha(valor):
    return valor.date() if isinstance(valor, datetime) else valor


@app.template_filter("fecha")
def filtro_fecha(valor, con_hora=False):
    if not valor:
        return "—"
    if con_hora and isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y %H:%M")
    return valor.strftime("%d/%m/%Y")


@app.template_filter("tamano")
def filtro_tamano(num_bytes):
    if not num_bytes:
        return "—"
    return f"{num_bytes / 1024:.0f} KB" if num_bytes >= 1024 else f"{num_bytes} B"


@app.template_filter("iniciales")
def filtro_iniciales(nombre):
    partes = (nombre or "").split()
    return "".join(p[0] for p in partes[:2]).upper()


def paginar(items, pagina):
    total = len(items)
    paginas = max(1, math.ceil(total / POR_PAGINA))
    pagina = min(max(1, pagina), paginas)
    inicio = (pagina - 1) * POR_PAGINA
    info = {
        "pagina": pagina,
        "paginas": paginas,
        "total": total,
        "desde": inicio + 1 if total else 0,
        "hasta": min(inicio + POR_PAGINA, total),
    }
    return items[inicio:inicio + POR_PAGINA], info


def pagina_actual():
    try:
        return int(request.args.get("pagina", 1))
    except ValueError:
        return 1


def url_modificada(quitar=None, valor=None, **cambios):
    """URL actual cambiando parámetros (se usa en filtros, chips y paginación)."""
    args = request.args.to_dict(flat=False)
    if "pagina" not in cambios:
        args.pop("pagina", None)
    if quitar:
        if valor is None:
            args.pop(quitar, None)
        else:
            args[quitar] = [v for v in args.get(quitar, []) if v != valor]
    for clave, nuevo in cambios.items():
        if nuevo in (None, ""):
            args.pop(clave, None)
        else:
            args[clave] = [str(nuevo)]
    args = {k: v for k, v in args.items() if v and v != [""]}
    return request.path + ("?" + urlencode(args, doseq=True) if args else "")


def filtrar_facetas(items, predicados):
    """Devuelve una función que filtra items con todos los predicados activos,
    pudiendo excluir uno (para calcular los conteos de esa faceta)."""
    activos = {k: p for k, p in predicados.items() if p is not None}

    def filtrar(excluir=None):
        return [i for i in items if all(p(i) for k, p in activos.items() if k != excluir)]

    return filtrar



@app.before_request
def cargar_usuario():
    g.usuario = None
    if request.endpoint == "static":
        return
    usuario_id = session.get("usuario_id")
    if usuario_id:
        g.usuario = consultar(
            "SELECT id, usuario, nombre, rol FROM usuarios WHERE id = %s AND activo = 1",
            (usuario_id,), uno=True,
        )
        if g.usuario is None:
            session.clear()


def token_csrf():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


def campo_csrf():
    return Markup(f'<input type="hidden" name="csrf_token" value="{token_csrf()}">')


@app.before_request
def verificar_csrf():
    if request.method == "POST":
        enviado = request.form.get("csrf_token", "")
        if not enviado or not secrets.compare_digest(enviado, session.get("csrf", "")):
            abort(400, "El formulario expiró. Recarga la página e inténtalo de nuevo.")


def login_requerido(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if g.usuario is None:
            return redirect(url_for("login", siguiente=request.full_path))
        return vista(*args, **kwargs)
    return envoltura


def solo_admin(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if g.usuario is None:
            return redirect(url_for("login", siguiente=request.full_path))
        if g.usuario["rol"] != "admin":
            abort(403)
        return vista(*args, **kwargs)
    return envoltura


app.jinja_env.globals.update(campo_csrf=campo_csrf, url_modificada=url_modificada)


@app.context_processor
def variables_plantillas():
    usuario = g.get("usuario")
    return {
        "usuario": usuario,
        "es_admin": bool(usuario and usuario["rol"] == "admin"),
        "PERFILES": PERFILES,
        "ESTADOS_DOCUMENTO": ESTADOS_DOCUMENTO,
        "ESTADOS_ARCHIVO": ESTADOS_ARCHIVO,
        "DIAS_POR_VENCER": DIAS_POR_VENCER,
    }


@app.errorhandler(HTTPException)
def manejar_error(error):
    mensajes = {
        403: "Tu usuario no tiene permiso para realizar esta acción. Solo el administrador puede modificar expedientes.",
        404: "No encontramos lo que buscas. Es posible que haya sido eliminado.",
        413: "El archivo supera el tamaño máximo permitido de 512 KB.",
    }
    mensaje = mensajes.get(error.code, error.description)
    return render_template("error.html", codigo=error.code, mensaje=mensaje), error.code



def estado_de_archivo(version, version_max, vencimiento, hoy=None):
    hoy = hoy or date.today()
    if version < version_max:
        return "obsoleto"
    if vencimiento and vencimiento < hoy:
        return "vencido"
    if vencimiento and vencimiento <= hoy + timedelta(days=DIAS_POR_VENCER):
        return "por_vencer"
    return "vigente"


def cargar_expedientes(cur, empleado_id=None):
    """Arma el expediente completo (requisitos, estados y avance) de uno o todos los empleados."""
    hoy = date.today()
    cur.execute("""SELECT codigo, nombre, descripcion, requiere_vencimiento
                   FROM tipos_documento WHERE activo = 1 ORDER BY orden, nombre""")
    tipos = cur.fetchall()
    cur.execute("SELECT perfil, tipo_codigo FROM requisitos_perfil")
    requisitos = {}
    for fila in cur.fetchall():
        requisitos.setdefault(fila["perfil"], set()).add(fila["tipo_codigo"])

    where_emp, where_doc, params = "", "", ()
    if empleado_id is not None:
        where_emp, where_doc, params = " WHERE id = %s", " WHERE empleado_id = %s", (empleado_id,)

    cur.execute("SELECT id, nombre, dui, perfil, observaciones, fecha_registro FROM empleados"
                + where_emp + " ORDER BY id", params)
    empleados = cur.fetchall()
    cur.execute("SELECT empleado_id, tipo_codigo, estado, observacion FROM estado_documentos"
                + where_doc, params)
    estados = {(f["empleado_id"], f["tipo_codigo"]): f for f in cur.fetchall()}
    cur.execute("SELECT empleado_id, tipo_codigo, version, fecha_vencimiento FROM archivos"
                + where_doc, params)
    ultimos, num_archivos = {}, {}
    for f in cur.fetchall():
        clave = (f["empleado_id"], f["tipo_codigo"])
        num_archivos[f["empleado_id"]] = num_archivos.get(f["empleado_id"], 0) + 1
        if clave not in ultimos or f["version"] > ultimos[clave]["version"]:
            ultimos[clave] = f

    for emp in empleados:
        requeridos_perfil = requisitos.get(emp["perfil"], set())
        documentos = []
        for tipo in tipos:
            clave = (emp["id"], tipo["codigo"])
            info = estados.get(clave)
            ultimo = ultimos.get(clave)
            documentos.append({
                "codigo": tipo["codigo"],
                "nombre": tipo["nombre"],
                "descripcion": tipo["descripcion"],
                "requiere_vencimiento": bool(tipo["requiere_vencimiento"]),
                "requerido": tipo["codigo"] in requeridos_perfil,
                "estado": info["estado"] if info else "pendiente",
                "observacion": info["observacion"] if info else None,
                "version": ultimo["version"] if ultimo else None,
                "vencimiento": ultimo["fecha_vencimiento"] if ultimo else None,
                "estado_archivo": estado_de_archivo(1, 1, ultimo["fecha_vencimiento"], hoy) if ultimo else None,
            })
        requeridos = [d for d in documentos if d["requerido"]]
        cumplidos = {d["codigo"] for d in requeridos
                     if d["estado"] == "validado" and d["estado_archivo"] != "vencido"}
        emp.update({
            "documentos": documentos,
            "total_requeridos": len(requeridos),
            "validados": len(cumplidos),
            "avance": round(len(cumplidos) * 100 / len(requeridos)) if requeridos else 100,
            "completo": len(cumplidos) == len(requeridos),
            "faltantes": [d for d in requeridos if d["codigo"] not in cumplidos],
            "num_archivos": num_archivos.get(emp["id"], 0),
            "con_revision": any(d["estado"] == "en_revision" for d in documentos),
            "con_rechazos": any(d["estado"] == "rechazado" for d in documentos),
            "con_vencidos": any(d["estado_archivo"] == "vencido" for d in documentos),
            "con_por_vencer": any(d["estado_archivo"] == "por_vencer" for d in documentos),
        })
    return empleados, tipos


def fijar_estado(cur, empleado_id, tipo_codigo, estado, observacion):
    datos = (estado, observacion, g.usuario["id"], datetime.now(), empleado_id, tipo_codigo)
    cur.execute("SELECT 1 AS existe FROM estado_documentos WHERE empleado_id = %s AND tipo_codigo = %s",
                (empleado_id, tipo_codigo))
    if cur.fetchone():
        cur.execute("""UPDATE estado_documentos
                       SET estado = %s, observacion = %s, actualizado_por = %s, fecha_actualizacion = %s
                       WHERE empleado_id = %s AND tipo_codigo = %s""", datos)
    else:
        cur.execute("""INSERT INTO estado_documentos
                       (estado, observacion, actualizado_por, fecha_actualizacion, empleado_id, tipo_codigo)
                       VALUES (%s, %s, %s, %s, %s, %s)""", datos)



FILTROS_EXPEDIENTE = {
    "completo": ("Expediente completo", lambda e: e["completo"]),
    "incompleto": ("Expediente incompleto", lambda e: not e["completo"]),
    "revision": ("Con documentos en revisión", lambda e: e["con_revision"]),
    "rechazado": ("Con documentos rechazados", lambda e: e["con_rechazos"]),
    "por_vencer": ("Con documentos por vencer", lambda e: e["con_por_vencer"]),
    "vencido": ("Con documentos vencidos", lambda e: e["con_vencidos"]),
}
ORDEN_EMPLEADOS = {
    "nombre": ("Nombre (A-Z)", lambda e: normalizar(e["nombre"]), False),
    "nombre_desc": ("Nombre (Z-A)", lambda e: normalizar(e["nombre"]), True),
    "recientes": ("Registro más reciente", lambda e: e["fecha_registro"], True),
    "avance_desc": ("Mayor avance", lambda e: e["avance"], True),
    "avance": ("Menor avance", lambda e: e["avance"], False),
}


def filtrar_empleados(expedientes, tipos):
    args = request.args
    q = args.get("q", "").strip()
    qn = normalizar(q)
    perfiles = [p for p in args.getlist("perfil") if p in PERFILES]
    expediente = [x for x in args.getlist("expediente") if x in FILTROS_EXPEDIENTE]
    nombres_tipo = {t["codigo"]: t["nombre"] for t in tipos}
    falta = args.get("falta", "") if args.get("falta", "") in nombres_tipo else ""
    desde, hasta = a_fecha(args.get("desde")), a_fecha(args.get("hasta"))
    orden = args.get("orden") if args.get("orden") in ORDEN_EMPLEADOS else "nombre"

    def le_falta(e, codigo):
        return any(d["codigo"] == codigo for d in e["faltantes"])

    def en_rango(e):
        fecha = solo_fecha(e["fecha_registro"])
        return (not desde or fecha >= desde) and (not hasta or fecha <= hasta)

    filtrar = filtrar_facetas(expedientes, {
        "q": (lambda e: qn in normalizar(e["nombre"]) or qn in e["dui"]) if q else None,
        "perfil": (lambda e: e["perfil"] in perfiles) if perfiles else None,
        "expediente": (lambda e: any(FILTROS_EXPEDIENTE[x][1](e) for x in expediente)) if expediente else None,
        "falta": (lambda e: le_falta(e, falta)) if falta else None,
        "fecha": en_rango if (desde or hasta) else None,
    })

    resultado = filtrar()
    _, clave, inverso = ORDEN_EMPLEADOS[orden]
    resultado.sort(key=lambda e: normalizar(e["nombre"]))
    resultado.sort(key=clave, reverse=inverso)

    base_perfil, base_exp, base_falta = filtrar("perfil"), filtrar("expediente"), filtrar("falta")
    facetas = {
        "perfil": [(k, v, sum(e["perfil"] == k for e in base_perfil)) for k, v in PERFILES.items()],
        "expediente": [(k, v[0], sum(bool(v[1](e)) for e in base_exp)) for k, v in FILTROS_EXPEDIENTE.items()],
        "falta": [(t["codigo"], t["nombre"], sum(le_falta(e, t["codigo"]) for e in base_falta)) for t in tipos],
    }

    chips = []
    if q:
        chips.append((f"Búsqueda: “{q}”", url_modificada(quitar="q")))
    for p in perfiles:
        chips.append((f"Perfil: {PERFILES[p]}", url_modificada(quitar="perfil", valor=p)))
    for x in expediente:
        chips.append((FILTROS_EXPEDIENTE[x][0], url_modificada(quitar="expediente", valor=x)))
    if falta:
        chips.append((f"Le falta: {nombres_tipo[falta]}", url_modificada(quitar="falta")))
    if desde:
        chips.append((f"Desde {desde:%d/%m/%Y}", url_modificada(quitar="desde")))
    if hasta:
        chips.append((f"Hasta {hasta:%d/%m/%Y}", url_modificada(quitar="hasta")))

    seleccion = {"q": q, "perfil": perfiles, "expediente": expediente, "falta": falta,
                 "desde": args.get("desde", ""), "hasta": args.get("hasta", ""), "orden": orden}
    return resultado, facetas, chips, seleccion



@app.route("/")
def inicio():
    return redirect(url_for("listar_empleados"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.usuario:
        return redirect(url_for("listar_empleados"))
    error = None
    if request.method == "POST":
        nombre_usuario = request.form.get("usuario", "").strip().lower()
        clave = request.form.get("clave", "")
        fila = consultar("SELECT id, password_hash, activo FROM usuarios WHERE usuario = %s",
                         (nombre_usuario,), uno=True)
        if fila and fila["activo"] and check_password_hash(fila["password_hash"], clave):
            session.clear()
            session.permanent = True
            session["usuario_id"] = fila["id"]
            with cursor_bd() as cur:
                registrar(cur, "inicio_sesion", f"Inicio de sesión de '{nombre_usuario}'", fila["id"])
            siguiente = request.args.get("siguiente", "")
            if not siguiente.startswith("/") or siguiente.startswith("//"):
                siguiente = url_for("listar_empleados")
            return redirect(siguiente)
        error = "Usuario o contraseña incorrectos."
    return render_template("login.html", error=error), (401 if error else 200)


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if g.usuario:
        return redirect(url_for("listar_empleados"))

    errores = []
    datos = {"nombre": "", "usuario": ""}

    if request.method == "POST":
        datos["nombre"] = request.form.get("nombre", "").strip()
        datos["usuario"] = request.form.get("usuario", "").strip().lower()
        clave = request.form.get("clave", "")
        confirmar = request.form.get("confirmar_clave", "")

        if not 3 <= len(datos["nombre"]) <= 100:
            errores.append("El nombre debe tener entre 3 y 100 caracteres.")

        if not re.fullmatch(r"[a-z0-9_]{3,50}", datos["usuario"]):
            errores.append(
                "El usuario debe tener entre 3 y 50 caracteres. "
                "Solo se permiten letras, números y guion bajo."
            )

        if len(clave) < 12:
            errores.append("La contraseña debe tener al menos 12 caracteres.")

        if clave != confirmar:
            errores.append("Las contraseñas no coinciden.")

        if not errores:
            existente = consultar(
                "SELECT id FROM usuarios WHERE usuario = %s",
                (datos["usuario"],),
                uno=True
            )

            if existente:
                errores.append("Ese nombre de usuario ya está registrado.")
            else:
                try:
                    with cursor_bd() as cur:
                        cur.execute(
                            """
                            INSERT INTO usuarios
                                (usuario, nombre, password_hash, rol, activo)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (
                                datos["usuario"],
                                datos["nombre"],
                                generate_password_hash(
                                    clave,
                                    method=METODO_HASH
                                ),
                                "consulta",
                                1
                            )
                        )

                    flash(
                        "Cuenta creada correctamente. Ya puedes iniciar sesión.",
                        "exito"
                    )
                    return redirect(url_for("login"))

                except mysql.connector.IntegrityError:
                    errores.append("Ese nombre de usuario ya está registrado.")

    return render_template(
        "registro.html",
        errores=errores,
        datos=datos
    )


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("login"))



@app.route("/empleados")
@login_requerido
def listar_empleados():
    with cursor_bd() as cur:
        expedientes, tipos = cargar_expedientes(cur)
    resultado, facetas, chips, seleccion = filtrar_empleados(expedientes, tipos)
    empleados, paginacion = paginar(resultado, pagina_actual())
    return render_template(
        "empleados.html", empleados=empleados, paginacion=paginacion, facetas=facetas,
        chips=chips, sel=seleccion, ordenes=ORDEN_EMPLEADOS, total_general=len(expedientes),
    )


def leer_formulario_empleado():
    datos = {k: request.form.get(k, "").strip() for k in ("nombre", "dui", "perfil", "observaciones")}
    errores = []
    if not datos["nombre"] or len(datos["nombre"]) > 100:
        errores.append("El nombre es obligatorio y debe tener máximo 100 caracteres.")
    if not PATRON_DUI.match(datos["dui"]):
        errores.append("El DUI debe tener el formato 00000000-0.")
    if datos["perfil"] not in PERFILES:
        errores.append("Seleccione un perfil válido.")
    if len(datos["observaciones"]) > 255:
        errores.append("Las observaciones deben tener máximo 255 caracteres.")
    return datos, errores


@app.route("/empleados/nuevo", methods=["GET", "POST"])
@solo_admin
def registrar_empleado():
    datos = {"nombre": "", "dui": "", "perfil": "", "observaciones": ""}
    errores = []
    if request.method == "POST":
        datos, errores = leer_formulario_empleado()
        if not errores:
            with cursor_bd() as cur:
                cur.execute("SELECT id FROM empleados WHERE dui = %s", (datos["dui"],))
                if cur.fetchone():
                    errores.append("Ya existe un empleado registrado con ese DUI.")
                else:
                    cur.execute(
                        """INSERT INTO empleados (nombre, dui, perfil, observaciones, fecha_registro)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (datos["nombre"], datos["dui"], datos["perfil"],
                         datos["observaciones"] or None, datetime.now()),
                    )
                    nuevo_id = cur.lastrowid
                    registrar(cur, "crear_empleado", f"{datos['nombre']} (DUI {datos['dui']})")
            if not errores:
                flash("Empleado registrado. Ahora puedes subir sus documentos.", "exito")
                return redirect(url_for("listar_archivos_empleado", empleado_id=nuevo_id))
    return render_template("empleado_form.html", datos=datos, errores=errores, empleado_id=None)


@app.route("/empleados/editar/<int:id>", methods=["GET", "POST"])
@solo_admin
def editar_empleado(id):
    datos = consultar("SELECT id, nombre, dui, perfil, observaciones FROM empleados WHERE id = %s",
                      (id,), uno=True)
    if not datos:
        abort(404)
    datos["observaciones"] = datos["observaciones"] or ""
    errores = []
    if request.method == "POST":
        datos, errores = leer_formulario_empleado()
        if not errores:
            with cursor_bd() as cur:
                cur.execute("SELECT id FROM empleados WHERE dui = %s AND id <> %s", (datos["dui"], id))
                if cur.fetchone():
                    errores.append("Ese DUI ya pertenece a otro empleado.")
                else:
                    cur.execute(
                        "UPDATE empleados SET nombre = %s, dui = %s, perfil = %s, observaciones = %s WHERE id = %s",
                        (datos["nombre"], datos["dui"], datos["perfil"], datos["observaciones"] or None, id),
                    )
                    registrar(cur, "editar_empleado", f"{datos['nombre']} (ID {id})")
            if not errores:
                flash("Datos del empleado actualizados.", "exito")
                return redirect(url_for("detalle_empleado", id=id))
    return render_template("empleado_form.html", datos=datos, errores=errores, empleado_id=id)


@app.route("/empleados/eliminar/<int:id>", methods=["POST"])
@solo_admin
def eliminar_empleado(id):
    if request.form.get("confirmado") != "si":
        flash("La eliminación no fue confirmada.", "error")
        return redirect(url_for("listar_empleados"))
    with cursor_bd() as cur:
        cur.execute("SELECT nombre, dui FROM empleados WHERE id = %s", (id,))
        empleado = cur.fetchone()
        if not empleado:
            abort(404)
        cur.execute("SELECT COUNT(*) AS n FROM archivos WHERE empleado_id = %s", (id,))
        num = cur.fetchone()["n"]
        
        cur.execute("DELETE FROM empleados WHERE id = %s", (id,))
        registrar(cur, "eliminar_empleado",
                  f"{empleado['nombre']} (DUI {empleado['dui']}) junto con {num} archivo(s)")
    flash(f"Se eliminó a {empleado['nombre']} y sus {num} documento(s).", "exito")
    return redirect(url_for("listar_empleados"))


@app.route("/empleados/detalle/<int:id>")
@login_requerido
def detalle_empleado(id):
    with cursor_bd() as cur:
        expedientes, _ = cargar_expedientes(cur, id)
    if not expedientes:
        abort(404)
    return render_template("detalle.html", empleado=expedientes[0])


@app.route("/empleados/exportar")
@login_requerido
def exportar_csv():
    with cursor_bd() as cur:
        expedientes, tipos = cargar_expedientes(cur)
    resultado, _, _, _ = filtrar_empleados(expedientes, tipos)

    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(["ID", "Nombre", "DUI", "Perfil", "Requisitos validados", "Total requisitos",
                       "Avance %", "Estado", "Documentos faltantes", "Observaciones"])
    for e in resultado:
        escritor.writerow([
            e["id"], e["nombre"], e["dui"], PERFILES[e["perfil"]], e["validados"], e["total_requeridos"],
            e["avance"], "Completo" if e["completo"] else "Incompleto",
            "; ".join(d["nombre"] for d in e["faltantes"]), e["observaciones"] or "",
        ])
    nombre = "expedientes_" + datetime.now().strftime("%Y%m%d_%H%M") + ".csv"
    return Response("\ufeff" + salida.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={nombre}"})


class ErrorSubida(Exception):
    def __init__(self, mensaje, codigo=400):
        super().__init__(mensaje)
        self.mensaje, self.codigo = mensaje, codigo


def pagina_archivos(empleado_id, error=None, codigo=200):
    with cursor_bd() as cur:
        expedientes, _ = cargar_expedientes(cur, empleado_id)
        if not expedientes:
            abort(404)
        cur.execute("""
            SELECT a.id, a.tipo_codigo, t.nombre AS tipo_nombre, a.nombre_original, a.mime_type,
                   a.tamano_bytes, a.version, a.fecha_vencimiento, a.fecha_subida, u.nombre AS subido_por
            FROM archivos a
            JOIN tipos_documento t ON t.codigo = a.tipo_codigo
            LEFT JOIN usuarios u ON u.id = a.subido_por
            WHERE a.empleado_id = %s
            ORDER BY t.orden, a.version DESC
        """, (empleado_id,))
        archivos = cur.fetchall()

    version_max = {}
    for a in archivos:
        version_max[a["tipo_codigo"]] = max(version_max.get(a["tipo_codigo"], 0), a["version"])
    for a in archivos:
        a["estado"] = estado_de_archivo(a["version"], version_max[a["tipo_codigo"]], a["fecha_vencimiento"])
    return render_template("archivos_empleado.html", empleado=expedientes[0], archivos=archivos,
                           error=error, tamano_max=TAMANO_MAXIMO_ARCHIVO), codigo


@app.route("/empleados/<int:empleado_id>/archivos")
@login_requerido
def listar_archivos_empleado(empleado_id):
    return pagina_archivos(empleado_id)


@app.route("/empleados/<int:empleado_id>/archivos/subir", methods=["POST"])
@solo_admin
def subir_archivo(empleado_id):
    try:
        archivo = request.files.get("archivo")
        if archivo is None or not (archivo.filename or "").strip():
            raise ErrorSubida("Seleccione o arrastre un archivo PDF o Word.")

        nombre_original = Path(archivo.filename.replace("\\", "/")).name.strip()
        if not nombre_original or len(nombre_original) > 255:
            raise ErrorSubida("El nombre del archivo no es válido.")

        extension = Path(nombre_original).suffix.lower()
        if extension not in FIRMAS_ARCHIVO:
            raise ErrorSubida("Solo se permiten archivos .pdf, .doc y .docx.")

        contenido = archivo.stream.read(TAMANO_MAXIMO_ARCHIVO + 1)
        if not contenido:
            raise ErrorSubida("El archivo está vacío.")
        if len(contenido) > TAMANO_MAXIMO_ARCHIVO:
            raise ErrorSubida("El archivo supera el tamaño máximo permitido de 512 KB.", 413)
        if not contenido.startswith(FIRMAS_ARCHIVO[extension]):
            raise ErrorSubida(f"El contenido no corresponde a un archivo {extension} válido.")

        tipo_codigo = request.form.get("tipo_documento", "").strip()
        fecha_texto = request.form.get("fecha_vencimiento", "").strip()

        with cursor_bd() as cur:
            cur.execute("SELECT id, nombre FROM empleados WHERE id = %s FOR UPDATE", (empleado_id,))
            empleado = cur.fetchone()
            if empleado is None:
                raise ErrorSubida("El empleado no existe.", 404)

            cur.execute("""SELECT codigo, nombre, requiere_vencimiento FROM tipos_documento
                           WHERE codigo = %s AND activo = 1""", (tipo_codigo,))
            tipo = cur.fetchone()
            if tipo is None:
                raise ErrorSubida("Tipo de documento no permitido.")

            fecha_vencimiento = None
            if fecha_texto:
                fecha_vencimiento = a_fecha(fecha_texto)
                if fecha_vencimiento is None:
                    raise ErrorSubida("La fecha debe tener formato AAAA-MM-DD.")
                if fecha_vencimiento < date.today():
                    raise ErrorSubida("El documento ya está vencido. Solicite uno vigente al empleado.")
            elif tipo["requiere_vencimiento"]:
                raise ErrorSubida(f"La fecha de vencimiento es obligatoria para: {tipo['nombre']}.")

            cur.execute("""SELECT COALESCE(MAX(version), 0) AS ultima FROM archivos
                           WHERE empleado_id = %s AND tipo_codigo = %s""", (empleado_id, tipo_codigo))
            nueva_version = cur.fetchone()["ultima"] + 1

            cur.execute("""
                INSERT INTO archivos (empleado_id, tipo_codigo, nombre_original, mime_type, tamano_bytes,
                                      contenido, version, fecha_vencimiento, fecha_subida, subido_por)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (empleado_id, tipo_codigo, nombre_original, MIME_POR_EXTENSION[extension], len(contenido),
                  contenido, nueva_version, fecha_vencimiento, datetime.now(), g.usuario["id"]))

            fijar_estado(cur, empleado_id, tipo_codigo, "en_revision", None)
            registrar(cur, "subir_archivo",
                      f"{tipo['nombre']} v{nueva_version} de {empleado['nombre']} (ID {empleado_id}): {nombre_original}")

    except ErrorSubida as e:
        return pagina_archivos(empleado_id, error=e.mensaje, codigo=e.codigo)
    except mysql.connector.Error:
        app.logger.exception("Error al guardar el archivo en MySQL")
        return pagina_archivos(empleado_id, codigo=500,
                               error="No se pudo guardar el archivo debido a un error en la base de datos.")

    flash(f"{tipo['nombre']} subido como versión {nueva_version}. Queda en revisión.", "exito")
    return redirect(url_for("listar_archivos_empleado", empleado_id=empleado_id))


@app.route("/empleados/<int:empleado_id>/documentos/<codigo>/estado", methods=["POST"])
@solo_admin
def cambiar_estado_documento(empleado_id, codigo):
    destino = redirect(url_for("listar_archivos_empleado", empleado_id=empleado_id))
    estado = request.form.get("estado", "")
    observacion = request.form.get("observacion", "").strip()[:255] or None
    if estado not in ESTADOS_DOCUMENTO:
        flash("Estado no válido.", "error")
        return destino
    if estado == "rechazado" and not observacion:
        flash("Para rechazar un documento escriba el motivo en la observación.", "error")
        return destino

    with cursor_bd() as cur:
        cur.execute("SELECT nombre FROM empleados WHERE id = %s", (empleado_id,))
        empleado = cur.fetchone()
        cur.execute("SELECT nombre FROM tipos_documento WHERE codigo = %s", (codigo,))
        tipo = cur.fetchone()
        if not empleado or not tipo:
            abort(404)
        cur.execute("SELECT COUNT(*) AS n FROM archivos WHERE empleado_id = %s AND tipo_codigo = %s",
                    (empleado_id, codigo))
        if estado in ("validado", "en_revision") and cur.fetchone()["n"] == 0:
            flash(f"No se puede marcar como «{ESTADOS_DOCUMENTO[estado]}»: no hay archivo de {tipo['nombre']}.", "error")
            return destino
        fijar_estado(cur, empleado_id, codigo, estado, observacion)
        registrar(cur, "estado_documento",
                  f"{tipo['nombre']} de {empleado['nombre']} → {ESTADOS_DOCUMENTO[estado]}"
                  + (f" ({observacion})" if observacion else ""))
    flash(f"{tipo['nombre']}: estado actualizado a «{ESTADOS_DOCUMENTO[estado]}».", "exito")
    return destino


@app.route("/archivos/eliminar/<int:archivo_id>", methods=["POST"])
@solo_admin
def eliminar_archivo(archivo_id):
    """Eliminación restringida de un documento individual:
    solo admin + confirmación escrita + motivo obligatorio + registro en bitácora."""
    with cursor_bd() as cur:
        cur.execute("""
            SELECT a.id, a.empleado_id, a.tipo_codigo, a.version, a.nombre_original,
                   e.nombre AS empleado, t.nombre AS tipo
            FROM archivos a
            JOIN empleados e ON e.id = a.empleado_id
            JOIN tipos_documento t ON t.codigo = a.tipo_codigo
            WHERE a.id = %s
        """, (archivo_id,))
        archivo = cur.fetchone()
        if not archivo:
            abort(404)
        destino = redirect(url_for("listar_archivos_empleado", empleado_id=archivo["empleado_id"]))

        motivo = request.form.get("motivo", "").strip()[:200]
        if request.form.get("confirmacion", "").strip().upper() != "ELIMINAR" or len(motivo) < 5:
            flash("Para eliminar un documento debe escribir ELIMINAR y un motivo de al menos 5 caracteres.", "error")
            return destino

        cur.execute("SELECT MAX(version) AS v FROM archivos WHERE empleado_id = %s AND tipo_codigo = %s",
                    (archivo["empleado_id"], archivo["tipo_codigo"]))
        era_actual = archivo["version"] == cur.fetchone()["v"]

        cur.execute("DELETE FROM archivos WHERE id = %s", (archivo_id,))

        if era_actual:
            cur.execute("SELECT COUNT(*) AS n FROM archivos WHERE empleado_id = %s AND tipo_codigo = %s",
                        (archivo["empleado_id"], archivo["tipo_codigo"]))
            quedan = cur.fetchone()["n"]
            fijar_estado(cur, archivo["empleado_id"], archivo["tipo_codigo"],
                         "en_revision" if quedan else "pendiente",
                         f"Se eliminó la versión v{archivo['version']}: {motivo}"[:255])
        registrar(cur, "eliminar_archivo",
                  f"{archivo['tipo']} v{archivo['version']} ({archivo['nombre_original']}) de "
                  f"{archivo['empleado']}. Motivo: {motivo}")

    flash(f"Se eliminó {archivo['tipo']} v{archivo['version']}.", "exito")
    return destino


@app.route("/archivos/descargar/<int:archivo_id>")
@login_requerido
def descargar_archivo(archivo_id):
    archivo = consultar("SELECT nombre_original, mime_type, contenido FROM archivos WHERE id = %s",
                        (archivo_id,), uno=True)
    if not archivo or not archivo["contenido"]:
        abort(404)
    ver_en_linea = request.args.get("ver") == "1" and archivo["mime_type"] == "application/pdf"
    return send_file(io.BytesIO(bytes(archivo["contenido"])), mimetype=archivo["mime_type"],
                     as_attachment=not ver_en_linea, download_name=archivo["nombre_original"])


ORDEN_DOCUMENTOS = {
    "recientes": ("Subidos recientemente", lambda a: a["fecha_subida"], True),
    "antiguos": ("Subidos hace más tiempo", lambda a: a["fecha_subida"], False),
    "vence": ("Vencen primero", lambda a: (a["fecha_vencimiento"] is None, a["fecha_vencimiento"] or date.max), False),
    "empleado": ("Empleado (A-Z)", lambda a: normalizar(a["empleado"]), False),
    "tipo": ("Tipo de documento", lambda a: a["orden"], False),
}


@app.route("/documentos")
@login_requerido
def buscar_documentos():
    with cursor_bd() as cur:
        cur.execute("SELECT codigo, nombre FROM tipos_documento WHERE activo = 1 ORDER BY orden")
        tipos = cur.fetchall()
        cur.execute("""
            SELECT a.id, a.empleado_id, e.nombre AS empleado, e.dui, e.perfil, a.tipo_codigo,
                   t.nombre AS tipo, t.orden, a.nombre_original, a.tamano_bytes, a.version,
                   a.fecha_vencimiento, a.fecha_subida
            FROM archivos a
            JOIN empleados e ON e.id = a.empleado_id
            JOIN tipos_documento t ON t.codigo = a.tipo_codigo
        """)
        archivos = cur.fetchall()

    version_max = {}
    for a in archivos:
        clave = (a["empleado_id"], a["tipo_codigo"])
        version_max[clave] = max(version_max.get(clave, 0), a["version"])
    for a in archivos:
        a["estado"] = estado_de_archivo(a["version"], version_max[(a["empleado_id"], a["tipo_codigo"])],
                                        a["fecha_vencimiento"])
        a["formato"] = Path(a["nombre_original"]).suffix.lower().lstrip(".")

    args = request.args
    nombres_tipo = {t["codigo"]: t["nombre"] for t in tipos}
    formatos = {"pdf": "PDF", "doc": "Word (.doc)", "docx": "Word (.docx)"}
    q = args.get("q", "").strip()
    qn = normalizar(q)
    sel = {
        "q": q,
        "tipo": [t for t in args.getlist("tipo") if t in nombres_tipo],
        "estado": [s for s in args.getlist("estado") if s in ESTADOS_ARCHIVO],
        "perfil": [p for p in args.getlist("perfil") if p in PERFILES],
        "formato": [f for f in args.getlist("formato") if f in formatos],
        "desde": args.get("desde", ""),
        "hasta": args.get("hasta", ""),
        "orden": args.get("orden") if args.get("orden") in ORDEN_DOCUMENTOS else "recientes",
    }
    desde, hasta = a_fecha(sel["desde"]), a_fecha(sel["hasta"])

    def en_rango(a):
        fecha = solo_fecha(a["fecha_subida"])
        return (not desde or fecha >= desde) and (not hasta or fecha <= hasta)

    def coincide(a):
        return (qn in normalizar(a["empleado"]) or qn in a["dui"] or qn in normalizar(a["nombre_original"]))

    filtrar = filtrar_facetas(archivos, {
        "q": coincide if q else None,
        "tipo": (lambda a: a["tipo_codigo"] in sel["tipo"]) if sel["tipo"] else None,
        "estado": (lambda a: a["estado"] in sel["estado"]) if sel["estado"] else None,
        "perfil": (lambda a: a["perfil"] in sel["perfil"]) if sel["perfil"] else None,
        "formato": (lambda a: a["formato"] in sel["formato"]) if sel["formato"] else None,
        "fecha": en_rango if (desde or hasta) else None,
    })
    resultado = filtrar()
    _, clave, inverso = ORDEN_DOCUMENTOS[sel["orden"]]
    resultado.sort(key=clave, reverse=inverso)

    def contar(faceta, campo, opciones):
        base = filtrar(faceta)
        return [(k, v, sum(a[campo] == k for a in base)) for k, v in opciones.items()]

    facetas = {
        "tipo": contar("tipo", "tipo_codigo", nombres_tipo),
        "estado": contar("estado", "estado", ESTADOS_ARCHIVO),
        "perfil": contar("perfil", "perfil", PERFILES),
        "formato": contar("formato", "formato", formatos),
    }

    chips = []
    if q:
        chips.append((f"Búsqueda: “{q}”", url_modificada(quitar="q")))
    for campo, etiquetas, prefijo in (("tipo", nombres_tipo, ""), ("estado", ESTADOS_ARCHIVO, "Estado: "),
                                      ("perfil", PERFILES, "Perfil: "), ("formato", formatos, "")):
        for valor in sel[campo]:
            chips.append((prefijo + etiquetas[valor], url_modificada(quitar=campo, valor=valor)))
    if desde:
        chips.append((f"Subido desde {desde:%d/%m/%Y}", url_modificada(quitar="desde")))
    if hasta:
        chips.append((f"Subido hasta {hasta:%d/%m/%Y}", url_modificada(quitar="hasta")))

    documentos, paginacion = paginar(resultado, pagina_actual())
    return render_template("documentos.html", documentos=documentos, paginacion=paginacion,
                           facetas=facetas, chips=chips, sel=sel, ordenes=ORDEN_DOCUMENTOS,
                           total_general=len(archivos))


@app.route("/resumen")
@login_requerido
def resumen():
    with cursor_bd() as cur:
        expedientes, tipos = cargar_expedientes(cur)
        cur.execute("""
            SELECT a.empleado_id, e.nombre AS empleado, a.tipo_codigo, t.nombre AS tipo,
                   a.version, a.fecha_vencimiento
            FROM archivos a
            JOIN empleados e ON e.id = a.empleado_id
            JOIN tipos_documento t ON t.codigo = a.tipo_codigo
        """)
        archivos = cur.fetchall()

    total = len(expedientes)
    completos = sum(e["completo"] for e in expedientes)
    incompletos = total - completos

    def porcentaje(parte, de=None):
        de = total if de is None else de
        return round(parte * 100 / de, 1) if de else 0

    por_perfil = []
    for clave, nombre in PERFILES.items():
        grupo = [e for e in expedientes if e["perfil"] == clave]
        hechos = sum(e["completo"] for e in grupo)
        por_perfil.append({"nombre": nombre, "total": len(grupo), "completos": hechos,
                           "pct": porcentaje(hechos, len(grupo))})

    por_tipo = []
    for tipo in tipos:
        fila = {"nombre": tipo["nombre"], "requerido_por": 0, **{k: 0 for k in ESTADOS_DOCUMENTO}}
        for e in expedientes:
            doc = next(d for d in e["documentos"] if d["codigo"] == tipo["codigo"])
            if doc["requerido"]:
                fila["requerido_por"] += 1
                fila[doc["estado"]] += 1
        if fila["requerido_por"]:
            por_tipo.append(fila)

    version_max = {}
    for a in archivos:
        clave = (a["empleado_id"], a["tipo_codigo"])
        version_max[clave] = max(version_max.get(clave, 0), a["version"])
    conteo_archivos = {k: 0 for k in ESTADOS_ARCHIVO}
    alertas_vencimiento = []
    for a in archivos:
        a["estado"] = estado_de_archivo(a["version"], version_max[(a["empleado_id"], a["tipo_codigo"])],
                                        a["fecha_vencimiento"])
        conteo_archivos[a["estado"]] += 1
        if a["estado"] in ("vencido", "por_vencer"):
            alertas_vencimiento.append(a)
    alertas_vencimiento.sort(key=lambda a: a["fecha_vencimiento"])

    pct_completos = porcentaje(completos)
    if total == 0:
        nivel, alerta = "vacio", "Todavía no hay empleados registrados."
    elif pct_completos >= 75:
        nivel, alerta = "alto", "La mayoría de los expedientes está completa."
    elif pct_completos >= 40:
        nivel, alerta = "medio", "Hay una cantidad importante de expedientes por completar."
    else:
        nivel, alerta = "bajo", "Menos de la mitad de los expedientes está completa."

    return render_template(
        "resumen.html", total=total, completos=completos, incompletos=incompletos,
        pct_completos=pct_completos, pct_incompletos=porcentaje(incompletos),
        nivel=nivel, alerta=alerta, por_perfil=por_perfil, por_tipo=por_tipo,
        conteo_archivos=conteo_archivos, alertas_vencimiento=alertas_vencimiento,
        requieren_atencion=sorted([e for e in expedientes if not e["completo"]], key=lambda e: e["avance"]),
    )

ACCIONES_BITACORA = {
    "inicio_sesion": "Inicio de sesión",
    "crear_empleado": "Empleado creado",
    "editar_empleado": "Empleado editado",
    "eliminar_empleado": "Empleado eliminado",
    "subir_archivo": "Archivo subido",
    "estado_documento": "Cambio de estado",
    "eliminar_archivo": "Archivo eliminado",
}


@app.route("/bitacora")
@solo_admin
def ver_bitacora():
    accion = request.args.get("accion", "")
    where, params = ("WHERE b.accion = %s", (accion,)) if accion in ACCIONES_BITACORA else ("", ())
    total = consultar(f"SELECT COUNT(*) AS n FROM bitacora b {where}", params, uno=True)["n"]
    paginas = max(1, math.ceil(total / 20))
    pagina = min(max(1, pagina_actual()), paginas)
    registros = consultar(f"""
        SELECT b.fecha, b.accion, b.detalle, u.nombre AS usuario
        FROM bitacora b LEFT JOIN usuarios u ON u.id = b.usuario_id
        {where} ORDER BY b.id DESC LIMIT %s OFFSET %s
    """, params + (20, (pagina - 1) * 20))
    paginacion = {"pagina": pagina, "paginas": paginas, "total": total,
                  "desde": (pagina - 1) * 20 + 1 if total else 0, "hasta": min(pagina * 20, total)}
    return render_template("bitacora.html", registros=registros, paginacion=paginacion,
                           acciones=ACCIONES_BITACORA, accion=accion)

@app.cli.command("crear-usuario")
@click.argument("usuario")
@click.argument("nombre")
@click.option("--rol", type=click.Choice(["admin", "consulta"]), default="consulta")
@click.password_option("--clave", prompt="Contraseña")
def crear_usuario(usuario, nombre, rol, clave):
    with cursor_bd() as cur:
        cur.execute("INSERT INTO usuarios (usuario, nombre, password_hash, rol) VALUES (%s, %s, %s, %s)",
                    (usuario.strip().lower(), nombre, generate_password_hash(clave, method=METODO_HASH), rol))
    click.echo(f"Usuario '{usuario}' creado con rol {rol}.")


if __name__ == "__main__":
    app.run(debug=True)