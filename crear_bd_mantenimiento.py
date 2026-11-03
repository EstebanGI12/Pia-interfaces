import sqlite3
import random
from datetime import datetime, timedelta
import os

# Asegurar que se cree en la carpeta actual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'wiptrack.db')

def reconstruir_base_datos():
    # Conectar a la base de datos
    conexion = sqlite3.connect(DB_PATH)
    cursor = conexion.cursor()

    # 1. TABLA MÁQUINAS (Antes Estaciones)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS maquinas (
        id_maquina TEXT PRIMARY KEY,
        nombre TEXT NOT NULL,
        estado TEXT NOT NULL,
        ultima_revision TEXT
    )
    ''')

    # 2. TABLA ALMACÉN / INVENTARIO
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS almacen (
        id_pieza TEXT PRIMARY KEY,
        nombre_pieza TEXT NOT NULL,
        cantidad_disponible INTEGER NOT NULL,
        ubicacion TEXT NOT NULL
    )
    ''')

    # 3. TABLA ALERTAS / TICKETS DE MANTENIMIENTO
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS alertas (
        id_ticket INTEGER PRIMARY KEY AUTOINCREMENT,
        id_maquina TEXT NOT NULL,
        pieza_requerida TEXT NOT NULL,
        estado_ticket TEXT NOT NULL,
        fecha_alerta TEXT NOT NULL,
        operario_asignado TEXT,
        FOREIGN KEY (id_maquina) REFERENCES maquinas (id_maquina),
        FOREIGN KEY (pieza_requerida) REFERENCES almacen (id_pieza)
    )
    ''')

    # --- LIMPIAR DATOS ANTERIORES (Por si se corre de nuevo) ---
    cursor.execute('DELETE FROM alertas')
    cursor.execute('DELETE FROM almacen')
    cursor.execute('DELETE FROM maquinas')

    # --- POBLAR DATOS DE PRUEBA ---
    
    # Insertar Máquinas (Solo 1 en falla para la prueba)
    maquinas_data = [
        ('MQ-01', 'FRESADORA CNC', 'OPERANDO', '2026-10-10'),
        ('MQ-02', 'PRENSA HIDRÁULICA', 'OPERANDO', '2026-10-05'),
        ('MQ-03', 'BRAZO ROBÓTICO KUKA', 'FALLA', '2026-10-01'),
        ('MQ-04', 'HORNO DE FUNDICIÓN', 'OPERANDO', '2026-10-11')
    ]
    cursor.executemany('INSERT INTO maquinas VALUES (?, ?, ?, ?)', maquinas_data)

    # Insertar Inventario del Almacén
    almacen_data = [
        ('PZ-100', 'Motor Trifásico 5HP', 2, 'Pasillo A - Estante 2'),
        ('PZ-101', 'Banda Transportadora 5m', 5, 'Pasillo C - Rack 1'),
        ('PZ-102', 'Sensor Óptico Infrarrojo', 12, 'Cajonera 4 - Gaveta B'),
        ('PZ-103', 'Baleros de Alta Velocidad', 50, 'Pasillo B - Estante 1'),
        ('PZ-104', 'Servomotor Eje Z', 1, 'Cuarto de Control - Caja Fuerte')
    ]
    cursor.executemany('INSERT INTO almacen VALUES (?, ?, ?, ?)', almacen_data)

    # Crear la alerta inicial (La Máquina 03 necesita un Servomotor)
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO alertas (id_maquina, pieza_requerida, estado_ticket, fecha_alerta, operario_asignado)
        VALUES ('MQ-03', 'PZ-104', 'PENDIENTE', ?, 'Sin Asignar')
    ''', (fecha_actual,))

    # Guardar y cerrar
    conexion.commit()
    conexion.close()
    
    print("Base de datos de Mantenimiento y Almacén reconstruida con éxito.")

if __name__ == '__main__':
    reconstruir_base_datos()