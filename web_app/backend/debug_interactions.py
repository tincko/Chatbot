from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, Interaction
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "chatbot.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

interactions = db.query(Interaction).all()
print(f"Found {len(interactions)} interactions in DB")
for i in interactions:
    print(f"ID: {i.id} | Filename: {i.filename} | Patient: {i.patient.nombre if i.patient else 'None'}")

db.close()
