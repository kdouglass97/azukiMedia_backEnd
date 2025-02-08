from fastapi import APIRouter
from fastapi.responses import JSONResponse, FileResponse
import os
from datetime import datetime
import re
from app.crewai.agents import get_summary_from_agents
from app.database.supabase_client import insert_summary_to_db, fetch_history_from_db  # ✅ Import database functions

# ✅ Initialize Router
router = APIRouter()

# ✅ Serve Homepage
@router.get("/")
async def serve_homepage():
    index_path = "app/static/index.html"
    
    if not os.path.exists(index_path):
        print(f"❌ ERROR: index.html not found at {index_path}")
        return JSONResponse(content={"error": "index.html not found"}, status_code=404)

    return FileResponse(index_path)

# ✅ Manually Handle OPTIONS for /summary/{topic}
@router.options("/summary/{topic}")
async def options_summary(topic: str):
    return JSONResponse(
        content={"message": "Preflight OK"},
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

# ✅ News Summary API Endpoint (Calls CrewAI + Stores in Supabase)
@router.get("/summary/{topic}")
async def get_summary(topic: str):
    print(f"🟢 Received request for topic: {topic}")  # ✅ Log API calls
    try:
        result = get_summary_from_agents(topic)  # ✅ Calls CrewAI processing
        print(f"✅ CrewAI Result: {result}")  # ✅ Log AI results

        # ✅ Save to Supabase
        insert_summary_to_db(topic, result)  

        return JSONResponse(
            content={"topic": topic, "summary": result},
            headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        print(f"❌ ERROR: {e}")  # ✅ Log any crashes
        return JSONResponse(
            content={"error": "Server error", "details": str(e)},
            status_code=500
        )

# ✅ Convert Markdown to HTML for frontend display
def markdown_to_html(text: str) -> str:
    text = text.replace("\n", "<br>")  # Convert newlines to `<br>`
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)  # Convert bold text
    text = re.sub(r"\[([^\]]+)\]\((https?:\/\/[^\)]+)\)", r'<a href="\2" target="_blank">\1</a>', text)  # Convert links
    return text

# ✅ History API Endpoint (Fetch Past Summaries)
@router.get("/history/{topic}")
async def get_history(topic: str):
    print(f"📜 Fetching history for topic: {topic}")
    
    try:
        history_data = fetch_history_from_db(topic)  # ✅ Fetch summaries from DB
        print(f"📡 Querying Supabase for topic history: {topic}")

        # ✅ Format response
        formatted_history = []
        for entry in history_data:
            formatted_entry = {
                "id": entry["id"],  # ✅ Include UUID for tracking
                "date": datetime.strptime(entry["created_at"], "%Y-%m-%dT%H:%M:%S.%f").strftime("%b %d, %Y, %I:%M %p"),
                "summary": markdown_to_html(entry["summary"]),
            }
            formatted_history.append(formatted_entry)

        return JSONResponse(content={"topic": topic, "history": formatted_history})

    except Exception as e:
        print(f"❌ ERROR fetching history: {e}")
        return JSONResponse(
            content={"error": "Server error", "details": str(e)},
            status_code=500
        )
