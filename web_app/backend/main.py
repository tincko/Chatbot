
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from fastapi.middleware.cors import CORSMiddleware
from orchestrator import DualLLMOrchestrator

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

class ChatResponse(BaseModel):
    response: str
    suggested_reply: str

@app.get("/models")
def get_models():
    return {"models": orchestrator.list_models()}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    try:
        result = orchestrator.chat(
            req.chatbot_model,
            req.patient_model,
            req.history,
            req.message,
            req.psychologist_system_prompt,
            req.patient_system_prompt
        )
        return ChatResponse(
            response=result["response"],
            suggested_reply=result["suggested_reply"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
