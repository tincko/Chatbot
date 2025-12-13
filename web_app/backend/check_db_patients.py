import sqlite3
import os

DB_PATH = "chatbot.db"

def check_patients():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file {DB_PATH} not found.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patients';")
        if not cursor.fetchone():
            print("Table 'patients' does not exist in the database.")
            conn.close()
            return

        print("--- Contenido de la tabla 'patients' ---")
        cursor.execute("SELECT id, name, age, transplant_type FROM patients")
        rows = cursor.fetchall()
        
        if not rows:
            print("La tabla 'patients' está vacía.")
        else:
            for row in rows:
                print(f"ID: {row[0]}, Nombre: {row[1]}, Edad: {row[2]}, Tipo: {row[3]}")
                
        # Count total
        print(f"\nTotal de pacientes: {len(rows)}")
        
        conn.close()

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")

if __name__ == "__main__":
    check_patients()
