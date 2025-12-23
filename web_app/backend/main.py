from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
import shutil
import re
from datetime import datetime
from orchestrator import DualLLMOrchestrator
from rag_manager import RAGManager
from sqlalchemy.orm import Session
from database import get_db, init_db
import db_helpers

# Initialize database on startup
init_db()


from sqlalchemy.orm import Session
from database import get_db, init_db
import db_helpers

# Initialize database on startup
init_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = DualLLMOrchestrator()
rag_manager = RAGManager()

class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] # [{"role": "user", "content": "..."}, ...]
    chatbot_model: str
    patient_model: str
    psychologist_system_prompt: Optional[str] = None
    patient_system_prompt: Optional[str] = None
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    top_k: Optional[int] = 40
    max_tokens: Optional[int] = 600
    presence_penalty: Optional[float] = 0.1
    frequency_penalty: Optional[float] = 0.2
    rag_documents: Optional[List[str]] = []

class ChatResponse(BaseModel):
    response: str

class SuggestionRequest(BaseModel):
    history: List[Dict[str, str]]
    user_message: str
    psychologist_response: str
    patient_model: str
    patient_system_prompt: Optional[str] = None
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    top_k: Optional[int] = 40
    max_tokens: Optional[int] = 600
    presence_penalty: Optional[float] = 0.1
    frequency_penalty: Optional[float] = 0.2
    rag_documents: Optional[List[str]] = []

class ChatResponse(BaseModel):
    response: str

class SuggestionRequest(BaseModel):
    history: List[Dict[str, str]]
    user_message: str
    psychologist_response: str
    patient_model: str
    patient_system_prompt: Optional[str] = None
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    top_k: Optional[int] = 40
    max_tokens: Optional[int] = 600
    presence_penalty: Optional[float] = 0.1
    frequency_penalty: Optional[float] = 0.2

class SuggestionResponse(BaseModel):
    suggested_reply: str

class GenerateProfileRequest(BaseModel):
    model: str
    guidance: Optional[str] = None

@app.get("/api/models")
def get_models():
    return {"models": orchestrator.list_models()}

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    try:
        # RAG Retrieval
        context_text = ""
        if req.rag_documents:
            print(f"Performing RAG search in documents: {req.rag_documents}")
            retrieved_docs = rag_manager.query(req.message, n_results=3, filter_filenames=req.rag_documents)
            if retrieved_docs:
                context_text = "\n\n=== RELEVANT CONTEXT FROM DOCUMENTS ===\n"
                for i, doc in enumerate(retrieved_docs):
                    context_text += f"--- Excerpt {i+1} ---\n{doc}\n"
                context_text += "=======================================\n"
                print(f"RAG Context length: {len(context_text)}")

        response = orchestrator.chat_psychologist(
            req.chatbot_model,
            req.history,
            req.message,
            req.psychologist_system_prompt,
            req.temperature,
            req.top_p,
            req.top_k,
            req.max_tokens,
            req.presence_penalty,
            req.frequency_penalty,
            context=context_text 
        )
        return ChatResponse(response=response)
    except Exception as e:
        print(f"Error in chat_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/suggest", response_model=SuggestionResponse)
def suggest_endpoint(req: SuggestionRequest):
    try:
        suggestion = orchestrator.generate_suggestion_only(
            req.patient_model,
            req.history,
            req.user_message,
            req.psychologist_response,
            req.patient_system_prompt,
            req.temperature,
            req.top_p,
            req.top_k,
            req.max_tokens,
            req.presence_penalty,
            req.frequency_penalty
        )
        return SuggestionResponse(suggested_reply=suggestion)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PATIENTS_FILE = os.path.join(BASE_DIR, "patients.json")

@app.get("/api/patients")
def get_patients(db: Session = Depends(get_db)):
    """Get all patients from database"""
    try:
        return db_helpers.get_all_patients(db)
    except Exception as e:
        print(f"Error reading patients: {e}")
        return []
    return []

@app.post("/api/patients")
def save_patients(patients: List[Dict[str, Any]], db: Session = Depends(get_db)):
    """Save/update patients in database"""
    try:
        db_helpers.create_or_update_patients(db, patients)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

PROMPTS_FILE = os.path.join(BASE_DIR, "prompts.json")

@app.get("/api/prompts")
def get_prompts():
    if os.path.exists(PROMPTS_FILE):
        try:
            with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading prompts file: {e}")
            return {}
    return {}

@app.post("/api/prompts")
def save_prompts(prompts: Dict[str, str]):
    try:
        # Merge with existing if any
        existing = {}
        if os.path.exists(PROMPTS_FILE):
            with open(PROMPTS_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        
        existing.update(prompts)
        

        with open(PROMPTS_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate_profile")
def generate_profile(request: GenerateProfileRequest):
    try:
        profile = orchestrator.generate_patient_profile(request.model, request.guidance)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

DIALOGOS_DIR = os.path.join(BASE_DIR, "dialogos")
if not os.path.exists(DIALOGOS_DIR):
    os.makedirs(DIALOGOS_DIR)

class SaveInteractionRequest(BaseModel):
    timestamp: str
    config: Dict[str, Any]
    messages: List[Dict[str, Any]]

@app.post("/api/save_interaction")
def save_interaction(data: SaveInteractionRequest, db: Session = Depends(get_db)):
    """Save interaction to database"""
    try:
        result = db_helpers.save_interaction(db, data.dict())
        return result
    except Exception as e:
        print(f"Error saving interaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interactions")
def get_interactions(db: Session = Depends(get_db)):
    """Get all interactions from database"""
    return db_helpers.get_all_interactions(db)

@app.get("/api/interactions/{filename}")
def get_interaction_detail(filename: str, db: Session = Depends(get_db)):
    """Get interaction details from database"""
    interaction = db_helpers.get_interaction_by_filename(db, filename)
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    return interaction

@app.delete("/api/interactions/{filename}")
def delete_interaction(filename: str, db: Session = Depends(get_db)):
    """Delete interaction from database"""
    try:
        db_helpers.delete_interaction_by_filename(db, filename)
        return {"status": "success", "message": "Interaction deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AnalyzeRequest(BaseModel):
    filenames: List[str]
    model: str
    prompt: str
    document_filenames: Optional[List[str]] = []
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    top_k: Optional[int] = 40
    max_tokens: Optional[int] = 2000
    presence_penalty: Optional[float] = 0.1
    frequency_penalty: Optional[float] = 0.2

class GenerateInteractionRequest(BaseModel):
    patient_profile: Dict
    patient_system_prompt: str
    psychologist_system_prompt: str
    chatbot_model: str
    patient_model: str
    turns: Optional[int] = 10
    psychologist_temperature: Optional[float] = 0.7
    patient_temperature: Optional[float] = 0.7

class AnalysisChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]]
    interaction_filenames: List[str]
    document_filenames: List[str]
    model: str
    system_prompt: str
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    top_k: Optional[int] = 40
    max_tokens: Optional[int] = 2000
    presence_penalty: Optional[float] = 0.1
    frequency_penalty: Optional[float] = 0.2

DOCUMENTS_DIR = os.path.join(BASE_DIR, "documentos")
if not os.path.exists(DOCUMENTS_DIR):
    os.makedirs(DOCUMENTS_DIR)

@app.post("/api/upload_document")
async def upload_document(files: List[UploadFile] = File(...), chunk_size: int = 1000, overlap: int = 200):
    saved_filenames = []
    try:
        for file in files:
            filepath = os.path.join(DOCUMENTS_DIR, file.filename)
            with open(filepath, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_filenames.append(file.filename)
            
            # Index the document
            rag_manager.add_document(file.filename, filepath, chunk_size=chunk_size, overlap=overlap)
            
        return {"status": "success", "filenames": saved_filenames}
    except Exception as e:
        print(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
def get_documents():
    if not os.path.exists(DOCUMENTS_DIR):
        return []
    files = [f for f in os.listdir(DOCUMENTS_DIR) if os.path.isfile(os.path.join(DOCUMENTS_DIR, f))]
    return files

@app.delete("/api/documents/{filename}")
def delete_document(filename: str):
    filepath = os.path.join(DOCUMENTS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        os.remove(filepath)
        # Also remove from vector db
        rag_manager.delete_document(filename)
        return {"status": "success", "message": "Document deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ReindexRequest(BaseModel):
    chunk_size: int = 1000
    overlap: int = 200

@app.post("/api/reindex_documents")
def reindex_documents(req: ReindexRequest):
    try:
        # Clear existing collection
        rag_manager.clear_collection()
        
        files = []
        # Re-index all files in DOCUMENTS_DIR
        if os.path.exists(DOCUMENTS_DIR):
            files = [f for f in os.listdir(DOCUMENTS_DIR) if os.path.isfile(os.path.join(DOCUMENTS_DIR, f))]
            for filename in files:
                filepath = os.path.join(DOCUMENTS_DIR, filename)
                rag_manager.add_document(filename, filepath, chunk_size=req.chunk_size, overlap=req.overlap)
        
        return {"status": "success", "message": f"Se re-indexaron {len(files)} documentos."}
    except Exception as e:
        print(f"Error re-indexing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate_interaction")
def generate_interaction(req: GenerateInteractionRequest, db: Session = Depends(get_db)):
    try:
        print(f"Received interaction generation request for patient: {req.patient_profile.get('nombre')} with {req.turns} turns.")
        messages = orchestrator.simulate_interaction(
            req.chatbot_model,
            req.patient_model,
            req.psychologist_system_prompt,
            req.patient_system_prompt,
            turns=req.turns,
            psychologist_temperature=req.psychologist_temperature,
            patient_temperature=req.patient_temperature
        )
        
        # Save interaction
        now = datetime.now()
        timestamp_iso = now.isoformat()
        timestamp_safe = now.strftime("%Y-%m-%d_%H-%M-%S")
        patient_name = req.patient_profile.get('nombre', 'Unknown')
        # Sanitize filename: remove invalid chars for Windows/Linux filesystems
        patient_name = re.sub(r'[<>:"/\\|?*]', '', patient_name).strip().replace(" ", "_")
        filename = f"auto_{patient_name}_{timestamp_safe}.json"
        
        # We don't necessarily need to save to file anymore if we have DB, but keeping it for backup/debug is fine. 
        # Or we can rely on save_interaction to generate the filename and we just use that.
        # However, db_helpers.save_interaction generates its own filename based on timestamp. 
        # To reuse the logic and keep consistency, let's construct the data object and pass it to db_helpers.
        
        data = {
            "timestamp": timestamp_iso,
            "config": {
                "chatbot_model": req.chatbot_model,
                "patient_model": req.patient_model,
                "psychologist_system_prompt": req.psychologist_system_prompt,
                "patient_system_prompt": req.patient_system_prompt,
                "patient_name": req.patient_profile.get('nombre', 'Unknown'),
                "mode": "autonomous",
                # Pass params so they get saved to DB columns too
                "psychologist_temperature": req.psychologist_temperature,
                "patient_temperature": req.patient_temperature,
            },
            "messages": messages
        }
        
        # Save to DB
        # This will create a filename like interaction_TIMESTAMP.json in the DB record
        # and return it.
        result = db_helpers.save_interaction(db, data)
        saved_filename = result['filename']

        # OPTIONAL: Save to file system as well using the SAME filename from DB to match
        filepath = os.path.join(DIALOGOS_DIR, saved_filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        return {"status": "success", "filename": saved_filename, "messages": messages}
        
    except Exception as e:
        print(f"Error generating interaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze_interactions")
def analyze_interactions_endpoint(req: AnalyzeRequest, db: Session = Depends(get_db)):
    try:
        # 1. Load content of all selected files from database
        interactions_content = []
        patient_models = set()
        patient_prompts = set()
        
        # Get interactions from database
        # Try to find in DB first
        db_interactions = db_helpers.get_interactions_by_filenames(db, req.filenames)
        
        # Helper to find interaction in DB list
        def find_in_db(fname):
            for i in db_interactions:
                if i.get('filename') == fname:
                    return i
            return None

        print(f"DEBUG: Processing {len(req.filenames)} filenames: {req.filenames}")
        print(f"DEBUG: Filenames type: {type(req.filenames)}")
        if len(req.filenames) > 0:
            print(f"DEBUG: First filename repr: {repr(req.filenames[0])}")
        
        for fname in req.filenames:
            data = find_in_db(fname)
            print(f"DEBUG: find_in_db('{fname}') returned: {'FOUND' if data else 'NONE'}")
            
            # Fallback 1: Direct DB lookup for single file (Paranoid check)
            if not data:
                print(f"DEBUG: Attempting direct DB lookup for {fname}")
                direct_data = db_helpers.get_interaction_by_filename(db, fname)
                if direct_data:
                    data = direct_data
                    print(f"DEBUG: Found {fname} via direct DB lookup.")

            # Fallback 2: If not in DB, try loading from disk (JSON file)
            if not data:
                fpath = os.path.join(DIALOGOS_DIR, fname)
                print(f"DEBUG: Checking disk for {fname} at {fpath}")
                if os.path.exists(fpath):
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            print(f"DEBUG: Found {fname} on disk.")
                    except Exception as e:
                        print(f"Error reading interaction file {fname}: {e}")
                else:
                    print(f"DEBUG: {fname} NOT FOUND on disk.")
            
            if data:
                # Extract relevant info for analysis
                timestamp = data.get('timestamp', 'Unknown Date')
                config = data.get('config', {})
                
                if 'patient_model' in config:
                    patient_models.add(config['patient_model'])
                if 'patient_system_prompt' in config:
                    patient_prompts.add(config['patient_system_prompt'])
                messages = data.get('messages', [])
                
                # Extract patient name from config
                patient_name = config.get('patient_name', 'Unknown Patient')
                
                # Format conversation
                conversation_text = f"--- Interaction Date: {timestamp} | Patient: {patient_name} ---\n"
                for msg in messages:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    conversation_text += f"{role.upper()}: {content}\n"
                
                interactions_content.append(conversation_text)
            else:
                 print(f"Warning: Interaction {fname} not found in DB or disk.")
        
        if not interactions_content and not req.document_filenames: # Modified condition
            return {"analysis": "No se encontraron interacciones o documentos válidos para analizar."}
            








            
        full_context = "\n\n".join(interactions_content)

        # 2. Append Documents Content if any
        if req.document_filenames:
            full_context += "\n\n=== REFERENCE DOCUMENTS ===\n"
            for doc_name in req.document_filenames:
                doc_path = os.path.join(DOCUMENTS_DIR, doc_name)
                if os.path.exists(doc_path):
                    try:
                        # Use docling via rag_manager to get text
                        conv_result = rag_manager.doc_converter.convert(doc_path)
                        content = conv_result.document.export_to_markdown()
                        
                        full_context += f"\n--- Document: {doc_name} ---\n{content}\n"
                    except Exception as e:
                        print(f"Error reading document {doc_name}: {e}")
                        full_context += f"\n--- Document: {doc_name} (Error reading content) ---\n"
        
        # 3. Call Orchestrator to analyze
        analysis = orchestrator.analyze_interactions(
            req.model, 
            full_context, 
            req.prompt,
            temperature=req.temperature,
            top_p=req.top_p,
            top_k=req.top_k,
            max_tokens=req.max_tokens,
            presence_penalty=req.presence_penalty,
            frequency_penalty=req.frequency_penalty
        )
        return {
            "analysis": analysis,
            "metadata": {
                "patient_models": list(patient_models),
                "patient_prompts": list(patient_prompts)
            }
        }

    except Exception as e:
        print(f"Error analyzing interactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis_chat")
def analysis_chat_endpoint(req: AnalysisChatRequest, db: Session = Depends(get_db)):
    try:
        # 1. Get Interactions Content from database
        interactions_text = ""
        
        # Get interactions from database
        interactions = db_helpers.get_interactions_by_filenames(db, req.interaction_filenames)
        
        for data in interactions:
            timestamp = data.get('timestamp', 'Unknown')
            patient = data.get('config', {}).get('patient_name', 'Unknown')
            # Find filename from all interactions
            all_ints = db_helpers.get_all_interactions(db)
            filename = next((i['filename'] for i in all_ints if i['timestamp'] == timestamp), 'unknown')
            interactions_text += f"\n--- Interaction: {filename} ({timestamp}, Patient: {patient}) ---\n"
            for msg in data.get('messages', []):
                interactions_text += f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}\n"
        
        # 2. Get RAG Content
        rag_text = ""
        if req.document_filenames:
            # We query the RAG system with the user's message
            # But we filter by the selected documents
            docs = rag_manager.query(req.message, n_results=5, filter_filenames=req.document_filenames)
            if docs:
                rag_text = "\n".join(docs)
            else:
                rag_text = "No relevant document chunks found for this query."
        
        # 3. Combine Context
        full_context = ""
        if interactions_text:
            full_context += f"--- SELECTED INTERACTIONS ---\n{interactions_text}\n"
        if rag_text:
            full_context += f"\n--- RELEVANT DOCUMENT CHUNKS (RAG) ---\n{rag_text}\n"
            
        if not full_context:
            full_context = "No context selected."
            
        # 4. Call Orchestrator
        response = orchestrator.chat_analysis(
            req.model, 
            req.history + [{"role": "user", "content": req.message}], 
            req.system_prompt, 
            full_context,
            temperature=req.temperature,
            top_p=req.top_p,
            top_k=req.top_k,
            max_tokens=req.max_tokens,
            presence_penalty=req.presence_penalty,
            frequency_penalty=req.frequency_penalty
        )
        
        return {"response": response}
        
    except Exception as e:
        print(f"Error in analysis chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)