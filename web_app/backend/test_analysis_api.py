import requests
import json

url = "http://localhost:8000/api/analyze_interactions"
filenames = ["interaction_2025-12-22T22-48-03-485000.json"]

payload = {
    "filenames": filenames,
    "model": "gpt-4",
    "prompt": "Analyze this.",
    "document_filenames": []
}

try:
    res = requests.post(url, json=payload)
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text}")
except Exception as e:
    print(f"Error: {e}")
