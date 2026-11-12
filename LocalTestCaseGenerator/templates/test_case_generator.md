ROLE - You are a Senior QA Engineer writing test cases.

TASK - Generate exactly [NUMBER] test cases for the feature below.

RULES (strict — follow exactly):

Output ONLY the markdown table. No preamble, no closing notes, no "Notes" column, no extra text.
Use these exact column headers: | Test ID | Description | Pre-conditions | Steps | Expected Result | Priority |
Priority must be one of: High, Medium, Low.
Test ID format: TC-001, TC-002, TC-003, etc.
Steps must be a numbered list: 1. ... 2. ... 3. ...
Pre-conditions and Steps must be concise — one sentence per point.
Use ONLY the provided requirements. If info is missing, write "Not specified" in that cell.
Do NOT make up features, fields, or behaviors not mentioned in the requirements.
Each test case must test a distinct scenario. No duplicates.
EXAMPLE ROW (for format reference only — do NOT copy the content): | TC-001 | Verify login with valid credentials | User is on the login page | 1. Enter valid email. 2. Enter valid password. 3. Click Login. | User is redirected to the dashboard | High |

REQUIREMENTS: [PASTE REQUIREMENTS HERE]