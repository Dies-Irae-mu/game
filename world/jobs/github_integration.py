import requests
from django.conf import settings
from evennia.utils import logger

GITHUB_TOKEN = getattr(settings, "GITHUB_TOKEN", None)
GITHUB_REPOSITORY = getattr(settings, "GITHUB_REPOSITORY", None)
GITHUB_BASE_URL = getattr(settings, "GITHUB_BASE_URL", "https://api.github.com")


def _headers():
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"
    return headers


def create_issue(title: str, body: str):
    """Create a new GitHub issue. Returns the issue number or None."""
    if not GITHUB_REPOSITORY:
        logger.log_warn("GITHUB_REPOSITORY not configured; skipping issue creation")
        return None
    url = f"{GITHUB_BASE_URL}/repos/{GITHUB_REPOSITORY}/issues"
    try:
        resp = requests.post(
            url, json={"title": title, "body": body}, headers=_headers()
        )
        if resp.status_code == 201:
            num = resp.json().get("number")
            logger.log_info(f"Created GitHub issue #{num}")
            return num
        logger.log_err(f"Failed to create GitHub issue: {resp.status_code} {resp.text}")
    except Exception as err:
        logger.log_err(f"Error creating GitHub issue: {err}")
    return None


def add_comment(issue_number: int, body: str):
    """Add a comment to an existing GitHub issue."""
    if not (GITHUB_REPOSITORY and issue_number):
        return
    url = f"{GITHUB_BASE_URL}/repos/{GITHUB_REPOSITORY}/issues/{issue_number}/comments"
    try:
        resp = requests.post(url, json={"body": body}, headers=_headers())
        if resp.status_code not in (200, 201):
            logger.log_err(
                f"Failed to add comment to GitHub issue: {resp.status_code} {resp.text}"
            )
    except Exception as err:
        logger.log_err(f"Error adding GitHub comment: {err}")
