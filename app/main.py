from fastapi import FastAPI

app = FastAPI()  # Ensure FastAPI instance exists

@app.get("/")
def home():
    return {"message": "AI News API is running!"}

@app.get("/summary/{topic}")
def get_summary(topic: str):
    return {"topic": topic, "summary": f"Summary for {topic}: Important news in the last 6 hours."}