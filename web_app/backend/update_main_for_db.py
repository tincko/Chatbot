"""
Complete update script for main.py to use SQLite for all operations.
This updates patient management, interaction management, and analysis endpoints.
"""

import re

print("Reading main.py...")
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Add database imports
print("1. Adding database imports...")
imports_pattern = r'(from rag_manager import RAGManager)'
imports_replacement = r'\1\nfrom sqlalchemy.orm import Session\nfrom database import get_db, init_db\nimport db_helpers\n\n# Initialize database on startup\ninit_db()'
content = re.sub(imports_pattern, imports_replacement, content, count=1)

# Step 2: Add Depends to FastAPI import
content = content.replace(
    'from fastapi import FastAPI, HTTPException, UploadFile, File',
    'from fastapi import FastAPI, HTTPException, UploadFile, File, Depends'
)

# Step 3: Update get_patients endpoint
old_get_patients = r'@app\.get\("/api/patients"\)\ndef get_patients\(\):.*?return \[\]'
new_get_patients = '''@app.get("/api/patients")
def get_patients(db: Session = Depends(get_db)):
    """Get all patients from database"""
    try:
        return db_helpers.get_all_patients(db)
    except Exception as e:
        print(f"Error reading patients: {e}")
        return []'''
content = re.sub(old_get_patients, new_get_patients, content, flags=re.DOTALL)

# Step 4: Update save_patients endpoint
old_save_patients = r'@app\.post\("/api/patients"\)\ndef save_patients\(patients: List\[Dict\[str, Any\]\]\):.*?raise HTTPException\(status_code=500, detail=str\(e\)\)'
new_save_patients = '''@app.post("/api/patients")
def save_patients(patients: List[Dict[str, Any]], db: Session = Depends(get_db)):
    """Save/update patients in database"""
    try:
        db_helpers.create_or_update_patients(db, patients)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))'''
content = re.sub(old_save_patients, new_save_patients, content, flags=re.DOTALL)

# Step 5: Update save_interaction endpoint
old_save = r'@app\.post\("/api/save_interaction"\)\ndef save_interaction\(data: SaveInteractionRequest\):.*?raise HTTPException\(status_code=500, detail=str\(e\)\)'
new_save = '''@app.post("/api/save_interaction")
def save_interaction(data: SaveInteractionRequest, db: Session = Depends(get_db)):
    """Save interaction to database"""
    try:
        result = db_helpers.save_interaction(db, data.dict())
        return result
    except Exception as e:
        print(f"Error saving interaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))'''
content = re.sub(old_save, new_save, content, flags=re.DOTALL)

# Step 6: Update get_interactions endpoint
old_get_ints = r'@app\.get\("/api/interactions"\)\ndef get_interactions\(\):.*?return interactions'
new_get_ints = '''@app.get("/api/interactions")
def get_interactions(db: Session = Depends(get_db)):
    """Get all interactions from database"""
    return db_helpers.get_all_interactions(db)'''
content = re.sub(old_get_ints, new_get_ints, content, flags=re.DOTALL)

# Step 7: Update get_interaction_detail endpoint
old_detail = r'@app\.get\("/api/interactions/\{filename\}"\)\ndef get_interaction_detail\(filename: str\):.*?raise HTTPException\(status_code=500, detail=str\(e\)\)'
new_detail = '''@app.get("/api/interactions/{filename}")
def get_interaction_detail(filename: str, db: Session = Depends(get_db)):
    """Get interaction details from database"""
    interaction = db_helpers.get_interaction_by_filename(db, filename)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction'''
content = re.sub(old_detail, new_detail, content, flags=re.DOTALL)

# Step 8: Update delete_interaction endpoint  
old_delete = r'@app\.delete\("/api/interactions/\{filename\}"\)\ndef delete_interaction\(filename: str\):.*?raise HTTPException\(status_code=500, detail=str\(e\)\)'
new_delete = '''@app.delete("/api/interactions/{filename}")
def delete_interaction(filename: str, db: Session = Depends(get_db)):
    """Delete interaction from database"""
    try:
        db_helpers.delete_interaction_by_filename(db, filename)
        return {"status": "success", "message": "Interaction deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))'''
content = re.sub(old_delete, new_delete, content, flags=re.DOTALL)

# Step 9: Update analyze_interactions_endpoint (the critical one for analysis)
old_analyze = r'@app\.post\("/api/analyze_interactions"\)\ndef analyze_interactions_endpoint\(req: AnalyzeRequest\):.*?for filename in req\.filenames:.*?interactions_content\.append\(conversation_text\)'
new_analyze = '''@app.post("/api/analyze_interactions")
def analyze_interactions_endpoint(req: AnalyzeRequest, db: Session = Depends(get_db)):
    try:
        # 1. Load interactions from database using filenames
        interactions_content = []
        patient_models = set()
        patient_prompts = set()
        
        # Get all interactions by filenames
        interactions = db_helpers.get_interactions_by_filenames(db, req.filenames)
        
        for interaction_data in interactions:
            # Extract relevant info for analysis
            timestamp = interaction_data.get('timestamp', 'Unknown Date')
            config = interaction_data.get('config', {})
            
            if 'patient_model' in config:
                patient_models.add(config['patient_model'])
            if 'patient_system_prompt' in config:
                patient_prompts.add(config['patient_system_prompt'])
            messages = interaction_data.get('messages', [])
            
            # Extract patient name from config
            patient_name = config.get('patient_name', 'Unknown Patient')
            
            # Format conversation
            conversation_text = f"--- Interaction Date: {timestamp} | Patient: {patient_name} ---\\n"
            for msg in messages:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                conversation_text += f"{role.upper()}: {content}\\n"
            
            interactions_content.append(conversation_text)'''
content = re.sub(old_analyze, new_analyze, content, flags=re.DOTALL)

# Step 10: Update analysis_chat_endpoint
old_analysis_chat = r'@app\.post\("/api/analysis_chat"\)\ndef analysis_chat_endpoint\(req: AnalysisChatRequest\):.*?for filename in req\.interaction_filenames:.*?interactions_text \+= f"\{msg\.get'
new_analysis_chat = '''@app.post("/api/analysis_chat")
def analysis_chat_endpoint(req: AnalysisChatRequest, db: Session = Depends(get_db)):
    try:
        # 1. Get Interactions Content from database
        interactions_text = ""
        interactions = db_helpers.get_interactions_by_filenames(db, req.interaction_filenames)
        
        for interaction_data in interactions:
            timestamp = interaction_data.get('timestamp', 'Unknown')
            patient = interaction_data.get('config', {}).get('patient_name', 'Unknown')
            filename = [i for i in db_helpers.get_all_interactions(db) if i['timestamp'] == timestamp][0]['filename'] if db_helpers.get_all_interactions(db) else 'unknown'
            interactions_text += f"\\n--- Interaction: {filename} ({timestamp}, Patient: {patient}) ---\\n"
            for msg in interaction_data.get('messages', []):
                interactions_text += f"{msg.get('role', 'unknown').upper()}: {msg.get'''
content = re.sub(old_analysis_chat, new_analysis_chat, content, flags=re.DOTALL)

print("Writing updated main.py...")
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ main.py updated successfully for SQLite!")
print("🔄 Backend should auto-reload...")
