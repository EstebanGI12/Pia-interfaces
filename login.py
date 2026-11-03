import customtkinter as ctk
import tkinter as tk
import subprocess
import os
from tkinter import messagebox

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class LoginPrincipalApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WIP TRACK - Sistema de Rastreo Industrial")
        self.geometry("1024x768")
        self.configure(fg_color="#1a1a1a")
        
        # Logo Superior Izquierda
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.place(x=30, y=25)
        
        ctk.CTkLabel(logo_frame, text="⚙️", font=("Arial", 26), text_color="#00d2ff").pack(side="left", padx=(0, 5))
        lbl_wip = ctk.CTkLabel(logo_frame, text="WIP", font=("Arial", 22, "bold"), text_color="#00d2ff")
        lbl_wip.pack(side="left")
        lbl_track = ctk.CTkLabel(logo_frame, text=" TRACK", font=("Arial", 22, "bold"), text_color="#ff9800")
        lbl_track.pack(side="left")
        
        sub_lbl = ctk.CTkLabel(self, text="SISTEMAS DE RASTREO INDUSTRIAL", font=("Arial", 10, "bold"), text_color="gray")
        sub_lbl.place(x=68, y=57)
        
        # Contenedor Central
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Ícono de Usuario Grande
        icon_lbl = ctk.CTkLabel(center_frame, text="👤", font=("Arial", 60), text_color="gray")
        icon_lbl.pack(pady=(0, 10))
        
        # Pregunta ¿Qué eres?
        title_lbl = ctk.CTkLabel(center_frame, text="¿Qué eres?", font=("Arial", 18, "bold"), text_color="white")
        title_lbl.pack(pady=(0, 40))
        
        # Botones de Selección
        btn_frame = ctk.CTkFrame(center_frame, fg_color="transparent")
        btn_frame.pack()
        
        btn_operador = ctk.CTkButton(btn_frame, text="Operador", font=("Arial", 16, "bold"), 
                                     fg_color="#333333", hover_color="#444444", text_color="white",
                                     width=160, height=50, corner_radius=6,
                                     command=self.abrir_login_operador)
        btn_operador.pack(side="left", padx=20)
        
        btn_supervisor = ctk.CTkButton(btn_frame, text="Supervisor", font=("Arial", 16, "bold"), 
                                       fg_color="#333333", hover_color="#444444", text_color="white",
                                       width=160, height=50, corner_radius=6,
                                       command=self.abrir_login_supervisor)
        btn_supervisor.pack(side="left", padx=20)

    def abrir_login_operador(self):
        self.destroy()
        app_op = LoginOperadorApp()
        app_op.mainloop()

    def abrir_login_supervisor(self):
        self.destroy()
        app_sup = LoginSupervisorApp()
        app_sup.mainloop()


class LoginSupervisorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WIP TRACK - Login Supervisor")
        self.geometry("1024x768")
        self.configure(fg_color="#1a1a1a")
        
        # Logo Superior Izquierda
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.place(x=30, y=25)
        
        ctk.CTkLabel(logo_frame, text="⚙️", font=("Arial", 26), text_color="#00d2ff").pack(side="left", padx=(0, 5))
        ctk.CTkLabel(logo_frame, text="WIP", font=("Arial", 22, "bold"), text_color="#00d2ff").pack(side="left")
        ctk.CTkLabel(logo_frame, text=" TRACK", font=("Arial", 22, "bold"), text_color="#ff9800").pack(side="left")
        
        ctk.CTkLabel(self, text="SISTEMAS DE RASTREO INDUSTRIAL", font=("Arial", 10, "bold"), text_color="gray").place(x=68, y=57)
        
        # Contenedor Central
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Ícono de Supervisor
        ctk.CTkLabel(center_frame, text="👨‍💼", font=("Arial", 60), text_color="gray").pack(pady=(0, 5))
        ctk.CTkLabel(center_frame, text="Supervisor", font=("Arial", 18, "bold"), text_color="white").pack(pady=(0, 30))
        
        # Campos de Entrada
        self.entry_user = ctk.CTkEntry(center_frame, placeholder_text="Nombre de Usuario", font=("Arial", 14), 
                                       width=280, height=40, fg_color="#333333", border_color="#444444", text_color="white")
        self.entry_user.pack(pady=10)
        self.entry_user.insert(0, "ADMIN") # Sugerencia de autocompletado
        
        self.entry_pass = ctk.CTkEntry(center_frame, placeholder_text="Contraseña", font=("Arial", 14), 
                                       width=280, height=40, fg_color="#333333", border_color="#444444", text_color="white", show="*")
        self.entry_pass.pack(pady=10)
        self.entry_pass.insert(0, "123") # Sugerencia
        
        # Botón ENTER
        btn_enter = ctk.CTkButton(center_frame, text="ENTER", font=("Arial", 14, "bold"), 
                                  fg_color="#333333", hover_color="#444444", text_color="white",
                                  width=280, height=40, corner_radius=6,
                                  command=self.validar_login)
        btn_enter.pack(pady=(20, 0))
        
        # Botón Volver
        btn_volver = ctk.CTkButton(center_frame, text="← Volver", font=("Arial", 12), 
                                   fg_color="transparent", text_color="gray", hover_color="#222222",
                                   command=self.volver_principal)
        btn_volver.pack(pady=(10, 0))

    def validar_login(self):
        usuario = self.entry_user.get().strip().upper()
        if usuario == "ADMIN":
            self.destroy()
            script_path = os.path.join(BASE_DIR, "supervisor_mantenimiento.py")
            subprocess.Popen(["python", script_path])
        else:
            messagebox.showerror("Error", "Usuario de supervisor incorrecto. Usa: ADMIN")

    def volver_principal(self):
        self.destroy()
        app = LoginPrincipalApp()
        app.mainloop()


class LoginOperadorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WIP TRACK - Login Operador")
        self.geometry("1024x768")
        self.configure(fg_color="#1a1a1a")
        
        # Logo Superior Izquierda
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.place(x=30, y=25)
        
        ctk.CTkLabel(logo_frame, text="⚙️", font=("Arial", 26), text_color="#00d2ff").pack(side="left", padx=(0, 5))
        ctk.CTkLabel(logo_frame, text="WIP", font=("Arial", 22, "bold"), text_color="#00d2ff").pack(side="left")
        ctk.CTkLabel(logo_frame, text=" TRACK", font=("Arial", 22, "bold"), text_color="#ff9800").pack(side="left")
        
        ctk.CTkLabel(self, text="SISTEMAS DE RASTREO INDUSTRIAL", font=("Arial", 10, "bold"), text_color="gray").place(x=68, y=57)
        
        # Contenedor Central
        center_frame = ctk.CTkFrame(self, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Ícono de Operador (Casco/Herramientas)
        ctk.CTkLabel(center_frame, text="👷‍♂️", font=("Arial", 60), text_color="gray").pack(pady=(0, 5))
        ctk.CTkLabel(center_frame, text="Operador", font=("Arial", 18, "bold"), text_color="white").pack(pady=(0, 30))
        
        ctk.CTkLabel(center_frame, text="Cuentas válidas: PROD o ALM", font=("Arial", 11), text_color="#00e676").pack(pady=(0, 5))
        
        # Campos de Entrada
        self.entry_user = ctk.CTkEntry(center_frame, placeholder_text="ID de Empleado (PROD o ALM)", font=("Arial", 14), 
                                       width=280, height=40, fg_color="#333333", border_color="#444444", text_color="white")
        self.entry_user.pack(pady=5)
        
        self.entry_pass = ctk.CTkEntry(center_frame, placeholder_text="Contraseña / PIN", font=("Arial", 14), 
                                       width=280, height=40, fg_color="#333333", border_color="#444444", text_color="white", show="*")
        self.entry_pass.pack(pady=10)
        self.entry_pass.insert(0, "123")
        
        # Botón ENTER
        btn_enter = ctk.CTkButton(center_frame, text="ENTER", font=("Arial", 14, "bold"), 
                                  fg_color="#333333", hover_color="#444444", text_color="white",
                                  width=280, height=40, corner_radius=6,
                                  command=self.validar_login)
        btn_enter.pack(pady=(20, 0))
        
        # Botón Volver
        btn_volver = ctk.CTkButton(center_frame, text="← Volver", font=("Arial", 12), 
                                   fg_color="transparent", text_color="gray", hover_color="#222222",
                                   command=self.volver_principal)
        btn_volver.pack(pady=(10, 0))

    def validar_login(self):
        usuario = self.entry_user.get().strip().upper()
        
        if usuario == "PROD":
            self.destroy()
            script_path = os.path.join(BASE_DIR, "operario_produccion.py")
            subprocess.Popen(["python", script_path])
        elif usuario == "ALM":
            self.destroy()
            script_path = os.path.join(BASE_DIR, "operario_almacen.py")
            subprocess.Popen(["python", script_path])
        else:
            messagebox.showerror("Error", "ID de Empleado no reconocido.\nUsa 'PROD' para Producción o 'ALM' para Almacén.")

    def volver_principal(self):
        self.destroy()
        app = LoginPrincipalApp()
        app.mainloop()


if __name__ == "__main__":
    app = LoginPrincipalApp()
    app.mainloop()