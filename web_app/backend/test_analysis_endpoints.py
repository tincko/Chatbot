import requests
import json

# Configuración
BASE_URL = "http://localhost:8000"

# Test 1: Obtener lista de interacciones
print("=" * 60)
print("TEST 1: Obtener lista de interacciones")
print("=" * 60)
response = requests.get(f"{BASE_URL}/api/interactions")
interactions = response.json()
print(f"✅ Total interacciones: {len(interactions)}")
if interactions:
    print(f"Primera interacción: {interactions[0]['filename']}")
    filename = interactions[0]['filename']
else:
    print("⚠️ No hay interacciones en la base de datos")
    exit(0)

# Test 2: Analizar interacciones
print("\n" + "=" * 60)
print("TEST 2: Analizar interacciones desde SQLite")
print("=" * 60)

analyze_request = {
    "filenames": [filename],
    "model": "qwen2.5:7b",
    "prompt": "Resume brevemente esta interacción terapéutica.",
    "document_filenames": [],
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "max_tokens": 500
}

print(f"Enviando petición de análisis para: {filename}")
print(f"Modelo: {analyze_request['model']}")
print(f"Prompt: {analyze_request['prompt']}")

try:
    response = requests.post(
        f"{BASE_URL}/api/analyze_interactions",
        json=analyze_request,
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ ANÁLISIS EXITOSO:")
        print("-" * 60)
        print(result.get('analysis', 'No analysis returned'))
        print("-" * 60)
        if 'metadata' in result:
            print(f"\nMetadata:")
            print(f"  - Patient models: {result['metadata'].get('patient_models', [])}")
            print(f"  - Patient prompts count: {len(result['metadata'].get('patient_prompts', []))}")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        
except requests.exceptions.Timeout:
    print("⏱️ Timeout - El análisis está tardando más de 60 segundos")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Chat de análisis
print("\n" + "=" * 60)
print("TEST 3: Chat de análisis con historial desde SQLite")
print("=" * 60)

chat_request = {
    "message": "¿Cuál fue el tema principal de esta sesión?",
    "history": [],
    "interaction_filenames": [filename],
    "document_filenames": [],
    "model": "qwen2.5:7b",
    "system_prompt": "Eres un asistente que ayuda a analizar sesiones terapéuticas.",
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 40,
    "max_tokens": 500
}

print(f"Enviando mensaje: {chat_request['message']}")
print(f"Con interacción: {filename}")

try:
    response = requests.post(
        f"{BASE_URL}/api/analysis_chat",
        json=chat_request,
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        print("\n✅ CHAT EXITOSO:")
        print("-" * 60)
        print(result.get('response', 'No response returned'))
        print("-" * 60)
    else:
        print(f"❌ Error {response.status_code}: {response.text}")
        
except requests.exceptions.Timeout:
    print("⏱️ Timeout - El chat está tardando más de 60 segundos")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("FIN DE LAS PRUEBAS")
print("=" * 60)
