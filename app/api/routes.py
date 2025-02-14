import os
import re
import logging
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

logger = logging.getLogger(__name__)
router = APIRouter()

# ✅ Helper to convert Markdown to HTML
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
    expected_token = os.getenv("CRON_SECRET_TOKEN")

    # 🔍 Debugging: Log received vs expected tokens
    logger.info(f"🔍 Received X-CRON-TOKEN: {x_cron_token}")
    logger.info(f"🔍 Expected CRON_SECRET_TOKEN: {expected_token}")

    # Ensure token comparison is correct
    if not expected_token:
        logger.error("❌ CRON_SECRET_TOKEN is missing from environment variables!")
        return JSONResponse(status_code=500, content={"error": "Server error: Missing secret token"})

    if x_cron_token.strip() != expected_token.strip():  # Strip spaces to avoid mismatch
        logger.warning("⚠️ Unauthorized access attempt to /cron_update")
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})

    try:
        logger.info("✅ Authorized cron request - Starting update")
        TRACKED_TOPICS = ["almaty", "tblisi", "deFi"]
        results = []
        
        for topic in TRACKED_TOPICS:
            logger.info(f"📌 Generating new summary for topic: {topic}")
            summary_text = get_summary_from_agents(topic)

            if not summary_text:
                logger.error(f"❌ Failed to generate summary for topic: {topic}")
                results.append({"topic": topic, "updated": False, "error": "Failed to generate summary"})
                continue

            success = insert_summary_to_db(topic, summary_text)
            results.append({"topic": topic, "updated": success})

            if success:
                logger.info(f"✅ Successfully updated summary for: {topic}")
            else:
                logger.error(f"❌ Failed to insert summary into DB for: {topic}")

        logger.info(f"✅ Cron update completed for topics: {TRACKED_TOPICS}")
        return {"updated_topics": results}

    except Exception as e:
        logger.exception("❌ Error in /cron_update endpoint")
        return JSONResponse(status_code=500, content={"error": str(e)})

@router.get("/search")
def search_summary(topic: str = Query(...)):
    """
    Checks if a summary for the topic exists and is less than 6 hours old.
    If so, returns that summary; otherwise, generates a new summary, stores it, and returns it.
    """
    try:
        logger.info("Received /search request for topic: %s", topic)
        insert_search_log(topic)

        existing = fetch_summary_from_db(topic)
        if existing:
            created_at = datetime.fromisoformat(existing["created_at"])
            if (datetime.utcnow() - created_at).total_seconds() / 3600.0 < 6:
                return {
                    "topic": topic,
                    "summary": markdown_to_html(existing["summary"]),
                    "created_at": existing["created_at"]
                }

        summary_text = get_summary_from_agents(topic)
        success = insert_summary_to_db(topic, summary_text)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save summary.")

        return {
            "topic": topic,
            "summary": markdown_to_html(summary_text),
            "created_at": None
        }
    except Exception as e:
        logger.exception("Error in /search endpoint for topic: %s", topic)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/summary/{topic}")
def get_summary_only(topic: str):
    try:
        existing = fetch_summary_from_db(topic)
        if not existing:
            raise HTTPException(status_code=404, detail="No summary found for this topic.")
        return {
            "topic": topic,
            "summary": markdown_to_html(existing["summary"]),
            "created_at": existing["created_at"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{topic}")
async def get_history(topic: str):
    try:
        history_data = fetch_history_from_db(topic)
        if not history_data:
            return {"topic": topic, "history": []}
        return {"topic": topic, "history": [
            {"id": entry.get("id", "unknown-id"), "date": entry.get("created_at", "unknown-date"),
             "summary": markdown_to_html(entry.get("summary", ""))}
            for entry in history_data]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
