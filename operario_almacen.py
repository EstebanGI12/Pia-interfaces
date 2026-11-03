import customtkinter as ctk
import tkinter as tk
import sqlite3
import os
import random
import sys
import subprocess
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'wiptrack.db')

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG_SIDEBAR = "#212b33"
BG_MAIN = "#28323a"
BG_CARD = "#43525c"
BG_STATION = "#1c2329"
CYAN_ACTIVE = "#00d2ff"
BG_ACTIVE_MENU = "#184555"

GREEN = "#00e676"
YELLOW = "#ffd600"
RED = "#ff4444"
ORANGE = "#ff9800"

class OperarioAlmacenApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ALMACÉN - Sistema de Suministros y Refacciones")
        
        try:
            self.state("zoomed")
        except:
            self.geometry("1280x800")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=0, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(1, weight=1)
        
        self.sidebar = ctk.CTkFrame(self.main_container, width=220, corner_radius=0, fg_color=BG_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(20, 5))
        ctk.CTkLabel(logo_frame, text="WIP", font=("Arial", 22, "bold"), text_color="white").pack(side="left")
        ctk.CTkLabel(logo_frame, text=" STORE", font=("Arial", 22, "bold"), text_color=ORANGE).pack(side="left")
        
        ctk.CTkLabel(self.sidebar, text="CONTROL DE ALMACÉN", font=("Arial", 8), text_color="gray").pack()
        ctk.CTkLabel(self.sidebar, text="🟢 EN TURNO", font=("Arial", 12, "bold"), text_color=GREEN).pack(pady=(5, 30))
        
        self.menus = ["INVENTARIO", "SOLICITUDES", "ENTRADAS/SALIDAS", "CONFIGURACIONES"]
        self.menu_buttons = {}
        
        for m in self.menus:
            text_color = "white" if "SOLICITUDES" not in m else YELLOW
            btn = ctk.CTkButton(self.sidebar, text=m, fg_color="transparent", text_color=text_color,
                                border_width=0, hover_color=BG_ACTIVE_MENU, anchor="w", font=("Arial", 14), height=45,
                                command=lambda name=m: self.cambiar_vista(name))
            btn.pack(pady=5, padx=0, fill="x")
            self.menu_buttons[m] = btn
            
        self.content_area = ctk.CTkFrame(self.main_container, fg_color=BG_MAIN, corner_radius=0)
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)
        
        self.vista_actual = "INVENTARIO"
        self.cambiar_vista("INVENTARIO")
        
        self.alarm_btn_ref = None
        self.alarm_estado_blink = True
        self.iniciar_tintineo_alerta()

    def iniciar_tintineo_alerta(self):
        try:
            pendientes = self.obtener_solicitudes_pendientes_count()
            if pendientes > 0 and self.alarm_btn_ref and self.alarm_btn_ref.winfo_exists():
                if self.alarm_estado_blink:
                    self.alarm_btn_ref.configure(fg_color="#ff1111", text_color="white", border_color="white")
                    self.alarm_estado_blink = False
                else:
                    self.alarm_btn_ref.configure(fg_color="#3d1c23", text_color=RED, border_color=RED)
                    self.alarm_estado_blink = True
            elif self.alarm_btn_ref and self.alarm_btn_ref.winfo_exists():
                self.alarm_btn_ref.configure(fg_color="#104a25", text_color=GREEN, border_color=GREEN)
        except:
            pass
        self.after(600, self.iniciar_tintineo_alerta)

    def obtener_solicitudes_pendientes_count(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM alertas WHERE estado_ticket='PENDIENTE'")
            count = c.fetchone()[0]
            conn.close()
            return count
        except:
            return 0

    def obtener_todo_almacen(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT id_pieza, nombre_pieza, cantidad_disponible, ubicacion FROM almacen ORDER BY nombre_pieza")
            datos = c.fetchall()
            conn.close()
            return datos
        except: return []

    def buscar_piezas_almacen_multi(self, query):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            q = '%' + query.strip() + '%'
            c.execute("SELECT id_pieza, nombre_pieza, cantidad_disponible, ubicacion FROM almacen WHERE id_pieza LIKE ? OR nombre_pieza LIKE ? ORDER BY nombre_pieza", (q, q))
            datos = c.fetchall()
            conn.close()
            return datos
        except: return []

    def obtener_solicitudes_activas(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            query = """
                SELECT a.id_ticket, m.nombre, p.nombre_pieza, p.ubicacion, p.cantidad_disponible, a.fecha_alerta 
                FROM alertas a 
                JOIN maquinas m ON a.id_maquina = m.id_maquina 
                JOIN almacen p ON a.pieza_requerida = p.id_pieza 
                WHERE a.estado_ticket = 'PENDIENTE'
                ORDER BY a.fecha_alerta DESC
            """
            cursor.execute(query)
            datos = cursor.fetchall()
            conn.close()
            return datos
        except:
            return []
            
    def despachar_solicitud(self, id_ticket, id_pieza):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # Verificar si hay stock
            c.execute("SELECT cantidad_disponible FROM almacen WHERE id_pieza=?", (id_pieza,))
            stock = c.fetchone()
            
            if stock and stock[0] > 0:
                # Restar 1 al stock
                c.execute("UPDATE almacen SET cantidad_disponible = cantidad_disponible - 1 WHERE id_pieza=?", (id_pieza,))
                # Cerrar el ticket
                c.execute("UPDATE alertas SET estado_ticket = 'COMPLETADO' WHERE id_ticket=?", (id_ticket,))
                conn.commit()
                print(f"Ticket {id_ticket} despachado. Stock actualizado.")
            else:
                print("No hay stock suficiente para despachar.")
                
            conn.close()
            self.cambiar_vista("SOLICITUDES") # Refrescar
        except Exception as e:
            print("Error al despachar:", e)

    def limpiar_contenido(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()
            
    def actualizar_botones_sidebar(self, vista_activa):
        for m, btn in self.menu_buttons.items():
            if m == vista_activa:
                btn.configure(fg_color=BG_ACTIVE_MENU, text_color=CYAN_ACTIVE)
            else:
                default_color = YELLOW if "SOLICITUDES" in m else "white"
                btn.configure(fg_color="transparent", text_color=default_color)

    def cambiar_vista(self, vista):
        self.vista_actual = vista
        self.limpiar_contenido()
        self.actualizar_botones_sidebar(vista)
        
        container = ctk.CTkFrame(self.content_area, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        container.grid_rowconfigure(2, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(container, height=40, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text="DIA: 30-10-2026", font=("Arial", 12), text_color="lightgray").pack(side="left", padx=20)
        ctk.CTkLabel(header, text="🕒 HORA: TURNO 1 📶", font=("Arial", 12), text_color="lightgray").pack(side="left", padx=20)
        
        pendientes = self.obtener_solicitudes_pendientes_count()
        if pendientes > 0:
            alerta_texto = f"⚠️ {pendientes} SOLICITUD(ES) PENDIENTE(S)"
            alerta_color = RED
            bg_col = "#3d1c23"
        else:
            alerta_texto = "✔️ CERO SOLICITUDES PENDIENTES"
            alerta_color = GREEN
            bg_col = "#104a25"
            
        self.alarm_btn_ref = ctk.CTkButton(header, text=alerta_texto, 
                                           fg_color=bg_col, 
                                           text_color=alerta_color, border_color=alerta_color, border_width=1, 
                                           hover_color="#4a1c23" if pendientes > 0 else "#166b36")
        self.alarm_btn_ref.pack(side="right", padx=10)
        
        ctk.CTkLabel(header, text="📦 OPERARIO ALMACÉN", font=("Arial", 12), text_color="lightgray").pack(side="right", padx=20)

        if vista == "INVENTARIO":
            self.crear_vista_inventario(container)
        elif "SOLICITUDES" in vista:
            self.crear_vista_solicitudes(container)
        elif vista == "ENTRADAS/SALIDAS":
            self.crear_vista_movimientos(container)
        elif vista == "CONFIGURACIONES":
            self.crear_vista_configuraciones(container)

    def crear_vista_inventario(self, parent):
        search_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        search_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(search_frame, text="Catálogo y Control de Inventario", font=("Arial", 18, "bold"), text_color=CYAN_ACTIVE).pack(anchor="w", padx=20, pady=(15, 5))
        
        sub_box = ctk.CTkFrame(search_frame, fg_color="transparent")
        sub_box.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkLabel(sub_box, text="Buscar Pieza (ID o Nombre):", font=("Arial", 12)).pack(side="left", padx=(0, 10))
        
        entry_sn = ctk.CTkEntry(sub_box, width=250)
        entry_sn.pack(side="left", padx=(0, 10))
        
        catalog_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        catalog_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        def renderizar_catalogo(items):
            for widget in catalog_frame.winfo_children(): 
                widget.destroy()
                
            if not items:
                ctk.CTkLabel(catalog_frame, text="❌ NO SE ENCONTRARON PIEZAS", font=("Arial", 14, "bold"), text_color=RED).pack(pady=40)
                return
                
            for pz in items:
                id_pz, nombre, cant, ubicacion = pz
                color_estado = GREEN if cant > 0 else RED
                estado_txt = f"{cant} ud." if cant > 0 else "0 ud."
                
                card = ctk.CTkFrame(catalog_frame, fg_color=BG_CARD, corner_radius=8, border_color="#3a464f", border_width=1)
                card.pack(fill="x", pady=5, padx=5)
                
                info_izq = ctk.CTkFrame(card, fg_color="transparent")
                info_izq.pack(side="left", padx=15, pady=10, fill="x", expand=True)
                ctk.CTkLabel(info_izq, text=f"📦 {nombre}", font=("Arial", 16, "bold"), text_color="white").pack(anchor="w")
                ctk.CTkLabel(info_izq, text=f"ID: {id_pz}", font=("Arial", 12), text_color="gray").pack(anchor="w")
                
                info_med = ctk.CTkFrame(card, fg_color="transparent", width=250)
                info_med.pack(side="left", padx=10, fill="y")
                ctk.CTkLabel(info_med, text="UBICACIÓN", font=("Arial", 10, "bold"), text_color="gray").pack(pady=(10, 0))
                ctk.CTkLabel(info_med, text=f"📍 {ubicacion}", font=("Arial", 14, "bold"), text_color=ORANGE).pack()
                
                info_der = ctk.CTkFrame(card, fg_color="transparent", width=180)
                info_der.pack(side="right", padx=20, fill="y")
                ctk.CTkLabel(info_der, text="EN STOCK", font=("Arial", 10, "bold"), text_color="gray").pack(pady=(10, 0))
                ctk.CTkLabel(info_der, text=estado_txt, font=("Arial", 18, "bold"), text_color=color_estado).pack()
                
                # Botón de ajuste rápido para el operario de almacén
                btn_ajustar = ctk.CTkButton(info_der, text="✏️ Ajustar", fg_color="transparent", border_width=1, border_color="gray", text_color="white", height=20, width=60)
                btn_ajustar.pack(pady=(5, 0))

        def buscar_btn_click():
            q = entry_sn.get().strip()
            if q == "":
                items = self.obtener_todo_almacen()
            else:
                items = self.buscar_piezas_almacen_multi(q)
            renderizar_catalogo(items)

        def limpiar_busqueda():
            entry_sn.delete(0, 'end')
            buscar_btn_click()

        ctk.CTkButton(sub_box, text="Buscar", fg_color=BG_ACTIVE_MENU, text_color=CYAN_ACTIVE, width=100, command=buscar_btn_click).pack(side="left")
        ctk.CTkButton(sub_box, text="🔄 Ver Todo", fg_color="#333333", text_color="white", hover_color="#444444", command=limpiar_busqueda).pack(side="left", padx=10)
        
        limpiar_busqueda()

    def crear_vista_solicitudes(self, parent):
        alarm_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        alarm_frame.pack(fill="both", expand=True, pady=10)
        
        header_tick = ctk.CTkFrame(alarm_frame, fg_color="transparent")
        header_tick.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(header_tick, text="SOLICITUDES DE REFACCIONES", font=("Arial", 18, "bold"), text_color=YELLOW).pack(side="left")
        ctk.CTkButton(header_tick, text="🔄 Refrescar", width=100, fg_color=BG_ACTIVE_MENU, command=lambda: self.cambiar_vista("SOLICITUDES")).pack(side="right")
        
        solicitudes = self.obtener_solicitudes_activas()
        if not solicitudes:
             ctk.CTkLabel(alarm_frame, text="✔️ NO HAY SOLICITUDES PENDIENTES", font=("Arial", 14, "bold"), text_color=GREEN).pack(pady=40)
             return
             
        for sol in solicitudes:
            id_t, maq, pieza, ubic, stock, fecha = sol
            
            box = ctk.CTkFrame(alarm_frame, fg_color=BG_MAIN, border_color=YELLOW, border_width=1)
            box.pack(fill="x", padx=30, pady=8)
            
            info_frame = ctk.CTkFrame(box, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=10)
            
            ctk.CTkLabel(info_frame, text=f"🚨 TICKET #{id_t} - PARA: {maq}", font=("Arial", 14, "bold"), text_color=RED).pack(anchor="w", pady=(0, 2))
            ctk.CTkLabel(info_frame, text=f"Entregar: {pieza}", font=("Arial", 16, "bold"), text_color="white").pack(anchor="w", pady=2)
            ctk.CTkLabel(info_frame, text=f"Ir a: {ubic} | Stock Actual: {stock}", font=("Arial", 12), text_color=ORANGE).pack(anchor="w", pady=2)
            
            # Botón de despachar
            if stock > 0:
                # El usuario no seleccionará, pasamos la refacción por defecto del sistema de pruebas (REF-001) 
                # En un sistema real, sacarías el ID de la pieza de la tabla
                btn_despachar = ctk.CTkButton(box, text="✅ DESPACHAR Y CERRAR", fg_color=GREEN, hover_color="#00b359", text_color="black", font=("Arial", 12, "bold"), width=150, height=40,
                                              command=lambda t=id_t: self.despachar_solicitud(t, "REF-001"))
                btn_despachar.pack(side="right", padx=20)
            else:
                ctk.CTkLabel(box, text="❌ SIN STOCK", font=("Arial", 14, "bold"), text_color=RED).pack(side="right", padx=20)

    def crear_vista_movimientos(self, parent):
        ctk.CTkLabel(parent, text="📥 ENTRADAS Y SALIDAS DE MATERIAL", font=("Arial", 24, "bold"), text_color="white").pack(anchor="w", pady=(0, 15))
        
        form_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        form_frame.pack(fill="both", expand=True, padx=50, pady=20)
        
        ctk.CTkLabel(form_frame, text="Registrar Nuevo Movimiento", font=("Arial", 18, "bold"), text_color=CYAN_ACTIVE).pack(pady=(20, 30))
        
        row1 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row1.pack(fill="x", padx=50, pady=10)
        ctk.CTkLabel(row1, text="Tipo de Movimiento:", font=("Arial", 14), width=150, anchor="w").pack(side="left")
        ctk.CTkComboBox(row1, values=["Entrada (Ingreso a Stock)", "Salida (Mantenimiento)", "Ajuste por Merma"], width=300).pack(side="left", padx=10)
        
        row2 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row2.pack(fill="x", padx=50, pady=10)
        ctk.CTkLabel(row2, text="Código de Pieza:", font=("Arial", 14), width=150, anchor="w").pack(side="left")
        ctk.CTkEntry(row2, width=300, placeholder_text="Ej: REF-001").pack(side="left", padx=10)
        
        row3 = ctk.CTkFrame(form_frame, fg_color="transparent")
        row3.pack(fill="x", padx=50, pady=10)
        ctk.CTkLabel(row3, text="Cantidad:", font=("Arial", 14), width=150, anchor="w").pack(side="left")
        ctk.CTkEntry(row3, width=100).pack(side="left", padx=10)
        
        ctk.CTkButton(form_frame, text="💾 REGISTRAR MOVIMIENTO", font=("Arial", 14, "bold"), fg_color=GREEN, hover_color="#00b359", text_color="black", height=45, width=250).pack(pady=40)

    def crear_vista_configuraciones(self, parent):
        conf_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        conf_frame.pack(fill="both", expand=True, pady=10)
        
        ctk.CTkLabel(conf_frame, text="CONFIGURACIONES DEL SISTEMA", font=("Arial", 20, "bold"), text_color=CYAN_ACTIVE).pack(pady=(30, 20))
        
        info_usuario = ctk.CTkFrame(conf_frame, fg_color=BG_MAIN, corner_radius=8)
        info_usuario.pack(pady=10, padx=50, fill="x")
        
        ctk.CTkLabel(info_usuario, text="👤 Usuario: Operario de Almacén", font=("Arial", 16, "bold"), text_color="white").pack(pady=(15, 5))
        ctk.CTkLabel(info_usuario, text="🏢 Planta: FIME Industrial | Nivel de Acceso: Almacén y Surtido", font=("Arial", 14), text_color="lightgray").pack(pady=(0, 15))
        
        btn_logout = ctk.CTkButton(conf_frame, text="🚪 CERRAR SESIÓN", 
                                   font=("Arial", 16, "bold"), 
                                   fg_color=RED, 
                                   hover_color="#cc0000",
                                   text_color="white",
                                   height=50,
                                   width=250,
                                   command=self.cerrar_sesion)
        btn_logout.pack(pady=40)
        
    def cerrar_sesion(self):
        # 1. Cierra la ventana del operario almacén
        self.destroy()
        
        # 2. Intenta abrir el archivo de login original
        try:
            ruta_login = os.path.join(BASE_DIR, "login.py")
            if os.path.exists(ruta_login):
                subprocess.Popen([sys.executable, ruta_login])
            else:
                print(f"ATENCIÓN: No se encontró 'login.py' en {BASE_DIR}.")
                print("Asegúrate de que tu archivo de inicio de sesión se llame 'login.py'")
        except Exception as e:
            print("Error al intentar volver al login:", e)

if __name__ == "__main__":
    app = OperarioAlmacenApp()
    app.mainloop()