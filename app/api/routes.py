from fastapi import APIRouter
from fastapi.responses import JSONResponse, FileResponse
import os
from app.crewai.agents import get_summary_from_agents

# ✅ Initialize Router
router = APIRouter()

# ✅ Serve Homepage (Static HTML)
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

# ✅ News Summary API Endpoint (Calls CrewAI)
@router.get("/summary/{topic}")
async def get_summary(topic: str):
    print(f"🟢 Received request for topic: {topic}")  # ✅ Log API calls

    try:
        result = get_summary_from_agents(topic)  # ✅ Calls CrewAI processing
        print(f"✅ CrewAI Result: {result}")  # ✅ Log AI results

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
