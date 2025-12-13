import requests
import json

try:
    response = requests.get("http://localhost:8000/api/patients")
    if response.status_code == 200:
        data = response.json()
        print(f"Status: {response.status_code}")
        print(f"Total pacientes devueltos por la API: {len(data)}")
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"Error: Status {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error de conexión: {e}")
