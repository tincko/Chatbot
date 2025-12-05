"""
Script to update main.py to use SQLite database.
Run this to add database integration to main.py
"""

import re

# Read current main.py
with open('main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add imports after rag_manager import
imports_to_add = """from sqlalchemy.orm import Session
from database import get_db, init_db
import db_helpers

# Initialize database on startup
init_db()

"""

# Find the position after "from rag_manager import RAGManager"
pattern = r'(from rag_manager import RAGManager\s*\r?\n)'
replacement = r'\1' + imports_to_add
content = re.sub(pattern, replacement, content, count=1)

# Replace get_patients endpoint
old_patients_get = r'@app\.get\("/api/patients"\)\s*def get_patients\(\):[^@]*?return \[\]'
new_patients_get = '''@app.get("/api/patients")
def get_patients(db: Session = Depends(get_db)):
    """Get all patients from database"""
    try:
        return db_helpers.get_all_patients(db)
    except Exception as e:
        print(f"Error reading patients: {e}")
        return []'''

content = re.sub(old_patients_get, new_patients_get, content, flags=re.DOTALL)

# Replace save_patients endpoint
old_patients_post = r'@app\.post\("/api/patients"\)\s*def save_patients\(patients: List\[Dict\[str, Any\]\]\):[^@]*?raise HTTPException\(status_code=500, detail=str\(e\)\)'
new_patients_post = '''@app.post("/api/patients")
def save_patients(patients: List[Dict[str, Any]], db: Session = Depends(get_db)):
    """Save/update patients in database"""
    try:
        db_helpers.create_or_update_patients(db, patients)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))'''

content = re.sub(old_patients_post, new_patients_post, content, flags=re.DOTALL)

# Replace save_interaction endpoint
old_save_interaction = r'@app\.post\("/api/save_interaction"\)\s*def save_interaction\(data: SaveInteractionRequest\):[^@]*?raise HTTPException\(status_code=500, detail=str\(e\)\)'
new_save_interaction = '''@app.post("/api/save_interaction")
def save_interaction(data: SaveInteractionRequest, db: Session = Depends(get_db)):
    """Save interaction to database"""
    try:
        result = db_helpers.save_interaction(db, data.dict())
        return result
    except Exception as e:
        print(f"Error saving interaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))'''

content = re.sub(old_save_interaction, new_save_interaction, content, flags=re.DOTALL)

# Replace get_interactions endpoint
old_get_interactions = r'@app\.get\("/api/interactions"\)\s*def get_interactions\(\):[^@]*?return interactions'
new_get_interactions = '''@app.get("/api/interactions")
def get_interactions(db: Session = Depends(get_db)):
    """Get all interactions from database"""
    return db_helpers.get_all_interactions(db)'''

content = re.sub(old_get_interactions, new_get_interactions, content, flags=re.DOTALL)

# Replace get_interaction_detail endpoint
old_get_detail = r'@app\.get\("/api/interactions/\{filename\}"\)\s*def get_interaction_detail\(filename: str\):[^@]*?raise HTTPException\(status_code=500, detail=str\(e\)\)'
new_get_detail = '''@app.get("/api/interactions/{filename}")
def get_interaction_detail(filename: str, db: Session = Depends(get_db)):
    """Get interaction details from database"""
    interaction = db_helpers.get_interaction_by_filename(db, filename)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction'''

content = re.sub(old_get_detail, new_get_detail, content, flags=re.DOTALL)

# Replace delete_interaction endpoint
old_delete = r'@app\.delete\("/api/interactions/\{filename\}"\)\s*def delete_interaction\(filename: str\):[^@]*?raise HTTPException\(status_code=500, detail=str\(e\)\)'
new_delete = '''@app.delete("/api/interactions/{filename}")
def delete_interaction(filename: str, db: Session = Depends(get_db)):
    """Delete interaction from database"""
    try:
        db_helpers.delete_interaction_by_filename(db, filename)
        return {"status": "success", "message": "Interaction deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))'''

content = re.sub(old_delete, new_delete, content, flags=re.DOTALL)

# Write updated main.py
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ main.py updated to use SQLite database!")
print("🔄 The backend should auto-reload...")
