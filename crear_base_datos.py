import sqlite3
import random
from datetime import datetime, timedelta

def crear_base_datos():
    # Conectar a la base de datos (se creará el archivo si no existe)
    conexion = sqlite3.connect('wiptrack.db')
    cursor = conexion.cursor()

    # 1. Crear tabla de ESTACIONES
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS estaciones (
        id INTEGER PRIMARY KEY,
        nombre TEXT NOT NULL,
        estado TEXT NOT NULL,
        rendimiento TEXT
    )
    ''')

    # 2. Crear tabla de PIEZAS (Trazabilidad)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS piezas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sn TEXT UNIQUE NOT NULL,
        tipo_motor TEXT NOT NULL,
        estacion_actual INTEGER,
        estado TEXT NOT NULL,
        fuerza REAL,
        torque REAL,
        presion REAL,
        fecha_registro TEXT NOT NULL,
        FOREIGN KEY (estacion_actual) REFERENCES estaciones (id)
    )
    ''')

    # 3. Crear tabla de KPIS (Para la analítica global)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS kpis (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        oee REAL,
        tasa_desechos REAL,
        disponibilidad REAL,
        actuacion REAL
    )
    ''')

    # --- LLENAR DATOS INICIALES ---
    
    # Limpiar tablas por si el script se corre dos veces
    cursor.execute('DELETE FROM piezas')
    cursor.execute('DELETE FROM estaciones')
    cursor.execute('DELETE FROM kpis')

    # Insertar Estaciones
    estaciones_data = [
        (1, 'PRENSA', 'OPERANDO', '82%'),
        (2, 'ATORNILLADORA', 'EN ESPERA', '-'),
        (3, 'PRUEBAS DE VACIO', 'FALLA', '-'),
        (4, 'EMBALAJE', 'OPERANDO', '100%')
    ]
    cursor.executemany('INSERT INTO estaciones VALUES (?, ?, ?, ?)', estaciones_data)

    # Insertar KPIs
    cursor.execute('INSERT INTO kpis VALUES (1, 84.5, 1.8, 93.1, 91.0)')

    # Generar 50 piezas de prueba (SN-2026-98701 hasta 98750)
    tipos_motor = ['MOTOR TIPO A', 'MOTOR TIPO B']
    estados_posibles = ['APROBADO', 'RECHAZADO', 'EN PROCESO']
    
    fecha_base = datetime(2026, 10, 12, 8, 0, 0) # Empezar turno a las 8 AM

    for i in range(1, 51):
        sn = f"SN-2026-{98700 + i}"
        tipo = random.choice(tipos_motor)
        
        # Lógica para distribuir las piezas
        if i < 40:
            # Las primeras 39 ya terminaron y pasaron por embalaje
            estacion = 4
            estado = 'APROBADO' if random.random() > 0.05 else 'RECHAZADO' # 5% de rechazo
        else:
            # Las últimas 11 están regadas en la línea
            estacion = random.randint(1, 3)
            estado = 'EN PROCESO'
            
        fuerza = round(random.uniform(12.0, 12.8), 2)
        torque = round(random.uniform(4.0, 4.5), 2)
        presion = round(random.uniform(-0.9, -0.7), 2)
        
        # Sumar algunos minutos a la fecha para simular flujo
        fecha_base += timedelta(minutes=random.randint(2, 10))
        fecha_str = fecha_base.strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute('''
        INSERT INTO piezas (sn, tipo_motor, estacion_actual, estado, fuerza, torque, presion, fecha_registro)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (sn, tipo, estacion, estado, fuerza, torque, presion, fecha_str))

    # Guardar cambios y cerrar
    conexion.commit()
    conexion.close()
    
    print("Base de datos 'wiptrack.db' creada y poblada con 50 piezas exitosamente.")

if __name__ == '__main__':
    crear_base_datos()