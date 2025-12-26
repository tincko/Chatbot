import sqlite3
import os

# Get absolute path to the database
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'chatbot.db')

def migrate():
    print(f"Checking database at: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print("Database not found. Please run the application once to create it.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if 'title' column exists in 'interactions' table
        cursor.execute("PRAGMA table_info(interactions)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'title' not in column_names:
            print("Adding 'title' column to 'interactions' table...")
            cursor.execute("ALTER TABLE interactions ADD COLUMN title TEXT")
            conn.commit()
            print("Migration successful.")
        else:
            print("'title' column already exists.")
            
    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
