# Jira FastMCP Server

Lightweight MCP server that exposes Jira operations for MCP‑compatible AI tools.

## Prerequisites
- Python 3.10+
- Jira Cloud/Server credentials with API token or password (Cloud recommended).

## Setup
1) Create a virtualenv and install deps:
```bash
pip install -r requirements.txt
```
2) Copy `.env.example` to `.env` and set:
```
JIRA_SITE=https://your-domain.atlassian.net
JIRA_USER=your-email@example.com
JIRA_TOKEN=your-api-token
```
3) Run the server (stdio transport by default):
```bash
fastmcp run servers/jira_mcp.py
```
   Or expose over HTTP:
```bash
fastmcp run servers/jira_mcp.py --transport http --port 8000
```

## Exposed MCP tools
- `search_issues(jql, limit=50)`
- `get_issue(issue_key, expand_rendered=True)`
- `create_issue(project_key, summary, description, issue_type='Task', assignee=None)`
- `add_comment(issue_key, comment)`
- `list_transitions(issue_key)`
- `transition_issue(issue_key, transition_name)`

All tools return JSON-ready objects for downstream AI clients.

## Notes
- Uses Atlassian's newer `/rest/api/3/search/jql` endpoint.
- `assignee` must be the accountId on Cloud. Omit to leave unassigned.
- HTTP client uses a shared connection with a 30s timeout; adjust as needed.
