from fastapi import FastAPI

app = FastAPI()  # Ensure this line exists

@app.get("/")
def home():
    return {"message": "AI News API is running!"}
