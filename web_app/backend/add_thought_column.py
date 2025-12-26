import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chatbot.db')

def migrate():
    print(f"Checking database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column exists
        cursor.execute("PRAGMA table_info(messages)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'thought' not in columns:
            print("Adding 'thought' column to messages table...")
            cursor.execute("ALTER TABLE messages ADD COLUMN thought TEXT")
            conn.commit()
            print("Migration successful.")
        else:
            print("'thought' column already exists.")
            
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
