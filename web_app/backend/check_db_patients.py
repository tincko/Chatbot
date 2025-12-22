import sqlite3
import os
import sys

# Ensure proper encoding
sys.stdout.reconfigure(encoding='utf-8')

DB_PATH = "chatbot.db"

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database file {DB_PATH} not found.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # --- PATIENTS ---
        print("\n=== PACIENTES EN BASE DE DATOS ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='patients';")
        if not cursor.fetchone():
            print("❌ La tabla 'patients' NO existe.")
        else:
            try:
                # Using correct column names from database.py
                cursor.execute("SELECT id, nombre, edad, tipo_trasplante FROM patients")
                rows = cursor.fetchall()
                
                if not rows:
                    print("⚠️ La tabla 'patients' está vacía.")
                else:
                    for row in rows:
                        print(f"👤 [{row[0]}] {row[1]} (Edad: {row[2]}) - {row[3]}")
                    print(f"Total pacientes: {len(rows)}")
            except sqlite3.Error as e:
                print(f"❌ Error consultando pacientes: {e}")

        # --- INTERACTIONS ---
        print("\n=== SESIONES (INTERACCIONES) ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='interactions';")
        if not cursor.fetchone():
            print("❌ La tabla 'interactions' NO existe.")
        else:
            try:
                cursor.execute("SELECT id, filename, timestamp, patient_id FROM interactions ORDER BY timestamp DESC")
                rows = cursor.fetchall()
                
                if not rows:
                    print("⚠️ No hay interacciones registradas.")
                else:
                    print(f"{'ID':<5} | {'Date':<20} | {'Patient ID':<15} | {'Filename'}")
                    print("-" * 60)
                    for row in rows:
                        pid = row[3] if row[3] else "None"
                        print(f"{row[0]:<5} | {row[2]:<20} | {pid:<15} | {row[1]}")
                    print(f"Total sesiones: {len(rows)}")
            except sqlite3.Error as e:
                print(f"❌ Error consultando interacciones: {e}")
        
        conn.close()

    except sqlite3.Error as e:
        print(f"SQLite connection error: {e}")

if __name__ == "__main__":
    check_db()
