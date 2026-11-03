import customtkinter as ctk
import tkinter as tk
import sqlite3

# Configuración base
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG_SIDEBAR = "#212b33"
BG_MAIN = "#28323a"
BG_CARD = "#43525c"
BG_STATION = "#3a464f"
CYAN_ACTIVE = "#00d2ff"
BG_ACTIVE_MENU = "#184555"

GREEN = "#00e676"
YELLOW = "#ffd600"
RED = "#ff4444"

class WipTrackApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WIP TRACK - Sistema de Rastreo Industrial")
        
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
        ctk.CTkLabel(logo_frame, text=" TRACK", font=("Arial", 22, "bold"), text_color="#a3e635").pack(side="left")
        
        ctk.CTkLabel(self.sidebar, text="SISTEMAS DE RASTREO INDUSTRIAL", font=("Arial", 8), text_color="gray").pack()
        ctk.CTkLabel(self.sidebar, text="🟢 ONLINE", font=("Arial", 12, "bold"), text_color=GREEN).pack(pady=(5, 30))
        
        self.menus = ["PANEL", "EQUIPO", "TRAZABILIDAD", "⚠️ ALARMAS (2)", "ANALITICA", "CONFIGURACIONES"]
        self.menu_buttons = {}
        
        for m in self.menus:
            text_color = "white" if "ALARMAS" not in m else YELLOW
            btn = ctk.CTkButton(self.sidebar, text=m, fg_color="transparent", text_color=text_color,
                                border_width=0, hover_color=BG_ACTIVE_MENU, anchor="w", font=("Arial", 14), height=45,
                                command=lambda name=m: self.cambiar_vista(name))
            btn.pack(pady=5, padx=0, fill="x")
            self.menu_buttons[m] = btn
            
        self.content_area = ctk.CTkFrame(self.main_container, fg_color=BG_MAIN, corner_radius=0)
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)
        
        self.cambiar_vista("PANEL")

    # ----- FUNCIONES DE LECTURA A LA BASE DE DATOS -----
    def obtener_kpis(self):
        try:
            conn = sqlite3.connect('wiptrack.db')
            cursor = conn.cursor()
            cursor.execute("SELECT oee, tasa_desechos, disponibilidad, actuacion FROM kpis WHERE id = 1")
            datos = cursor.fetchone()
            conn.close()
            return datos if datos else (0.0, 0.0, 0.0, 0.0)
        except:
            return (0.0, 0.0, 0.0, 0.0)

    def obtener_estaciones(self):
        try:
            conn = sqlite3.connect('wiptrack.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, nombre, estado, rendimiento FROM estaciones")
            datos = cursor.fetchall()
            conn.close()
            return datos
        except:
            return []

    def buscar_pieza(self, sn):
        try:
            conn = sqlite3.connect('wiptrack.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT p.sn, p.tipo_motor, e.nombre, p.estado, p.fecha_registro 
                FROM piezas p 
                LEFT JOIN estaciones e ON p.estacion_actual = e.id 
                WHERE p.sn = ?
            ''', (sn,))
            datos = cursor.fetchone()
            conn.close()
            return datos
        except:
            return None

    # ----- LÓGICA DE LA INTERFAZ -----
    def limpiar_contenido(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()
            
    def actualizar_botones_sidebar(self, vista_activa):
        for m, btn in self.menu_buttons.items():
            if m == vista_activa:
                btn.configure(fg_color=BG_ACTIVE_MENU, text_color=CYAN_ACTIVE)
            else:
                default_color = YELLOW if "ALARMAS" in m else "white"
                btn.configure(fg_color="transparent", text_color=default_color)

    def cambiar_vista(self, vista):
        self.limpiar_contenido()
        self.actualizar_botones_sidebar(vista)
        
        container = ctk.CTkFrame(self.content_area, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        container.grid_rowconfigure(2, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        header = ctk.CTkFrame(container, height=40, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text="DIA: 12-10-2026", font=("Arial", 12), text_color="lightgray").pack(side="left", padx=20)
        ctk.CTkLabel(header, text="🕒 HORA: 2:50:45 📶", font=("Arial", 12), text_color="lightgray").pack(side="left", padx=20)
        
        alarm_btn = ctk.CTkButton(header, text="⚠️ ALARMA ACTIVADA / RASTREADOR DE NOTIFICACION", 
                                  fg_color="#3d1c23", text_color=RED, border_color=RED, border_width=1, hover_color="#4a1c23")
        alarm_btn.pack(side="right", padx=10)
        
        ctk.CTkLabel(header, text="👤 SUPERVISOR: NoobMaster69", font=("Arial", 12), text_color="lightgray").pack(side="right", padx=20)

        if vista == "PANEL":
            self.crear_vista_panel(container)
        elif vista == "EQUIPO":
            self.crear_vista_equipo(container)
        elif vista == "TRAZABILIDAD":
            self.crear_vista_trazabilidad(container)
        elif "ALARMAS" in vista:
            self.crear_vista_alarmas(container)
        elif vista == "ANALITICA":
            self.crear_vista_analitica(container)
        elif vista == "CONFIGURACIONES":
            self.crear_vista_configuraciones(container)

    def crear_vista_panel(self, parent):
        title_frame = ctk.CTkFrame(parent, fg_color="transparent")
        title_frame.pack(fill="x", pady=(0, 15))
        
        titles_inner = ctk.CTkFrame(title_frame, fg_color="transparent")
        titles_inner.pack(side="left")
        ctk.CTkLabel(titles_inner, text="LINEA DE MONTAJE 3", font=("Arial", 24, "bold"), text_color="white").pack(anchor="w")
        ctk.CTkLabel(titles_inner, text="PANEL GENERAL", font=("Arial", 16), text_color="white").pack(anchor="w")
        
        badge_online = ctk.CTkFrame(title_frame, fg_color="#104a25", corner_radius=8, border_color=GREEN, border_width=1)
        badge_online.pack(side="left", padx=30)
        ctk.CTkLabel(badge_online, text="🟢 SISTEMA ONLINE", font=("Arial", 18, "bold"), text_color=GREEN).pack(padx=15, pady=5)
        
        # --- CARGAR KPIs DE LA BASE DE DATOS ---
        kpi_datos = self.obtener_kpis()
        oee, desechos, _, _ = kpi_datos
        
        kpi_frame = ctk.CTkFrame(parent, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=10)
        kpi_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        box1 = ctk.CTkFrame(kpi_frame, fg_color=BG_CARD, corner_radius=10, height=130)
        box1.grid(row=0, column=0, sticky="nsew", padx=5)
        box1.grid_propagate(False)
        ctk.CTkLabel(box1, text="EFICIENCIA GLOBAL (OEE BD)", font=("Arial", 11, "bold"), text_color="white").pack(pady=(10, 0))
        
        canvas = tk.Canvas(box1, width=140, height=70, bg=BG_CARD, highlightthickness=0)
        canvas.pack(pady=5)
        canvas.create_arc(10, 10, 130, 130, start=0, extent=180, outline="#28323a", width=12, style="arc")
        canvas.create_arc(10, 10, 130, 130, start=45, extent=135, outline=GREEN, width=12, style="arc")
        ctk.CTkLabel(box1, text=f"{oee}%", font=("Arial", 20, "bold"), text_color="white", bg_color=BG_CARD).place(relx=0.5, rely=0.7, anchor="center")
        ctk.CTkLabel(box1, text="EN VIVO", font=("Arial", 9, "bold"), text_color=GREEN, bg_color=BG_CARD).place(relx=0.85, rely=0.5, anchor="center")

        box2 = ctk.CTkFrame(kpi_frame, fg_color=BG_CARD, corner_radius=10, height=130)
        box2.grid(row=0, column=1, sticky="nsew", padx=5)
        box2.grid_propagate(False)
        ctk.CTkLabel(box2, text="PRODUCCION / OBJETIVO", font=("Arial", 12, "bold"), text_color="white").pack(pady=(10, 15))
        ctk.CTkLabel(box2, text="1240 / 1500", font=("Arial", 28, "bold"), text_color="white").pack()
        prog_frame = ctk.CTkFrame(box2, fg_color="transparent")
        prog_frame.pack(fill="x", padx=20, pady=10)
        prog = ctk.CTkProgressBar(prog_frame, progress_color=GREEN, fg_color="#28323a", height=10)
        prog.set(0.82)
        prog.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(prog_frame, text="82%", font=("Arial", 10)).pack(side="right", padx=(10,0))

        box3 = ctk.CTkFrame(kpi_frame, fg_color=BG_CARD, corner_radius=10, height=130)
        box3.grid(row=0, column=2, sticky="nsew", padx=5)
        box3.grid_propagate(False)
        ctk.CTkLabel(box3, text="ALARMAS ACTIVAS", font=("Arial", 12, "bold"), text_color="white").pack(pady=(10, 10))
        ctk.CTkLabel(box3, text="2", font=("Arial", 32, "bold"), text_color=RED).pack()
        warn_frame = ctk.CTkFrame(box3, fg_color="transparent")
        warn_frame.pack(pady=5)
        ctk.CTkLabel(warn_frame, text="1 CRITICA,", font=("Arial", 11, "bold"), text_color=RED).pack(side="left")
        ctk.CTkLabel(warn_frame, text=" 1 ADVERTENCIA", font=("Arial", 11, "bold"), text_color=YELLOW).pack(side="left")

        box4 = ctk.CTkFrame(kpi_frame, fg_color=BG_CARD, corner_radius=10, height=130)
        box4.grid(row=0, column=3, sticky="nsew", padx=5)
        box4.grid_propagate(False)
        ctk.CTkLabel(box4, text="TIEMPO DE CICLO PROMEDIO", font=("Arial", 12, "bold"), text_color="white").pack(pady=(10, 15))
        ctk.CTkLabel(box4, text="42.5 s", font=("Arial", 28, "bold"), text_color="white").pack()
        ctk.CTkLabel(box4, text="DENTRO DEL LIMITE", font=("Arial", 11, "bold"), text_color=GREEN).pack(pady=10)

        # --- CARGAR ESTACIONES DE LA BASE DE DATOS ---
        est_wrap = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10)
        est_wrap.pack(fill="both", expand=True, pady=(20, 0))
        
        header_est = ctk.CTkFrame(est_wrap, fg_color="transparent")
        header_est.pack(fill="x", padx=20, pady=(15, 0))
        ctk.CTkLabel(header_est, text="ESTADO DE ESTACIONES (BASE DE DATOS)", font=("Arial", 18, "bold"), text_color="white").pack(side="left")
        
        ctk.CTkButton(header_est, text="🔄 Actualizar", width=100, fg_color=BG_ACTIVE_MENU, 
                      command=lambda: self.cambiar_vista("PANEL")).pack(side="right")
        
        est_flow = ctk.CTkFrame(est_wrap, fg_color="transparent")
        est_flow.pack(fill="both", expand=True, padx=20, pady=15)
        
        est_flow.grid_columnconfigure((0,2,4,6), weight=3)
        est_flow.grid_columnconfigure((1,3,5), weight=1)
        est_flow.grid_rowconfigure(0, weight=1)
        
        estaciones_bd = self.obtener_estaciones()
        
        for i, est in enumerate(estaciones_bd):
            id_est, nombre, estado, rend = est
            
            if estado == 'OPERANDO':
                color, bg_status, icon = GREEN, "#104a25", "✔️ "
            elif estado == 'FALLA':
                color, bg_status, icon = RED, "#4a1515", "❗ "
            else:
                color, bg_status, icon = YELLOW, "#4a4210", "⏸️ "
                
            box = ctk.CTkFrame(est_flow, fg_color=BG_STATION, corner_radius=10)
            box.grid(row=0, column=i*2, sticky="nsew")
            
            ctk.CTkLabel(box, text=f"ESTACION {id_est}:\n{nombre}", font=("Arial", 14, "bold"), justify="left").pack(anchor="w", padx=15, pady=(20, 20))
            
            status_btn = ctk.CTkButton(box, text=f"{icon}{estado}", fg_color=bg_status, text_color=color, 
                                       font=("Arial", 14, "bold"), hover=False, corner_radius=8)
            status_btn.pack(fill="x", padx=15, pady=(0, 20), side="bottom")
            
            if i < 3:
                ctk.CTkLabel(est_flow, text="➔", font=("Arial", 24, "bold"), text_color="gray").grid(row=0, column=i*2+1)


    def crear_vista_equipo(self, parent):
        info_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        info_frame.pack(fill="both", expand=True, pady=10)
        ctk.CTkLabel(info_frame, text="ESTADO DEL EQUIPAMIENTO INDUSTRIAL", font=("Arial", 18, "bold"), text_color=CYAN_ACTIVE).pack(pady=20)
        equipos = [
            "• ESTACION 1 - CORTADORA CNC | 2800 RPM | TEMP: 42°C | Mantenimiento en: 140 hrs",
            "• ESTACION 2 - ROMPEPRENSA | 12.4 bar | TEMP: 38°C | Mantenimiento en: 82 hrs",
            "• ESTACION 3 - ROBOT DE ENSAMBLE | 0 RPM | TEMP: 31°C | Mantenimiento en: 35 hrs",
            "• ESTACION 4 - ESTACION DE SOLDADURA | 180 A | TEMP: 240°C | Mantenimiento en: 12 hrs",
            "• ESTACION 5 - SISTEMA DE INSPECCION | ⚠️ FALLA / CÁMARA ERROR",
            "• ESTACION 6 - EMPACAR Y SELLAR | 🟢 SALUD 100% | Mantenimiento en: 400 hrs"
        ]
        for eq in equipos:
            ctk.CTkLabel(info_frame, text=eq, font=("Arial", 14), anchor="w").pack(anchor="w", padx=30, pady=8)

    # --- TRAZABILIDAD CONECTADA A BASE DE DATOS ---
    def crear_vista_trazabilidad(self, parent):
        search_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        search_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(search_frame, text="Búsqueda de Historial de Pieza (BD en Vivo)", font=("Arial", 16, "bold")).pack(anchor="w", padx=20, pady=(15, 5))
        
        sub_box = ctk.CTkFrame(search_frame, fg_color="transparent")
        sub_box.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkLabel(sub_box, text="ID / Número de Serie:", font=("Arial", 12)).pack(side="left", padx=(0, 10))
        
        entry_sn = ctk.CTkEntry(sub_box, width=250)
        entry_sn.pack(side="left", padx=(0, 10))
        entry_sn.insert(0, "SN-2026-98745")
        
        result_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        result_frame.pack(fill="both", expand=True, pady=10)
        
        def buscar_btn_click():
            for widget in result_frame.winfo_children():
                widget.destroy()
                
            sn = entry_sn.get()
            pieza = self.buscar_pieza(sn)
            
            if pieza:
                sn_db, tipo, estacion, estado, fecha = pieza
                color = GREEN if estado == 'APROBADO' else (RED if estado == 'RECHAZADO' else YELLOW)
                
                ctk.CTkLabel(result_frame, text=f"RESULTADO: {tipo} ({estado})", font=("Arial", 18, "bold"), text_color=color).pack(pady=(20,10))
                ctk.CTkLabel(result_frame, text=f"Número de Serie: {sn_db}", font=("Arial", 14)).pack(pady=5)
                ctk.CTkLabel(result_frame, text=f"Ubicación actual: {estacion}", font=("Arial", 14)).pack(pady=5)
                ctk.CTkLabel(result_frame, text=f"Última actualización: {fecha}", font=("Arial", 13), text_color="gray").pack(pady=15)
            else:
                ctk.CTkLabel(result_frame, text="❌ PIEZA NO ENCONTRADA EN LA BASE DE DATOS", font=("Arial", 16, "bold"), text_color=RED).pack(pady=30)
        
        ctk.CTkButton(sub_box, text="Buscar", fg_color=BG_ACTIVE_MENU, text_color=CYAN_ACTIVE, width=100, command=buscar_btn_click).pack(side="left")
        
        buscar_btn_click()

    def crear_vista_alarmas(self, parent):
        alarm_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        alarm_frame.pack(fill="both", expand=True, pady=10)
        ctk.CTkLabel(alarm_frame, text="REGISTRO DE ALARMAS E INCIDENTES ACTIVOS", font=("Arial", 18, "bold"), text_color=RED).pack(pady=20)
        alarmas = [
            "🚨 [CRÍTICO 19:35:12] ESTACIÓN 05 - CÁMARA DESCONECTADA",
            "⚠️ [ADVERTENCIA 19:40:50] ESTACIÓN 03 - ALERTA DE COLISIÓN",
            "⚠️ [ADVERTENCIA 18:45:30] ESTACIÓN 02 - CAÍDA DE PRESIÓN"
        ]
        for al in alarmas:
            ctk.CTkLabel(alarm_frame, text=al, font=("Arial", 14), text_color="#ffaaaa").pack(anchor="w", padx=30, pady=12)

    def crear_vista_analitica(self, parent):
        kpi_datos = self.obtener_kpis()
        oee, desechos, disp, act = kpi_datos
        
        ana_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        ana_frame.pack(fill="both", expand=True, pady=10)
        ctk.CTkLabel(ana_frame, text="ANÁLISIS Y RENDIMIENTO DE LA PRODUCCIÓN (OEE - BD)", font=("Arial", 18, "bold"), text_color=CYAN_ACTIVE).pack(pady=20)
        ctk.CTkLabel(ana_frame, text=f"• OEE Global: {oee}%", font=("Arial", 15)).pack(anchor="w", padx=40, pady=10)
        ctk.CTkLabel(ana_frame, text=f"• Tasa de Desechos: {desechos}%", font=("Arial", 15)).pack(anchor="w", padx=40, pady=10)
        ctk.CTkLabel(ana_frame, text=f"• Disponibilidad: {disp}%", font=("Arial", 15)).pack(anchor="w", padx=40, pady=10)
        ctk.CTkLabel(ana_frame, text=f"• Actuación / Rendimiento: {act}%", font=("Arial", 15)).pack(anchor="w", padx=40, pady=10)

    def crear_vista_configuraciones(self, parent):
        conf_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        conf_frame.pack(fill="both", expand=True, pady=10)
        ctk.CTkLabel(conf_frame, text="CONFIGURACIONES DEL SISTEMA", font=("Arial", 18, "bold")).pack(pady=20)
        ctk.CTkLabel(conf_frame, text="• Operador / Supervisor Actual: NoobMaster69", font=("Arial", 14)).pack(anchor="w", padx=40, pady=10)
        ctk.CTkLabel(conf_frame, text="• Línea de Producción: Línea de Montaje 3", font=("Arial", 14)).pack(anchor="w", padx=40, pady=10)
        ctk.CTkButton(conf_frame, text="Cerrar Sesión", fg_color=RED, hover_color="#cc0000", font=("Arial", 14, "bold")).pack(anchor="w", padx=40, pady=30)

if __name__ == "__main__":
    app = WipTrackApp()
    app.mainloop()