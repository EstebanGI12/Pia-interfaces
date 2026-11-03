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
ORANGE = "#a86b0f"

class SupervisorMantenimientoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SUPERVISOR - Sistema de Mantenimiento y Almacén")
        
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
        ctk.CTkLabel(logo_frame, text="CMMS", font=("Arial", 22, "bold"), text_color="white").pack(side="left")
        ctk.CTkLabel(logo_frame, text=" TRACK", font=("Arial", 22, "bold"), text_color="#a3e635").pack(side="left")
        
        ctk.CTkLabel(self.sidebar, text="MANTENIMIENTO E INVENTARIO", font=("Arial", 8), text_color="gray").pack()
        ctk.CTkLabel(self.sidebar, text="🟢 ONLINE", font=("Arial", 12, "bold"), text_color=GREEN).pack(pady=(5, 30))
        
        self.menus = ["PANEL", "MÁQUINAS", "ALMACÉN", "⚠️ TICKETS", "ANALÍTICA", "CONFIGURACIONES"]
        self.menu_buttons = {}
        
        for m in self.menus:
            text_color = "white" if "TICKETS" not in m else YELLOW
            btn = ctk.CTkButton(self.sidebar, text=m, fg_color="transparent", text_color=text_color,
                                border_width=0, hover_color=BG_ACTIVE_MENU, anchor="w", font=("Arial", 14), height=45,
                                command=lambda name=m: self.cambiar_vista(name))
            btn.pack(pady=5, padx=0, fill="x")
            self.menu_buttons[m] = btn
            
        self.content_area = ctk.CTkFrame(self.main_container, fg_color=BG_MAIN, corner_radius=0)
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)
        
        self.vista_actual = "PANEL"
        self.cambiar_vista("PANEL")
        
        self.alarm_btn_ref = None
        self.estado_planta_ref = None
        self.alerta_mostrada = False
        
        self.verificar_falla_general()
        self.actualizar_estado_alerta()
        self.sembrar_almacen_si_vacio()
        self.sincronizar_fallas_tickets()

    def sembrar_almacen_si_vacio(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS almacen (id_pieza TEXT PRIMARY KEY, nombre_pieza TEXT, cantidad_disponible INTEGER, ubicacion TEXT)")
            c.execute("SELECT COUNT(*) FROM almacen")
            if c.fetchone()[0] == 0:
                datos = [
                    ("REF-001", "Banda Transportadora", 5, "Pasillo A - Estante 2"),
                    ("REF-002", "Sensor Óptico", 12, "Pasillo B - Cajón 1"),
                    ("REF-003", "Motor a Pasos", 0, "Pasillo C - Estante 4 (AGOTADO)"),
                    ("REF-004", "Engranaje 30 Dientes", 45, "Pasillo A - Cajón 5"),
                    ("REF-005", "Válvula Neumática", 2, "Pasillo B - Estante 1"),
                    ("REF-006", "PLC Siemens S7", 0, "Almacén Central (AGOTADO)"),
                    ("REF-007", "Cilindro Hidráulico", 8, "Pasillo D - Piso"),
                ]
                c.executemany("INSERT INTO almacen VALUES (?, ?, ?, ?)", datos)
                conn.commit()
            conn.close()
        except:
            pass

    def sincronizar_fallas_tickets(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            c.execute("SELECT id_maquina FROM maquinas WHERE estado='OPERANDO'")
            operando = c.fetchall()
            for (m_id,) in operando:
                c.execute("UPDATE alertas SET estado_ticket='RESUELTO' WHERE id_maquina=? AND estado_ticket='PENDIENTE'", (m_id,))
                
            c.execute("SELECT id_maquina FROM maquinas WHERE estado='FALLA'")
            fallas = c.fetchall()
            for (m_id,) in fallas:
                c.execute("SELECT COUNT(*) FROM alertas WHERE id_maquina=? AND estado_ticket='PENDIENTE'", (m_id,))
                if c.fetchone()[0] == 0:
                    ticket_id = f"TK-{random.randint(1000, 9999)}"
                    pieza = random.choice(["REF-001", "REF-002", "REF-004", "REF-005", "REF-007"])
                    c.execute("INSERT INTO alertas (id_ticket, id_maquina, pieza_requerida, estado_ticket, fecha_alerta) VALUES (?, ?, ?, ?, datetime('now'))", 
                              (ticket_id, m_id, pieza, 'PENDIENTE'))
                              
            conn.commit()
            conn.close()
        except Exception as e:
            pass
        self.after(2000, self.sincronizar_fallas_tickets)

    def verificar_falla_general(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM maquinas")
            total = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM maquinas WHERE estado='FALLA'")
            fallas = c.fetchone()[0]
            conn.close()
            
            if total > 0 and fallas == total:
                if not self.alerta_mostrada:
                    self.mostrar_alerta_general()
            else:
                if self.alerta_mostrada:
                    self.ocultar_alerta_general()
        except:
            pass
        self.after(3000, self.verificar_falla_general)

    def actualizar_estado_alerta(self):
        try:
            disp, _, total_maq, pendientes, maquinas_falla = self.obtener_resumen()
            if self.alarm_btn_ref and self.alarm_btn_ref.winfo_exists():
                if maquinas_falla > 0 or pendientes > 0:
                    texto = "Error en la planta" if maquinas_falla > 0 else f"⚠️ {pendientes} TICKET(S) PENDIENTE(S)"
                    self.alarm_btn_ref.configure(
                        text=texto,
                        fg_color="#3d1c23",
                        text_color=RED,
                        border_color=RED,
                    )
                else:
                    self.alarm_btn_ref.configure(text="✔️ PLANTA FUNCIONANDO", fg_color="#104a25", text_color=GREEN, border_color=GREEN)

            if self.estado_planta_ref and self.estado_planta_ref.winfo_exists():
                if maquinas_falla > 0:
                    self.estado_planta_ref.configure(text="Error en la planta", text_color=RED)
                elif pendientes == 0 and total_maq > 0 and disp == 100:
                    self.estado_planta_ref.configure(text="ÓPTIMO", text_color=GREEN)
                else:
                    self.estado_planta_ref.configure(text="MANTENIMIENTO\nREQUERIDO", text_color=YELLOW)
        except:
            pass
        self.after(3000, self.actualizar_estado_alerta)

    def mostrar_alerta_general(self):
        self.alerta_mostrada = True
        self.alerta_frame = ctk.CTkFrame(self, fg_color="#5e0000", corner_radius=0)
        self.alerta_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        self.lbl_falla = ctk.CTkLabel(self.alerta_frame, text="Error en la planta", font=("Arial", 50, "bold"), text_color="white")
        self.lbl_falla.pack(expand=True, pady=(80, 10))
        
        ctk.CTkLabel(self.alerta_frame, text="TODAS LAS MÁQUINAS ESTÁN FUERA DE SERVICIO", font=("Arial", 30, "bold"), text_color="#ffcc00").pack(pady=10)
        ctk.CTkLabel(self.alerta_frame, text="POR SEGURIDAD, SE REQUIERE DETENER TODOS LOS\nPROCESOS DISPONIBLES DURANTE 1 MINUTO.", font=("Arial", 24), text_color="white", justify="center").pack(pady=30)
        
        ctk.CTkButton(self.alerta_frame, text="Esperando intervención de Mantenimiento...", font=("Arial", 18), fg_color="#330000", hover_color="#330000", state="disabled", height=50, width=450).pack(pady=40)

    def ocultar_alerta_general(self):
        self.alerta_mostrada = False
        if hasattr(self, 'alerta_frame'):
            self.alerta_frame.destroy()
            self.cambiar_vista(self.vista_actual)

    def obtener_resumen(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM maquinas")
            total_maq = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM maquinas WHERE estado='OPERANDO'")
            maq_activas = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM alertas WHERE estado_ticket='PENDIENTE'")
            tickets_pendientes = c.fetchone()[0]

            c.execute("SELECT COUNT(*) FROM maquinas WHERE estado='FALLA'")
            maquinas_falla = c.fetchone()[0]
            
            conn.close()
            disp = round((maq_activas / total_maq) * 100, 1) if total_maq > 0 else 0
            return disp, maq_activas, total_maq, tickets_pendientes, maquinas_falla
        except:
            return 0.0, 0, 0, 0, 0

    def obtener_maquinas(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id_maquina, nombre, estado, ultima_revision FROM maquinas")
            datos = cursor.fetchall()
            conn.close()
            return datos
        except:
            return []

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
            
    def obtener_alertas_activas(self):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            query = "SELECT a.id_ticket, m.nombre, p.nombre_pieza, a.estado_ticket, a.fecha_alerta FROM alertas a JOIN maquinas m ON a.id_maquina = m.id_maquina JOIN almacen p ON a.pieza_requerida = p.id_pieza ORDER BY a.fecha_alerta DESC"
            cursor.execute(query)
            datos = cursor.fetchall()
            conn.close()
            return datos
        except:
            return []

    def limpiar_contenido(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()
            
    def actualizar_botones_sidebar(self, vista_activa):
        for m, btn in self.menu_buttons.items():
            if m == vista_activa:
                btn.configure(fg_color=BG_ACTIVE_MENU, text_color=CYAN_ACTIVE)
            else:
                default_color = YELLOW if "TICKETS" in m else "white"
                btn.configure(fg_color="transparent", text_color=default_color)

    def cambiar_vista(self, vista):
        self.vista_actual = vista
        self.estado_planta_ref = None
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
        
        _, _, _, pendientes, maquinas_falla = self.obtener_resumen()
        if maquinas_falla > 0:
            alerta_texto = "Error en la planta"
            alerta_color = RED
            bg_col = "#3d1c23"
        elif pendientes > 0:
            alerta_texto = f"⚠️ {pendientes} TICKET(S) PENDIENTE(S)"
            alerta_color = RED
            bg_col = "#3d1c23"
        else:
            alerta_texto = "✔️ PLANTA FUNCIONANDO"
            alerta_color = GREEN
            bg_col = "#104a25"
            
        self.alarm_btn_ref = ctk.CTkButton(header, text=alerta_texto, 
                                           fg_color=bg_col, 
                                           text_color=alerta_color, border_color=alerta_color, border_width=1, 
                                           hover_color="#4a1c23" if maquinas_falla > 0 or pendientes > 0 else "#166b36")
        self.alarm_btn_ref.pack(side="right", padx=10)
        
        ctk.CTkLabel(header, text="👤 SUPERVISOR MANTENIMIENTO", font=("Arial", 12), text_color="lightgray").pack(side="right", padx=20)

        if vista == "PANEL":
            self.crear_vista_panel(container)
        elif vista == "MÁQUINAS":
            self.crear_vista_maquinas(container)
        elif vista == "ALMACÉN":
            self.crear_vista_almacen(container)
        elif "TICKETS" in vista:
            self.crear_vista_tickets(container)
        elif vista == "ANALÍTICA":
            self.crear_vista_analitica(container)
        elif vista == "CONFIGURACIONES":
            self.crear_vista_configuraciones(container)

    def crear_vista_panel(self, parent):
        title_frame = ctk.CTkFrame(parent, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 15))
        
        titles_inner = ctk.CTkFrame(title_frame, fg_color="transparent")
        titles_inner.pack(side="left")
        ctk.CTkLabel(titles_inner, text="SUPERVISIÓN DE PLANTA", font=("Arial", 24, "bold"), text_color="white").pack(anchor="w")
        ctk.CTkLabel(titles_inner, text="PANEL GENERAL", font=("Arial", 16), text_color="white").pack(anchor="w")
        
        disp, maq_activas, total_maq, tickets_pendientes, maquinas_falla = self.obtener_resumen()
        
        kpi_frame = ctk.CTkFrame(parent, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=10)
        kpi_frame.grid_columnconfigure((0, 1, 2, 3), weight=0, minsize=250)
        kpi_frame.grid_anchor("center")
        
        box1 = ctk.CTkFrame(kpi_frame, fg_color=BG_CARD, corner_radius=10, width=250, height=130)
        box1.grid(row=0, column=0, padx=5)
        box1.grid_propagate(False)
        ctk.CTkLabel(box1, text="DISPONIBILIDAD GLOBAL", font=("Arial", 11, "bold"), text_color="white").pack(pady=(10, 0))
        
        canvas = tk.Canvas(box1, width=140, height=70, bg=BG_CARD, highlightthickness=0)
        canvas.pack(pady=5)
        canvas.create_arc(10, 10, 130, 130, start=0, extent=180, outline="#28323a", width=12, style="arc")
        color_disp = GREEN if disp >= 75 else (YELLOW if disp >= 50 else RED)
        extent_val = int(180 * (disp / 100)) if disp > 0 else 0
        canvas.create_arc(10, 10, 130, 130, start=180-extent_val, extent=extent_val, outline=color_disp, width=12, style="arc")
        ctk.CTkLabel(box1, text=f"{disp}%", font=("Arial", 20, "bold"), text_color="white", bg_color=BG_CARD).place(relx=0.5, rely=0.7, anchor="center")
        
        box2 = ctk.CTkFrame(kpi_frame, fg_color=BG_CARD, corner_radius=10, width=250, height=130)
        box2.grid(row=0, column=1, padx=5)
        box2.grid_propagate(False)
        ctk.CTkLabel(box2, text="MÁQUINAS OPERANDO", font=("Arial", 12, "bold"), text_color="white").pack(pady=(10, 15))
        ctk.CTkLabel(box2, text=f"{maq_activas} / {total_maq}", font=("Arial", 28, "bold"), text_color="white").pack()
        prog_frame = ctk.CTkFrame(box2, fg_color="transparent")
        prog_frame.pack(fill="x", padx=20, pady=10)
        prog = ctk.CTkProgressBar(prog_frame, progress_color=color_disp, fg_color="#28323a", height=10)
        prog.set(maq_activas/total_maq if total_maq>0 else 0)
        prog.pack(side="left", fill="x", expand=True)

        box3 = ctk.CTkFrame(kpi_frame, fg_color=BG_CARD, corner_radius=10, width=250, height=130)
        box3.grid(row=0, column=2, padx=5)
        box3.grid_propagate(False)
        ctk.CTkLabel(box3, text="TICKETS PENDIENTES", font=("Arial", 12, "bold"), text_color="white").pack(pady=(10, 10))
        ctk.CTkLabel(box3, text=str(tickets_pendientes), font=("Arial", 32, "bold"), text_color=RED if tickets_pendientes > 0 else GREEN).pack()
        if tickets_pendientes > 0:
            ctk.CTkLabel(box3, text="REQUIERE ATENCIÓN", font=("Arial", 11, "bold"), text_color=RED).pack(pady=5)
        else:
            ctk.CTkLabel(box3, text="TODO AL DÍA", font=("Arial", 11, "bold"), text_color=GREEN).pack(pady=5)

        box4 = ctk.CTkFrame(kpi_frame, fg_color=BG_CARD, corner_radius=10, width=250, height=130)
        box4.grid(row=0, column=3, padx=5)
        box4.grid_propagate(False)
        ctk.CTkLabel(box4, text="ESTADO DE LA PLANTA", font=("Arial", 12, "bold"), text_color="white").pack(pady=(10, 15))
        if maquinas_falla > 0:
            estado_texto, estado_color = "Error en la planta", RED
        elif tickets_pendientes == 0 and disp == 100:
            estado_texto, estado_color = "ÓPTIMO", GREEN
        else:
            estado_texto, estado_color = "MANTENIMIENTO\nREQUERIDO", YELLOW
        self.estado_planta_ref = ctk.CTkLabel(
            box4, text=estado_texto, font=("Arial", 20, "bold"), text_color=estado_color
        )
        self.estado_planta_ref.pack(pady=10)

        est_wrap = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10)
        est_wrap.pack(fill="both", expand=True, pady=(20, 0))
        
        header_est = ctk.CTkFrame(est_wrap, fg_color="transparent")
        header_est.pack(fill="x", padx=20, pady=(15, 0))
        ctk.CTkLabel(header_est, text="ESTADO DE MÁQUINAS EN PISO", font=("Arial", 18, "bold"), text_color="white").pack(side="left")
        ctk.CTkButton(header_est, text="🔄 Actualizar", width=100, fg_color=BG_ACTIVE_MENU, 
                      command=lambda: self.cambiar_vista("PANEL")).pack(side="right")
        
        est_flow = ctk.CTkFrame(est_wrap, fg_color="transparent")
        est_flow.pack(fill="both", expand=True, padx=20, pady=15)
        
        est_flow.grid_columnconfigure((0, 2, 4, 6), weight=0, minsize=240)
        est_flow.grid_columnconfigure((1, 3, 5), weight=0, minsize=15)
        est_flow.grid_anchor("center")
        
        maquinas_bd = self.obtener_maquinas()
        
        if not maquinas_bd:
            ctk.CTkLabel(est_flow, text="⚠️ NO SE ENCONTRÓ LA BASE DE DATOS", 
                         font=("Arial", 18, "bold"), text_color=RED).grid(row=0, column=0, columnspan=7, pady=40)
            return

        for i, maq in enumerate(maquinas_bd):
            id_maq, nombre, estado, ultima_rev = maq
            if estado == 'OPERANDO':
                color, bg_status, icon = GREEN, "#104a25", "✔️ "
            elif estado == 'FALLA':
                color, bg_status, icon = RED, "#4a1515", "❗ "
            else:
                color, bg_status, icon = YELLOW, "#4a4210", "⏸️ "
                
            box = ctk.CTkFrame(est_flow, fg_color=BG_STATION, corner_radius=10, width=240, height=440, border_color="#3a464f", border_width=1)
            box.grid(row=0, column=i*2)
            box.grid_propagate(False)
            ctk.CTkLabel(box, text=f"{id_maq}:\n{nombre}", font=("Arial", 14, "bold"), justify="left").pack(anchor="w", padx=15, pady=(20, 20))
            status_btn = ctk.CTkButton(box, text=f"{icon}{estado}", fg_color=bg_status, text_color=color, font=("Arial", 14, "bold"), hover=False, corner_radius=8)
            status_btn.pack(fill="x", padx=15, pady=(0, 20), side="bottom")

    def crear_vista_maquinas(self, parent):
        scroll_maq = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll_maq.pack(fill="both", expand=True, pady=10)
        
        header_maq = ctk.CTkFrame(scroll_maq, fg_color="transparent")
        header_maq.pack(fill="x", padx=10, pady=(0, 15))
        ctk.CTkLabel(header_maq, text="PANEL DE TELEMETRÍA Y CONTROL DE MÁQUINAS", font=("Arial", 20, "bold"), text_color=CYAN_ACTIVE).pack(side="left")
        ctk.CTkButton(header_maq, text="🔄 Refrescar", width=100, fg_color=BG_ACTIVE_MENU, command=lambda: self.cambiar_vista("MÁQUINAS")).pack(side="right")
        
        grid_maq = ctk.CTkFrame(scroll_maq, fg_color="transparent")
        grid_maq.pack(fill="both", expand=True)
        grid_maq.grid_columnconfigure((0, 1, 2), weight=0, minsize=340)
        grid_maq.grid_anchor("center")
        
        maquinas_bd = self.obtener_maquinas()
        
        if not maquinas_bd:
            ctk.CTkLabel(scroll_maq, text="❌ NO HAY DATOS DE MÁQUINAS", font=("Arial", 16, "bold"), text_color=RED).pack(pady=40)
            return
            
        row, col = 0, 0
        for maq in maquinas_bd:
            id_maq, nombre, estado, ultima_rev = maq
            
            b_color = "#3a464f"
            t_color = GREEN
            if estado == 'OPERANDO':
                t_color = GREEN
            elif estado == 'FALLA':
                t_color = RED
                b_color = RED
            else:
                t_color = ORANGE
                
            card = ctk.CTkFrame(grid_maq, fg_color=BG_STATION, corner_radius=12, width=340, border_color=b_color, border_width=1)
            card.grid(row=row, column=col, padx=10, pady=10)
            
            ctk.CTkLabel(card, text=f"{id_maq} - {nombre}", font=("Arial", 14, "bold"), text_color="white", anchor="w").pack(fill="x", padx=15, pady=(15, 5))
            
            status_frame = ctk.CTkFrame(card, fg_color="transparent")
            status_frame.pack(fill="x", padx=15, pady=(0, 15))
            canvas_dot = tk.Canvas(status_frame, width=12, height=12, bg=BG_STATION, highlightthickness=0)
            canvas_dot.pack(side="left", pady=3)
            canvas_dot.create_oval(2, 2, 10, 10, fill=t_color, outline="")
            ctk.CTkLabel(status_frame, text=estado, font=("Arial", 13, "bold"), text_color=t_color).pack(side="left", padx=5)
            
            params_frame = ctk.CTkFrame(card, fg_color="transparent")
            params_frame.pack(fill="x", padx=15, pady=10)
            params_frame.grid_columnconfigure((0, 1), weight=1)
            
            val_izq, val_der = "0", "0"
            lbl_izq, lbl_der = "PARÁMETRO", "VALOR"
            
            if estado == 'FALLA':
                val_izq = "---"
                val_der = "---"
                lbl_izq = "SIN CONEXIÓN"
                lbl_der = "SIN COMUNICACIÓN"
            else:
                if 'Fresadora' in nombre or 'Corte' in nombre or 'CNC' in nombre:
                    lbl_izq = "VELOCIDAD"
                    val_izq = f"{random.randint(1800, 3200)} RPM"
                    lbl_der = "TEMPERATURA"
                    val_der = f"{random.randint(35, 55)}°C"
                elif 'Prensa' in nombre:
                    lbl_izq = "PRESIÓN"
                    val_izq = f"{round(random.uniform(10.5, 15.2), 1)} bar"
                    lbl_der = "TEMPERATURA"
                    val_der = f"{random.randint(30, 45)}°C"
                elif 'Horno' in nombre or 'Soldadura' in nombre:
                    lbl_izq = "CORRIENTE / ACTUAL"
                    val_izq = f"{random.randint(120, 220)} A"
                    lbl_der = "TEMPERATURA"
                    val_der = f"{random.randint(180, 280)}°C"
                elif 'Robot' in nombre:
                    if estado != 'OPERANDO':
                        val_izq = "0 RPM"
                        val_der = f"{random.randint(25, 35)}°C"
                    else:
                        val_izq = f"{random.randint(100, 300)} RPM"
                        val_der = f"{random.randint(30, 40)}°C"
                    lbl_izq = "VELOCIDAD"
                    lbl_der = "TEMPERATURA"
                else:
                    lbl_izq = "TELEMETRÍA"
                    val_izq = "APOYAR"
                    lbl_der = "SALUD"
                    val_der = "100%"
            
            v_box_l = ctk.CTkFrame(params_frame, fg_color="transparent")
            v_box_l.grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(v_box_l, text=lbl_izq, font=("Arial", 11), text_color="lightgray").pack()
            ctk.CTkLabel(v_box_l, text=val_izq, font=("Arial", 14, "bold"), text_color="white").pack(pady=(2,0))
            
            v_box_r = ctk.CTkFrame(params_frame, fg_color="transparent")
            v_box_r.grid(row=0, column=1, sticky="e")
            ctk.CTkLabel(v_box_r, text=lbl_der, font=("Arial", 11), text_color="lightgray").pack()
            ctk.CTkLabel(v_box_r, text=val_der, font=("Arial", 14, "bold"), text_color="white").pack(pady=(2,0))
            
            ctk.CTkFrame(card, fg_color="#3a464f", height=1).pack(fill="x", padx=15, pady=10)
            
            if estado == 'FALLA':
                alert_frame = ctk.CTkFrame(card, fg_color="transparent")
                alert_frame.pack(fill="x", padx=15, pady=5)
                ctk.CTkLabel(alert_frame, text="⚠️ ERROR DE SISTEMA DETECTADO", font=("Arial", 12, "bold"), text_color=YELLOW, anchor="w").pack(fill="x")
                
                btn_detalles = ctk.CTkButton(card, text="⚠️ LLAMAR A MANTENIMIENTO", fg_color="transparent", border_width=2, border_color=YELLOW, text_color=YELLOW, hover_color="#333300", font=("Arial", 12, "bold"))
                btn_detalles.pack(pady=(10, 15), padx=15, fill="x")
            else:
                hrs_manto = random.randint(10, 450)
                txt_hrs = f"MANTENIMIENTO EN: {hrs_manto} HRS"
                col_hrs = "lightgray"
                if hrs_manto < 24:
                    col_hrs = YELLOW
                
                ctk.CTkLabel(card, text=txt_hrs, font=("Arial", 11), text_color=col_hrs).pack(pady=(5, 10))
                
                btn_detalles = ctk.CTkButton(card, text="DETALLES >", width=120, fg_color="transparent", border_width=1, border_color=CYAN_ACTIVE, text_color=CYAN_ACTIVE, hover_color=BG_ACTIVE_MENU,
                                             command=lambda m_id=id_maq, m_name=nombre: self.mostrar_detalles_maquina(m_id, m_name))
                btn_detalles.pack(pady=(0, 15))
            
            col += 1
            if col > 2:
                col = 0
                row += 1

    def mostrar_detalles_maquina(self, m_id, m_name):
        ventana_detalles = ctk.CTkToplevel(self)
        ventana_detalles.title(f"Detalles de Máquina - {m_id}")
        ventana_detalles.geometry("500x550")
        ventana_detalles.attributes("-topmost", True)
        ventana_detalles.configure(fg_color=BG_MAIN)
        ventana_detalles.grab_set() 
        
        header = ctk.CTkFrame(ventana_detalles, fg_color=BG_CARD, corner_radius=0)
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text=f"{m_id} - {m_name}", font=("Arial", 20, "bold"), text_color=CYAN_ACTIVE).pack(pady=20)
        
        zona = random.choice(["ZONA A - Ensamblaje", "ZONA B - Corte", "ZONA C - Soldadura", "ZONA D - Empaque"])
        operario = random.choice(["Juan Pérez", "Carlos Slim", "María Rodríguez", "Sin Asignar"])
        ip_red = f"192.168.1.{random.randint(10, 200)}"
        piezas_compatibles = random.sample(["REF-001 Banda", "REF-002 Sensor", "REF-004 Engranaje", "REF-005 Válvula", "REF-007 Cilindro"], 2)
        
        info_frame = ctk.CTkFrame(ventana_detalles, fg_color="transparent")
        info_frame.pack(fill="both", expand=True, padx=30)
        
        def add_detail(parent, label, value):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", pady=10)
            ctk.CTkLabel(row, text=label, font=("Arial", 12, "bold"), text_color="lightgray", width=150, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=value, font=("Arial", 14), text_color="white", anchor="w").pack(side="left")
        
        add_detail(info_frame, "Ubicación en Piso:", zona)
        add_detail(info_frame, "Operario Asignado:", operario)
        add_detail(info_frame, "Dirección IP:", ip_red)
        
        ctk.CTkFrame(info_frame, fg_color="#3a464f", height=1).pack(fill="x", pady=15)
        
        ctk.CTkLabel(info_frame, text="Refacciones Compatibles:", font=("Arial", 14, "bold"), text_color=ORANGE, anchor="w").pack(fill="x", pady=(5, 10))
        for pz in piezas_compatibles:
            ctk.CTkLabel(info_frame, text=f"• {pz}", font=("Arial", 14), text_color="white", anchor="w").pack(fill="x", padx=15, pady=2)
            
        ctk.CTkFrame(info_frame, fg_color="#3a464f", height=1).pack(fill="x", pady=15)
            
        ctk.CTkButton(ventana_detalles, text="Cerrar Detalles", command=ventana_detalles.destroy, fg_color=BG_ACTIVE_MENU, hover_color="#1b5a70").pack(pady=20)

    def crear_vista_almacen(self, parent):
        search_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        search_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(search_frame, text="Catálogo Global de Refacciones y Stock", font=("Arial", 18, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
        
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
                ctk.CTkLabel(catalog_frame, text="❌ NO SE ENCONTRARON PIEZAS EN EL CATÁLOGO", font=("Arial", 14, "bold"), text_color=RED).pack(pady=40)
                return
                
            for pz in items:
                id_pz, nombre, cant, ubicacion = pz
                color_estado = GREEN if cant > 0 else RED
                estado_txt = f"✔️ EN STOCK: {cant} ud." if cant > 0 else "❌ AGOTADO"
                
                card = ctk.CTkFrame(catalog_frame, fg_color=BG_CARD, corner_radius=8)
                card.pack(fill="x", pady=5, padx=5)
                
                info_izq = ctk.CTkFrame(card, fg_color="transparent")
                info_izq.pack(side="left", padx=15, pady=10, fill="x", expand=True)
                ctk.CTkLabel(info_izq, text=f"📦 {nombre}", font=("Arial", 16, "bold"), text_color="white").pack(anchor="w")
                ctk.CTkLabel(info_izq, text=f"ID: {id_pz}", font=("Arial", 12), text_color="gray").pack(anchor="w")
                
                info_med = ctk.CTkFrame(card, fg_color="transparent", width=250)
                info_med.pack(side="left", padx=10, fill="y")
                ctk.CTkLabel(info_med, text="UBICACIÓN", font=("Arial", 10, "bold"), text_color="gray").pack(pady=(10, 0))
                ctk.CTkLabel(info_med, text=f"📍 {ubicacion}", font=("Arial", 14, "bold"), text_color=CYAN_ACTIVE).pack()
                
                info_der = ctk.CTkFrame(card, fg_color="transparent", width=180)
                info_der.pack(side="right", padx=20, fill="y")
                ctk.CTkLabel(info_der, text=estado_txt, font=("Arial", 14, "bold"), text_color=color_estado).pack(pady=15)

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
        ctk.CTkButton(sub_box, text="🔄 Ver Todo el Catálogo", fg_color="#333333", text_color="white", hover_color="#444444", command=limpiar_busqueda).pack(side="left", padx=10)
        
        limpiar_busqueda()

    def crear_vista_tickets(self, parent):
        alarm_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        alarm_frame.pack(fill="both", expand=True, pady=10)
        
        header_tick = ctk.CTkFrame(alarm_frame, fg_color="transparent")
        header_tick.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(header_tick, text="TICKETS DE MANTENIMIENTO", font=("Arial", 18, "bold"), text_color=RED).pack(side="left")
        ctk.CTkButton(header_tick, text="🔄 Refrescar", width=100, fg_color=BG_ACTIVE_MENU, command=lambda: self.cambiar_vista("⚠️ TICKETS")).pack(side="right")
        
        alertas = self.obtener_alertas_activas()
        if not alertas:
             ctk.CTkLabel(alarm_frame, text="✔️ PLANTA FUNCIONANDO AL 100%\nNO HAY TICKETS PENDIENTES", font=("Arial", 16, "bold"), text_color=GREEN, justify="center").pack(pady=60)
             return
             
        for al in alertas:
            id_t, maq, pieza, estado, fecha = al
            box = ctk.CTkFrame(alarm_frame, fg_color=BG_MAIN, border_color=RED, border_width=1)
            box.pack(fill="x", padx=30, pady=8)
            ctk.CTkLabel(box, text=f"🚨 TICKET #{id_t} - {maq}", font=("Arial", 14, "bold"), text_color=RED).pack(anchor="w", padx=15, pady=(10, 2))
            ctk.CTkLabel(box, text=f"Refacción: {pieza}", font=("Arial", 13, "bold"), text_color=YELLOW).pack(anchor="w", padx=15, pady=2)

    def crear_vista_analitica(self, parent):
        scroll_ana = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll_ana.pack(fill="both", expand=True)
        
        ctk.CTkLabel(scroll_ana, text="📊 DASHBOARD DE ANALÍTICA INDUSTRIAL", font=("Arial", 22, "bold"), text_color=CYAN_ACTIVE).pack(anchor="w", pady=(0, 15))
        
        grid_graficas = ctk.CTkFrame(scroll_ana, fg_color="transparent")
        grid_graficas.pack(fill="both", expand=True)
        grid_graficas.grid_columnconfigure((0, 1), weight=1)
        
        plt.style.use('dark_background')
        
        # Gráfica 1
        card1 = ctk.CTkFrame(grid_graficas, fg_color=BG_CARD, corner_radius=12)
        card1.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        ctk.CTkLabel(card1, text="📉 Fallas Presentadas en la Semana", font=("Arial", 16, "bold")).pack(pady=(15, 5))
        
        fig1, ax1 = plt.subplots(figsize=(5, 3.5), dpi=100)
        fig1.patch.set_facecolor('#43525c')
        ax1.set_facecolor('#28323a')
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
        fallas_sem = [3, 5, 2, 6, 4]
        ax1.plot(dias, fallas_sem, marker='o', color='#ff4444', linewidth=2.5, markersize=8)
        ax1.set_title("Total Fallas: 20", fontsize=11, color='white')
        ax1.set_ylabel("N° Fallas", fontsize=10, color='white')
        ax1.tick_params(axis='x', colors='white', labelsize=9)
        ax1.tick_params(axis='y', colors='white', labelsize=9)
        ax1.grid(True, linestyle='--', alpha=0.3, color='gray')
        fig1.tight_layout()
        
        canvas1 = FigureCanvasTkAgg(fig1, master=card1)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)
        
        # Gráfica 2
        card2 = ctk.CTkFrame(grid_graficas, fg_color=BG_CARD, corner_radius=12)
        card2.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        ctk.CTkLabel(card2, text="🛠️ Estado de Reparación de Fallas", font=("Arial", 16, "bold")).pack(pady=(15, 5))
        
        fig2, ax2 = plt.subplots(figsize=(5, 3.5), dpi=100)
        fig2.patch.set_facecolor('#43525c')
        ax2.set_facecolor('#28323a')
        estados = ['Reparadas', 'En Proceso', 'Pendientes']
        cantidades = [16, 2, 2]
        colores = ['#00e676', '#ffd600', '#ff4444']
        ax2.bar(estados, cantidades, color=colores, width=0.6)
        ax2.set_ylabel("Cantidad", fontsize=10, color='white')
        ax2.tick_params(axis='x', colors='white', labelsize=9)
        ax2.tick_params(axis='y', colors='white', labelsize=9)
        ax2.grid(axis='y', linestyle='--', alpha=0.3, color='gray')
        fig2.tight_layout()
        
        canvas2 = FigureCanvasTkAgg(fig2, master=card2)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)
        
        # Gráfica 3
        card3 = ctk.CTkFrame(grid_graficas, fg_color=BG_CARD, corner_radius=12)
        card3.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        ctk.CTkLabel(card3, text="⚙️ Operaciones Determinadas (Módulos Terminados en Planta)", font=("Arial", 16, "bold")).pack(pady=(15, 5))
        
        fig3, ax3 = plt.subplots(figsize=(10, 3.5), dpi=100)
        fig3.patch.set_facecolor('#43525c')
        ax3.set_facecolor('#28323a')
        modulos = ['MQ-01 (Fresadora)', 'MQ-02 (Prensa)', 'MQ-03 (Robot Kuka)', 'MQ-04 (Horno)']
        operaciones_completadas = [142, 118, 95, 130]
        bars = ax3.barh(modulos, operaciones_completadas, color='#00d2ff', height=0.5)
        ax3.set_xlabel("Operaciones Exitosas Terminadas", fontsize=10, color='white')
        ax3.tick_params(axis='x', colors='white', labelsize=9)
        ax3.tick_params(axis='y', colors='white', labelsize=9)
        ax3.grid(axis='x', linestyle='--', alpha=0.3, color='gray')
        for bar in bars:
            width = bar.get_width()
            ax3.text(width + 2, bar.get_y() + bar.get_height()/2, f'{width} op.', 
                     va='center', ha='left', color='white', fontsize=10, fontweight='bold')
        fig3.tight_layout()
        
        canvas3 = FigureCanvasTkAgg(fig3, master=card3)
        canvas3.draw()
        canvas3.get_tk_widget().pack(fill="both", expand=True, padx=15, pady=15)

    def crear_vista_configuraciones(self, parent):
        conf_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        conf_frame.pack(fill="both", expand=True, pady=10)
        
        ctk.CTkLabel(conf_frame, text="CONFIGURACIONES DEL SISTEMA", font=("Arial", 20, "bold"), text_color=CYAN_ACTIVE).pack(pady=(30, 20))
        
        info_usuario = ctk.CTkFrame(conf_frame, fg_color=BG_MAIN, corner_radius=8)
        info_usuario.pack(pady=10, padx=50, fill="x")
        
        ctk.CTkLabel(info_usuario, text="👤 Usuario: Supervisor de Mantenimiento", font=("Arial", 16, "bold"), text_color="white").pack(pady=(15, 5))
        ctk.CTkLabel(info_usuario, text="🏢 Planta: FIME Industrial | Nivel de Acceso: Total", font=("Arial", 14), text_color="lightgray").pack(pady=(0, 15))
        
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
        self.destroy()
        try:
            ruta_login = os.path.join(BASE_DIR, "login.py")
            if os.path.exists(ruta_login):
                subprocess.Popen([sys.executable, ruta_login])
            else:
                print(f"ATENCIÓN: No se encontró 'login.py' en {BASE_DIR}.")
        except Exception as e:
            print("Error al intentar volver al login:", e)

if __name__ == "__main__":
    app = SupervisorMantenimientoApp()
    app.mainloop()