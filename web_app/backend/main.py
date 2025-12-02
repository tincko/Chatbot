from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
import shutil
import re
from pypdf import PdfReader
from orchestrator import DualLLMOrchestrator
from rag_manager import RAGManager

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

class SuggestionResponse(BaseModel):
    suggested_reply: str

class GenerateProfileRequest(BaseModel):
    model: str

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
def get_patients():
    if os.path.exists(PATIENTS_FILE):
        try:
            with open(PATIENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading patients file: {e}")
            return []
    return []

@app.post("/api/patients")
def save_patients(patients: List[Dict[str, Any]]):
    try:
        with open(PATIENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(patients, f, indent=2, ensure_ascii=False)
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
        profile = orchestrator.generate_patient_profile(request.model)
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
def save_interaction(data: SaveInteractionRequest):
    try:
        # Create a filename based on the timestamp
        filename = f"interaction_{data.timestamp.replace(':', '-').replace('.', '-')}.json"
        filepath = os.path.join(DIALOGOS_DIR, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data.dict(), f, indent=2, ensure_ascii=False)
            
        return {"status": "success", "filename": filename}
    except Exception as e:
        print(f"Error saving interaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/interactions")
def get_interactions():
    interactions = []
    if os.path.exists(DIALOGOS_DIR):
        files = [f for f in os.listdir(DIALOGOS_DIR) if f.endswith('.json')]
        files.sort(reverse=True) # Newest first
        
        # import re # Local import to avoid changing top of file - now global
        
        for filename in files:
            try:
                filepath = os.path.join(DIALOGOS_DIR, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    config = data.get('config', {})
                    timestamp = data.get('timestamp', '')
                    
                    # Try to extract patient name
                    patient_name = "Desconocido"
                    patient_prompt = config.get('patient_system_prompt', '')
                    if patient_prompt:
                        # Look for "Sos el PACIENTE: {name}" with various terminators
                        match = re.search(r"Sos el PACIENTE[:\s]+(.*?)(?:,|\.|;|\n|$)", patient_prompt, re.IGNORECASE)
                        if match:
                            patient_name = match.group(1).strip()
                        else:
                            # Fallback: try to find just the name line
                            first_line = patient_prompt.split('\n')[0]
                            if "Sos el PACIENTE" in first_line:
                                patient_name = first_line.replace("Sos el PACIENTE", "").replace(":", "").strip().split(',')[0].strip()

                    interactions.append({
                        "filename": filename,
                        "timestamp": timestamp,
                        "chatbot_model": config.get('chatbot_model', 'N/A'),
                        "patient_model": config.get('patient_model', 'N/A'),
                        "patient_name": patient_name
                    })
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                continue
                
    return interactions

@app.get("/api/interactions/{filename}")
def get_interaction_detail(filename: str):
    filepath = os.path.join(DIALOGOS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Interaction not found")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/interactions/{filename}")
def delete_interaction(filename: str):
    filepath = os.path.join(DIALOGOS_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Interaction not found")
    
    try:
        os.remove(filepath)
        return {"status": "success", "message": "Interaction deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AnalyzeRequest(BaseModel):
    filenames: List[str]
    model: str
    prompt: str
    document_filenames: Optional[List[str]] = []

class AnalysisChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]]
    interaction_filenames: List[str]
    document_filenames: List[str]
    model: str
    system_prompt: str

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
        
        return {"status": "success", "message": f"Re-indexed {len(files)} documents."}
    except Exception as e:
        print(f"Error re-indexing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze_interactions")
def analyze_interactions_endpoint(req: AnalyzeRequest):
    try:
        # 1. Load content of all selected files
        interactions_content = []
        for filename in req.filenames:
            filepath = os.path.join(DIALOGOS_DIR, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Extract relevant info for analysis
                    timestamp = data.get('timestamp', 'Unknown Date')
                    config = data.get('config', {})
                    messages = data.get('messages', [])
                    
                    # Extract patient name from config (similar logic to get_interactions)
                    patient_name = "Unknown Patient"
                    patient_prompt = config.get('patient_system_prompt', '')
                    # import re # This import is now global
                    match = re.search(r"Sos el PACIENTE[:\s]+(.*?)(?:,|\.|;|\n|$)", patient_prompt, re.IGNORECASE)
                    if match:
                        patient_name = match.group(1).strip()
                    
                    # Format conversation
                    conversation_text = f"--- Interaction Date: {timestamp} | Patient: {patient_name} ---\n"
                    for msg in messages:
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')
                        conversation_text += f"{role.upper()}: {content}\n"
                    
                    interactions_content.append(conversation_text)
        
        if not interactions_content and not req.document_filenames: # Modified condition
            return {"analysis": "No valid interactions or documents found to analyze."}
            
        full_context = "\n\n".join(interactions_content)

        # 2. Append Documents Content if any
        if req.document_filenames:
            full_context += "\n\n=== REFERENCE DOCUMENTS ===\n"
            for doc_name in req.document_filenames:
                doc_path = os.path.join(DOCUMENTS_DIR, doc_name)
                if os.path.exists(doc_path):
                    try:
                        content = ""
                        if doc_name.lower().endswith('.pdf'):
                            reader = PdfReader(doc_path)
                            for page in reader.pages:
                                content += page.extract_text() + "\n"
                        else:
                            # Try reading as text
                            with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                        
                        full_context += f"\n--- Document: {doc_name} ---\n{content}\n"
                    except Exception as e:
                        print(f"Error reading document {doc_name}: {e}")
                        full_context += f"\n--- Document: {doc_name} (Error reading content) ---\n"
        
        # 3. Call Orchestrator to analyze
        analysis = orchestrator.analyze_interactions(req.model, full_context, req.prompt)
        return {"analysis": analysis}

    except Exception as e:
        print(f"Error analyzing interactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analysis_chat")
def analysis_chat_endpoint(req: AnalysisChatRequest):
    try:
        # 1. Get Interactions Content
        interactions_text = ""
        for filename in req.interaction_filenames:
            filepath = os.path.join(DIALOGOS_DIR, filename)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Format conversation (simplified)
                    timestamp = data.get('timestamp', 'Unknown')
                    patient = data.get('config', {}).get('patient_name', 'Unknown')
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
        response = orchestrator.chat_analysis(req.model, req.history + [{"role": "user", "content": req.message}], req.system_prompt, full_context)
        
        return {"response": response}
        
    except Exception as e:
        print(f"Error in analysis chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)