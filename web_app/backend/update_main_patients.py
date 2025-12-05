"""
Careful update of main.py - adds database support without breaking syntax
"""

with open('main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find line with "from rag_manager import RAGManager"
for i, line in enumerate(lines):
    if 'from rag_manager import RAGManager' in line:
        # Insert after this line
        lines.insert(i+1, 'from sqlalchemy.orm import Session\n')
        lines.insert(i+2, 'from database import get_db, init_db\n')
        lines.insert(i+3, 'import db_helpers\n')
        lines.insert(i+4, '\n')
        lines.insert(i+5, '# Initialize database on startup\n')
        lines.insert(i+6, 'init_db()\n')
        lines.insert(i+7, '\n')
        break

# Update FastAPI import
for i, line in enumerate(lines):
    if line.startswith('from fastapi import FastAPI, HTTPException, UploadFile, File'):
        lines[i] = 'from fastapi import FastAPI, HTTPException, UploadFile, File, Depends\n'
        break

# Update get_patients
for i, line in enumerate(lines):
    if 'def get_patients():' in line:
        lines[i] = 'def get_patients(db: Session = Depends(get_db)):\n'
        # Find the function body and replace
        j = i + 1
        indent_count = 0
        while j < len(lines):
            if lines[j].strip() == '' or lines[j].strip().startswith('#'):
                j += 1
                continue
            if lines[j].strip().startswith('if os.path.exists'):
                # Replace entire function body
                lines[j] = '    """Get all patients from database"""\n'
                lines[j+1] = '    try:\n'
                lines.insert(j+2, '        return db_helpers.get_all_patients(db)\n')
                lines.insert(j+3, '    except Exception as e:\n')
                lines.insert(j+4, '        print(f"Error reading patients: {e}")\n')
                lines.insert(j+5, '        return []\n')
                # Remove old lines
                k = j + 6
                while k < len(lines) and not lines[k].startswith('@app') and not lines[k].startswith('app.'):
                    lines.pop(k)
                break
            j += 1
        break

# Update save_patients
for i, line in enumerate(lines):
    if 'def save_patients(patients: List[Dict[str, Any]]):' in line:
        lines[i] = 'def save_patients(patients: List[Dict[str, Any]], db: Session = Depends(get_db)):\n'
        # Replace function body
        j = i + 1
        lines[j] = '    """Save/update patients in database"""\n'
        lines[j+1] = '    try:\n'
        lines.insert(j+2, '        db_helpers.create_or_update_patients(db, patients)\n')
        lines.insert(j+3, '        return {"status": "success"}\n')
        lines.insert(j+4, '    except Exception as e:\n')
        lines.insert(j+5, '        raise HTTPException(status_code=500, detail=str(e))\n')
        # Remove old lines
        k = j + 6
        while k < len(lines) and not lines[k].startswith('@app'):
            lines.pop(k)
        break

# Save
with open('main.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✅ main.py updated - patients endpoints now use SQLite")
