from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

# ✅ Load Environment Variables
load_dotenv()

# ✅ Initialize FastAPI App
app = FastAPI()

# ✅ Mount Static Directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ✅ CORS Middleware
#    Allows both your production site and local dev origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://azukimedia.up.railway.app",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Import & Include Routes (points to routes.py)
from app.api.routes import router as api_router
app.include_router(api_router)

# ✅ Local Run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
