
from database import engine
from sqlalchemy import text

def add_sentiment_column():
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE messages ADD COLUMN sentiment JSON"))
            print("✅ Columna 'sentiment' añadida exitosamente.")
        except Exception as e:
            if "duplicate column name" in str(e):
                print("ℹ️ La columna 'sentiment' ya existe.")
            else:
                print(f"❌ Error al añadir columna: {e}")

if __name__ == "__main__":
    add_sentiment_column()
