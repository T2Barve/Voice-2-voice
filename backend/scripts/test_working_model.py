import os
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
server_env_path = BASE_DIR.parent / "server" / ".env"
load_dotenv(server_env_path, override=True)

api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
os.environ["GOOGLE_API_KEY"] = api_key

test_models = ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro", "gemini-flash-latest", "gemini-pro-latest"]

for m_name in test_models:
    print(f"Testing model: {m_name}")
    try:
        model = ChatGoogleGenerativeAI(model=m_name, temperature=0.7)
        response = model.invoke("Say hello")
        print(f"  Success! Response: {response.content}")
        break  # Use the first one that works
    except Exception as e:
        print(f"  Failed: {e}")
