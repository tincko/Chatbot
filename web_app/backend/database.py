"""
Database models and configuration for the chatbot application.
Uses SQLite with SQLAlchemy ORM.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'chatbot.db')}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Patient(Base):
    """Patient profile data"""
    __tablename__ = "patients"
    
    id = Column(String, primary_key=True)  # e.g., 'carlos_68'
    nombre = Column(String, nullable=False)
    edad = Column(Integer)
    tipo_trasplante = Column(String)
    medicacion = Column(String)
    adherencia_previa = Column(String)
    contexto = Column(String)
    nivel_educativo = Column(String)
    estilo_comunicacion = Column(String)
    fortalezas = Column(String)
    dificultades = Column(String)
    notas_equipo = Column(String)
    idiosincrasia = Column(String)
    preferred_patient_model = Column(String)
    last_interaction_file = Column(String)  # For compatibility
    last_interaction_id = Column(Integer, ForeignKey('interactions.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    interactions = relationship("Interaction", back_populates="patient", foreign_keys="Interaction.patient_id")


class Interaction(Base):
    """A conversation session between patient and psychologist"""
    __tablename__ = "interactions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    patient_id = Column(String, ForeignKey('patients.id'), index=True)
    
    # Configuration
    chatbot_model = Column(String)
    patient_model = Column(String)
    psychologist_system_prompt = Column(Text)
    patient_system_prompt = Column(Text)
    
    # LLM parameters (stored as JSON for flexibility)
    psychologist_params = Column(JSON)  # temperature, top_p, etc.
    patient_params = Column(JSON)
    
    # RAG
    rag_documents = Column(JSON)  # List of document filenames
    
    # Legacy filename for compatibility
    filename = Column(String, unique=True, index=True)
    
    # User-defined Title
    title = Column(Text, nullable=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="interactions", foreign_keys=[patient_id])
    messages = relationship("Message", back_populates="interaction", cascade="all, delete-orphan", order_by="Message.order")


class Message(Base):
    """Individual message in a conversation"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    interaction_id = Column(Integer, ForeignKey('interactions.id'), nullable=False, index=True)
    
    order = Column(Integer, nullable=False)  # Order in conversation
    role = Column(String, nullable=False, index=True)  # user, assistant, system, episode
    content = Column(Text, nullable=False)
    thought = Column(Text, nullable=True)
    
    # Metadata
    suggested_reply_used = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interaction = relationship("Interaction", back_populates="messages")


def init_db():
    """Initialize the database, creating all tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully")


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    # Initialize database if run directly
    init_db()
    print(f"Database created at: {DATABASE_URL}")
