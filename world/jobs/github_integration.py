import requests
from django.conf import settings
from evennia.utils import logger
import sys
import traceback

print("Loading github_integration.py", file=sys.stderr)
print(f"dir(settings): {[attr for attr in dir(settings) if 'GITHUB' in attr]}",
      file=sys.stderr)

# Try to access the settings directly
try:
    GITHUB_TOKEN = settings.GITHUB_TOKEN
    print(f"Direct access - GITHUB_TOKEN: {GITHUB_TOKEN}", file=sys.stderr)
except AttributeError:
    GITHUB_TOKEN = None
    print("AttributeError when accessing settings.GITHUB_TOKEN", file=sys.stderr)

try:
    GITHUB_REPOSITORY = settings.GITHUB_REPOSITORY
    print(f"Direct access - GITHUB_REPOSITORY: {GITHUB_REPOSITORY}",
          file=sys.stderr)
except AttributeError:
    GITHUB_REPOSITORY = None
    print("AttributeError when accessing settings.GITHUB_REPOSITORY",
          file=sys.stderr)

GITHUB_BASE_URL = getattr(settings, "GITHUB_BASE_URL", "https://api.github.com")

print(f"GITHUB_TOKEN: {GITHUB_TOKEN}", file=sys.stderr)
print(f"GITHUB_REPOSITORY: {GITHUB_REPOSITORY}", file=sys.stderr)
print(f"GITHUB_BASE_URL: {GITHUB_BASE_URL}", file=sys.stderr)

# Log configuration at module load time
logger.log_info(f"GitHub Integration - Token exists: {bool(GITHUB_TOKEN)}")
logger.log_info(
    f"GitHub Integration - Repository configured: {bool(GITHUB_REPOSITORY)}")
logger.log_info(f"GitHub Integration - Base URL: {GITHUB_BASE_URL}")


def _headers():
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    else:
        logger.log_warn(
            "GitHub token is not configured, requests will be unauthenticated")
    return headers


def create_issue(title: str, body: str):
    """Create a new GitHub issue. Returns the issue number or None."""

    logger.log_info(f"Attempting to create GitHub issue: {title}")
    logger.log_info(f"GITHUB_REPOSITORY: {GITHUB_REPOSITORY}")
    logger.log_info(f"GITHUB_BASE_URL: {GITHUB_BASE_URL}")
    logger.log_info(f"GITHUB_TOKEN: {'configured' if GITHUB_TOKEN else 'not configured'}")
    
    if not GITHUB_REPOSITORY:
        logger.log_warn("GITHUB_REPOSITORY not configured; skipping issue creation")
        return None
        
    url = f"{GITHUB_BASE_URL}/repos/{GITHUB_REPOSITORY}/issues"
    logger.log_info(f"Making request to: {url}")
    
    try:
        headers = _headers()
        logger.log_info(f"Using headers: {headers}")
        
        resp = requests.post(
            url, json={"title": title, "body": body}, headers=headers
        )
        logger.log_info(f"GitHub API response status: {resp.status_code}")
        logger.log_info(f"GitHub API response body: {resp.text[:500]}") # Log first 500 chars of response
        
        if resp.status_code == 201:
            num = resp.json().get("number")
            logger.log_info(f"Created GitHub issue #{num}")
            return num
        logger.log_err(f"Failed to create GitHub issue: {resp.status_code} {resp.text}")
    except Exception as err:
        logger.log_err(f"Error creating GitHub issue: {err}")
        logger.log_err(f"Error traceback: {traceback.format_exc()}")
    return None


def add_comment(issue_number: int, body: str):
    """Add a comment to an existing GitHub issue."""
    logger.log_info(f"Attempting to add comment to GitHub issue #{issue_number}")
    
    if not GITHUB_REPOSITORY:
        logger.log_warn("GITHUB_REPOSITORY not configured; skipping comment addition")
        return False
    if not issue_number:
        logger.log_warn("No issue number provided; skipping comment addition")
        return False
        
    url = f"{GITHUB_BASE_URL}/repos/{GITHUB_REPOSITORY}/issues/{issue_number}/comments"
    logger.log_info(f"Making request to: {url}")
    
    try:
        headers = _headers()
        logger.log_info(f"Using headers: {headers}")
        
        resp = requests.post(url, json={"body": body}, headers=headers)
        logger.log_info(f"GitHub API response status: {resp.status_code}")
        logger.log_info(f"GitHub API response body: {resp.text[:500]}") # Log first 500 chars of response
        
        if resp.status_code not in (200, 201):
            logger.log_err(
                f"Failed to add comment to GitHub issue: {resp.status_code} {resp.text}"
            )
            return False
        return True
    except Exception as err:
        logger.log_err(f"Error adding GitHub comment: {err}")
        logger.log_err(f"Error traceback: {traceback.format_exc()}")
    return False


def close_issue(issue_number: int):
    """Close an existing GitHub issue."""
    logger.log_info(f"Attempting to close GitHub issue #{issue_number}")
    
    if not GITHUB_REPOSITORY:
        logger.log_warn("GITHUB_REPOSITORY not configured; skipping issue closure")
        return False
    if not issue_number:
        logger.log_warn("No issue number provided; skipping issue closure")
        return False
        
    url = f"{GITHUB_BASE_URL}/repos/{GITHUB_REPOSITORY}/issues/{issue_number}"
    logger.log_info(f"Making request to: {url}")
    
    try:
        headers = _headers()
        logger.log_info(f"Using headers: {headers}")
        
        # First get the current state of the issue
        get_resp = requests.get(url, headers=headers)
        logger.log_info(f"GitHub API GET response status: {get_resp.status_code}")
        
        if get_resp.status_code != 200:
            logger.log_err(f"Failed to get GitHub issue: {get_resp.status_code} {get_resp.text}")
            return False
            
        issue_data = get_resp.json()
        current_state = issue_data.get('state')
        
        if current_state == 'closed':
            logger.log_info(f"GitHub issue #{issue_number} is already closed")
            return True
        
        # GitHub API requires a PATCH request with state=closed to close an issue
        resp = requests.patch(url, json={"state": "closed"}, headers=headers)
        logger.log_info(f"GitHub API PATCH response status: {resp.status_code}")
        logger.log_info(f"GitHub API PATCH response body: {resp.text}")
        
        if resp.status_code not in (200, 201):
            logger.log_err(
                f"Failed to close GitHub issue: {resp.status_code} {resp.text}"
            )
            return False
        else:
            logger.log_info(f"Successfully closed GitHub issue #{issue_number}")
            return True
    except Exception as err:
        logger.log_err(f"Error closing GitHub issue: {err}")
        logger.log_err(f"Error traceback: {traceback.format_exc()}")
    
    return False
