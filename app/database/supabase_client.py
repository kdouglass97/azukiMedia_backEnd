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


def insert_summary_to_db(topic: str, summary: str):
    print(f"📤 Inserting into Supabase: topic={topic}, summary={summary[:100]}...")

    try:
        response = supabase.table("summaries").insert({
            "topic": topic,
            "summary": summary
        }).execute()
        print(f"📝 Insert Response: {response}")
        
        # ✅ Check if insertion failed
        if "error" in response and response["error"]:
            print(f"⚠️ Supabase Error: {response['error']}")
        
    except Exception as e:
        print(f"❌ ERROR inserting into DB: {e}")

def fetch_history_from_db(topic: str):
    """Fetch summaries for a given topic, sorted by newest first."""
    try:
        response = supabase.table("summaries").select("*").eq("topic", topic).order("created_at", desc=True).execute()
        return response.data  # ✅ Return only the data part
    except Exception as e:
        print(f"❌ ERROR fetching from DB: {e}")
        return []
