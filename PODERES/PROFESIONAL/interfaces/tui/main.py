#!/usr/bin/env python3
"""
SCFV v6.3 - TUI Definitiva (Centro de Control Profesional)
Autor: Domingo E. Díaz N.
"""
import sys
import os
import csv
import json
import subprocess
from pathlib import Path
from datetime import datetime
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, VerticalScroll
from textual.widgets import (
    Header, Footer, Button, Static, Input, RichLog,
    TabbedContent, TabPane, DataTable, Label, TextArea,
    ListView, ListItem
)
from textual import work

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class SCFVApp(App):
    CSS = """
    #log { height: 12; border: solid $primary; background: $surface; }
    #div_log { height: 15; border: solid $warning; background: $surface; }
    #log_events { height: 15; border: solid $success; background: $surface; }
    .button-row { height: 3; padding: 1; }
    .info-box { border: solid $accent; padding: 1; margin: 1; }
    DataTable { height: 15; }
    #editor { height: 20; border: solid $primary; }
    #metrics { border: solid $secondary; padding: 1; }
    """
    BINDINGS = [
        ("q", "salir", "Salir"),
        ("p", "procesar_lote", "Procesar Lote"),
        ("e", "exportar_libros", "Exportar Libros"),
        ("d", "ver_diario", "Ver Diario"),
        ("m", "ver_mayor", "Ver Mayor"),
        ("i", "ver_inventario", "Ver Inventario"),
        ("r", "recargar", "Recargar Todo"),
    ]

    def action_salir(self): self.exit()
    def action_procesar_lote(self):
        self.tabbed_content.active = "procesar"
        self.query_one("#csv_path").focus()
    def action_exportar_libros(self):
        self.tabbed_content.active = "libros"
        self.query_one("#exportar_btn").press()
    def action_ver_diario(self):
        self.tabbed_content.active = "libros"
        self.mostrar_csv("libros/diario.csv", "Diario")
    def action_ver_mayor(self):
        self.tabbed_content.active = "libros"
        self.mostrar_csv("libros/mayor.csv", "Mayor")
    def action_ver_inventario(self):
        self.tabbed_content.active = "libros"
        self.mostrar_csv("libros/inventario.csv", "Inventario")
    def action_recargar(self):
        self.actualizar_tablero()
        self.cargar_lista_reglas()
        self.cargar_eventos()
        self.cargar_logs()
        self.cargar_inventario()

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="dashboard") as self.tabbed_content:
            # --- TABLERO ---
            with TabPane("📊 Tablero", id="dashboard"):
                yield Static("SCFV v6.3 - Sistema Contable Fractal Verificable", classes="info-box")
                yield Static("Soberano · Local-First · Trazable", classes="info-box")
                yield Static("👤 Autor: Domingo E. Díaz N. (C.P.C.)", classes="info-box")
                yield Static(f"📂 Directorio: {os.getcwd()}", id="dir_info")
                yield Static("🔗 Hash actual: [Cargando...]", id="hash_info")
                yield Static("📊 Eventos: [Cargando...]", id="eventos_info")
                yield Static("📅 Último procesamiento: [Cargando...]", id="ultimo_proceso")
                yield Static("📦 Inventario: [Cargando...]", id="inventario_resumen")

            # --- PROCESAR LOTE ---
            with TabPane("📂 Procesar Lote", id="procesar"):
                yield Label("📄 Ruta del archivo CSV:")
                yield Input(placeholder="ejemplos/ejemplo_completo.csv", id="csv_path")
                with Horizontal(classes="button-row"):
                    yield Button("🚀 Procesar Lote", variant="primary", id="procesar_btn")
                    yield Button("🧹 Limpiar Logs", variant="warning", id="clear_log")
                    yield Button("📊 Ver Estado", variant="default", id="estado_btn")
                yield RichLog(id="log", wrap=True, highlight=True)

            # --- LIBROS ---
            with TabPane("📚 Libros", id="libros"):
                with Horizontal(classes="button-row"):
                    yield Button("📤 Exportar Libros", variant="primary", id="exportar_btn")
                    yield Button("📊 Generar EEFF", variant="success", id="eeff_btn")
                    yield Button("📄 Generar PDFs", variant="success", id="pdf_btn")
                    yield Button("📖 Ver Diario", id="ver_diario")
                    yield Button("📊 Ver Mayor", id="ver_mayor")
                    yield Button("📦 Ver Inventario", id="ver_inventario")
                    yield Button("📋 Ver EEFF", id="ver_eeff")
                yield DataTable(id="tabla_libros")

            # --- REGLAS ---
            with TabPane("📝 Reglas", id="reglas"):
                yield Label("📁 Archivos .scfv:")
                yield ListView(id="lista_reglas")
                yield Label("✏️ Contenido:")
                yield TextArea(id="editor", language="plain")
                with Horizontal(classes="button-row"):
                    yield Button("💾 Guardar Regla", variant="primary", id="guardar_regla")
                    yield Button("🔄 Recargar Lista", variant="default", id="recargar_reglas")

            # --- DIVERGENCIAS ---
            with TabPane("⚠️ Divergencias", id="divergencias"):
                with Horizontal(classes="button-row"):
                    yield Button("🔄 Cargar Reporte", variant="warning", id="cargar_div")
                    yield Button("🧹 Limpiar", variant="default", id="clear_div")
                yield RichLog(id="div_log", wrap=True, highlight=True)

            # --- EVENT STORE (NUEVO) ---
            with TabPane("🔗 Event Store", id="event_store"):
                with Horizontal(classes="button-row"):
                    yield Button("🔄 Ver Eventos", variant="primary", id="ver_eventos")
                    yield Button("✅ Verificar Cadena", variant="success", id="verificar_cadena")
                    yield Button("🧹 Limpiar", variant="default", id="clear_events")
                yield DataTable(id="tabla_eventos")
                yield RichLog(id="log_events", wrap=True, highlight=True)

            # --- LOGS (NUEVO) ---
            with TabPane("📋 Logs", id="logs"):
                with Horizontal(classes="button-row"):
                    yield Button("🔄 Cargar Logs", variant="primary", id="cargar_logs")
                    yield Button("🧹 Limpiar", variant="default", id="clear_logs")
                yield RichLog(id="log_viewer", wrap=True, highlight=True)

            # --- UTILIDADES (NUEVO) ---
            with TabPane("⚙️ Utilidades", id="utilidades"):
                yield Static("🧰 Utilidades del Sistema", classes="info-box")
                with Horizontal(classes="button-row"):
                    yield Button("💾 Respaldar Sistema", variant="primary", id="backup_btn")
                    yield Button("🧹 Limpiar BD", variant="warning", id="clean_btn")
                    yield Button("📊 Estado del Sistema", variant="default", id="sys_status_btn")
                yield RichLog(id="util_log", wrap=True, highlight=True)

        yield Footer()

    def on_mount(self):
        self.actualizar_tablero()
        self.cargar_lista_reglas()
        self.cargar_eventos()
        self.cargar_logs()
        self.cargar_inventario()

    def actualizar_tablero(self):
        try:
            from PODERES.CONTABLE.event_store import EventStore
            es = EventStore("scfv.db")
            hash_final = es.obtener_hash_final()
            eventos = len(es.obtener_todos())
            es.cerrar()
            self.query_one("#hash_info").update(f"🔗 Hash actual: {hash_final[:16]}...")
            self.query_one("#eventos_info").update(f"📊 Eventos: {eventos}")
        except:
            self.query_one("#hash_info").update("🔗 Hash actual: (sin base de datos)")
            self.query_one("#eventos_info").update("📊 Eventos: 0")
        
        # Último procesamiento
        if os.path.exists("reporte_mensual.json"):
            try:
                with open("reporte_mensual.json", 'r') as f:
                    data = json.load(f)
                    total = data.get('total', 0)
                    ok = len(data.get('convergencias', []))
                    div = len(data.get('divergencias', []))
                    self.query_one("#ultimo_proceso").update(f"📅 Último lote: {total} filas, {ok} OK, {div} divergencias")
            except:
                pass

    def cargar_inventario(self):
        if os.path.exists("inventario_saldos.json"):
            try:
                with open("inventario_saldos.json", 'r') as f:
                    data = json.load(f)
                    productos = len(data)
                    self.query_one("#inventario_resumen").update(f"📦 Inventario: {productos} productos activos")
            except:
                self.query_one("#inventario_resumen").update("📦 Inventario: sin datos")
        else:
            self.query_one("#inventario_resumen").update("📦 Inventario: sin datos")

    def cargar_lista_reglas(self):
        lista = self.query_one("#lista_reglas")
        lista.clear()
        ruta_reglas = Path("reglas")
        if ruta_reglas.exists():
            for f in ruta_reglas.glob("*.scfv"):
                lista.append(ListItem(Label(f.name), id=f.name.replace(".", "_")))
        else:
            lista.append(ListItem(Static("⚠️ Carpeta 'reglas/' no encontrada")))

    def on_list_view_selected(self, event: ListView.Selected):
        item = event.item
        nombre = event.item.id.replace("_", ".")
        if nombre.startswith("⚠️"):
            return
        ruta = Path("reglas") / nombre
        if ruta.exists():
            with open(ruta, 'r', encoding='utf-8') as f:
                contenido = f.read()
            editor = self.query_one("#editor")
            editor.text = contenido
            editor._file_path = str(ruta)

    def on_button_pressed(self, event: Button.Pressed):
        log = self.query_one("#log")
        div_log = self.query_one("#div_log")
        tabla = self.query_one("#tabla_libros")
        btn_id = event.button.id
        # --- PROCESAR ---
        if btn_id == "procesar_btn":
            ruta = self.query_one("#csv_path").value.strip()
            if not ruta:
                log.write("⚠️ Error: Introduce la ruta del archivo CSV.")
                return
            if not os.path.exists(ruta):
                log.write(f"⚠️ Error: El archivo '{ruta}' no existe.")
                return
            self.procesar_lote(ruta)
        elif btn_id == "clear_log":
            log.clear()
        elif btn_id == "estado_btn":
            self.actualizar_tablero()
            self.cargar_inventario()
            log.write("✅ Tablero actualizado.")

        # --- LIBROS ---
        elif btn_id == "exportar_btn":
            log.write("📤 Exportando libros...")
            self.ejecutar_script("exportar_libros.py", log)
        elif btn_id == "eeff_btn":
            log.write("📊 Generando Estados Financieros...")
            self.ejecutar_script("generar_eeff.py", log)
        elif btn_id == "pdf_btn":
            log.write("📄 Generando PDFs...")
            self.ejecutar_script("generar_pdf.py", log)
        elif btn_id == "ver_diario":
            self.mostrar_csv("libros/diario.csv", "Diario")
        elif btn_id == "ver_mayor":
            self.mostrar_csv("libros/mayor.csv", "Mayor")
        elif btn_id == "ver_inventario":
            self.mostrar_csv("libros/inventario.csv", "Inventario")
        elif btn_id == "ver_eeff":
            self.mostrar_eeff()

        # --- REGLAS ---
        elif btn_id == "guardar_regla":
            editor = self.query_one("#editor")
            if hasattr(editor, '_file_path') and editor._file_path:
                try:
                    with open(editor._file_path, 'w', encoding='utf-8') as f:
                        f.write(editor.text)
                    log.write(f"✅ Regla guardada: {editor._file_path}")
                except Exception as e:
                    log.write(f"❌ Error al guardar: {e}")
            else:
                log.write("⚠️ Selecciona una regla de la lista.")
        elif btn_id == "recargar_reglas":
            self.cargar_lista_reglas()
            log.write("🔄 Lista recargada.")

        # --- DIVERGENCIAS ---
        elif btn_id == "cargar_div":
            div_log.clear()
            if os.path.exists("reporte_mensual.json"):
                try:
                    with open("reporte_mensual.json", 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    div_log.write("📋 REPORTE DE DIVERGENCIAS")
                    div_log.write(f"Total filas: {data.get('total', 0)}")
                    div_log.write(f"Procesadas OK: {data.get('procesados', 0)}")
                    div_log.write(f"Convergencias: {len(data.get('convergencias', []))}")
                    div_log.write(f"Divergencias: {len(data.get('divergencias', []))}")
                    for d in data.get('divergencias', [])[:5]:
                        div_log.write(f"  ⚠️ Fila {d.get('indice')}: {d.get('error', 'Error desconocido')}")
                    if len(data.get('divergencias', [])) > 5:
                        div_log.write(f"  ... y {len(data.get('divergencias', [])) - 5} más.")
                    div_log.write(f"🔗 Hash final: {data.get('hash_final', 'N/A')[:16]}...")
                except Exception as e:
                    div_log.write(f"❌ Error: {e}")
            else:
                div_log.write("⚠️ No existe 'reporte_mensual.json'.")
        elif btn_id == "clear_div":
            div_log.clear()

        # --- EVENT STORE ---
        elif btn_id == "ver_eventos":
            self.cargar_eventos()
        elif btn_id == "verificar_cadena":
            self.verificar_cadena()
        elif btn_id == "clear_events":
            self.query_one("#tabla_eventos").clear()
            self.query_one("#log_events").clear()

        # --- LOGS ---
        elif btn_id == "cargar_logs":
            self.cargar_logs()
        elif btn_id == "clear_logs":
            self.query_one("#log_viewer").clear()

        # --- UTILIDADES ---
        elif btn_id == "backup_btn":
            self.ejecutar_script("scripts/backup.sh", self.query_one("#util_log"), is_bash=True)
        elif btn_id == "clean_btn":
            self.query_one("#util_log").write("🧹 Limpiando base de datos...")
            try:
                if os.path.exists("scfv.db"):
                    os.remove("scfv.db")
                self.query_one("#util_log").write("✅ Base de datos eliminada.")
                self.actualizar_tablero()
            except Exception as e:
                self.query_one("#util_log").write(f"❌ Error: {e}")
        elif btn_id == "sys_status_btn":
            self.util_log_status()

    # --- MÉTODOS AUXILIARES ---
    def ejecutar_script(self, script, log_widget, is_bash=False):
        try:
            if is_bash:
                result = subprocess.run(["bash", script], capture_output=True, text=True, cwd=os.getcwd())
            else:
                result = subprocess.run(["python", script], capture_output=True, text=True, cwd=os.getcwd())
            log_widget.write(result.stdout)
            if result.stderr:
                log_widget.write(f"⚠️ {result.stderr}")
            log_widget.write("✅ Comando ejecutado.")
            self.actualizar_tablero()
            self.cargar_inventario()
        except Exception as e:
            log_widget.write(f"❌ Error: {e}")

    def util_log_status(self):
        util_log = self.query_one("#util_log")
        util_log.clear()
        util_log.write("📊 ESTADO DEL SISTEMA")
        util_log.write(f"📂 Directorio: {os.getcwd()}")
        # Tamaño de archivos
        for f in ["scfv.db", "reporte_mensual.json", "inventario_saldos.json"]:
            if os.path.exists(f):
                size = os.path.getsize(f)
                util_log.write(f"📄 {f}: {size} bytes")
            else:
                util_log.write(f"📄 {f}: No existe")
        # Archivos en libros/
        if os.path.exists("libros"):
            files = os.listdir("libros")
            util_log.write(f"📚 Libros: {len(files)} archivos")
        else:
            util_log.write("📚 Libros: carpeta no existe")

    @work(exclusive=True)
    async def procesar_lote(self, ruta_csv: str):
        log = self.query_one("#log")
        log.write("⏳ Iniciando procesamiento...")
        try:
            from PODERES.PROFESIONAL.interfaces.loader.batch_processor import BatchProcessor
            bp = BatchProcessor()
            import io
            from contextlib import redirect_stdout
            f = io.StringIO()
            with redirect_stdout(f):
                reporte = bp.procesar_csv(ruta_csv)
            log.write(f.getvalue())
            if reporte.get("convergencias"):
                log.write(f"✅ Procesadas OK: {len(reporte['convergencias'])}")
            if reporte.get("divergencias"):
                log.write(f"⚠️ Divergencias: {len(reporte['divergencias'])}")
            log.write(f"🔗 Hash final: {reporte.get('hash_final', 'N/A')[:16]}...")
            self.actualizar_tablero()
            self.cargar_inventario()
            log.write("✅ Procesamiento completado.")
        except Exception as e:
            log.write(f"❌ Error: {e}")
            import traceback
            log.write(traceback.format_exc())

    def cargar_eventos(self):
        tabla = self.query_one("#tabla_eventos")
        log_ev = self.query_one("#log_events")
        tabla.clear()
        log_ev.clear()
        try:
            from PODERES.CONTABLE.event_store import EventStore
            es = EventStore("scfv.db")
            eventos = es.obtener_todos()
            if not eventos:
                tabla.add_column("Mensaje")
                tabla.add_row("No hay eventos en el Event Store.")
                return
            # Mostrar últimos 20 eventos
            tabla.add_column("ID")
            tabla.add_column("Tipo")
            tabla.add_column("Correlation ID")
            tabla.add_column("Hash (primeros 16)")
            for e in eventos[-20:]:
                tabla.add_row(
                    e.get('event_id', '')[:8],
                    e.get('tipo_evento', ''),
                    e.get('correlation_id', '')[:12],
                    e.get('hash_actual', '')[:16]
                )
            log_ev.write(f"✅ Mostrando últimos {len(eventos[-20:])} de {len(eventos)} eventos.")
        except Exception as e:
            tabla.add_column("Error")
            tabla.add_row(f"Error: {e}")

    def verificar_cadena(self):
        log_ev = self.query_one("#log_events")
        log_ev.write("🔍 Verificando integridad de la cadena...")
        try:
            from PODERES.CONTABLE.event_store import EventStore
            es = EventStore("scfv.db")
            ok, msg = es.verificar_cadena()
            if ok:
                log_ev.write(f"✅ Cadena verificada: {msg}")
            else:
                log_ev.write(f"❌ Error en cadena: {msg}")
        except Exception as e:
            log_ev.write(f"❌ Error: {e}")

    def cargar_logs(self):
        log_viewer = self.query_one("#log_viewer")
        log_viewer.clear()
        ruta_log = Path("logs/scfv.log")
        if not ruta_log.exists():
            log_viewer.write("⚠️ No existe logs/scfv.log. Procesa un lote para generar logs.")
            return
        try:
            with open(ruta_log, 'r', encoding='utf-8') as f:
                lineas = f.readlines()
            # Mostrar últimas 30 líneas
            for linea in lineas[-30:]:
                log_viewer.write(linea.strip())
            log_viewer.write(f"\n✅ Mostrando últimas {len(lineas[-30:])} de {len(lineas)} líneas.")
        except Exception as e:
            log_viewer.write(f"❌ Error al leer logs: {e}")

    def mostrar_csv(self, ruta, titulo):
        tabla = self.query_one("#tabla_libros")
        tabla.clear()
        if not os.path.exists(ruta):
            tabla.add_column("Mensaje")
            tabla.add_row(f"⚠️ El archivo {ruta} no existe. Exporta los libros primero.")
            return
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                encabezados = next(reader, None)
                if encabezados:
                    tabla.add_column("N°")
                    for col in encabezados:
                        tabla.add_column(col)
                    for i, row in enumerate(reader, start=1):
                        tabla.add_row(str(i), *row)
                else:
                    tabla.add_column("Mensaje")
                    tabla.add_row("Archivo vacío")
        except Exception as e:
            tabla.add_column("Error")
            tabla.add_row(f"Error al leer {ruta}: {e}")

    def mostrar_eeff(self):
        tabla = self.query_one("#tabla_libros")
        tabla.clear()
        for archivo in ["balance_general.csv", "estado_resultados.csv"]:
            ruta = os.path.join("libros", archivo)
            if os.path.exists(ruta):
                tabla.add_column("Mensaje")
                tabla.add_row(f"📄 {archivo} (vista rápida)")
                with open(ruta, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        tabla.add_row("", " | ".join(row))
            else:
                tabla.add_row(f"⚠️ {archivo} no encontrado. Genera EEFF.")

if __name__ == "__main__":
    SCFVApp().run()
