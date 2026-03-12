---
name: jira-fastmcp
description: Operate the Jira FastMCP server in this repository for Jira issue search, issue retrieval, issue creation, commenting, and workflow transitions. Use when Codex should work through the local MCP server instead of calling Jira directly, especially for JQL searches, reading issue details, creating tasks, adding comments, or moving issues between statuses.
---

# Jira FastMCP

## Overview

Use the MCP tools exposed by this repository as the primary interface to Jira.
Prefer this skill when the task is operational Jira work rather than server development.

Read [references/server-capabilities.md](references/server-capabilities.md) when you need setup details, exact tool names, argument shapes, return fields, or Jira-specific caveats.

## Quick Start

Confirm that the MCP server is available before relying on it.
If the server is not already configured in the harness, use the repository setup in [references/server-capabilities.md](references/server-capabilities.md).

Use the tools in this order:

1. Use `search_issues` to discover issue keys from JQL.
2. Use `get_issue` when full issue details or rendered fields are needed.
3. Use `create_issue` for new work items.
4. Use `add_comment` for updates or follow-up notes.
5. Use `list_transitions` before `transition_issue`.

## Workflow

Start with the smallest operation that answers the request.
Do not fetch full issues when a search result is sufficient.

When reading:

- Use `search_issues` for lists, triage, recent updates, assignee views, or status summaries.
- Use `get_issue` only after you already know the issue key or need full fields.

When writing:

- Keep descriptions and comments concise. The current server wraps text as a single Jira paragraph in Atlassian Document Format.
- Pass `assignee` only when you have the Jira Cloud `accountId` or the correct Server/DC identifier.

When transitioning:

- Always call `list_transitions` first.
- Use one of the returned transition names exactly or case-insensitively.
- If the desired status is not offered, report the available transitions instead of guessing.

## Operating Rules

- Prefer MCP tools over direct REST calls for supported actions.
- If the requested capability is unsupported by this server, say so explicitly and either extend the server or use another approved path.
- Do not invent Jira fields or transition names. Use the data returned by the server.
- Preserve the user's Jira terminology in summaries and comments.

## Limits

This server currently supports only:

- search by JQL
- fetch issue details
- create issue
- add comment
- list transitions
- transition issue

For unsupported work such as attachments, worklogs, sprint operations, or custom field management, update [servers/jira_mcp.py](/c:/codebase/wicky/atlasian-mcp/servers/jira_mcp.py) or use a different integration.
