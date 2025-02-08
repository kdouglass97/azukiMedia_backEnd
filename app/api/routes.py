from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os
from datetime import datetime
import re
from app.database.supabase_client import insert_summary_to_db, fetch_history_from_db, fetch_summary_from_db
from app.crewai.agents import get_summary_from_agents

router = APIRouter()

@router.get("/")
async def serve_homepage():
    index_path = "app/static/index.html"
    
    if not os.path.exists(index_path):
        return JSONResponse(content={"error": "index.html not found"}, status_code=404)

    return FileResponse(index_path)

import re

# ✅ Function to Convert Markdown to HTML for Proper Styling
def markdown_to_html(text: str) -> str:
    """Converts markdown-style text to HTML"""
    text = text.replace("\n", "<br>")  # Convert newlines to `<br>`
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)  # Convert bold text
    text = re.sub(r"\[([^\]]+)\]\((https?:\/\/[^\)]+)\)", r'<a href="\2" target="_blank">\1</a>', text)  # Convert links
    return text

@router.get("/history/{topic}")
async def get_history(topic: str):
    print(f"📜 Fetching history for topic: {topic}")

    try:
        history_data = fetch_history_from_db(topic)
        print(f"📡 Supabase Raw Data: {history_data}")  # Debug log

        if not history_data:
            return JSONResponse(content={"topic": topic, "history": []})

        formatted_history = []
        for entry in history_data:
            formatted_entry = {
                "id": entry.get("id", "unknown-id"),  # ✅ Avoid crashes on missing ID
                "date": entry.get("created_at", "unknown-date"),
                "summary": markdown_to_html(entry.get("summary", "")),  # ✅ Avoid crashes on missing summary
            }
            formatted_history.append(formatted_entry)

        return JSONResponse(content={"topic": topic, "history": formatted_history})

    except Exception as e:
        print(f"❌ ERROR fetching history: {e}")  # Debug log
        return JSONResponse(content={"error": "Server error", "details": str(e)}, status_code=500)
