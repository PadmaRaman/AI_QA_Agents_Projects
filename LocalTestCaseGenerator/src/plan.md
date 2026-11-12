# Implementation Plan: Local Test Case Generator (Jira + Antigravity / Gemini 4 Argon)

## 1. Overview & Architecture
Based on [FineTuned-Prompt.md](file:///c:/Users/rampa/VisualStudioCode/AI_QA_Agents_Projects/LocalTestCaseGenerator/src/FineTuned-Prompt.md), we will build a two-page **Streamlit** web application in Python (`3.10+`) that:
1. Connects to **Jira REST API v3** using credentials stored in `.env` (and editable via the Settings UI).
2. Extracts Jira Ticket IDs (e.g., `PROJ-101`, `KAN-42`) from a conversational chat interface.
3. Fetches the ticket details (Summary, Description, Acceptance Criteria, Issue Type).
4. Combines the Jira context with the local test case template in `templates/` ([test_case_generator.md](file:///c:/Users/rampa/VisualStudioCode/AI_QA_Agents_Projects/LocalTestCaseGenerator/templates/test_case_generator.md) / `test_case_template.md`) and Anti-Hallucination rules ([AI_Hallucinations.rules.md](file:///c:/Users/rampa/VisualStudioCode/AI_QA_Agents_Projects/LocalTestCaseGenerator/templates/AI_Hallucinations.rules.md)).
5. Calls the **Gemini 4 Argon** (`gemini-4-argon`) model via the **Antigravity / Gemini connection** to generate a structured Test Plan and Test Cases table.

---

## 2. Target Folder Structure

```text
LocalTestCaseGenerator/
├── .env                          # Local credentials (auto-loaded & updated by Settings page)
├── .env.example                  # Template showing expected .env keys
├── .gitignore                    # Ensures .env, __pycache__, etc. are never committed
├── requirements.txt              # Python dependencies
├── app.py                        # Page 1: AI Test Generator (Chat Interface & Main Entrypoint)
├── pages/
│   └── settings.py               # Page 2: Settings & Configuration (Reads/Writes .env & session_state)
├── utils/
│   ├── __init__.py
│   ├── config.py                 # Helper to load/save .env variables & sync with st.session_state
│   ├── jira_client.py            # Jira REST API v3 client (ticket regex parser + issue fetcher)
│   └── llm_client.py             # Antigravity / Gemini 4 Argon client & template prompt builder
└── templates/
    ├── test_case_template.md     # Standardized test plan & test case markdown template
    ├── test_case_generator.md    # Existing strict table rules template
    └── AI_Hallucinations.rules.md# Existing anti-hallucination verification rules
```

---

## 3. `.env` Credentials Schema
As soon as you provide or populate the `.env` file, the app will read and persist these keys using `python-dotenv` (`load_dotenv` / `set_key`):

```ini
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your_jira_api_token_here
ANTIGRAVITY_API_KEY=your_antigravity_or_gemini_api_key_here
ANTIGRAVITY_BASE_URL=             # Optional: custom endpoint if using a proxy/gateway
ANTIGRAVITY_MODEL=gemini-4-argon  # Default model identifier
```
*(Note: If your `.env` uses slightly different variable names when you share it, `utils/config.py` will map your exact key names directly.)*

---

## 4. Component-by-Component Implementation Plan

### Step 1: Environment, Security & Dependencies
- **`.gitignore`**: Add `.env`, `.venv/`, `__pycache__/`, and `config.json` to prevent credential leaks.
- **`requirements.txt`**:
  - `streamlit>=1.32.0`
  - `requests>=2.31.0`
  - `python-dotenv>=1.0.1`
  - `google-genai>=0.3.0` / `openai>=1.14.0` (plus standard `requests` fallback so the Antigravity connection works seamlessly whether via Google GenAI SDK, OpenAI-compatible gateway, or REST endpoint).

### Step 2: Configuration Manager (`utils/config.py`)
- Automatically loads `.env` from `LocalTestCaseGenerator/.env` on startup.
- Initializes `st.session_state` with `JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`, and `ANTIGRAVITY_API_KEY`.
- Provides `save_credentials(...)` using `dotenv.set_key()` so updates on Page 2 persist in `.env` across app reloads.
- Provides `validate_credentials()` to check if all required keys are present before making API calls.

### Step 3: Jira REST API Client (`utils/jira_client.py`)
- **Ticket ID Extractor (`extract_jira_id(text: str)`)**:
  - Uses regex `\b([A-Z][A-Z0-9_]+-\d+)\b` (case-insensitive with `.upper()`) to parse IDs like `KAN-42` or `PROJ-101` from natural language prompts.
- **Ticket Fetcher (`fetch_jira_issue(issue_key: str, base_url: str, email: str, api_token: str)`)**:
  - Calls `GET {JIRA_BASE_URL}/rest/api/3/issue/{issue_key}` with `HTTPBasicAuth(email, api_token)` and `Accept: application/json`.
  - Parses Atlassian Document Format (ADF) descriptions and custom/acceptance criteria fields into clean plain text/markdown:
    - `key`, `summary`, `issue_type`, `status`, `priority`, `description`, `acceptance_criteria`.
  - **Error Handling**:
    - `401 / 403`: Returns clear authentication failure message prompting user to check Jira Email / API Token in Settings.
    - `404`: Returns clear message that Jira ID `{issue_key}` was not found or user lacks permission.
    - Connection/Timeout errors handled gracefully.

### Step 4: Template Ingestion & LLM Client (`utils/llm_client.py` & `templates/test_case_template.md`)
- **Template Loading**:
  - Loads `templates/test_case_template.md` (and incorporates the strict table formatting from `templates/test_case_generator.md` and rules from `templates/AI_Hallucinations.rules.md`).
  - Handles missing template file errors gracefully.
- **Antigravity (`gemini-4-argon`) Integration**:
  - Constructs a system + user prompt containing:
    1. Role & Anti-Hallucination constraints.
    2. Exact template structure (`Test Plan Summary` + `| Test ID | Title / Description | Pre-conditions | Test Steps | Expected Result | Priority |`).
    3. Extracted Jira Ticket JSON context (Summary, Issue Type, Description, Acceptance Criteria).
    4. User's specific chat instructions (e.g., number of test cases or focus area).
  - Calls the `gemini-4-argon` model via the configured Antigravity connection and returns the formatted Markdown response.

### Step 5: Page 2 — Settings & Configuration (`pages/settings.py`)
- Dedicated Streamlit page with masked password inputs (`type="password"`) for:
  - **Jira Base URL** (`https://your-domain.atlassian.net`)
  - **Jira Account Email ID**
  - **Jira API Token** (masked)
  - **Antigravity API Token / Connection Key** (masked)
- **"Save Configuration" button**: Writes directly to `.env` and updates `st.session_state`.
- **"Test Jira Connection" button**: Calls `GET /rest/api/3/myself` to immediately verify the Jira credentials from `.env`.

### Step 6: Page 1 — AI Test Generator Chat Interface (`app.py`)
- Conversational UI built with `st.chat_message` and `st.chat_input("e.g., Generate a test plan and functional test cases for Jira ID: KAN-42")`.
- Maintains chat history in `st.session_state.messages`.
- **Workflow on User Message**:
  1. Checks if credentials are configured in `.env` / `st.session_state`. If missing, displays a warning with a direct link (`st.page_link("pages/settings.py")`) to configure Settings first.
  2. Extracts the Jira Ticket ID via regex. If no Jira ID is detected, prompts the user to include a valid ticket ID (e.g., `PROJ-101`).
  3. Shows an expandable status indicator (`st.status`) as it:
     - Parses Jira ID `{JIRA_ID}`
     - Fetches ticket details from Jira REST API
     - Loads `templates/test_case_template.md`
     - Generates the Test Plan & Test Cases via `gemini-4-argon`
  4. Renders the structured Markdown output in the chat UI and provides a **Download Markdown / CSV** button for the generated test cases.

---

## 5. Immediate Execution Steps (Once `.env` Credentials Are Shared)
1. **Create `.env` & `.gitignore`** with your exact credentials and verify key names.
2. **Create `requirements.txt`** and install dependencies if needed.
3. **Create `templates/test_case_template.md`** aligned with your existing `templates/test_case_generator.md`.
4. **Implement `utils/config.py`, `utils/jira_client.py`, and `utils/llm_client.py`**.
5. **Implement `app.py` and `pages/settings.py`**.
6. **Smoke-test the Jira API connection and launch instructions** (`streamlit run app.py`).
