# app/api/routes.py

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
import os
import re
from datetime import datetime, timedelta

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

@router.get("/check")
def check_summary(topic: str = Query(...)):
    """
    Checks if a summary for 'topic' exists in the DB.
    Returns a minimal JSON with 'found' + summary if found.
    """
    existing = fetch_summary_from_db(topic)
    if existing:
        return {
            "topic": topic,
            "found": True,
            "summary": existing["summary"],
            "created_at": existing["created_at"],
        }
    else:
        return {
            "topic": topic,
            "found": False,
            "summary": None,
            "created_at": None,
        }
@router.post("/cron_update")
def cron_auto_update():
    # List of topics to auto-update for MVP.
    TRACKED_TOPICS = ["almaty", "tblisi", "deFi"]
    results = []

    for topic in TRACKED_TOPICS:
        summary_text = get_summary_from_agents(topic)
        success = insert_summary_to_db(topic, summary_text)
        results.append({"topic": topic, "updated": success})
    
    return {"updated_topics": results}

@router.get("/search")
def search_summary(topic: str = Query(...)):
    """
    Checks if a summary for the topic exists and is less than 6 hours old.
    If so, returns that summary. Otherwise, generates a new summary, stores it,
    and returns it.
    """
    existing = fetch_summary_from_db(topic)
    if existing:
        # Parse the created_at timestamp from the DB (assumed to be in ISO format)
        created_at_str = existing["created_at"]
        created_at = datetime.fromisoformat(created_at_str)
        now = datetime.utcnow()

        # Calculate the time difference in hours
        hours_diff = (now - created_at).total_seconds() / 3600.0

        if hours_diff < 6:
            # If the existing summary is less than 6 hours old, return it
            html_summary = markdown_to_html(existing["summary"])
            return {
                "topic": topic,
                "summary": html_summary,
                "created_at": existing["created_at"]
            }
        # Otherwise, fall through to generate a new summary

    # Either no summary exists or it is older than 6 hours, so generate a new one
    summary_text = get_summary_from_agents(topic)
    success = insert_summary_to_db(topic, summary_text)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save summary.")

    # Convert new summary from Markdown to HTML
    html_summary = markdown_to_html(summary_text)
    return {
        "topic": topic,
        "summary": html_summary,
        "created_at": None  # Optionally, you could fetch the new created_at from DB
    }

# ✅ GET /summary/{topic}
@router.get("/summary/{topic}")
def get_summary_only(topic: str):
    existing = fetch_summary_from_db(topic)
    if not existing:
        raise HTTPException(status_code=404, detail="No summary found for this topic.")
    
    html_summary = markdown_to_html(existing["summary"])
    return {
        "topic": topic,
        "summary": html_summary,
        "created_at": existing["created_at"]
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

