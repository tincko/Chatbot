import requests
import json

URL = "http://10.5.0.2:1234/v1/chat/completions"

payload = {
    "model": "mental_llama3.1-8b-mix-sft",  # el nombre que ves en LM Studio
    "messages": [
        {"role": "user", "content": "Hola, ¿podés responder este mensaje de prueba?"}
    ],
    "temperature": 0.7,
}

response = requests.post(URL, json=payload, timeout=120)

print("Status code:", response.status_code)
print("Raw response:")
print(response.text)

try:
    data = response.json()
    print("\nContenido del assistant:")
    print(data["choices"][0]["message"]["content"])
except json.JSONDecodeError:
    print("No se pudo parsear JSON.")
