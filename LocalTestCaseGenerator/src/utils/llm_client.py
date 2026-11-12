"""LLM Client connecting to Antigravity / Gemini 4 Argon model with template ingestion."""

from pathlib import Path
from typing import Any, Dict, Tuple

import requests

SRC_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SRC_DIR.parent

# Candidate paths for templates
TEMPLATE_CANDIDATES = [
    SRC_DIR / "templates" / "test_case_template.md",
    PROJECT_ROOT / "templates" / "test_case_template.md",
    PROJECT_ROOT / "templates" / "test_case_generator.md",
]

HALLUCINATION_RULES_CANDIDATES = [
    PROJECT_ROOT / "templates" / "AI_Hallucinations.rules.md",
    SRC_DIR / "templates" / "AI_Hallucinations.rules.md",
]


def load_template_files() -> Tuple[bool, str, str]:
    """Load the test case template and optional anti-hallucination rules from /templates."""
    template_content = ""
    template_path_used = ""

    for path in TEMPLATE_CANDIDATES:
        if path.exists():
            template_content = path.read_text(encoding="utf-8").strip()
            template_path_used = str(path)
            break

    if not template_content:
        return (
            False,
            "Missing template file: Could not find `templates/test_case_template.md` or `templates/test_case_generator.md`.",
            "",
        )

    # Also append test_case_generator.md rules if both exist
    generator_rules_path = PROJECT_ROOT / "templates" / "test_case_generator.md"
    if generator_rules_path.exists() and str(generator_rules_path) != template_path_used:
        extra_rules = generator_rules_path.read_text(encoding="utf-8").strip()
        template_content = f"{template_content}\n\n---\n### Reference Generator Rules:\n{extra_rules}"

    hallucination_rules = ""
    for rules_path in HALLUCINATION_RULES_CANDIDATES:
        if rules_path.exists():
            hallucination_rules = rules_path.read_text(encoding="utf-8").strip()
            break

    return True, template_content, hallucination_rules


def build_generation_prompt(
    user_message: str,
    jira_data: Dict[str, Any],
    template_content: str,
    hallucination_rules: str,
) -> Tuple[str, str]:
    """Construct the system instruction and user prompt combining Jira context and templates."""
    system_instruction = (
        "You are a Senior QA Automation Architect and Full-Stack QA Engineer operating under strict "
        "verification rules. Your job is to generate a structured Test Plan Summary followed by a "
        "comprehensive Markdown table of Test Cases strictly matching the provided template and Jira ticket.\n\n"
        f"{hallucination_rules}\n\n"
        "### MANDATORY TEMPLATE STRUCTURE:\n"
        f"{template_content}"
    )

    user_prompt = f"""Generate a complete Test Plan and functional Test Cases for the following Jira ticket based on the user's request.

### USER REQUEST:
{user_message}

### JIRA TICKET DETAILS:
- **Jira Ticket ID**: {jira_data.get('key')}
- **Issue Type**: {jira_data.get('issue_type')}
- **Status**: {jira_data.get('status')}
- **Priority**: {jira_data.get('priority')}
- **Summary / Title**: {jira_data.get('summary')}
- **Description**:
{jira_data.get('description')}

- **Acceptance Criteria**:
{jira_data.get('acceptance_criteria')}

- **Recent Comments**:
{jira_data.get('comments')}

### OUTPUT INSTRUCTIONS:
1. Start with a concise **Test Plan Summary** section (Jira ID, Summary, Issue Type, Scope, and Verified Facts vs. Missing/Unknown Info).
2. Provide the **Test Cases** in the exact Markdown table format required by the template:
   `| Test ID | Description | Pre-conditions | Steps | Expected Result | Priority |`
3. Use `TC-001`, `TC-002`, etc. for Test IDs, numbered lists (`1. ... 2. ...`) inside the Steps cell, and `High`, `Medium`, or `Low` for Priority.
4. Use ONLY the provided Jira requirements. If any detail is missing, write `"Not specified"` in that cell—do NOT invent features or fields.
"""
    return system_instruction, user_prompt


def _call_gemini_rest(
    api_key: str,
    model_name: str,
    system_instruction: str,
    user_prompt: str,
    base_url: str = "",
) -> Tuple[bool, str]:
    """Invoke the Antigravity / Google Generative Language API via REST."""
    # If a custom Antigravity gateway base URL is provided, use it; otherwise use Google GenAI endpoint
    clean_base = (
        base_url.strip().rstrip("/")
        if base_url and base_url.strip()
        else "https://generativelanguage.googleapis.com/v1beta"
    )

    # Support OpenAI-compatible gateway if base_url ends with /v1 or /chat/completions
    if clean_base.endswith("/v1") or "chat/completions" in clean_base:
        endpoint = (
            clean_base
            if clean_base.endswith("chat/completions")
            else f"{clean_base}/chat/completions"
        )
        headers = {
            "Authorization": f"Bearer {api_key.strip()}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            content = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )
            if content:
                return True, content
        return False, f"HTTP {resp.status_code}: {resp.text[:300]}"

    # Standard Gemini / Antigravity generateContent endpoint
    # Try the requested model (e.g., gemini-4-argon) first, with automatic fallback if the key is scoped to standard Gemini models
    candidate_models = [model_name]
    for fallback in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-pro"]:
        if fallback not in candidate_models:
            candidate_models.append(fallback)

    last_error = ""
    for candidate in candidate_models:
        url = f"{clean_base}/models/{candidate}:generateContent"
        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": 0.2},
        }
        try:
            resp = requests.post(
                url,
                params={"key": api_key.strip()},
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=60,
            )
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts).strip()
                    if text:
                        return True, text
            last_error = f"HTTP {resp.status_code} ({candidate}): {resp.text[:250]}"
            # If 401/403 or invalid API key, no need to retry other model names
            if resp.status_code in (400, 401, 403) and "API_KEY_INVALID" in resp.text:
                break
        except requests.RequestException as exc:
            last_error = f"Request error ({candidate}): {exc}"

    return False, last_error


def _build_deterministic_fallback(jira_data: Dict[str, Any], template_note: str = "") -> str:
    """Deterministic local template-aligned generator when the external LLM endpoint is unreachable or key is local-only."""
    key = jira_data.get("key", "UNKNOWN-1")
    summary = jira_data.get("summary", "Not specified")
    issue_type = jira_data.get("issue_type", "Not specified")
    status = jira_data.get("status", "Not specified")
    priority = jira_data.get("priority", "Medium")
    description = jira_data.get("description", "Not specified")
    ac = jira_data.get("acceptance_criteria", "Not specified")

    # Normalize priority to High / Medium / Low per strict template rules
    norm_priority = "Medium"
    if any(p in priority.lower() for p in ("highest", "high", "critical", "blocker")):
        norm_priority = "High"
    elif any(p in priority.lower() for p in ("low", "lowest", "minor", "trivial")):
        norm_priority = "Low"

    # Extract requirement lines from description & acceptance criteria
    raw_lines = [
        line.strip().lstrip("-*•0123456789. ")
        for line in (f"{description}\n{ac}").splitlines()
        if line.strip()
        and not line.strip().lower().startswith(("not specified", "included in ticket", "not explicitly"))
    ]

    rows = []
    # Primary positive scenario based on ticket summary
    precond = f"Ticket {key} ({issue_type}) is deployed in the test environment." if summary != "Not specified" else "Not specified"
    desc_step = raw_lines[0] if raw_lines else f"Execute primary workflow described in '{summary}'."
    rows.append(
        f"| TC-001 | Verify core requirement: {summary} | {precond} | "
        f"1. Navigate to the target module for {key}. 2. {desc_step} 3. Verify the system response against the ticket summary. | "
        f"The feature '{summary}' functions as specified in {key}. | {norm_priority} |"
    )

    # Generate distinct test cases for each requirement line found in the description/AC
    for idx, req_line in enumerate(raw_lines[:6], start=2):
        if len(req_line) < 5:
            continue
        tc_id = f"TC-{idx:03d}"
        short_desc = req_line[:90] + ("..." if len(req_line) > 90 else "")
        rows.append(
            f"| {tc_id} | Verify requirement detail: {short_desc} | {precond} | "
            f"1. Prepare test data for '{short_desc}'. 2. Perform the action specified in the requirement. 3. Observe the output. | "
            f"System behavior strictly matches: {short_desc} | {norm_priority} |"
        )

    # Validation / negative check strictly scoped to provided info
    next_id = f"TC-{len(rows) + 1:03d}"
    rows.append(
        f"| {next_id} | Verify validation and error handling for: {summary} | {precond} | "
        f"1. Attempt the workflow for '{summary}' with missing or invalid inputs. 2. Submit the request. | "
        f"{'Not specified' if description == 'Not specified' else 'System prevents invalid submission and preserves state.'} | Medium |"
    )

    table_md = "\n".join(rows)
    missing_info = (
        "Ticket description or explicit acceptance criteria are not specified in Jira."
        if description == "Not specified"
        else "None (all assertions mapped directly to Jira ticket fields)."
    )

    return f"""### 1. Test Plan Summary
- **Jira Ticket ID**: `{key}`
- **Summary**: {summary}
- **Issue Type**: {issue_type} | **Status**: {status} | **Jira Priority**: {priority}
- **Verified Facts**:
  - Summary: {summary}
  - Description: {description}
  - Acceptance Criteria: {ac}
- **Missing / Unknown Information**: {missing_info}

### 2. Generated Test Cases

| Test ID | Description | Pre-conditions | Steps | Expected Result | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
{table_md}
{template_note}"""


def generate_test_cases_with_llm(
    user_message: str,
    jira_data: Dict[str, Any],
    api_key: str,
    model_name: str = "gemini-4-argon",
    base_url: str = "",
) -> Tuple[bool, str]:
    """Load template, build prompt, and call Antigravity (gemini-4-argon) to generate test cases."""
    ok, template_content, hallucination_rules = load_template_files()
    if not ok:
        return False, template_content

    system_instruction, user_prompt = build_generation_prompt(
        user_message=user_message,
        jira_data=jira_data,
        template_content=template_content,
        hallucination_rules=hallucination_rules,
    )

    # Hook into Antigravity SDK / REST endpoint for Gemini 4 Argon (gemini-4-argon)
    llm_ok, llm_response = _call_gemini_rest(
        api_key=api_key,
        model_name=model_name or "gemini-4-argon",
        system_instruction=system_instruction,
        user_prompt=user_prompt,
        base_url=base_url,
    )

    if llm_ok:
        return True, llm_response

    # If the Antigravity token (`AQ....`) requires a local Antigravity gateway or the cloud endpoint rejected it,
    # provide the full template-compliant test plan & test cases derived directly from the live Jira ticket
    # along with a clear diagnostic note.
    diagnostic_note = (
        f"\n\n> **Note on Antigravity (`{model_name}`) Connection**: Direct cloud call returned `{llm_response}`. "
        "The test plan and test cases above were generated using the local strict-template engine directly from your live Jira ticket."
    )
    fallback_output = _build_deterministic_fallback(jira_data, template_note=diagnostic_note)
    return True, fallback_output
