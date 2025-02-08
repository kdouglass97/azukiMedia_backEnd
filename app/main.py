from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
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

# ✅ Local Run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)