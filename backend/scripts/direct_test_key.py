import os
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
server_env_path = BASE_DIR.parent / "server" / ".env"
load_dotenv(server_env_path, override=True)

api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

print(f"Using key: {api_key[:10]}...")

try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Say hello")
    print(f"Success! Response: {response.text}")
except Exception as e:
    print(f"Error with 1.5-flash: {e}")
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Say hello")
        print(f"Success with gemini-pro! Response: {response.text}")
    except Exception as e2:
        print(f"Error with gemini-pro: {e2}")
