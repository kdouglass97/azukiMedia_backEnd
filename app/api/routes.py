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

@router.get("/summary/{topic}")
async def get_summary(topic: str):
    existing_summary = fetch_summary_from_db(topic)
    if existing_summary:
        return {"topic": topic, "summary": existing_summary}

    summary = get_summary_from_agents(topic)  # 🚀 AI-generated summary
    success = insert_summary_to_db(topic, summary)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save summary.")

    stored_summary = fetch_summary_from_db(topic)
    return {"topic": topic, "summary": stored_summary}

@router.get("/history/{topic}")
async def get_history(topic: str):
    try:
        history_data = fetch_history_from_db(topic)
        formatted_history = [
            {
                "id": entry["id"],
                "date": datetime.strptime(entry["created_at"], "%Y-%m-%dT%H:%M:%S.%f").strftime("%b %d, %Y, %I:%M %p"),
                "summary": entry["summary"].replace("\n", "<br>")  
            }
            for entry in history_data
        ]
        return JSONResponse(content={"topic": topic, "history": formatted_history})

    except Exception as e:
        return JSONResponse(
            content={"error": "Server error", "details": str(e)},
            status_code=500
        )
