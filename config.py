import sys
import os
from dotenv import load_dotenv
from google import genai
from pymongo import MongoClient

load_dotenv()

# 1. Initialize Modern Gemini Client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("❌ Error: GEMINI_API_KEY not found in environment variables.")
    sys.exit(1)

client_gemini = genai.Client(api_key=GEMINI_API_KEY)

# 2. Initialize MongoDB (Production Atlas / Local Fallback)
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

try:
    client_mongo = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client_mongo.admin.command('ping')
    print("✅ Connected to MongoDB Database")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")
    sys.exit(1)

db = client_mongo['agent_forge_db']
agents_col = db['agents']
logs_col = db['activity_logs']
users_col = db['users']