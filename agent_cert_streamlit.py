import streamlit as st
import requests
import uuid
import json

# ==============================
# Configuration
# ==============================

API_URL = "https://elastic.snaplogic.com/api/1/rest/slsched/feed/SIE_Health_Dev/SHS_IT_DEI_HC_AI/Vikas/Cert_Agent_Task"
API_TOKEN = st.secrets.get("API_TOKEN", "uApLXaauiDtaYw8IJrad8Wdl9j1TL041")

REQUEST_TIMEOUT = 180


# ==============================
# Page Setup
# ==============================

st.set_page_config(
    page_title="HC Orchestration Agent",
    page_icon="🤖",
    layout="wide"
)


# ==============================
# Session Initialization
# ==============================

def initialize_session():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "last_raw_response" not in st.session_state:
        st.session_state.last_raw_response = None


# ==============================
# Backend Call (Stateless)
# ==============================

def call_agent(user_prompt: str):
    """
    Stateless API call.
    Only sends the current user message.
    """

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = [
        {
            "session_id": st.session_state.session_id,
            "messages": [
                {
                    "sl_role": "USER",
                    "content": user_prompt
                }
            ]
        }
    ]

    try:
        response = requests.post(
            API_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()
        st.session_state.last_raw_response = data

        return data

    except requests.exceptions.RequestException as e:
        return {"response": f"⚠️ API communication error: {str(e)}"}


# ==============================
# Response Normalization
# ==============================

def extract_response(data):
    """
    Strict schema enforcement.
    Backend must return:
    {
        "response": "some text"
    }
    """

    if isinstance(data, dict) and "response" in data:
        return data["response"]

    return "⚠️ Unexpected response format from backend."


# ==============================
# Sidebar
# ==============================

def display_sidebar():
    with st.sidebar:
        st.title("🔧 Configuration")

        st.markdown("**Session ID**")
        st.code(st.session_state.session_id)

        if st.button("♻️ New Session"):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.chat_history = []
            st.session_state.last_raw_response = None
            st.rerun()

        st.markdown("---")
        st.markdown("### Raw API Response")

        if st.session_state.last_raw_response:
            st.json(st.session_state.last_raw_response)
        else:
            st.write("No API response yet.")


# ==============================
# Chat UI
# ==============================

def display_chat():
    st.title("🤖 HC Orchestration Agent")
    st.write("Interact with the SnapLogic orchestration agent.")

    # Display chat history (LOCAL only, not sent to backend)
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"].lower()):
            st.markdown(message["content"])

    user_input = st.chat_input("Type your request here...")

    if user_input:
        # Display user message
        st.session_state.chat_history.append(
            {"role": "USER", "content": user_input}
        )

        with st.chat_message("assistant"):
            with st.spinner("Agent is processing..."):
                raw_data = call_agent(user_input)
                final_response = extract_response(raw_data)
                st.markdown(final_response)

        # Save assistant response locally
        st.session_state.chat_history.append(
            {"role": "ASSISTANT", "content": final_response}
        )

        st.rerun()


# ==============================
# Main
# ==============================

def main():
    initialize_session()
    display_sidebar()
    display_chat()


if __name__ == "__main__":
    main()
