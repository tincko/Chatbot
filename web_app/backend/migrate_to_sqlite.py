"""
Migration script to convert JSON files to SQLite database.
Run this once to migrate existing data.
"""

import json
import os
from datetime import datetime
from database import init_db, SessionLocal, Patient, Interaction, Message

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIALOGOS_DIR = os.path.join(BASE_DIR, "dialogos")
PATIENTS_FILE = os.path.join(BASE_DIR, "patients.json")


def migrate_patients():
    """Migrate patients from JSON to database"""
    db = SessionLocal()
    
    if not os.path.exists(PATIENTS_FILE):
        print("⚠️  No patients.json found")
        return
    
    try:
        with open(PATIENTS_FILE, 'r', encoding='utf-8') as f:
            patients_data = json.load(f)
        
        migrated_count = 0
        for patient_data in patients_data:
            # Check if patient already exists
            existing = db.query(Patient).filter(Patient.id == patient_data.get('id')).first()
            if existing:
                print(f"  ⏭️  Skipping existing patient: {patient_data.get('nombre')}")
                continue
            
            patient = Patient(
                id=patient_data.get('id'),
                nombre=patient_data.get('nombre'),
                edad=patient_data.get('edad'),
                tipo_trasplante=patient_data.get('tipo_trasplante'),
                medicacion=patient_data.get('medicacion'),
                adherencia_previa=patient_data.get('adherencia_previa'),
                contexto=patient_data.get('contexto'),
                nivel_educativo=patient_data.get('nivel_educativo'),
                estilo_comunicacion=patient_data.get('estilo_comunicacion'),
                fortalezas=patient_data.get('fortalezas'),
                dificultades=patient_data.get('dificultades'),
                notas_equipo=patient_data.get('notas_equipo'),
                idiosincrasia=patient_data.get('idiosincrasia'),
                preferred_patient_model=patient_data.get('preferred_patient_model'),
                last_interaction_file=patient_data.get('last_interaction_file')
            )
            db.add(patient)
            migrated_count += 1
        
        db.commit()
        print(f"✅ Migrated {migrated_count} patients")
        
    except Exception as e:
        print(f"❌ Error migrating patients: {e}")
        db.rollback()
    finally:
        db.close()


def migrate_interactions():
    """Migrate interactions from JSON files to database"""
    db = SessionLocal()
    
    if not os.path.exists(DIALOGOS_DIR):
        print("⚠️  No dialogos directory found")
        return
    
    files = [f for f in os.listdir(DIALOGOS_DIR) if f.endswith('.json')]
    migrated_count = 0
    skipped_count = 0
    
    for filename in files:
        try:
            # Check if already migrated
            existing = db.query(Interaction).filter(Interaction.filename == filename).first()
            if existing:
                skipped_count += 1
                continue
            
            filepath = os.path.join(DIALOGOS_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            config = data.get('config', {})
            messages_data = data.get('messages', [])
            timestamp_str = data.get('timestamp', '')
            
            # Parse timestamp
            try:
                if "T" in timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
            except:
                timestamp = datetime.utcnow()
            
            # Find patient_id from config
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
            migrated_count += 1
            
        except Exception as e:
            print(f"❌ Error migrating {filename}: {e}")
            db.rollback()
            continue
    
    db.close()
    print(f"✅ Migrated {migrated_count} interactions")
    print(f"⏭️  Skipped {skipped_count} existing interactions")


def main():
    print("🔄 Starting migration from JSON to SQLite...")
    print()
    
    # Initialize database
    print("1️⃣  Initializing database...")
    init_db()
    print()
    
    # Migrate patients
    print("2️⃣  Migrating patients...")
    migrate_patients()
    print()
    
    # Migrate interactions
    print("3️⃣  Migrating interactions...")
    migrate_interactions()
    print()
    
    print("✅ Migration complete!")
    print(f"📊 Database location: {os.path.join(BASE_DIR, 'chatbot.db')}")


if __name__ == "__main__":
    main()
