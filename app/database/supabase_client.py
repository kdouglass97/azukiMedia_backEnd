from supabase import create_client, Client
import os
from dotenv import load_dotenv

# ✅ Load Environment Variables
load_dotenv()

# ✅ Initialize Supabase Client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("❌ Supabase URL or Key is missing!")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
print(f"🔌 Connecting to Supabase at {SUPABASE_URL}")


def insert_summary_to_db(topic: str, summary: str) -> bool:
    """Stores the AI-generated summary into the database."""
    data = {"topic": topic, "summary": summary}
    response = supabase.table("summaries").insert(data).execute()
    
    return response.get("status_code") == 201  # ✅ Success if status code 201 (Created)

def fetch_summary_from_db(topic: str):
    """Retrieves the latest summary for a given topic."""
    response = supabase.table("summaries").select("summary").eq("topic", topic).order("created_at", desc=True).limit(1).execute()
    
    if response.data:
        return response.data[0]["summary"]
    return None  # No summary found
