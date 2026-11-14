(function () {
    "use strict";

    var modal = document.getElementById("modal-confirmar");
    var formularioPendiente = null;

    function abrirModal(form) {
        formularioPendiente = form;
        var requiereMotivo = form.hasAttribute("data-requiere-motivo");
        document.getElementById("modal-titulo").textContent = form.dataset.titulo || "¿Confirmar eliminación?";
        document.getElementById("modal-mensaje").textContent = form.dataset.confirmar;
        document.getElementById("modal-extra").hidden = !requiereMotivo;
        document.getElementById("modal-motivo").value = "";
        document.getElementById("modal-palabra").value = "";
        document.getElementById("modal-error").hidden = true;
        modal.hidden = false;
        document.body.style.overflow = "hidden";
        (requiereMotivo ? document.getElementById("modal-motivo")
                        : modal.querySelector("[data-cerrar-modal].btn")).focus();
    }

    function cerrarModal() {
        modal.hidden = true;
        document.body.style.overflow = "";
        formularioPendiente = null;
    }

    function mostrarErrorModal(texto) {
        var error = document.getElementById("modal-error");
        error.textContent = texto;
        error.hidden = false;
    }

    if (modal) {
        document.addEventListener("submit", function (evento) {
            var form = evento.target;
            if (form.matches("form[data-confirmar]")) {
                evento.preventDefault();
                abrirModal(form);
            }
        });

        modal.querySelectorAll("[data-cerrar-modal]").forEach(function (el) {
            el.addEventListener("click", cerrarModal);
        });

        document.addEventListener("keydown", function (evento) {
            if (evento.key === "Escape" && !modal.hidden) cerrarModal();
        });

        document.getElementById("modal-aceptar").addEventListener("click", function () {
            var form = formularioPendiente;
            if (!form) return;
            if (form.hasAttribute("data-requiere-motivo")) {
                var motivo = document.getElementById("modal-motivo").value.trim();
                var palabra = document.getElementById("modal-palabra").value.trim().toUpperCase();
                if (motivo.length < 5) return mostrarErrorModal("Escriba un motivo de al menos 5 caracteres.");
                if (palabra !== "ELIMINAR") return mostrarErrorModal("Debe escribir la palabra ELIMINAR para confirmar.");
                form.querySelector("[name=motivo]").value = motivo;
                form.querySelector("[name=confirmacion]").value = palabra;
            }
            var confirmado = form.querySelector("[name=confirmado]");
            if (confirmado) confirmado.value = "si";
            cerrarModal();
            form.submit(); 
        });
    }

    document.querySelectorAll("[data-autoenvio]").forEach(function (el) {
        el.addEventListener("change", function () {
            if (el.form) el.form.requestSubmit ? el.form.requestSubmit() : el.form.submit();
        });
    });

    document.querySelectorAll("[data-alternar]").forEach(function (boton) {
        boton.addEventListener("click", function () {
            var destino = document.querySelector(boton.dataset.alternar);
            if (destino) destino.classList.toggle("abierto");
        });
    });

    document.querySelectorAll("[data-cerrar-aviso]").forEach(function (boton) {
        boton.addEventListener("click", function () { boton.closest(".aviso").remove(); });
    });

    document.querySelectorAll("[data-mascara-dui]").forEach(function (input) {
        input.addEventListener("input", function () {
            var digitos = input.value.replace(/\D/g, "").slice(0, 9);
            input.value = digitos.length > 8 ? digitos.slice(0, 8) + "-" + digitos.slice(8) : digitos;
        });
    });

    var form = document.getElementById("form-subida");
    if (!form) return;

    var zona = document.getElementById("dropzone");
    var input = document.getElementById("archivo");
    var caja = zona.querySelector(".dropzone__archivo");
    var nombre = zona.querySelector(".dropzone__nombre");
    var error = document.getElementById("error-subida");
    var selectTipo = document.getElementById("tipo_documento");
    var fecha = document.getElementById("fecha_vencimiento");
    var marcaFecha = document.getElementById("marca-fecha");
    var maximo = parseInt(zona.dataset.max, 10);
    var extensiones = [".pdf", ".doc", ".docx"];

    function mostrarError(texto) {
        error.textContent = texto;
        error.hidden = !texto;
        zona.classList.toggle("dropzone--error", !!texto);
    }

    function validarArchivo(archivo) {
        var ext = archivo.name.slice(archivo.name.lastIndexOf(".")).toLowerCase();
        if (extensiones.indexOf(ext) === -1) return "Solo se permiten archivos PDF, DOC o DOCX.";
        if (archivo.size === 0) return "El archivo está vacío.";
        if (archivo.size > maximo) return "El archivo pesa " + Math.round(archivo.size / 1024) + " KB y el máximo es 512 KB.";
        return "";
    }

    function actualizarVista() {
        var archivo = input.files[0];
        if (!archivo) {
            caja.hidden = true;
            zona.classList.remove("dropzone--con-archivo");
            return;
        }
        var problema = validarArchivo(archivo);
        if (problema) {
            input.value = "";
            caja.hidden = true;
            zona.classList.remove("dropzone--con-archivo");
            mostrarError(problema);
            return;
        }
        mostrarError("");
        nombre.textContent = archivo.name + " (" + Math.max(1, Math.round(archivo.size / 1024)) + " KB)";
        caja.hidden = false;
        zona.classList.add("dropzone--con-archivo");
    }

    zona.addEventListener("click", function (evento) {
        if (!evento.target.closest("[data-quitar-archivo]")) input.click();
    });
    zona.addEventListener("keydown", function (evento) {
        if (evento.key === "Enter" || evento.key === " ") { evento.preventDefault(); input.click(); }
    });
    input.addEventListener("change", actualizarVista);

    ["dragenter", "dragover"].forEach(function (tipo) {
        zona.addEventListener(tipo, function (evento) {
            evento.preventDefault();
            zona.classList.add("dropzone--activa");
        });
    });
    ["dragleave", "drop"].forEach(function (tipo) {
        zona.addEventListener(tipo, function (evento) {
            evento.preventDefault();
            zona.classList.remove("dropzone--activa");
        });
    });
    zona.addEventListener("drop", function (evento) {
        var archivos = evento.dataTransfer.files;
        if (!archivos.length) return;
        var transferencia = new DataTransfer();
        transferencia.items.add(archivos[0]);
        input.files = transferencia.files;
        actualizarVista();
        if (archivos.length > 1) mostrarError("Solo se toma el primer archivo. Suba los documentos de uno en uno.");
    });

    ["dragover", "drop"].forEach(function (tipo) {
        window.addEventListener(tipo, function (evento) { evento.preventDefault(); });
    });

    zona.querySelector("[data-quitar-archivo]").addEventListener("click", function () {
        input.value = "";
        actualizarVista();
    });

    function actualizarFecha() {
        var opcion = selectTipo.options[selectTipo.selectedIndex];
        var obligatoria = opcion && opcion.dataset.vence === "1";
        marcaFecha.hidden = !obligatoria;
        fecha.required = obligatoria;
    }
    selectTipo.addEventListener("change", actualizarFecha);
    var hoy = new Date();
    fecha.min = hoy.getFullYear() + "-" + String(hoy.getMonth() + 1).padStart(2, "0") + "-" +
                String(hoy.getDate()).padStart(2, "0");

    form.addEventListener("submit", function (evento) {
        var problema = "";
        if (!selectTipo.value) problema = "Seleccione el tipo de documento.";
        else if (fecha.required && !fecha.value) problema = "La fecha de vencimiento es obligatoria para este documento.";
        else if (!input.files.length) problema = "Arrastre o seleccione un archivo para subir.";
        if (problema) {
            evento.preventDefault();
            mostrarError(problema);
        }
    });
})();