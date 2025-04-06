from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import requests
from dotenv import load_dotenv
from typing import List, Optional
from fastapi.responses import JSONResponse

# Load environment variables from .env file
load_dotenv()

# Set up FastAPI
app = FastAPI()

# Set up templates (Jinja2)
templates = Jinja2Templates(directory="templates")

# Constants
GITHUB_API_URL = "https://api.github.com/graphql"


def get_github_token() -> str:
    """Fetch GitHub token from environment variable."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GitHub token not found. Please set the GITHUB_TOKEN env variable.")
    return token


def fetch_pinned_repos(username: str, token: str) -> Optional[List[dict]]:
    """Fetch pinned repositories using GitHub GraphQL API."""
    query = f"""
    {{
      user(login: "{username}") {{
        pinnedItems(first: 6, types: [REPOSITORY]) {{
          edges {{
            node {{
              ... on Repository {{
                name
                description
                url
                stargazerCount
                forkCount
                primaryLanguage {{
                  name
                }}
              }}
            }}
          }}
        }}
      }}
    }}
    """

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(GITHUB_API_URL, json={"query": query}, headers=headers)

    if response.status_code == 200:
        return response.json()["data"]["user"]["pinnedItems"]["edges"]
    else:
        return None


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the homepage with the GitHub username form."""
    return templates.TemplateResponse("home.html", {"request": request})


@app.post("/repos", response_class=HTMLResponse)
async def repos(request: Request, username: str = Form(...)):
    """Fetch and display pinned repos based on the provided GitHub username."""
    token = os.getenv("GITHUB_TOKEN")
    repos = fetch_pinned_repos(username, token)
    if repos is None:
        return templates.TemplateResponse("home.html", {"request": request, "error": "Failed to fetch repos or no pinned repos found."})
    return templates.TemplateResponse("repos.html", {"request": request, "repos": repos, "username": username})
  

@app.get("/api/repos/{username}")
async def api_repos(username: str):
    token = get_github_token()
    repos = fetch_pinned_repos(username, token)
    if repos is None:
        return JSONResponse(content={"error": "Failed to fetch repos."}, status_code=400)
    return {"repos": repos}



