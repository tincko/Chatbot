"""
Database helper functions for CRUD operations.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from database import Patient, Interaction, Message
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


# ========== PATIENT OPERATIONS ==========

def get_all_patients(db: Session) -> List[Dict[str, Any]]:
    """Get all patients as dictionaries (compatible with JSON format)"""
    patients = db.query(Patient).all()
    return [patient_to_dict(p) for p in patients]


def get_patient_by_id(db: Session, patient_id: str) -> Optional[Dict[str, Any]]:
    """Get a single patient by ID"""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    return patient_to_dict(patient) if patient else None


def create_or_update_patients(db: Session, patients_data: List[Dict[str, Any]]):
    """Create or update multiple patients"""
    for patient_data in patients_data:
        patient_id = patient_data.get('id')
        existing = db.query(Patient).filter(Patient.id == patient_id).first()
        
        if existing:
            # Update
            for key, value in patient_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
        else:
            # Create
            patient = Patient(**patient_data)
            db.add(patient)
    
    db.commit()


def patient_to_dict(patient: Patient) -> Dict[str, Any]:
    """Convert Patient model to dictionary"""
    if not patient:
        return None
    
    return {
        'id': patient.id,
        'nombre': patient.nombre,
        'edad': patient.edad,
        'tipo_trasplante': patient.tipo_trasplante,
        'medicacion': patient.medicacion,
        'adherencia_previa': patient.adherencia_previa,
        'contexto': patient.contexto,
        'nivel_educativo': patient.nivel_educativo,
        'estilo_comunicacion': patient.estilo_comunicacion,
        'fortalezas': patient.fortalezas,
        'dificultades': patient.dificultades,
        'notas_equipo': patient.notas_equipo,
        'idiosincrasia': patient.idiosincrasia,
        'preferred_patient_model': patient.preferred_patient_model,
        'last_interaction_file': patient.last_interaction_file,
    }


# ========== INTERACTION OPERATIONS ==========

def save_interaction(db: Session, interaction_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Save a new interaction to database.
    Returns dict with status and filename for compatibility.
    """
    config = interaction_data.get('config', {})
    messages_data = interaction_data.get('messages', [])
    timestamp_str = interaction_data.get('timestamp', '')
    
    # Parse timestamp
    try:
        if "T" in timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            timestamp = datetime.fromisoformat(timestamp_str)
    except:
        timestamp = datetime.utcnow()
    
    # Create filename for compatibility
    filename = f"interaction_{timestamp.strftime('%Y-%m-%dT%H-%M-%S-%f')}.json"
    
    # Find patient_id
    patient_name = config.get('patient_name')
    patient_id = None
    if patient_name:
        patient = db.query(Patient).filter(Patient.nombre == patient_name).first()
        if patient:
            patient_id = patient.id
    
    # Create interaction
    interaction = Interaction(
        timestamp=timestamp,
        patient_id=patient_id,
        chatbot_model=config.get('chatbot_model'),
        patient_model=config.get('patient_model'),
        psychologist_system_prompt=config.get('psychologist_system_prompt'),
        patient_system_prompt=config.get('patient_system_prompt'),
        psychologist_params={
            'temperature': config.get('psychologist_temperature'),
            'top_p': config.get('psychologist_top_p'),
            'top_k': config.get('psychologist_top_k'),
            'max_tokens': config.get('psychologist_max_tokens'),
            'presence_penalty': config.get('psychologist_presence_penalty'),
            'frequency_penalty': config.get('psychologist_frequency_penalty'),
        },
        patient_params={
            'temperature': config.get('patient_temperature'),
            'top_p': config.get('patient_top_p'),
            'top_k': config.get('patient_top_k'),
            'max_tokens': config.get('patient_max_tokens'),
            'presence_penalty': config.get('patient_presence_penalty'),
            'frequency_penalty': config.get('patient_frequency_penalty'),
        },
        filename=filename
    )
    
    db.add(interaction)
    db.flush()  # Get interaction.id
    
    # Create messages
    for i, msg_data in enumerate(messages_data):
        message = Message(
            interaction_id=interaction.id,
            order=i,
            role=msg_data.get('role'),
            content=msg_data.get('content'),
            suggested_reply_used=msg_data.get('suggested_reply_used', False)
        )
        db.add(message)
    
    db.commit()
    
    # Update patient's last interaction
    if patient_id:
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if patient:
            patient.last_interaction_file = filename
            patient.last_interaction_id = interaction.id
            db.commit()
    
    return {'status': 'success', 'filename': filename}


def get_all_interactions(db: Session) -> List[Dict[str, Any]]:
    """
    Get all interactions summary (compatible with JSON format).
    Returns list sorted by timestamp (newest first).
    """
    interactions = db.query(Interaction).order_by(desc(Interaction.timestamp)).all()
    
    result = []
    for interaction in interactions:
        result.append({
            'filename': interaction.filename,
            'timestamp': interaction.timestamp.isoformat(),
            'chatbot_model': interaction.chatbot_model or 'N/A',
            'patient_model': interaction.patient_model or 'N/A',
            'patient_name': interaction.patient.nombre if interaction.patient else 'Desconocido'
        })
    
    return result


def get_interaction_by_filename(db: Session, filename: str) -> Optional[Dict[str, Any]]:
    """Get full interaction details by filename (for compatibility)"""
    interaction = db.query(Interaction).filter(Interaction.filename == filename).first()
    
    if not interaction:
        return None
    
    return interaction_to_dict(interaction)


def delete_interaction_by_filename(db: Session, filename: str):
    """Delete interaction by filename"""
    interaction = db.query(Interaction).filter(Interaction.filename == filename).first()
    if interaction:
        db.delete(interaction)
        db.commit()


def interaction_to_dict(interaction: Interaction) -> Dict[str, Any]:
    """Convert Interaction model to dictionary (JSON compatible)"""
    if not interaction:
        return None
    
    # Build config
    config = {
        'chatbot_model': interaction.chatbot_model,
        'patient_model': interaction.patient_model,
        'psychologist_system_prompt': interaction.psychologist_system_prompt,
        'patient_system_prompt': interaction.patient_system_prompt,
        'patient_name': interaction.patient.nombre if interaction.patient else None,
    }
    
    # Add psychologist params
    if interaction.psychologist_params:
        config.update({
            'psychologist_temperature': interaction.psychologist_params.get('temperature'),
            'psychologist_top_p': interaction.psychologist_params.get('top_p'),
            'psychologist_top_k': interaction.psychologist_params.get('top_k'),
            'psychologist_max_tokens': interaction.psychologist_params.get('max_tokens'),
            'psychologist_presence_penalty': interaction.psychologist_params.get('presence_penalty'),
            'psychologist_frequency_penalty': interaction.psychologist_params.get('frequency_penalty'),
        })
    
    # Add patient params
    if interaction.patient_params:
        config.update({
            'patient_temperature': interaction.patient_params.get('temperature'),
            'patient_top_p': interaction.patient_params.get('top_p'),
            'patient_top_k': interaction.patient_params.get('top_k'),
            'patient_max_tokens': interaction.patient_params.get('max_tokens'),
            'patient_presence_penalty': interaction.patient_params.get('presence_penalty'),
            'patient_frequency_penalty': interaction.patient_params.get('frequency_penalty'),
        })
    
    # Build messages
    messages = [
        {
            'role': msg.role,
            'content': msg.content,
            'suggested_reply_used': msg.suggested_reply_used
        }
        for msg in sorted(interaction.messages, key=lambda m: m.order)
    ]
    
    return {
        'timestamp': interaction.timestamp.isoformat(),
        'config': config,
        'messages': messages
    }


def get_interactions_by_filenames(db: Session, filenames: List[str]) -> List[Dict[str, Any]]:
    """Get multiple interactions by their filenames (for analysis)"""
    interactions = db.query(Interaction).filter(
        Interaction.filename.in_(filenames)
    ).all()
    
    return [interaction_to_dict(i) for i in interactions]


# ========== SEARCH & ANALYTICS ==========

def search_interactions_by_patient(db: Session, patient_id: str) -> List[Dict[str, Any]]:
    """Get all interactions for a specific patient"""
    interactions = db.query(Interaction).filter(
        Interaction.patient_id == patient_id
    ).order_by(desc(Interaction.timestamp)).all()
    
    return [interaction_to_dict(i) for i in interactions]


def get_interaction_stats(db: Session, patient_id: Optional[str] = None) -> Dict[str, Any]:
    """Get statistics about interactions"""
    query = db.query(Interaction)
    
    if patient_id:
        query = query.filter(Interaction.patient_id == patient_id)
    
    total_interactions = query.count()
    
    # Average messages per interaction
    avg_messages = db.query(func.avg(
        db.query(func.count(Message.id))
        .filter(Message.interaction_id == Interaction.id)
        .correlate(Interaction)
        .scalar_subquery()
    )).scalar() or 0
    
    return {
        'total_interactions': total_interactions,
        'average_messages_per_interaction': round(float(avg_messages), 2)
    }
