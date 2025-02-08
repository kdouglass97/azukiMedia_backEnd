from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Supabase URL or Key is missing!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def insert_summary_to_db(topic: str, summary: str) -> bool:
    data = {"topic": topic, "summary": summary}
    response = supabase.table("summaries").insert(data).execute()
    return response.status_code == 201  

def fetch_summary_from_db(topic: str):
    response = supabase.table("summaries").select("summary").eq("topic", topic).order("created_at", desc=True).limit(1).execute()
    return response.data[0]["summary"] if response.data else None  

def fetch_history_from_db(topic: str):
    """Retrieves all past summaries for a given topic."""
    response = supabase.table("summaries").select("*").eq("topic", topic).order("created_at", desc=True).execute()
    
    print("🔍 RAW DB RESPONSE:", response)  # ✅ Log database output

    if not response.data:
        return []

    return response.data  # ✅ Return full data instead of just summaries