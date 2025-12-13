import sqlite3
import os

DB_PATH = "chatbot.db"

def check_schema():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file {DB_PATH} not found.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check table info
        print("--- Esquema de la tabla 'patients' ---")
        cursor.execute("PRAGMA table_info(patients);")
        columns = cursor.fetchall()
        
        if not columns:
            print("No se pudo obtener información de la tabla (quizás no existe).")
        else:
            for col in columns:
                # cid, name, type, notnull, dflt_value, pk
                print(f"Columna: {col[1]} (Tipo: {col[2]})")

        # Try to select all raw
        print("\n--- Primeras 3 filas (Raw) ---")
        try:
            cursor.execute("SELECT * FROM patients LIMIT 3")
            rows = cursor.fetchall()
            for row in rows:
                print(row)
        except Exception as e:
            print(f"Error al seleccionar datos: {e}")

        conn.close()

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")

if __name__ == "__main__":
    check_schema()
