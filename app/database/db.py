from supabase import create_client
import os
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

# ✅ Connect to Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
