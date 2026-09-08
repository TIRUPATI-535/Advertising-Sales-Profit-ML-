import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")

url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "openrouter/free",
    "messages": [
        {
            "role": "user",
            "content": "Explain machine learning in 2 simple sentences."
        }
    ]
}

response = requests.post(
    url,
    headers=headers,
    json=data
)

print("Status Code:", response.status_code)
print("Response:")
print(response.json())