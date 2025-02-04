from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool
from starlette.middleware.base import BaseHTTPMiddleware

# ✅ Load API Keys
load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ Initialize FastAPI App
app = FastAPI()

# ✅ Serve Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# ✅ CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://azukimedia.up.railway.app"],  # ✅ Allow only your frontend
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

# ✅ Fix Permissions-Policy Errors
class PermissionsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["Permissions-Policy"] = "interest-cohort=()"
        return response

app.add_middleware(PermissionsMiddleware)

# ✅ Manually Handle OPTIONS for /summary/{topic}
@app.options("/summary/{topic}")
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

# ✅ Serve Homepage
@app.get("/")
async def serve_homepage():
    index_path = "static/index.html"
    
    if not os.path.exists(index_path):
        print(f"❌ ERROR: index.html not found at {index_path}")
        return JSONResponse(content={"error": "index.html not found"}, status_code=404)

    return FileResponse(index_path)

# ✅ Set Up Search Tool (Serper API)
search_tool = SerperDevTool(api_key=SERPER_API_KEY)

# ✅ Define CrewAI Agents
news_scraper = Agent(
    role="News Scraper",
    goal="Find the latest news, posts, newsletters, and media about {topic} from the last 6 hours, including images if relevant.",
    backstory="You specialize in tracking the latest events and collecting relevant articles with links and images.",
    verbose=True,
    tools=[search_tool],
)

content_analyzer = Agent(
    role="Content Analyzer",
    goal="Identify the most valuable, novel, and event-driven information from the scraped content.",
    backstory="You filter through information to extract key insights that are important and interesting.",
    verbose=True,
)

tweet_writer = Agent(
    role="Tweet Writer",
    goal="Summarize the key insights on {topic} in a bullet-point tweet, ensuring all important details are included. Attach links and mention images if available.",
    backstory="You create skimmable, engaging tweet summaries that deliver maximum impact in minimal words.",
    verbose=True,
)

# ✅ Define CrewAI Tasks
scrape_task = Task(
    description="Gather the latest news, blog posts, and social media updates about {topic} from the last 6 hours. Provide at least 5-10 sources, including article links and any relevant images.",
    expected_output="A structured list of articles, each with a title, summary, link, and image URL (if available).",
    agent=news_scraper,
)

analyze_task = Task(
    description="Analyze the collected content and extract the most valuable insights. Each insight should include a direct link to the source and mention an image if applicable.",
    expected_output="A bullet-point list of insights with their direct source links and image mentions.",
    agent=content_analyzer,
)

write_tweet_task = Task(
    description="Write a concise tweet summarizing the latest updates on {topic}. Ensure each bullet point contains a key insight and its direct source link. Mention images if available.",
    expected_output="A skimmable, bullet-point tweet with direct source links and image mentions where applicable.",
    agent=tweet_writer,
)

# ✅ News Summary API Endpoint
@app.get("/summary/{topic}")
async def get_summary(topic: str):
    print(f"🟢 Received request for topic: {topic}")  # ✅ Log API calls

    try:
        crew = Crew(
            agents=[news_scraper, content_analyzer, tweet_writer],
            tasks=[scrape_task, analyze_task, write_tweet_task],
            process=Process.sequential,
        )
        result = crew.kickoff(inputs={"topic": topic})
        print(f"✅ CrewAI Result: {result}")  # ✅ Log AI results

        # 🔹 Convert CrewAI Output to JSON String
        result_json = str(result)  # ✅ Ensure it's a JSON-serializable string

        return JSONResponse(
            content={"topic": topic, "summary": result_json},
            headers={"Access-Control-Allow-Origin": "*"}
        )
    except Exception as e:
        print(f"❌ ERROR: {e}")  # ✅ Log any crashes
        return JSONResponse(
            content={"error": "Server error", "details": str(e)},
            status_code=500
        )