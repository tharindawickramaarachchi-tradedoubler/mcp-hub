import os
import logging
from typing import Any, Dict, List, Optional
from venv import logger

import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment configuration
JIRA_SITE = os.environ["JIRA_SITE"].rstrip("/")
JIRA_USER = os.environ["JIRA_USER"]
JIRA_TOKEN = os.environ["JIRA_TOKEN"]

# Single shared HTTP client; FastMCP is single-process
session = httpx.Client(
    base_url=f"{JIRA_SITE}/rest/api/3",
    auth=(JIRA_USER, JIRA_TOKEN),
    headers={"Accept": "application/json"},
    timeout=30.0,
)

mcp = FastMCP(
    name="Tradedoubler Atlassian MCP Server",
    instructions="""
        You are an assistant for interacting with the Tradedoubler Atlassian suite, 
        including Jira. Use the provided tools to search for issues, 
        fetch issue details, create new issues, add comments, and transition issue states. 
        
        Always follow the tool specifications and return data in the expected formats.
    """,
)
logger.info("Initialized MCP server.")

def _request(method: str, path: str, **kwargs) -> Any:
    """Wrapper that raises for HTTP errors and returns JSON when present."""
    resp = session.request(method, path, **kwargs)
    resp.raise_for_status()
    return resp.json() if resp.text else None

# @mcp.tool
# def add(a: int, b: int) -> int:
#     """Adds two integer numbers together."""
#     return a + b

@mcp.tool
def search_issues(jql: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Search Jira issues using a JQL query.
    Args:
        jql: Jira Query Language string to filter issues.
        limit: Maximum number of results to return (up to 1000).
    Returns:
        List of issue dictionaries with key, summary, status, assignee, priority, and updated fields.
    """
    params = {
        "jql": jql,
        "maxResults": limit,
        "fields": "summary,status,assignee,priority,updated,created",
    }
    data = _request("GET", "/search/jql", params=params)
    return [
        {
            "key": issue["key"],
            "summary": issue["fields"]["summary"],
            "status": issue["fields"]["status"]["name"],
            "assignee": issue["fields"]["assignee"]["displayName"]
            if issue["fields"]["assignee"]
            else None,
            "priority": issue["fields"]["priority"]["name"],
            "updated": issue["fields"]["updated"],
        }
        for issue in data.get("issues", [])
    ]

@mcp.tool
def get_issue(issue_key: str, expand_rendered: bool = True) -> Dict[str, Any]:
    """Fetch a full Jira issue."""
    params = {"expand": "renderedFields"} if expand_rendered else None
    return _request("GET", f"/issue/{issue_key}", params=params)

@mcp.tool
def create_issue(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
    assignee: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a Jira issue using Atlassian doc-format description.
    assignee: accountId (Cloud) or username (Server/DC) if provided.
    """
    payload: Dict[str, Any] = {
        "fields": {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}],
                    }
                ],
            },
        }
    }

    if assignee:
        payload["fields"]["assignee"] = {"id": assignee}

    return _request("POST", "/issue", json=payload)

@mcp.tool
def add_comment(issue_key: str, comment: str) -> Dict[str, Any]:
    """Add a rich-text comment to an issue."""
    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": comment}]}],
        }
    }
    return _request("POST", f"/issue/{issue_key}/comment", json=payload)

@mcp.tool
def list_transitions(issue_key: str) -> List[str]:
    """Return available transition names for the issue."""
    data = _request("GET", f"/issue/{issue_key}/transitions")
    return [t["name"] for t in data.get("transitions", [])]

@mcp.tool
def transition_issue(issue_key: str, transition_name: str) -> str:
    """
    Move an issue to a named transition (case-insensitive).
    """
    transitions = _request("GET", f"/issue/{issue_key}/transitions")["transitions"]
    match = next(
        (t for t in transitions if t["name"].lower() == transition_name.lower()), None
    )
    if not match:
        available = [t["name"] for t in transitions]
        raise ValueError(
            f"Transition '{transition_name}' not available; options: {available}"
        )
    _request("POST", f"/issue/{issue_key}/transitions", json={"transition": {"id": match["id"]}})
    return f"Transitioned {issue_key} to {match['name']}"

def test_run():
    # Basic smoke test for tools; requires valid JIRA credentials and a test issue.
    issues = search_issues("assignee = currentUser() ORDER BY updated DESC")
    print (f"Found {len(issues)} issues in TEST project.")
    for issue in issues[:5]:
        print(f"- {issue['key']}: {issue['summary']} (Status: {issue['status']})")
    assert isinstance(issues, list)
    if issues:
        issue = get_issue(issues[0]["key"])
        assert "fields" in issue
        comment = add_comment(issues[0]["key"], "Test comment from MCP.")
        assert "id" in comment


if __name__ == "__main__":
    import sys
    if "--test" in sys.argv:
        test_run()
    else:
        logger.info("Starting MCP server...")
        #mcp.run() # STDIO (Standard Input/Output) transport
        mcp.run(transport="http", host="0.0.0.0", port=8005) # HTTP transport




