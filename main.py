import customtkinter as ctk

# Crear la ventana principal
ventana = ctk.CTk()
ventana.geometry("400x200") # Tamaño de la ventana (ancho x alto)
ventana.title("Mi primer programa")

# Crear el texto de "Hola Mundo"
texto = ctk.CTkLabel(ventana, text="¡Hola Mundo!", font=("Arial", 28, "bold"))
texto.pack(pady=60) # pack() lo centra en la ventana

# Mantener la ventana abierta
ventana.mainloop()