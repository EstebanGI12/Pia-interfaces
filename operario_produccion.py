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

class OperarioProduccionApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("OPERARIO - Control de Producción en Piso")
        
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
        
        # BARRA LATERAL
        self.sidebar = ctk.CTkFrame(self.main_container, width=220, corner_radius=0, fg_color=BG_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(pady=(20, 5))
        ctk.CTkLabel(logo_frame, text="WIP", font=("Arial", 22, "bold"), text_color="white").pack(side="left")
        ctk.CTkLabel(logo_frame, text=" TRACK", font=("Arial", 22, "bold"), text_color=CYAN_ACTIVE).pack(side="left")
        
        ctk.CTkLabel(self.sidebar, text="PISO DE PRODUCCIÓN", font=("Arial", 8), text_color="gray").pack()
        ctk.CTkLabel(self.sidebar, text="🟢 CONECTADO", font=("Arial", 12, "bold"), text_color=GREEN).pack(pady=(5, 30))
        
        self.menus = ["ESTACIONES", "REPORTAR FALLA", "METAS DIARIAS", "CONFIGURACIONES"]
        self.menu_buttons = {}
        
        for m in self.menus:
            text_color = "white" if m != "REPORTAR FALLA" else YELLOW
            btn = ctk.CTkButton(self.sidebar, text=m, fg_color="transparent", text_color=text_color,
                                border_width=0, hover_color=BG_ACTIVE_MENU, anchor="w", font=("Arial", 14), height=45,
                                command=lambda name=m: self.cambiar_vista(name))
            btn.pack(pady=5, padx=0, fill="x")
            self.menu_buttons[m] = btn
            
        # ÁREA DE CONTENIDO
        self.content_area = ctk.CTkFrame(self.main_container, fg_color=BG_MAIN, corner_radius=0)
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)
        
        self.vista_actual = "ESTACIONES"
        self.cambiar_vista("ESTACIONES")

    def limpiar_contenido(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()
            
    def actualizar_botones_sidebar(self, vista_activa):
        for m, btn in self.menu_buttons.items():
            if m == vista_activa:
                btn.configure(fg_color=BG_ACTIVE_MENU, text_color=CYAN_ACTIVE)
            else:
                default_color = YELLOW if m == "REPORTAR FALLA" else "white"
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
        ctk.CTkLabel(header, text="🕒 HORA: TURNO 1", font=("Arial", 12), text_color="lightgray").pack(side="left", padx=20)
        
        ctk.CTkLabel(header, text="👷 OPERARIO DE PRODUCCIÓN", font=("Arial", 12), text_color="lightgray").pack(side="right", padx=20)

        if vista == "ESTACIONES":
            self.crear_vista_estaciones(container)
        elif vista == "REPORTAR FALLA":
            self.crear_vista_reporte(container)
        elif vista == "METAS DIARIAS":
            self.crear_vista_metas(container)
        elif vista == "CONFIGURACIONES":
            self.crear_vista_configuraciones(container)

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

    def actualizar_estado_maquina(self, id_maquina, nuevo_estado):
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("UPDATE maquinas SET estado=? WHERE id_maquina=?", (nuevo_estado, id_maquina))
            conn.commit()
            conn.close()
            # Refrescar la vista actual para mostrar los cambios
            if self.vista_actual == "ESTACIONES":
                self.cambiar_vista("ESTACIONES")
        except Exception as e:
            print("Error al actualizar la base de datos:", e)

    def crear_vista_estaciones(self, parent):
        ctk.CTkLabel(parent, text="PANEL DE CONTROL DE ESTACIONES", font=("Arial", 24, "bold"), text_color="white").pack(anchor="w", pady=(0, 15))
        
        scroll_est = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll_est.pack(fill="both", expand=True)
        
        grid_est = ctk.CTkFrame(scroll_est, fg_color="transparent")
        grid_est.pack(fill="both", expand=True)
        grid_est.grid_columnconfigure((0, 1, 2), weight=1)
        
        maquinas_bd = self.obtener_maquinas()
        
        if not maquinas_bd:
            ctk.CTkLabel(scroll_est, text="⚠️ NO SE ENCONTRARON ESTACIONES EN LA BD", font=("Arial", 16, "bold"), text_color=RED).pack(pady=40)
            return

        row, col = 0, 0
        for maq in maquinas_bd:
            id_maq, nombre, estado, _ = maq
            
            b_color = "#3a464f"
            t_color = GREEN
            if estado == 'OPERANDO':
                t_color = GREEN
            elif estado == 'FALLA':
                t_color = RED
                b_color = RED
            else:
                t_color = ORANGE
                
            card = ctk.CTkFrame(grid_est, fg_color=BG_STATION, corner_radius=12, border_color=b_color, border_width=1)
            card.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
            
            ctk.CTkLabel(card, text=f"{id_maq}\n{nombre}", font=("Arial", 16, "bold"), text_color="white").pack(fill="x", padx=15, pady=(15, 5))
            
            status_frame = ctk.CTkFrame(card, fg_color="transparent")
            status_frame.pack(pady=(5, 15))
            canvas_dot = tk.Canvas(status_frame, width=15, height=15, bg=BG_STATION, highlightthickness=0)
            canvas_dot.pack(side="left", pady=3)
            canvas_dot.create_oval(2, 2, 13, 13, fill=t_color, outline="")
            ctk.CTkLabel(status_frame, text=estado, font=("Arial", 14, "bold"), text_color=t_color).pack(side="left", padx=5)
            
            ctk.CTkFrame(card, fg_color="#3a464f", height=1).pack(fill="x", padx=15, pady=5)
            
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=15, pady=(10, 15))
            
            # Botones de control rápido para el operario
            if estado != 'OPERANDO':
                btn_iniciar = ctk.CTkButton(btn_frame, text="▶ INICIAR", fg_color=GREEN, hover_color="#00b359", font=("Arial", 12, "bold"), text_color="black",
                                            command=lambda m_id=id_maq: self.actualizar_estado_maquina(m_id, "OPERANDO"))
                btn_iniciar.pack(side="left", expand=True, padx=5)
            
            if estado != 'PAUSA' and estado != 'FALLA':
                btn_pausar = ctk.CTkButton(btn_frame, text="⏸ PAUSAR", fg_color=ORANGE, hover_color="#cc7a00", font=("Arial", 12, "bold"), text_color="black",
                                            command=lambda m_id=id_maq: self.actualizar_estado_maquina(m_id, "PAUSA"))
                btn_pausar.pack(side="left", expand=True, padx=5)
                
            col += 1
            if col > 2:
                col = 0
                row += 1

    def crear_vista_reporte(self, parent):
        ctk.CTkLabel(parent, text="⚠️ REPORTE INMEDIATO DE FALLA A MANTENIMIENTO", font=("Arial", 22, "bold"), text_color=YELLOW).pack(anchor="w", pady=(0, 20))
        
        form_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        form_frame.pack(fill="both", expand=True, padx=50, pady=20)
        
        ctk.CTkLabel(form_frame, text="1. SELECCIONE LA ESTACIÓN AFECTADA:", font=("Arial", 14, "bold")).pack(anchor="w", padx=30, pady=(30, 5))
        
        maquinas = self.obtener_maquinas()
        nombres_maq = [f"{m[0]} - {m[1]}" for m in maquinas] if maquinas else ["NO HAY MÁQUINAS"]
        
        combo_maq = ctk.CTkComboBox(form_frame, values=nombres_maq, width=400, font=("Arial", 14))
        combo_maq.pack(anchor="w", padx=30, pady=(0, 20))
        
        ctk.CTkLabel(form_frame, text="2. DESCRIPCIÓN DEL PROBLEMA:", font=("Arial", 14, "bold")).pack(anchor="w", padx=30, pady=(10, 5))
        txt_desc = ctk.CTkTextbox(form_frame, width=400, height=100, font=("Arial", 14))
        txt_desc.pack(anchor="w", padx=30, pady=(0, 20))
        
        def enviar_reporte():
            seleccion = combo_maq.get()
            if seleccion != "NO HAY MÁQUINAS" and seleccion != "":
                id_maq = seleccion.split(" - ")[0]
                self.actualizar_estado_maquina(id_maq, "FALLA")
                
                # Opcional: Aquí podrías agregar código para insertar un "TICKET" en la tabla de alertas
                try:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    # Genera un ID de ticket aleatorio simple
                    ticket_id = f"TK-{random.randint(1000, 9999)}"
                    # Se requiere una pieza generica o la saca de otra tabla, aqui pondremos N/A o una de prueba
                    c.execute("INSERT INTO alertas (id_ticket, id_maquina, pieza_requerida, estado_ticket, fecha_alerta) VALUES (?, ?, ?, ?, datetime('now'))", 
                              (ticket_id, id_maq, 'REF-001', 'PENDIENTE'))
                    conn.commit()
                    conn.close()
                except Exception as e:
                    print("Error al crear ticket:", e)

                # Notificación visual básica
                for widget in form_frame.winfo_children():
                    widget.destroy()
                ctk.CTkLabel(form_frame, text="✅ REPORTE ENVIADO CON ÉXITO", font=("Arial", 24, "bold"), text_color=GREEN).pack(expand=True)
                ctk.CTkLabel(form_frame, text=f"La estación {id_maq} ha sido marcada en FALLA.\nMantenimiento ha sido notificado.", font=("Arial", 16), text_color="white", justify="center").pack(pady=20)
                ctk.CTkButton(form_frame, text="Volver a Estaciones", command=lambda: self.cambiar_vista("ESTACIONES")).pack(pady=20)

        ctk.CTkButton(form_frame, text="🚨 ENVIAR REPORTE DE EMERGENCIA", font=("Arial", 16, "bold"), fg_color=RED, hover_color="#cc0000", height=50, width=400, command=enviar_reporte).pack(anchor="w", padx=30, pady=30)

    def crear_vista_metas(self, parent):
        ctk.CTkLabel(parent, text="📈 METAS DIARIAS DE PRODUCCIÓN", font=("Arial", 24, "bold"), text_color="white").pack(anchor="w", pady=(0, 15))
        
        kpi_frame = ctk.CTkFrame(parent, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=10)
        kpi_frame.grid_columnconfigure((0,1), weight=1)
        
        # Meta 1
        box1 = ctk.CTkFrame(kpi_frame, fg_color=BG_CARD, corner_radius=12)
        box1.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        ctk.CTkLabel(box1, text="PIEZAS ENSAMBLADAS (TURNO ACTUAL)", font=("Arial", 14, "bold"), text_color="white").pack(pady=(20, 10))
        ctk.CTkLabel(box1, text="142 / 200", font=("Arial", 36, "bold"), text_color=CYAN_ACTIVE).pack(pady=10)
        prog1 = ctk.CTkProgressBar(box1, progress_color=CYAN_ACTIVE, width=300, height=15)
        prog1.set(142/200)
        prog1.pack(pady=20)
        
        # Meta 2
        box2 = ctk.CTkFrame(kpi_frame, fg_color=BG_CARD, corner_radius=12)
        box2.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        ctk.CTkLabel(box2, text="TIEMPO EFECTIVO DE TRABAJO (OEE)", font=("Arial", 14, "bold"), text_color="white").pack(pady=(20, 10))
        ctk.CTkLabel(box2, text="85%", font=("Arial", 36, "bold"), text_color=GREEN).pack(pady=10)
        prog2 = ctk.CTkProgressBar(box2, progress_color=GREEN, width=300, height=15)
        prog2.set(0.85)
        prog2.pack(pady=20)
        
    def crear_vista_configuraciones(self, parent):
        conf_frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=12)
        conf_frame.pack(fill="both", expand=True, pady=10)
        
        ctk.CTkLabel(conf_frame, text="CONFIGURACIONES DE USUARIO", font=("Arial", 20, "bold"), text_color=CYAN_ACTIVE).pack(pady=(30, 20))
        
        info_usuario = ctk.CTkFrame(conf_frame, fg_color=BG_MAIN, corner_radius=8)
        info_usuario.pack(pady=10, padx=50, fill="x")
        
        ctk.CTkLabel(info_usuario, text="👤 Usuario: Operario de Producción", font=("Arial", 16, "bold"), text_color="white").pack(pady=(15, 5))
        ctk.CTkLabel(info_usuario, text="🏢 Planta: FIME Industrial | Nivel de Acceso: Piso de Producción", font=("Arial", 14), text_color="lightgray").pack(pady=(0, 15))
        
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
        # 1. Cierra la ventana del operario
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
    app = OperarioProduccionApp()
    app.mainloop()