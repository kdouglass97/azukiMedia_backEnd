from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import os

# ✅ Load Environment Variables
load_dotenv()

# ✅ Initialize FastAPI App
app = FastAPI()

# ✅ Mount Static Directory (Ensures /static/style.css Works)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ✅ CORS Middleware (Adjust in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://azukimedia.up.railway.app"],  # ✅ Allow only your frontend
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

# ✅ Import & Include Routes from routes.py
from app.api.routes import router as api_router
app.include_router(api_router)

# ✅ Run Locally with `uvicorn app.main:app --reload`
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)