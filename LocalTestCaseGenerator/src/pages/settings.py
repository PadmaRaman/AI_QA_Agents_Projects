"""Page 2: Settings & Configuration for Jira REST API and Antigravity (Gemini 4 Argon)."""

import streamlit as st

from utils.config import ENV_FILE_PATH, load_app_config, save_app_config
from utils.jira_client import test_jira_connection
from utils.llm_client import load_template_files

st.set_page_config(
    page_title="Settings & Configuration | AI Test Generator",
    page_icon="⚙️",
    layout="wide",
)

# Load current configuration from src/.env and st.session_state
config = load_app_config()

st.title("⚙️ Settings & Configuration")
st.markdown(
    "Configure your **Jira REST API** credentials and **Antigravity (`gemini-4-argon`)** connection key. "
    f"Settings are saved locally in `{ENV_FILE_PATH}` and persisted across reloads."
)

st.divider()

with st.form("settings_form", clear_on_submit=False):
    st.subheader("1. Jira Cloud REST API Credentials")
    col1, col2 = st.columns(2)
    with col1:
        jira_base_url = st.text_input(
            "Jira Base URL",
            value=config.get("JIRA_BASE_URL", ""),
            placeholder="https://your-domain.atlassian.net",
            help="Your Atlassian Cloud domain URL without trailing slash.",
        )
        jira_email = st.text_input(
            "Jira Account Email ID",
            value=config.get("JIRA_EMAIL", ""),
            placeholder="your-email@example.com",
            help="The email address associated with your Jira account.",
        )
    with col2:
        jira_api_token = st.text_input(
            "Jira API Token",
            value=config.get("JIRA_API_TOKEN", ""),
            type="password",
            help="Your Atlassian API Token (masked for security).",
        )

    st.subheader("2. Antigravity / Gemini 4 Argon Configuration")
    col3, col4 = st.columns(2)
    with col3:
        antigravity_api_key = st.text_input(
            "Antigravity API Token / Connection Key",
            value=config.get("ANTIGRAVITY_API_KEY", ""),
            type="password",
            help="Your Antigravity or Google GenAI API Key (masked for security).",
        )
        antigravity_model = st.text_input(
            "Model Identifier",
            value=config.get("ANTIGRAVITY_MODEL", "gemini-4-argon"),
            placeholder="gemini-4-argon",
            help="Target model name configured for Antigravity (default: gemini-4-argon).",
        )
    with col4:
        antigravity_base_url = st.text_input(
            "Antigravity Custom Endpoint URL (Optional)",
            value=config.get("ANTIGRAVITY_BASE_URL", ""),
            placeholder="Leave blank for default endpoint",
            help="Optional custom gateway or proxy base URL.",
        )

    btn_col1, btn_col2 = st.columns([1, 1])
    with btn_col1:
        save_clicked = st.form_submit_button("💾 Save Configuration", use_container_width=True, type="primary")
    with btn_col2:
        test_clicked = st.form_submit_button("🔌 Save & Test Jira Connection", use_container_width=True)

if save_clicked or test_clicked:
    saved_path = save_app_config(
        jira_base_url=jira_base_url,
        jira_email=jira_email,
        jira_api_token=jira_api_token,
        antigravity_api_key=antigravity_api_key,
        antigravity_base_url=antigravity_base_url,
        antigravity_model=antigravity_model,
    )
    st.success(f"Configuration saved to `{saved_path}` and loaded into session state.")

    if test_clicked:
        with st.spinner("Testing connection to Jira REST API v3..."):
            ok, msg = test_jira_connection(jira_base_url, jira_email, jira_api_token)
            if ok:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ {msg}")

st.divider()

# Active Template Preview
st.subheader("📄 Active Test Case Template Preview")
tpl_ok, tpl_content, rules_content = load_template_files()
if tpl_ok:
    with st.expander("View Loaded Template & Anti-Hallucination Rules", expanded=False):
        st.markdown("#### Test Case Template")
        st.code(tpl_content, language="markdown")
        if rules_content:
            st.markdown("#### Anti-Hallucination Rules")
            st.code(rules_content, language="markdown")
else:
    st.warning(tpl_content)
