import requests

URL = "http://localhost:1234/v1/chat/completions"

payload = {
    "model": "mental_llama3.1-8b-mix-sft",
    "messages": [{"role": "user", "content": "Hola, prueba"}]
}

response = requests.post(URL, json=payload, timeout=30)

print("Status:", response.status_code)
print(response.text)
