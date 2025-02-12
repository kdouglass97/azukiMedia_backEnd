# app/api/routes.py

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import os
import re
from datetime import datetime

# ✅ Import your DB + AI helpers
from app.database.supabase_client import insert_summary_to_db, fetch_history_from_db, fetch_summary_from_db
from app.crewai.agents import get_summary_from_agents

router = APIRouter()

# ✅ Helper to convert Markdown to HTML
def markdown_to_html(text: str) -> str:
    """Converts markdown-style text to HTML"""
    text = text.replace("\n", "<br>")  # Convert newlines to <br>
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)  # Bold text
    text = re.sub(r"\[([^\]]+)\]\((https?:\/\/[^\)]+)\)", r'<a href="\2" target="_blank">\1</a>', text)  # Links
    return text

# ✅ GET /summary/{topic}
@router.get("/summary/{topic}")
async def get_summary(topic: str):
    """Fetch summary from DB or generate a new one if missing."""
    existing = fetch_summary_from_db(topic)
    if existing:
        # existing is {"summary": "...", "created_at": "..."}
        return {
            "topic": topic,
            "summary": markdown_to_html(existing["summary"]),
            "created_at": existing["created_at"]
        }

    # If not found, generate a new summary
    summary_text = get_summary_from_agents(topic)
    success = insert_summary_to_db(topic, summary_text)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save summary.")

    # We just inserted a new summary; let's return that with no date (or fetch again)
    return {
        "topic": topic,
        "summary": markdown_to_html(summary_text),
        "created_at": None
    }

# ✅ GET /history/{topic}
@router.get("/history/{topic}")
async def get_history(topic: str):
    """Fetch past summaries from the database."""
    print(f"📜 Fetching history for topic: {topic}")
    try:
        history_data = fetch_history_from_db(topic)
        if not history_data:
            return {"topic": topic, "history": []}

        # Format each entry for the frontend
        formatted_history = []
        for entry in history_data:
            formatted_history.append({
                "id": entry.get("id", "unknown-id"),
                "date": entry.get("created_at", "unknown-date"),
                "summary": markdown_to_html(entry.get("summary", "")),
            })

        return {"topic": topic, "history": formatted_history}

    except Exception as e:
        print(f"❌ ERROR fetching history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
