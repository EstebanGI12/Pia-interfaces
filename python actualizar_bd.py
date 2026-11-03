import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'wiptrack.db')

def agregar_tabla_produccion():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS produccion (
        sn_pieza TEXT PRIMARY KEY,
        modelo TEXT NOT NULL,
        estacion_actual TEXT NOT NULL,
        procesos_completados TEXT NOT NULL,
        estado TEXT NOT NULL
    )
    ''')
    cursor.execute('DELETE FROM produccion')
    datos_prueba = [
        ('MOT-1001', 'Motor V8 Básico', 'MQ-01 (FRESADORA)', 'Corte, Limpieza', 'EN PROCESO'),
        ('EJE-2050', 'Eje de Transmisión', 'MQ-02 (PRENSA)', 'Corte', 'EN PROCESO'),
        ('BRA-3005', 'Brazo Articulado', 'MQ-03 (ROBOT KUKA)', 'Corte, Moldeado, Ensamblaje', 'DETENIDO (MÁQUINA EN FALLA)'),
        ('SEN-4011', 'Carcasa Sensor', 'MQ-04 (HORNO)', 'Ninguno', 'LISTO PARA INICIAR')
    ]
    cursor.executemany('INSERT INTO produccion VALUES (?, ?, ?, ?, ?)', datos_prueba)
    conn.commit()
    conn.close()
    print("Tabla de Producción agregada con éxito.")

if __name__ == "__main__":
    agregar_tabla_produccion()