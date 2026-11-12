# Test Plan & Test Case Template

## 1. Test Plan Summary
- **Jira Ticket ID**: [JIRA_ID]
- **Title / Summary**: [SUMMARY]
- **Issue Type**: [ISSUE_TYPE]
- **Test Objective**: Verify the functional and non-functional requirements explicitly stated in the Jira ticket.
- **Scope / Preconditions**: Derived strictly from the ticket description and acceptance criteria.

## 2. Structured Test Cases
Generate the test cases strictly using the following Markdown table structure and columns:

| Test ID | Title / Description | Pre-conditions | Test Steps | Expected Result | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| TC-001 | [Concise scenario description] | [One-sentence precondition or "Not specified"] | 1. [Step 1] <br> 2. [Step 2] | [Expected outcome traceable to requirements] | High / Medium / Low |

### Formatting & Verification Rules:
1. **Columns**: Use these exact column headers: `| Test ID | Title / Description | Pre-conditions | Test Steps | Expected Result | Priority |`
2. **Test ID Format**: `TC-001`, `TC-002`, `TC-003`, etc.
3. **Priority**: Must be one of `High`, `Medium`, `Low`.
4. **Test Steps**: Must be a numbered list (`1. ... 2. ... 3. ...`).
5. **Anti-Hallucination**: Use ONLY the provided Jira ticket requirements. If information is missing, write `"Not specified"` in that cell. Do NOT invent features, fields, or behaviors not mentioned in the ticket.
6. **Distinct Scenarios**: Each test case must test a distinct scenario (positive, negative, edge cases based on the requirements) with no duplicates.
