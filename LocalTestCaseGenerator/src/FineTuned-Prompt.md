RICE-POT Master Prompt
R – Role
Act as a Senior Full-Stack Python Developer and QA Automation Architect specializing in AI-driven testing tools, REST API integrations, and rapid web prototyping with Streamlit.

I – Instructions
Build a clean, two-page Python web application using Streamlit that connects to Jira via REST API and uses the Antigravity connection (Gemini 4 Argon model) to automatically generate structured test plans and test cases from Jira tickets.

Implement the application with the following core architecture:

Page 1: AI Test Generator (Chat Interface)

Create a conversational UI similar to ChatGPT (st.chat_input and st.chat_message).

Allow the user to enter a prompt containing a Jira Ticket ID (e.g., "Create test cases for PROJ-101") and click Send.

Automatically extract the Jira ID from the user's message, fetch the ticket details (Summary, Description, Acceptance Criteria, Issue Type) using the saved Jira credentials, read the local test case template file from the /templates directory, and pass both to the Gemini 4 Argon model via the Antigravity connection to generate the output.

Page 2: Settings & Configuration

Create a dedicated settings page/tab to input and persist configuration details:

Jira Base URL (e.g., [https://your-domain.atlassian.net](https://your-domain.atlassian.net))

Jira Account Email ID

Jira API Token (masked password input)

Antigravity API Token / Connection Key (masked password input)

Save these settings locally (e.g., in a .env or local config.json file, alongside st.session_state) so they persist across app reloads.

Template Ingestion

Load a reference template (e.g., templates/test_case_template.md or .csv/.xlsx) and strictly map the AI-generated test cases and test plan to match its exact columns, headers, and structure.

C – Context
QA engineers need a lightweight, local utility to eliminate manual copy-pasting between Jira and test management documentation. Instead of manually reading user stories and formatting test cases, the user will configure their Jira and Antigravity credentials once in the Settings screen, and then use a familiar chat interface to generate standardized test plans/cases on demand using the Gemini 4 Argon model.

E – Examples
User Input on Page 1:

"Generate a test plan and functional test cases for Jira ID: KAN-42"

System Background Workflow:

Regex parses KAN-42 from input.

GET {JIRA_URL}/rest/api/3/issue/KAN-42 fetches ticket JSON using Basic Auth (email:jira_token).

App reads templates/test_case_template.md.

App sends the Jira context + template structure to Antigravity (gemini-4-argon).

Expected Assistant Output in Chat UI:
A well-formatted response displaying the generated Test Plan summary followed by a structured table/list of Test Cases (Test Case ID, Title, Preconditions, Test Steps, Expected Result) adhering strictly to the /templates file.

P – Parameters & Constraints
Tech Stack: Python 3.10+, streamlit, requests (for Jira REST API), python-dotenv (or json for local config storage), and the Antigravity SDK/REST client configured for gemini-4-argon.

Security: Mask all API tokens (type="password") in the Streamlit UI and ensure config files are added to .gitignore.

Error Handling: Gracefully handle missing credentials (prompt the user to configure Page 2 first), invalid Jira IDs (404), authentication failures (401), and missing template files.

Simplicity: Keep the codebase modular yet minimal—avoid heavy frontend frameworks (React/Angular) or complex databases.

O – Output
Provide the complete, ready-to-run solution structured as follows:

Folder Structure (showing app.py, pages/settings.py, utils/jira_client.py, utils/llm_client.py, and templates/test_case_template.md).

requirements.txt with exact dependencies.

Sample Template File (templates/test_case_template.md).

Full Python Source Code for all files, with clear inline comments showing where the Antigravity endpoint/SDK hooks into the Gemini 4 Argon model.

Setup & Run Instructions (how to install dependencies and launch via streamlit run app.py).

T – Tone
Technical, precise, pragmatic, and production-ready. Write clean, modular, PEP-8 compliant Python code without unnecessary filler or abstract placeholders.