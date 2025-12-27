
from database import SessionLocal, Message, Interaction
from orchestrator import DualLLMOrchestrator
import time

def analyze_all_interactions():
    db = SessionLocal()
    orchestrator = DualLLMOrchestrator()
    
    print("Iniciando análisis retroactivo de TODAS las interacciones...")
    
    # Get all user messages that don't have sentiment
    # We check if sentiment is NULL
    messages_to_analyze = db.query(Message).filter(
        Message.role == 'user',
        Message.sentiment == None
    ).all()
    
    total = len(messages_to_analyze)
    print(f"Encontrados {total} mensajes sin análisis.")
    
    count = 0
    for msg in messages_to_analyze:
        count += 1
        print(f"[{count}/{total}] Analizando mensaje ID {msg.id}...")
        
        try:
            # We use a default model if interaction doesn't specify one, or just the default chatbot model
            sentiment = orchestrator.analyze_sentiment(msg.content)
            if sentiment:
                msg.sentiment = sentiment
                db.commit() # Commit each one to save progress
            else:
                print(f"Skipping msg {msg.id} (no sentiment result)")
        except Exception as e:
            print(f"Error analyzing msg {msg.id}: {e}")
            
    print("Análisis completo.")
    db.close()

if __name__ == "__main__":
    analyze_all_interactions()
