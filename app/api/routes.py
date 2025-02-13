import os
import re
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Header
from fastapi.responses import JSONResponse
from app.database.supabase_client import (
    insert_summary_to_db,
    fetch_history_from_db,
    fetch_summary_from_db,
    insert_search_log
)
from app.crewai.agents import get_summary_from_agents
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Helper to convert Markdown to HTML
def markdown_to_html(text: str) -> str:
    """Converts markdown-style text to HTML."""
    text = text.replace("\n", "<br>")
    text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?:\/\/[^\)]+)\)", r'<a href="\2" target="_blank">\1</a>', text)
    return text

@router.get("/check")
def check_summary(topic: str = Query(...)):
    """
    Checks if a summary for the topic exists in the DB.
    Returns a minimal JSON with 'found' and summary details if found.
    """
    try:
        logger.info("Received /check request for topic: %s", topic)
        existing = fetch_summary_from_db(topic)
        if existing:
            logger.info("Summary found for topic: %s", topic)
            return {
                "topic": topic,
                "found": True,
                "summary": existing["summary"],
                "created_at": existing["created_at"],
            }
        else:
            logger.info("No summary found for topic: %s", topic)
            return {
                "topic": topic,
                "found": False,
                "summary": None,
                "created_at": None,
            }
    except Exception as e:
        logger.exception("Error in /check endpoint for topic: %s", topic)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cron_update")
def cron_auto_update(x_cron_token: str = Header(...)):
    """
    Auto-update endpoint for tracked topics.
    Requires a valid secret token in the header 'X-CRON-TOKEN' for authorization.
    """
    if x_cron_token != os.getenv("CRON_SECRET_TOKEN"):
        logger.warning("Unauthorized access attempt to /cron_update")
        raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        logger.info("Starting cron update for tracked topics")
        TRACKED_TOPICS = ["almaty", "tblisi", "deFi"]
        results = []
        for topic in TRACKED_TOPICS:
            logger.info("Generating new summary for topic: %s", topic)
            summary_text = get_summary_from_agents(topic)
            success = insert_summary_to_db(topic, summary_text)
            results.append({"topic": topic, "updated": success})
        logger.info("Cron update completed for topics: %s", TRACKED_TOPICS)
        return {"updated_topics": results}
    except Exception as e:
        logger.exception("Error in /cron_update endpoint")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
def search_summary(topic: str = Query(...)):
    """
    Checks if a summary for the topic exists and is less than 6 hours old.
    If so, returns that summary; otherwise, generates a new summary, stores it, and returns it.
    """
    try:
        logger.info("Received /search request for topic: %s", topic)
        # Log the search query for analytics
        try:
            insert_search_log(topic)
            logger.info("Search query logged: %s", topic)
        except Exception as log_error:
            logger.exception("Failed to log search query: %s", topic)
        
        existing = fetch_summary_from_db(topic)
        if existing:
            created_at_str = existing["created_at"]
            created_at = datetime.fromisoformat(created_at_str)
            now = datetime.utcnow()
            hours_diff = (now - created_at).total_seconds() / 3600.0

            if hours_diff < 6:
                logger.info("Returning cached summary for topic: %s", topic)
                html_summary = markdown_to_html(existing["summary"])
                return {
                    "topic": topic,
                    "summary": html_summary,
                    "created_at": existing["created_at"]
                }
            else:
                logger.info("Cached summary for topic '%s' is older than 6 hours; generating new one", topic)
        else:
            logger.info("No existing summary for topic: %s; generating new one", topic)

        # Generate a new summary since none exists or it's expired
        summary_text = get_summary_from_agents(topic)
        success = insert_summary_to_db(topic, summary_text)
        if not success:
            logger.error("Failed to save new summary for topic: %s", topic)
            raise HTTPException(status_code=500, detail="Failed to save summary.")

        html_summary = markdown_to_html(summary_text)
        logger.info("New summary generated for topic: %s", topic)
        return {
            "topic": topic,
            "summary": html_summary,
            "created_at": None  # Optionally, fetch the new created_at from DB
        }
    except Exception as e:
        logger.exception("Error in /search endpoint for topic: %s", topic)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary/{topic}")
def get_summary_only(topic: str):
    try:
        logger.info("Received /summary request for topic: %s", topic)
        existing = fetch_summary_from_db(topic)
        if not existing:
            logger.warning("No summary found for topic: %s", topic)
            raise HTTPException(status_code=404, detail="No summary found for this topic.")
        html_summary = markdown_to_html(existing["summary"])
        logger.info("Returning summary for topic: %s", topic)
        return {
            "topic": topic,
            "summary": html_summary,
            "created_at": existing["created_at"]
        }
    except Exception as e:
        logger.exception("Error in /summary endpoint for topic: %s", topic)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{topic}")
async def get_history(topic: str):
    """Fetch past summaries from the database."""
    try:
        logger.info("Fetching history for topic: %s", topic)
        history_data = fetch_history_from_db(topic)
        if not history_data:
            logger.info("No history data found for topic: %s", topic)
            return {"topic": topic, "history": []}

        formatted_history = []
        for entry in history_data:
            formatted_history.append({
                "id": entry.get("id", "unknown-id"),
                "date": entry.get("created_at", "unknown-date"),
                "summary": markdown_to_html(entry.get("summary", "")),
            })
        logger.info("Returning history for topic: %s", topic)
        return {"topic": topic, "history": formatted_history}
    except Exception as e:
        logger.exception("Error fetching history for topic: %s", topic)
        raise HTTPException(status_code=500, detail=str(e))
