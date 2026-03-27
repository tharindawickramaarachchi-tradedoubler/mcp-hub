import os
import logging
from typing import Any, Dict, List, Optional
from venv import logger

import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables from .env file
load_dotenv()

# Environment configuration
CONFLUENCE_SITE = os.environ.get("CONFLUENCE_SITE", os.environ["JIRA_SITE"]).rstrip("/")
CONFLUENCE_USER = os.environ.get("CONFLUENCE_USER", os.environ["JIRA_USER"])
CONFLUENCE_TOKEN = os.environ.get("CONFLUENCE_TOKEN", os.environ["JIRA_TOKEN"])

session = httpx.Client(
    base_url=f"{CONFLUENCE_SITE}/wiki/rest/api",
    auth=(CONFLUENCE_USER, CONFLUENCE_TOKEN),
    headers={"Accept": "application/json"},
    timeout=30.0,
)

mcp = FastMCP(
    name="Tradedoubler Atlassian Confluence MCP Server",
    instructions="""
        You are an assistant for searching and reading Atlassian Confluence documents.
        Use the provided tools to search pages, fetch content, and edit documents as needed.
        Always follow the tool specifications and return data in the expected formats.
    """,
)
logging.info("Initialized Confluence MCP server.")

def test_run():
    # Basic smoke test for tools; requires valid JIRA credentials and a test issue.
    print("Running Confluence MCP server tests...")
    # Example test: Search for pages related to "API"
    results = search_pages("API", limit=2)
    print(f"Search results: {results}")

@mcp.tool
def search_pages(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search Confluence pages by query string.
    Args:
        query: Search query for Confluence pages.
        limit: Maximum number of results to return.
    Returns:
        List of page dictionaries with id, title, and url.
    """
    params = {
        "cql": f'text ~ "{query}"',
        "limit": limit,
    }
    resp = session.get("/content/search", params=params)
    resp.raise_for_status()
    data = resp.json()
    return [
        {
            "id": page["id"],
            "title": page["title"],
            "url": f'{CONFLUENCE_SITE}/wiki{page["_links"]["webui"]}'
        }
        for page in data.get("results", [])
    ]

@mcp.tool
def get_page(page_id: str) -> Dict[str, Any]:
    """Fetch a Confluence page's content by ID."""
    resp = session.get(f"/content/{page_id}", params={"expand": "body.storage"})
    resp.raise_for_status()
    data = resp.json()
    return {
        "id": data["id"],
        "title": data["title"],
        "content": data["body"]["storage"]["value"],
        "url": f'{CONFLUENCE_SITE}/wiki{data["_links"]["webui"]}'
    }

@mcp.tool
def upload_attachment(page_id: str, file_path: str, comment: Optional[str] = None) -> Dict[str, Any]:
    """Upload a file attachment to a Confluence page."""
    filename = os.path.basename(file_path)
    headers = {"X-Atlassian-Token": "no-check"}
    data = {"comment": comment} if comment else {}

    with open(file_path, "rb") as file_handle:
        files = {"file": (filename, file_handle)}
        resp = session.post(
            f"/content/{page_id}/child/attachment",
            headers=headers,
            data=data,
            files=files,
        )

    resp.raise_for_status()
    result = resp.json()["results"][0]
    return {
        "id": result["id"],
        "title": result["title"],
        "mediaType": result["metadata"]["mediaType"],
        "fileSize": result["extensions"]["fileSize"],
        "comment": comment,
    }

@mcp.tool
def edit_page(page_id: str, new_content: str) -> Dict[str, Any]:
    """Edit a Confluence page's content."""
    # Fetch current version
    resp = session.get(f"/content/{page_id}")
    resp.raise_for_status()
    data = resp.json()
    version = data["version"]["number"] + 1
    payload = {
        "id": page_id,
        "type": "page",
        "title": data["title"],
        "body": {
            "storage": {
                "value": new_content,
                "representation": "storage"
            }
        },
        "version": {"number": version}
    }
    resp = session.put(f"/content/{page_id}", json=payload)
    resp.raise_for_status()
    return resp.json()

def test_run():
    logging.info("Running Confluence MCP server tests...")
    # Example test: Search for pages related to "API"
    results = search_pages("API", limit=2)
    logging.info(f"Search results: {results}")
    if results:
        page_id = results[0]["id"]
        page_content = get_page(page_id)
        logging.info(f"Page content for ID {page_id}: {page_content['content'][:100]}...")

if __name__ == "__main__":
    logging.info("Starting Confluence MCP server...")
    import sys
    if "--test" in sys.argv:
        test_run()
    else:
        logger.info("Starting MCP server...")
        mcp.run(transport="http", host="0.0.0.0", port=8006) # HTTP transport
