from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool
import os
from dotenv import load_dotenv

# ✅ Load API Keys
load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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

# ✅ Function to Run CrewAI Process
def get_summary_from_agents(topic: str) -> str:
    crew = Crew(
        agents=[news_scraper, content_analyzer, tweet_writer],
        tasks=[scrape_task, analyze_task, write_tweet_task],
        process=Process.sequential,
    )

    result = crew.kickoff(inputs={"topic": topic})
    return str(result)  # ✅ Ensure output is JSON-serializable
