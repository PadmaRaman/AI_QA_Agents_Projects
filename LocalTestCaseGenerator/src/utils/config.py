"""Configuration and .env credential management for Local Test Case Generator."""

import os
from pathlib import Path
from typing import Dict, Tuple

import streamlit as st
from dotenv import dotenv_values, load_dotenv, set_key

# Resolve paths relative to the src/ directory
SRC_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = SRC_DIR.parent
ENV_FILE_PATH = SRC_DIR / ".env"

CONFIG_KEYS = [
    "JIRA_BASE_URL",
    "JIRA_EMAIL",
    "JIRA_API_TOKEN",
    "ANTIGRAVITY_API_KEY",
    "ANTIGRAVITY_BASE_URL",
    "ANTIGRAVITY_MODEL",
]


def _clean_env_value(value: str | None) -> str:
    """Strip inline comments and surrounding whitespace from .env values."""
    if not value:
        return ""
    # Remove unquoted inline comments (e.g. "gemini-4-argon  # Default model")
    if " #" in value:
        value = value.split(" #", 1)[0]
    elif value.strip().startswith("#"):
        return ""
    return value.strip().strip("'").strip('"')


def load_app_config(force_reload: bool = False) -> Dict[str, str]:
    """Load configuration from src/.env into os.environ and st.session_state."""
    if ENV_FILE_PATH.exists():
        load_dotenv(dotenv_path=ENV_FILE_PATH, override=force_reload)
        file_values = dotenv_values(ENV_FILE_PATH)
    else:
        file_values = {}

    config: Dict[str, str] = {}
    for key in CONFIG_KEYS:
        raw_val = file_values.get(key) or os.getenv(key, "")
        cleaned_val = _clean_env_value(raw_val)
        if key == "ANTIGRAVITY_MODEL" and not cleaned_val:
            cleaned_val = "gemini-4-argon"
        if key == "JIRA_BASE_URL" and cleaned_val:
            cleaned_val = cleaned_val.rstrip("/")

        if force_reload or key not in st.session_state or not st.session_state[key]:
            st.session_state[key] = cleaned_val
        config[key] = st.session_state.get(key, cleaned_val)

    return config


def save_app_config(
    jira_base_url: str,
    jira_email: str,
    jira_api_token: str,
    antigravity_api_key: str,
    antigravity_base_url: str = "",
    antigravity_model: str = "gemini-4-argon",
) -> Path:
    """Persist configuration values to src/.env and update st.session_state."""
    ENV_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not ENV_FILE_PATH.exists():
        ENV_FILE_PATH.touch()

    updates = {
        "JIRA_BASE_URL": jira_base_url.strip().rstrip("/"),
        "JIRA_EMAIL": jira_email.strip(),
        "JIRA_API_TOKEN": jira_api_token.strip(),
        "ANTIGRAVITY_API_KEY": antigravity_api_key.strip(),
        "ANTIGRAVITY_BASE_URL": antigravity_base_url.strip(),
        "ANTIGRAVITY_MODEL": (antigravity_model.strip() or "gemini-4-argon"),
    }

    for key, val in updates.items():
        set_key(str(ENV_FILE_PATH), key, val, quote_mode="never")
        os.environ[key] = val
        st.session_state[key] = val

    return ENV_FILE_PATH


def validate_credentials() -> Tuple[bool, list[str]]:
    """Verify that all required Jira and Antigravity credentials are set."""
    config = load_app_config()
    required = {
        "JIRA_BASE_URL": "Jira Base URL",
        "JIRA_EMAIL": "Jira Account Email ID",
        "JIRA_API_TOKEN": "Jira API Token",
        "ANTIGRAVITY_API_KEY": "Antigravity API Token",
    }
    missing = [label for key, label in required.items() if not config.get(key)]
    return (len(missing) == 0, missing)
