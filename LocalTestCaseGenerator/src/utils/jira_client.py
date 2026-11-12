"""Jira REST API v3 Client for ticket extraction and issue fetching."""

import re
from typing import Any, Dict, Optional, Tuple

import requests
from requests.auth import HTTPBasicAuth

# Regex pattern to match standard Jira Ticket IDs (e.g., PROJ-101, KAN-42, QA_2-9)
JIRA_ID_REGEX = re.compile(r"\b([A-Za-z][A-Za-z0-9_]+-\d+)\b")


def extract_jira_id(user_prompt: str) -> Optional[str]:
    """Extract the first Jira Ticket ID from a natural language prompt."""
    if not user_prompt:
        return None
    match = JIRA_ID_REGEX.search(user_prompt)
    return match.group(1).upper() if match else None


def _parse_adf_node(node: Any) -> str:
    """Recursively convert Atlassian Document Format (ADF) JSON into plain text."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "".join(_parse_adf_node(item) for item in node)
    if not isinstance(node, dict):
        return str(node)

    node_type = node.get("type", "")
    text = node.get("text", "")
    content = node.get("content", [])
    children_text = "".join(_parse_adf_node(child) for child in content)

    if node_type == "text":
        return text
    if node_type in ("paragraph", "heading"):
        return f"{children_text}\n\n"
    if node_type == "listItem":
        return f"- {children_text.strip()}\n"
    if node_type in ("bulletList", "orderedList"):
        return f"{children_text}\n"
    if node_type == "hardBreak":
        return "\n"
    if node_type == "codeBlock":
        return f"```\n{children_text}\n```\n"

    return text + children_text


def _extract_acceptance_criteria(fields: Dict[str, Any], names_map: Dict[str, str]) -> str:
    """Search custom fields or description for Acceptance Criteria."""
    ac_parts = []
    for field_key, field_label in names_map.items():
        if "acceptance" in field_label.lower() or "criteria" in field_label.lower():
            raw_val = fields.get(field_key)
            if raw_val:
                parsed = _parse_adf_node(raw_val).strip()
                if parsed:
                    ac_parts.append(parsed)
    return "\n".join(ac_parts).strip()


def test_jira_connection(base_url: str, email: str, api_token: str) -> Tuple[bool, str]:
    """Verify Jira credentials against GET /rest/api/3/myself."""
    clean_url = base_url.strip().rstrip("/")
    if not clean_url or not email or not api_token:
        return False, "Missing Jira Base URL, Email, or API Token."

    endpoint = f"{clean_url}/rest/api/3/myself"
    try:
        response = requests.get(
            endpoint,
            auth=HTTPBasicAuth(email.strip(), api_token.strip()),
            headers={"Accept": "application/json"},
            timeout=15,
        )
        if response.status_code == 200:
            data = response.json()
            display_name = data.get("displayName", email)
            return True, f"Connected successfully as {display_name} ({email})."
        if response.status_code in (401, 403):
            return False, f"Authentication failed ({response.status_code}). Check your Jira Email and API Token."
        return False, f"Jira returned HTTP {response.status_code}: {response.text[:200]}"
    except requests.RequestException as exc:
        return False, f"Network error connecting to Jira: {exc}"


def fetch_jira_issue(
    issue_key: str,
    base_url: str,
    email: str,
    api_token: str,
) -> Dict[str, Any]:
    """Fetch Jira ticket details via GET /rest/api/3/issue/{issue_key}.

    Returns a dictionary containing:
      - success (bool)
      - error (str, if any)
      - status_code (int)
      - data (dict with key, summary, issue_type, status, priority, description, acceptance_criteria, comments)
    """
    clean_url = base_url.strip().rstrip("/")
    clean_key = issue_key.strip().upper()
    endpoint = f"{clean_url}/rest/api/3/issue/{clean_key}?expand=names"

    try:
        response = requests.get(
            endpoint,
            auth=HTTPBasicAuth(email.strip(), api_token.strip()),
            headers={"Accept": "application/json"},
            timeout=20,
        )
    except requests.RequestException as exc:
        return {
            "success": False,
            "status_code": 0,
            "error": f"Failed to reach Jira server at `{clean_url}`: {exc}",
        }

    if response.status_code == 401:
        return {
            "success": False,
            "status_code": 401,
            "error": "Jira Authentication Failed (401 Unauthorized). Please verify your Jira Email and API Token in Settings.",
        }
    if response.status_code == 403:
        return {
            "success": False,
            "status_code": 403,
            "error": f"Access Denied (403 Forbidden) for ticket `{clean_key}`. Check your Jira permissions or API token.",
        }
    if response.status_code == 404:
        return {
            "success": False,
            "status_code": 404,
            "error": f"Jira Ticket `{clean_key}` was not found (404). Please verify the Ticket ID and Jira Base URL.",
        }
    if response.status_code != 200:
        return {
            "success": False,
            "status_code": response.status_code,
            "error": f"Unexpected Jira API response (HTTP {response.status_code}): {response.text[:300]}",
        }

    payload = response.json()
    fields = payload.get("fields", {})
    names_map = payload.get("names", {})

    summary = fields.get("summary") or "Not specified"
    issue_type = (fields.get("issuetype") or {}).get("name") or "Not specified"
    status = (fields.get("status") or {}).get("name") or "Not specified"
    priority = (fields.get("priority") or {}).get("name") or "Not specified"

    raw_description = fields.get("description")
    description = _parse_adf_node(raw_description).strip() if raw_description else "Not specified"

    acceptance_criteria = _extract_acceptance_criteria(fields, names_map)
    if not acceptance_criteria:
        # Check if Acceptance Criteria is embedded inside the description text
        if "acceptance criteria" in description.lower():
            acceptance_criteria = "Included in Ticket Description"
        else:
            acceptance_criteria = "Not explicitly separated (refer to Description)"

    # Also extract recent comments if useful context exists
    comments_list = []
    comment_block = fields.get("comment", {})
    for c in (comment_block.get("comments") or [])[-5:]:
        body_text = _parse_adf_node(c.get("body")).strip()
        if body_text:
            author = (c.get("author") or {}).get("displayName", "User")
            comments_list.append(f"{author}: {body_text}")

    return {
        "success": True,
        "status_code": 200,
        "data": {
            "key": payload.get("key", clean_key),
            "summary": summary,
            "issue_type": issue_type,
            "status": status,
            "priority": priority,
            "description": description,
            "acceptance_criteria": acceptance_criteria,
            "comments": "\n".join(comments_list) if comments_list else "None",
            "url": f"{clean_url}/browse/{clean_key}",
        },
    }
