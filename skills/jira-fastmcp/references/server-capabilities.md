# Jira FastMCP Reference

## Setup

Use this repository:

- Install dependencies with `pip install -r requirements.txt`.
- Set `JIRA_SITE`, `JIRA_USER`, and `JIRA_TOKEN` in `.env`.
- Run `fastmcp run servers/jira_mcp.py` for stdio transport.
- Run `fastmcp run servers/jira_mcp.py --transport http --port 8000` for HTTP transport.

Use [basic_connection.py](/c:/codebase/wicky/atlasian-mcp/basic_connection.py) to verify Jira authentication and basic API access before debugging MCP behavior.

## Exposed Tools

### `search_issues(jql, limit=50)`

Use for JQL-based discovery and triage.

Returns a simplified list of issue objects with:

- `key`
- `summary`
- `status`
- `assignee`
- `priority`
- `updated`

Implementation detail:
The server sends `fields=summary,status,assignee,priority,updated,created` to Jira, but the tool currently returns only the simplified subset above.

### `get_issue(issue_key, expand_rendered=True)`

Use for full issue retrieval.

- `issue_key`: Jira key such as `PROJ-123`
- `expand_rendered`: when true, request `renderedFields`

Returns the Jira issue payload directly from Jira.

### `create_issue(project_key, summary, description, issue_type='Task', assignee=None)`

Use for basic issue creation.

- `project_key`: Jira project key
- `summary`: issue title
- `description`: plain text converted to a single ADF paragraph
- `issue_type`: defaults to `Task`
- `assignee`: optional identifier; code currently sends it as `{"id": assignee}`

Cloud caveat:
The repository README states that Jira Cloud requires `accountId`.

### `add_comment(issue_key, comment)`

Use for basic comments.

The comment is sent as a single Atlassian Document Format paragraph.

### `list_transitions(issue_key)`

Use before attempting a workflow change.

Returns a list of transition names only, not IDs.

### `transition_issue(issue_key, transition_name)`

Use to move an issue by transition name.

Behavior:

- Fetch transitions from Jira
- Match the provided name case-insensitively
- Post the selected transition ID back to Jira
- Raise an error listing available options if no match exists

## Operational Caveats

- The server uses Jira REST API v3 under `JIRA_SITE/rest/api/3`.
- Authentication is basic auth with `JIRA_USER` and `JIRA_TOKEN`.
- The shared `httpx.Client` timeout is 30 seconds.
- `create_issue` and `add_comment` support only simple single-paragraph text today.
- The server does not expose attachments, worklogs, board/sprint operations, or custom field helpers.

## Implementation Files

- Server: [servers/jira_mcp.py](/c:/codebase/wicky/atlasian-mcp/servers/jira_mcp.py)
- Connectivity check: [basic_connection.py](/c:/codebase/wicky/atlasian-mcp/basic_connection.py)
- Repo overview: [README.md](/c:/codebase/wicky/atlasian-mcp/README.md)
