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
    
    # If the insert was successful, response.data should contain a list of inserted rows.
    if response.data:
        return True
    return False

def fetch_summary_from_db(topic: str):
    """
    Fetch the most recent summary + created_at from the DB for a given topic.
    """
    response = (
        supabase
        .table("summaries")
        .select("summary, created_at")
        .eq("topic", topic)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    
    if response.data:
        # Return a dict with both summary + created_at
        return {
            "summary": response.data[0]["summary"],
            "created_at": response.data[0]["created_at"]
        }
    return None

def fetch_history_from_db(topic: str):
    """
    Fetch all summaries (except the newest one) for a given topic, newest-first.
    """
    response = (
        supabase
        .table("summaries")
        .select("*")
        .eq("topic", topic)
        .order("created_at", desc=True)
        .range(1, 999)  # Skip index 0 (the newest entry)
        .execute()
    )
    
    return response.data if response.data else []

def insert_search_log(query: str) -> bool:
    data = {"query": query}
    response = supabase.table("search_logs").insert(data).execute()
    if response.data:
        return True
    return False