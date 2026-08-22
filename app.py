"""
Shamba Advisor — Main Streamlit App
====================================

Dark, minimal chat interface (Claude/Qwen-style), with persistent
sign-in via a URL query parameter so returning farmers don't
need to retype their name every session.
"""

# =========================================================
# IMPORTS
# =========================================================

import html
from pathlib import Path

import streamlit as st

from ai.first_call import get_full_analysis
from ai.second_call import generate_action_plan

from utility.file_saver import save_report

from models.database_supabase import (
    get_or_create_farmer,
    create_chat,
    save_message,
    get_recent_chats,
    get_chat_history,
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Shamba Advisor",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# DARK, MINIMAL CSS (Claude/Qwen-style)
# =========================================================

st.html("""
<style>

/* =====================================================
   GENERAL APP
   ===================================================== */

.stApp {
    background-color: #1e1e1e !important;
    color: #e8e6e3 !important;
}

.main .block-container {
    max-width: 900px;
    padding-top: 1rem;
    padding-bottom: 6rem;
}


/* =====================================================
   HEADER
   ===================================================== */

.app-header {
    background-color: transparent !important;
    color: #e8e6e3 !important;
    padding: 14px 0 !important;
    margin-bottom: 16px !important;
    border: none !important;
}

.header-title {
    font-size: 20px;
    font-weight: 600;
}

.header-subtitle {
    font-size: 13px;
    opacity: 0.6;
    margin-top: 2px;
}


/* =====================================================
   CHAT MESSAGE ROW
   ===================================================== */

.chat-row {
    width: 100%;
    display: flex;
    margin-top: 12px;
    margin-bottom: 12px;
    box-sizing: border-box;
}

.bot-row {
    justify-content: flex-start;
}

.user-row {
    justify-content: flex-end;
}


/* =====================================================
   MESSAGE BUBBLES — Claude style 
   (Assistant = plain text, User = subtle box)
   ===================================================== */

.bot-bubble {
    background-color: transparent !important;
    color: #e8e6e3 !important;
    padding: 4px 0 !important;
    border-radius: 0 !important;
    max-width: 85% !important;
    font-size: 15px !important;
    line-height: 1.6 !important;
    border: none !important;
    overflow-wrap: anywhere !important;
}

.user-bubble {
    background-color: #2a2a28 !important;
    color: #e8e6e3 !important;
    padding: 10px 14px !important;
    border-radius: 12px !important;
    max-width: 75% !important;
    font-size: 15px !important;
    line-height: 1.55 !important;
    border: 1px solid #3a3a38 !important;
    overflow-wrap: anywhere !important;
}

.message-text {
    white-space: normal;
    word-wrap: break-word;
}

.sender-name {
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 4px;
    opacity: 0.5;
    letter-spacing: 0.02em;
}

/* Hide sender name for bot to make it look like plain text */
.bot-row .sender-name {
    display: block !important;
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 4px;
    opacity: 0.5;
    letter-spacing: 0.02em;
    color: #d97757 !important
}


/* =====================================================
   SIDEBAR — minimal list, plain text (no boxes)
   ===================================================== */

section[data-testid="stSidebar"] {
    background-color: #191919 !important;
    border-right: 1px solid #2f2f2d !important;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem !important;
}

section[data-testid="stSidebar"] .stButton > button {
    background-color: transparent !important;
    color: #a8a6a2 !important;
    border: none !important;
    text-align: left !important;
    padding: 6px 8px !important;
    font-size: 13.5px !important;
    border-radius: 4px !important;
    justify-content: flex-start !important;
    width: 100% !important;
    box-shadow: none !important;
    margin-bottom: 2px !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background-color: #262624 !important;
    color: #ffffff !important;
}

section[data-testid="stSidebar"] .stButton > button:active,
section[data-testid="stSidebar"] .stButton > button:focus {
    background-color: transparent !important;
    color: #ffffff !important;
    box-shadow: none !important;
    outline: none !important;
    border: none !important;
}


/* =====================================================
   CHAT INPUT — minimal, clean bar like Qwen
   ===================================================== */

div[data-testid="stChatInput"] {
    background-color: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 0 !important;
    margin-bottom: 0 !important;
}

div[data-testid="stChatInput"] > div {
    background-color: #2a2a28 !important;
    border: 1px solid #3a3a38 !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
}

div[data-testid="stChatInput"] textarea {
    background-color: transparent !important;
    color: #e8e6e3 !important;
    font-size: 14px !important;
    box-shadow: none !important;
    border: none !important;
    resize: none !important;
}

div[data-testid="stChatInput"] textarea:focus {
    box-shadow: none !important;
    border: none !important;
    outline: none !important;
}

div[data-testid="stChatInput"] textarea::placeholder {
    color: #6a6a68 !important;
    opacity: 0.7 !important;
}

div[data-testid="stChatInput"] button {
    background-color: #d97757 !important;
    color: #1e1e1e !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 6px 12px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    min-width: auto !important;
    width: auto !important;
    box-shadow: none !important;
}

div[data-testid="stChatInput"] button:hover {
    background-color: #e08b6e !important;
}

div[data-testid="stChatInput"] form {
    gap: 8px !important;
}


/* =====================================================
   MAIN-AREA BUTTONS (cause selection, start, etc.)
   ===================================================== */

.main .stButton > button {
    border-radius: 8px !important;
    background-color: #d97757 !important;
    color: #1e1e1e !important;
    border: none !important;
    font-weight: 500 !important;
    transition: background-color 0.15s ease !important;
}

.main .stButton > button:hover {
    background-color: #e08b6e !important;
    color: #1e1e1e !important;
}

.main .stButton > button:active,
.main .stButton > button:focus,
.main .stButton > button:focus:not(:active) {
    background-color: #d97757 !important;
    color: #1e1e1e !important;
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}


/* =====================================================
   TEXT INPUTS
   ===================================================== */

.stTextInput > div > div > input {
    background-color: #262624 !important;
    color: #e8e6e3 !important;
    border: 1px solid #3a3a38 !important;
}


/* =====================================================
   SPINNER
   ===================================================== */

[data-testid="stSpinner"] {
    background-color: #2a2a28 !important;
    border-radius: 10px !important;
    padding: 10px 16px !important;
    margin: 8px 0 !important;
    max-width: 320px !important;
    border: 1px solid #3a3a38 !important;
}

[data-testid="stSpinner"] > div {
    color: #d97757 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}

[data-testid="stSpinner"] svg {
    stroke: #d97757 !important;
}


/* =====================================================
   MOBILE
   ===================================================== */

@media (max-width: 768px) {

    .bot-bubble,
    .user-bubble {
        max-width: 90% !important;
        font-size: 14px !important;
    }

    .main .block-container {
        padding-left: 8px !important;
        padding-right: 8px !important;
    }

    .header-title {
        font-size: 18px !important;
    }

}

</style>
""")


# =========================================================
# SESSION STATE INITIALIZATION
# =========================================================

if "farmer_name" not in st.session_state:
    st.session_state.farmer_name = None

if "farmer_id" not in st.session_state:
    st.session_state.farmer_id = None

if "chat_id" not in st.session_state:
    st.session_state.chat_id = None

if "pending_analysis" not in st.session_state:
    st.session_state.pending_analysis = None

if "messages" not in st.session_state:
    st.session_state.messages = []


# =========================================================
# PERSISTENT SIGN-IN VIA URL QUERY PARAMETER
# =========================================================

if st.session_state.farmer_name is None:

    remembered_name = st.query_params.get("farmer")

    if remembered_name:

        try:
            farmer_id = get_or_create_farmer(remembered_name)
            st.session_state.farmer_name = remembered_name
            st.session_state.farmer_id = farmer_id

        except Exception:
            pass


# =========================================================
# WELCOME / FARMER NAME
# =========================================================

if st.session_state.farmer_name is None:

    st.html("""
    <div style="
        max-width:600px;
        margin:70px auto 20px auto;
        text-align:center;
    ">

        <div style="
            font-size:52px;
            margin-bottom:10px;
        ">
            🌱
        </div>

        <h1 style="
            color:#e8e6e3;
            margin-bottom:10px;
            font-weight:600;
        ">
            Shamba Advisor
        </h1>

        <p style="
            font-size:16px;
            color:#a8a6a2;
            line-height:1.5;
        ">
            Your AI farming assistant for planting,
            pests, irrigation, weather and harvest advice.
        </p>

    </div>
    """)

    name_input = st.text_input(
        "What's your name?",
        placeholder="Enter your name",
    )

    if st.button(
        "Start 🌱",
        use_container_width=True,
    ):

        if not name_input.strip():

            st.warning(
                "Please enter your name first."
            )

        else:

            farmer_name = name_input.strip()

            try:

                farmer_id = get_or_create_farmer(
                    farmer_name
                )

                st.session_state.farmer_name = farmer_name
                st.session_state.farmer_id = farmer_id
                st.session_state.chat_id = None
                st.session_state.pending_analysis = None
                st.session_state.messages = []

                st.query_params["farmer"] = farmer_name

                st.rerun()

            except Exception as e:

                st.error(
                    "I couldn't create your farmer profile."
                )

                st.exception(e)

    st.stop()


# =========================================================
# FARMER ID
# =========================================================

farmer_id = st.session_state.farmer_id


# =========================================================
# DISPLAY MESSAGE
# =========================================================

def show_message(role, content):
    """Dark, minimal message display. Bot -> left (plain text), Farmer -> right (subtle box)."""

    if content is None:
        return

    safe_content = html.escape(str(content))
    safe_content = safe_content.replace("\n", "<br>")

    if role == "user":

        st.html(f"""
        <div class="chat-row user-row">
            <div class="user-bubble">
                <div class="sender-name">You</div>
                <div class="message-text">{safe_content}</div>
            </div>
        </div>
        """)

    else:

        st.html(f"""
        <div class="chat-row bot-row">
            <div class="bot-bubble">
                <div class="sender-name">🌱 Shamba Advisor</div>
                <div class="message-text">{safe_content}</div>
            </div>
        </div>
        """)


# =========================================================
# BUILD CONVERSATION CONTEXT
# =========================================================

def build_conversation_context(history, current_message):
    """
    Creates a compact conversation context for Call 1, so
    follow-up questions are understood using recent history.
    """

    if not history:
        return current_message.strip()

    context_lines = []
    recent_history = history[-12:]

    for message in recent_history:

        role = message.get("role", "unknown")
        content = message.get("content", "")

        if not content:
            continue

        if role == "user":
            speaker = "Farmer"
        elif role == "assistant":
            speaker = "Shamba Advisor"
        else:
            speaker = role

        context_lines.append(f"{speaker}: {content}")

    previous_context = "\n".join(context_lines)

    return f"""
PREVIOUS CONVERSATION:

{previous_context}

CURRENT FARMER MESSAGE:

{current_message.strip()}

IMPORTANT:
Treat the CURRENT FARMER MESSAGE as the new message,
but use the previous conversation to understand references,
follow-up questions, missing context, and pronouns.

Do not assume that the current message starts a new conversation.
""".strip()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.html("""
    <div style="text-align:center; font-size:36px; margin-bottom:5px;">
        🌱
    </div>
    """)

    st.html("""
    <div style="
        text-align:center;
        font-size:17px;
        font-weight:600;
        color:#e8e6e3;
        margin-bottom:15px;
    ">
        Shamba Advisor
    </div>
    """)

    safe_name = html.escape(str(st.session_state.farmer_name or "Farmer"))

    st.html(f"""
    <div style="
        background:#262624;
        color:#e8e6e3;
        padding:10px 12px;
        border-radius:8px;
        margin-bottom:15px;
        border:1px solid #3a3a38;
        font-size:13.5px;
    ">
        👋 <strong>{safe_name}</strong>
    </div>
    """)

    if st.button("＋ New chat", use_container_width=True):

        st.session_state.chat_id = None
        st.session_state.pending_analysis = None
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("Recent chats")

    try:
        recent = get_recent_chats(farmer_id)
    except Exception:
        recent = []
        st.warning("Unable to load recent chats.")

    if not recent:
        st.caption("No chats yet — ask a question to start one.")
    else:
        for chat in recent:

            label = str(chat.get("title") or "Untitled chat")[:45]

            if st.button(label, key=f"chat_{chat['id']}", use_container_width=True):

                st.session_state.chat_id = chat["id"]
                st.session_state.pending_analysis = None
                st.session_state.messages = []
                st.rerun()


# =========================================================
# MAIN HEADER
# =========================================================

st.html("""
<div class="app-header">
    <div class="header-title">🌱 Shamba Advisor</div>
    <div class="header-subtitle">AI farming assistant</div>
</div>
""")


# =========================================================
# LOAD EXISTING CHAT HISTORY
# =========================================================

if st.session_state.chat_id:

    try:
        history = get_chat_history(st.session_state.chat_id)
        for msg in history:
            show_message(msg.get("role"), msg.get("content"))

    except Exception as e:
        history = []
        st.error("Unable to load this conversation.")
        st.exception(e)

else:
    history = []


# =========================================================
# CALL 2
# =========================================================

def run_call_two(analysis: dict, selected_cause: str = None):
    """
    Runs Call 2. The generated advice is displayed, saved to
    Supabase, saved as a report, and made available for download.
    """

    if not st.session_state.chat_id:
        st.error("No active conversation was found.")
        return

    with st.spinner("🌱 Preparing your farming advice..."):
        try:
            advice = generate_action_plan(analysis, selected_cause=selected_cause)
        except Exception as e:
            st.error("I couldn't generate the farming advice.")
            st.exception(e)
            return

    if advice is None:
        advice = "I couldn't generate advice right now. Please try again."

    advice = str(advice)

    show_message("assistant", advice)

    try:
        save_message(st.session_state.chat_id, "assistant", advice)
    except Exception as e:
        st.warning("The advice was generated, but I couldn't save it to the conversation.")
        st.exception(e)

    try:
        crop = analysis.get("crop")
        saved_path = save_report(st.session_state.farmer_name, crop, advice)
        saved_path = Path(saved_path)

        if saved_path.exists():
            with open(saved_path, "rb") as report_file:
                st.download_button(
                    label=" Download this report",
                    data=report_file,
                    file_name=saved_path.name,
                    mime="text/plain",
                    key=f"download_{st.session_state.chat_id}_{saved_path.name}",
                )

    except Exception as e:
        st.warning("The advice was generated, but the report could not be saved.")
        st.exception(e)


# =========================================================
# PENDING POSSIBLE CAUSE
# =========================================================

if st.session_state.pending_analysis:

    analysis = st.session_state.pending_analysis
    possible_causes = analysis.get("possible_causes") or []

    show_message(
        "assistant",
        "Here are the most likely causes — which matches what you're seeing?",
    )

    selected_cause = None

    if possible_causes:
        cols = st.columns(len(possible_causes))
        for i, cause in enumerate(possible_causes):
            if cols[i].button(str(cause), key=f"cause_{i}", use_container_width=True):
                selected_cause = str(cause)

    other_input = st.text_input(
        "Or describe it in your own words:",
        key="other_cause_input",
        placeholder="Describe what you are seeing...",
    )

    if st.button("Use my own description", key="other_cause_btn", use_container_width=True):
        if other_input.strip():
            selected_cause = other_input.strip()
        else:
            st.warning("Please describe the problem first.")

    if selected_cause:
        st.session_state.pending_analysis = None
        run_call_two(analysis, selected_cause=selected_cause)
    else:
        st.stop()


# =========================================================
# CHAT INPUT
# =========================================================

user_message = st.chat_input("Ask about planting, pests, irrigation, harvest...")


# =========================================================
# PROCESS NEW FARMER MESSAGE
# =========================================================

if user_message:

    user_message = user_message.strip()

    if not user_message:
        st.warning("Please type a question.")
        st.stop()

    if st.session_state.chat_id is None:
        try:
            st.session_state.chat_id = create_chat(farmer_id, title=user_message[:40])
        except Exception as e:
            st.error("I couldn't create the conversation.")
            st.exception(e)
            st.stop()

    previous_history = []
    try:
        previous_history = get_chat_history(st.session_state.chat_id)
    except Exception:
        previous_history = []

    show_message("user", user_message)

    try:
        save_message(st.session_state.chat_id, "user", user_message)
    except Exception as e:
        st.error("Your message could not be saved.")
        st.exception(e)
        st.stop()

    contextual_message = build_conversation_context(previous_history, user_message)

    with st.spinner(" Understanding your question..."):
        try:
            analysis = get_full_analysis(contextual_message)
        except Exception as e:
            st.error("I couldn't analyze your question.")
            st.exception(e)
            st.stop()

    possible_causes = analysis.get("possible_causes") or []

    if possible_causes:
        st.session_state.pending_analysis = analysis
        st.rerun()

    else:
        run_call_two(analysis)