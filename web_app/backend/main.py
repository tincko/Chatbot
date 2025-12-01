from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
from orchestrator import DualLLMOrchestrator
import os
import json

app = FastAPI(title="Dual-LLM Chat Interface")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = DualLLMOrchestrator()

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
            req.frequency_penalty
        )
        return ChatResponse(response=response)
    except Exception as e:
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

@app.post("/api/generate_profile")
def generate_profile(request: GenerateProfileRequest):
    try:
        profile = orchestrator.generate_patient_profile(request.model)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

DIALOGOS_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), "dialogos")
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
        
        import re # Local import to avoid changing top of file
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)