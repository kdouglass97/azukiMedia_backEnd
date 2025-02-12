from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from app.api.routes import router as api_router
from dotenv import load_dotenv
import os

# ✅ Load Environment Variables
load_dotenv()

# ✅ Initialize FastAPI App
app = FastAPI()

# ✅ Mount Static Directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ✅ CORS Middleware (Allows both local & production requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔥 ALLOW ALL ORIGINS
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Serve index.html for `/`
@app.get("/")
async def serve_homepage():
    index_path = "app/static/index.html"
    if not os.path.exists(index_path):
        return JSONResponse(content={"error": "index.html not found"}, status_code=404)
    return FileResponse(index_path)

# ✅ Import & Include Routes
from app.api.routes import router as api_router
app.include_router(api_router)

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
    port = int(os.getenv("PORT", 8000))  # ✅ Uses PORT from env, defaults to 8000
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
