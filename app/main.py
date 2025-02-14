import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv

# ✅ Load Environment Variables
load_dotenv()

# --- Sentry & Logging Setup ---
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get Sentry DSN from environment (set this in your .env file)
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    sentry_logging = LoggingIntegration(
        level=logging.INFO,         # Capture info and above as breadcrumbs
        event_level=logging.ERROR   # Send errors as events
    )
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[sentry_logging],
        environment=os.getenv("ENVIRONMENT", "development"),
        release="ai-news-summary@1.0.0"
    )

# ✅ Initialize FastAPI App
def create_app():
    app = FastAPI()

    # ✅ CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 🔥 ALLOW ALL ORIGINS
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ✅ Mount Static Directory
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    # ✅ Serve index.html for `/`
    @app.get("/")
    async def serve_homepage():
        index_path = "app/static/index.html"
        if not os.path.exists(index_path):
            logger.error("index.html not found")
            return JSONResponse(content={"error": "index.html not found"}, status_code=404)
        return FileResponse(index_path)

    # ✅ Import & Include Routes *AFTER* initializing app
    from app.api.routes import router as api_router
    app.include_router(api_router)

    return app

# ✅ Create FastAPI App
app = create_app()

# ✅ Global Middleware to Add CORS Headers to Every Response
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# ✅ Local & Production Run (Uses Railway's `$PORT`)
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))  # Uses PORT from env, defaults to 8000
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
