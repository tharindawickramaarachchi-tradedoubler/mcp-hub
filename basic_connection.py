import os
import sys
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

print("=" * 60)
print("JIRA Connection Test")
print("=" * 60)

# Check environment variables
try:
    JIRA_SITE = os.environ["JIRA_SITE"].rstrip("/")
    JIRA_USER = os.environ["JIRA_USER"]
    JIRA_TOKEN = os.environ["JIRA_TOKEN"]
    print(f"✓ Environment variables loaded")
    print(f"  Site: {JIRA_SITE}")
    print(f"  User: {JIRA_USER}")
    print(f"  Token: {'*' * len(JIRA_TOKEN[:4]) + JIRA_TOKEN[:4] + '...'}")
except KeyError as e:
    print(f"✗ Missing environment variable: {e}")
    print("\nPlease set the following environment variables:")
    print("  - JIRA_SITE")
    print("  - JIRA_USER")
    print("  - JIRA_TOKEN")
    sys.exit(1)

print("\n" + "-" * 60)
print("Testing connection...")
print("-" * 60)

# Create HTTP client
client = httpx.Client(
    base_url=f"{JIRA_SITE}/rest/api/3",
    auth=(JIRA_USER, JIRA_TOKEN),
    headers={"Accept": "application/json"},
    timeout=30.0,
)

try:
    # Test 1: Get current user info
    print("\n1. Testing authentication (GET /myself)...")
    response = client.get("/myself")
    response.raise_for_status()
    user_data = response.json()
    print(f"   ✓ Authenticated as: {user_data.get('displayName', 'Unknown')}")
    print(f"   Account ID: {user_data.get('accountId', 'N/A')}")
    print(f"   Email: {user_data.get('emailAddress', 'N/A')}")
    
    # Test 2: List accessible projects
    print("\n2. Fetching accessible projects...")
    response = client.get("/project")
    response.raise_for_status()
    projects = response.json()
    print(f"   ✓ Found {len(projects)} accessible project(s):")
    for proj in projects[:5]:  # Show first 5 projects
        print(f"     - {proj['key']}: {proj['name']}")
    if len(projects) > 5:
        print(f"     ... and {len(projects) - 5} more")
    
    # Test 3: Simple JQL search
    print("\n3. Testing JQL search (recent issues)...")
    response = client.get("/search/jql", params={
        "jql": "updated >= -30d order by updated DESC",
        "maxResults": 5,
        "fields": "summary,status"
    })
    response.raise_for_status()
    search_data = response.json()
    issue_count = search_data.get('total', 0)
    print(f"   ✓ Found {issue_count} total issue(s)")
    if search_data.get('issues'):
        print(f"   Recent issues:")
        for issue in search_data['issues'][:3]:
            print(f"     - {issue['key']}: {issue['fields']['summary'][:50]}...")
    
    print("\n" + "=" * 60)
    print("✓ All connection tests passed!")
    print("=" * 60)
    print("  fastmcp run servers/jira_mcp.py")
    
except httpx.HTTPStatusError as e:
    print(f"\n✗ HTTP Error {e.response.status_code}: {e.response.text}")
    if e.response.status_code == 401:
        print("\n  Authentication failed. Please check:")
        print("  - JIRA_USER is correct (usually your email)")
        print("  - JIRA_TOKEN is valid (generate at: https://id.atlassian.com/manage-profile/security/api-tokens)")
    elif e.response.status_code == 403:
        print("\n  Access denied. Your account may lack permissions.")
    sys.exit(1)
except httpx.ConnectError as e:
    print(f"\n✗ Connection Error: {e}")
    print(f"\n  Could not connect to {JIRA_SITE}")
    print("  Please check your JIRA_SITE URL")
    sys.exit(1)
except Exception as e:
    print(f"\n✗ Unexpected error: {e}")
    sys.exit(1)
finally:
    client.close()