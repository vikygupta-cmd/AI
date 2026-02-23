import streamlit as st
import requests
import uuid
import json
from datetime import datetime

# ======================================
# Configuration
# ======================================

API_URL = "https://elastic.snaplogic.com/api/1/rest/slsched/feed/SIE_Health_Dev/SHS_IT_DEI_HC_AI/Vikas/Cert_Agent_Task"
API_TOKEN = st.secrets.get("API_TOKEN", "uApLXaauiDtaYw8IJrad8Wdl9j1TL041")

REQUEST_TIMEOUT = 180

st.set_page_config(
    page_title="HC Orchestration Agent",
    page_icon="🤖",
    layout="wide"
)

# ======================================
# Session State Initialization
# ======================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "last_raw_response" not in st.session_state:
    st.session_state.last_raw_response = None


# ======================================
# Backend Call (100% Stateless)
# ======================================

def call_agent(user_prompt: str):
    """
    Fully stateless call.
    - New session_id per request
    - Unique request_id for tracing
    """

    request_id = str(uuid.uuid4())
    session_id = str(uuid.uuid4())

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = [
        {
            "session_id": session_id,
            "request_id": request_id,
            "timestamp": datetime.utcnow().isoformat(),
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
            json=payload,  # use json instead of data=json.dumps()
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()
        data = response.json()

        st.session_state.last_raw_response = data
        return data

    except requests.exceptions.Timeout:
        return {"response": "⚠️ Request timed out."}

    except requests.exceptions.RequestException as e:
        return {"response": f"⚠️ API error: {str(e)}"}


# ======================================
# Strict Response Parsing
# ======================================

def extract_response(data):
    """
    Enforces strict response schema.
    Backend must return:
    {
        "response": "text"
    }
    """

    if isinstance(data, dict) and "response" in data:
        return data["response"]

    if isinstance(data, list) and len(data) > 0:
        first = data[0]
        if isinstance(first, dict) and "response" in first:
            return first["response"]

    return "⚠️ Unexpected response format from backend."


# ======================================
# Sidebar
# ======================================

with st.sidebar:
    st.title("🔧 Debug Panel")

    if st.button("🧹 Clear Chat"):
        st.session_state.chat_history = []
        st.session_state.last_raw_response = None
        st.experimental_rerun()

    st.markdown("---")
    st.markdown("### Raw API Response")

    if st.session_state.last_raw_response:
        st.json(st.session_state.last_raw_response)
    else:
        st.write("No API response yet.")


# ======================================
# Main Chat Interface
# ======================================

st.title("🤖 HC Orchestration Agent")
st.write("Stateless SnapLogic Orchestration Interface")

# Display chat history (LOCAL ONLY)
for message in st.session_state.chat_history:
    with st.chat_message(message["role"].lower()):
        st.markdown(message["content"])

# User input
user_input = st.chat_input("Type your request...")

if user_input:

    # Add user message
    st.session_state.chat_history.append({
        "role": "USER",
        "content": user_input
    })

    with st.chat_message("assistant"):
        with st.spinner("Processing..."):

            raw_response = call_agent(user_input)
            final_text = extract_response(raw_response)

            st.markdown(final_text)

    # Store assistant reply locally
    st.session_state.chat_history.append({
        "role": "ASSISTANT",
        "content": final_text
    })
