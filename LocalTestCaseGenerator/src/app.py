"""Page 1: AI Test Generator (Chat Interface) connecting Jira REST API and Antigravity (Gemini 4 Argon)."""

import streamlit as st

from utils.config import load_app_config, validate_credentials
from utils.jira_client import extract_jira_id, fetch_jira_issue
from utils.llm_client import generate_test_cases_with_llm

st.set_page_config(
    page_title="AI Test Case Generator | Jira + Antigravity",
    page_icon="🧪",
    layout="wide",
)

# Load .env credentials into st.session_state on startup
config = load_app_config()
creds_valid, missing_fields = validate_credentials()

# Sidebar status & quick controls
with st.sidebar:
    st.header("🧪 AI Test Generator")
    st.caption("Powered by Jira REST API v3 & Antigravity (`gemini-4-argon`)")
    st.divider()

    st.subheader("Connection Status")
    if creds_valid:
        st.success("Credentials Configured")
        st.caption(f"**Jira**: `{config.get('JIRA_BASE_URL')}`")
        st.caption(f"**Account**: `{config.get('JIRA_EMAIL')}`")
        st.caption(f"**Model**: `{config.get('ANTIGRAVITY_MODEL', 'gemini-4-argon')}`")
    else:
        st.error(f"Missing: {', '.join(missing_fields)}")
        st.info("Open **Settings** in the sidebar navigation to configure your keys.")

    st.divider()
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main Header
st.title("🤖 AI Test Plan & Test Case Generator")
st.markdown(
    "Enter a prompt with a **Jira Ticket ID** (e.g., *\"Generate a test plan and functional test cases for Jira ID: KAN-42\"*). "
    "The app will automatically extract the ticket ID, fetch live details from Jira, apply your `/templates` structure, "
    "and generate standardized test cases via **Gemini 4 Argon**."
)

if not creds_valid:
    st.warning(
        f"⚠️ **Configuration Required**: Please configure {', '.join(missing_fields)} on the **Settings** page before generating test cases."
    )

# Initialize conversational chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Hello! I'm your **AI QA Test Case Generator** connected to Jira and **Gemini 4 Argon**.\n\n"
                "Send me a message containing a Jira Ticket ID (for example: `Create test cases for KAN-1` or "
                "`Generate a test plan and 5 functional test cases for PROJ-101`) to get started."
            ),
        }
    ]

# Render existing chat messages
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("ticket_key") and msg["role"] == "assistant":
            st.download_button(
                label=f"⬇️ Download {msg['ticket_key']} Test Cases (.md)",
                data=msg["content"],
                file_name=f"{msg['ticket_key']}_test_cases.md",
                mime="text/markdown",
                key=f"dl_{idx}_{msg['ticket_key']}",
            )

# Chat Input
user_prompt = st.chat_input("Enter a prompt with a Jira Ticket ID (e.g., 'Create test cases for KAN-42')...")

if user_prompt:
    # 1. Append and display user message
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # 2. Generate assistant response
    with st.chat_message("assistant"):
        # Re-validate credentials
        creds_valid, missing_fields = validate_credentials()
        if not creds_valid:
            err_msg = (
                f"❌ **Missing Credentials**: {', '.join(missing_fields)}. "
                "Please open the **Settings** page from the left sidebar to configure your credentials first."
            )
            st.error(err_msg)
            st.session_state.messages.append({"role": "assistant", "content": err_msg})
        else:
            jira_id = extract_jira_id(user_prompt)
            if not jira_id:
                no_id_msg = (
                    "⚠️ I couldn't detect a valid **Jira Ticket ID** in your message. "
                    "Please include a ticket key in standard format (e.g., `KAN-42`, `PROJ-101`, `SCRUM-5`)."
                )
                st.warning(no_id_msg)
                st.session_state.messages.append({"role": "assistant", "content": no_id_msg})
            else:
                with st.status(f"Processing Jira Ticket `{jira_id}`...", expanded=True) as status_box:
                    st.write(f"🔍 Extracted Jira Ticket ID: **`{jira_id}`**")
                    st.write(f"🌐 Fetching ticket details from `{config['JIRA_BASE_URL']}/rest/api/3/issue/{jira_id}`...")

                    jira_result = fetch_jira_issue(
                        issue_key=jira_id,
                        base_url=config["JIRA_BASE_URL"],
                        email=config["JIRA_EMAIL"],
                        api_token=config["JIRA_API_TOKEN"],
                    )

                    if not jira_result["success"]:
                        status_box.update(label=f"Failed to fetch `{jira_id}`", state="error", expanded=True)
                        err_text = f"❌ **Jira API Error**: {jira_result['error']}"
                        st.error(err_text)
                        st.session_state.messages.append({"role": "assistant", "content": err_text})
                    else:
                        ticket_data = jira_result["data"]
                        st.write(
                            f"✅ Fetched **`{ticket_data['key']}`**: *{ticket_data['summary']}* "
                            f"(`{ticket_data['issue_type']}` | `{ticket_data['status']}`)"
                        )
                        st.write("📄 Loading local template (`templates/test_case_template.md`) & Anti-Hallucination rules...")
                        st.write(
                            f"🤖 Generating Test Plan & Test Cases with **`{config.get('ANTIGRAVITY_MODEL', 'gemini-4-argon')}`**..."
                        )

                        gen_ok, generated_output = generate_test_cases_with_llm(
                            user_message=user_prompt,
                            jira_data=ticket_data,
                            api_key=config["ANTIGRAVITY_API_KEY"],
                            model_name=config.get("ANTIGRAVITY_MODEL", "gemini-4-argon"),
                            base_url=config.get("ANTIGRAVITY_BASE_URL", ""),
                        )

                        if not gen_ok:
                            status_box.update(label="Generation failed", state="error", expanded=True)
                            err_text = f"❌ **Generation Error**: {generated_output}"
                            st.error(err_text)
                            st.session_state.messages.append({"role": "assistant", "content": err_text})
                        else:
                            status_box.update(
                                label=f"Completed Test Cases for `{jira_id}`!",
                                state="complete",
                                expanded=False,
                            )
                            st.markdown(generated_output)
                            st.download_button(
                                label=f"⬇️ Download {jira_id} Test Cases (.md)",
                                data=generated_output,
                                file_name=f"{jira_id}_test_cases.md",
                                mime="text/markdown",
                                key=f"dl_live_{jira_id}",
                            )
                            st.session_state.messages.append(
                                {
                                    "role": "assistant",
                                    "content": generated_output,
                                    "ticket_key": jira_id,
                                }
                            )
