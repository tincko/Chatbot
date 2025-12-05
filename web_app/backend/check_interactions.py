from database import SessionLocal, Interaction

db = SessionLocal()
interactions = db.query(Interaction).all()

print(f"Total interacciones: {len(interactions)}")
for i in interactions:
    patient_name = i.patient.nombre if i.patient else "N/A"
    print(f"Filename: {i.filename}, Patient: {patient_name}")
