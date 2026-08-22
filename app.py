"""
Shamba Advisor — Main Streamlit App
====================================

WhatsApp-style farming assistant.

Project structure:

wca-ai-tool-s11-afric/
│
├── app.py
├── ai/
│   ├── first_call.py
│   └── second_call.py
│
├── utility/
│   └── file_saver.py
│
├── models/
│   └── database_supabase.py
│
├── weather/
│   └── open_meteo.py
│
└── .env

Features:
- Farmer registration
- Persistent Supabase conversations
- WhatsApp-style UI
- Bot messages on the left
- Farmer messages on the right
- Conversation memory
- Call 1 analysis
- Call 2 farming advice
- Possible-cause selection
- Weather integration through Call 1
- Report saving/downloading
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
# WHATSAPP-STYLE CSS
# =========================================================

st.html("""
<style>

/* =====================================================
   GENERAL APP
   ===================================================== */

.stApp {
    background-color: #efeae2;
}

.main .block-container {
    max-width: 1100px;
    padding-top: 1rem;
    padding-bottom: 6rem;
}


/* =====================================================
   WHATSAPP HEADER
   ===================================================== */

.whatsapp-header {
    background-color: #075e54;
    color: white;
    padding: 14px 20px;
    border-radius: 10px 10px 0 0;
    margin-bottom: 12px;

    box-shadow:
        0 1px 3px rgba(0, 0, 0, 0.20);
}

.header-title {
    font-size: 22px;
    font-weight: 700;
}

.header-subtitle {
    font-size: 13px;
    opacity: 0.85;
    margin-top: 2px;
}


/* =====================================================
   CHAT MESSAGE ROW
   ===================================================== */

.whatsapp-chat {
    width: 100%;
    display: flex;

    margin-top: 7px;
    margin-bottom: 7px;

    padding-left: 8px;
    padding-right: 8px;

    box-sizing: border-box;
}


/* =====================================================
   BOT = LEFT
   ===================================================== */

.bot-row {
    justify-content: flex-start;
}


/* =====================================================
   FARMER = RIGHT
   ===================================================== */

.user-row {
    justify-content: flex-end;
}


/* =====================================================
   BOT BUBBLE
   ===================================================== */

.bot-bubble {
    background-color: #ffffff;
    color: #111111;

    padding: 9px 13px;

    border-radius:
        7px
        7px
        7px
        2px;

    max-width: 72%;

    font-size: 15px;
    line-height: 1.5;

    box-shadow:
        0 1px 2px rgba(0, 0, 0, 0.15);

    overflow-wrap: anywhere;
}


/* =====================================================
   FARMER BUBBLE
   ===================================================== */

.user-bubble {
    background-color: #d9fdd3;
    color: #111111;

    padding: 9px 13px;

    border-radius:
        7px
        7px
        2px
        7px;

    max-width: 72%;

    font-size: 15px;
    line-height: 1.5;

    box-shadow:
        0 1px 2px rgba(0, 0, 0, 0.15);

    overflow-wrap: anywhere;
}


/* =====================================================
   MESSAGE TEXT
   ===================================================== */

.message-text {
    white-space: normal;
    word-wrap: break-word;
}


/* =====================================================
   SENDER NAME
   ===================================================== */

.sender-name {
    font-size: 11px;
    font-weight: 600;

    margin-bottom: 3px;

    opacity: 0.65;
}


/* =====================================================
   SIDEBAR
   ===================================================== */

section[data-testid="stSidebar"] {
    background-color: #f0f2f5;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1.5rem;
}


/* =====================================================
   CHAT INPUT
   ===================================================== */

[data-testid="stChatInput"] {
    background-color: #f0f2f5;
}


/* =====================================================
   BUTTONS
   ===================================================== */

.stButton > button {
    border-radius: 8px;
}


/* =====================================================
   MOBILE
   ===================================================== */

@media (max-width: 768px) {

    .bot-bubble,
    .user-bubble {
        max-width: 88%;
        font-size: 14px;
    }

    .main .block-container {
        padding-left: 8px;
        padding-right: 8px;
    }

    .header-title {
        font-size: 19px;
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

if "force_new_chat" not in st.session_state:
    st.session_state.force_new_chat = False

if "messages" not in st.session_state:
    st.session_state.messages = []


# =========================================================
# WELCOME / FARMER NAME
# =========================================================

if st.session_state.farmer_name is None:

    st.html("""
    <div style="
        max-width:650px;
        margin:70px auto 20px auto;
        text-align:center;
    ">

        <div style="
            font-size:60px;
            margin-bottom:10px;
        ">
            🌱
        </div>

        <h1 style="
            color:#075e54;
            margin-bottom:10px;
        ">
            Shamba Advisor
        </h1>

        <p style="
            font-size:17px;
            color:#555555;
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
                st.session_state.force_new_chat = False
                st.session_state.messages = []

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
    """
    WhatsApp-style message display.

    Bot    -> LEFT
    Farmer -> RIGHT
    """

    if content is None:
        return

    safe_content = html.escape(
        str(content)
    )

    safe_content = safe_content.replace(
        "\n",
        "<br>"
    )

    # -----------------------------------------------------
    # FARMER MESSAGE
    # -----------------------------------------------------

    if role == "user":

        st.html(f"""
        <div class="whatsapp-chat user-row">

            <div class="user-bubble">

                <div class="sender-name">
                    You
                </div>

                <div class="message-text">
                    {safe_content}
                </div>

            </div>

        </div>
        """)

    # -----------------------------------------------------
    # BOT MESSAGE
    # -----------------------------------------------------

    else:

        st.html(f"""
        <div class="whatsapp-chat bot-row">

            <div class="bot-bubble">

                <div class="sender-name">
                    🌱 Shamba Advisor
                </div>

                <div class="message-text">
                    {safe_content}
                </div>

            </div>

        </div>
        """)


# =========================================================
# BUILD CONVERSATION CONTEXT
# =========================================================

def build_conversation_context(history, current_message):
    """
    Creates a compact conversation context for Call 1.

    The database remains the permanent record.

    This function simply gives Call 1 enough previous
    conversation context to understand follow-up questions
    such as:

        Farmer:
        "I want to plant maize."

        Bot:
        "What area are you farming in?"

        Farmer:
        "Nakuru."

    The second message should NOT be interpreted as a
    completely independent conversation.
    """

    if not history:
        return current_message.strip()

    context_lines = []

    # Keep the context reasonably small.
    # The database still contains the complete history.
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

        context_lines.append(
            f"{speaker}: {content}"
        )

    previous_context = "\n".join(
        context_lines
    )

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

    # =====================================================
    # LOGO
    # =====================================================

    st.html("""
    <div style="
        text-align:center;
        font-size:42px;
        margin-bottom:5px;
    ">
        🌱
    </div>
    """)

    # =====================================================
    # TITLE
    # =====================================================

    st.html("""
    <div style="
        text-align:center;
        font-size:20px;
        font-weight:700;
        color:#075e54;
        margin-bottom:15px;
    ">
        Shamba Advisor
    </div>
    """)

    # =====================================================
    # FARMER NAME
    # =====================================================

    safe_name = html.escape(
        str(
            st.session_state.farmer_name
            or "Farmer"
        )
    )

    st.html(f"""
    <div style="
        background:#ffffff;
        color:#111111;
        padding:12px;
        border-radius:10px;
        margin-bottom:15px;
        border:1px solid #dddddd;
    ">
        👋 <strong>{safe_name}</strong>
    </div>
    """)

    # =====================================================
    # NEW CHAT
    # =====================================================

    if st.button(
        "＋ New chat",
        use_container_width=True,
    ):

        st.session_state.chat_id = None

        st.session_state.pending_analysis = None

        st.session_state.force_new_chat = True

        st.session_state.messages = []

        st.rerun()

    # =====================================================
    # RECENT CHATS
    # =====================================================

    st.divider()

    st.subheader("💬 Recent chats")

    try:

        recent = get_recent_chats(
            farmer_id
        )

    except Exception:

        recent = []

        st.warning(
            "Unable to load recent chats."
        )

    if not recent:

        st.caption(
            "No chats yet — ask a question to start one."
        )

    else:

        for chat in recent:

            label = (
                chat.get("title")
                or "Untitled chat"
            )

            label = str(label)[:45]

            if st.button(
                label,
                key=f"chat_{chat['id']}",
                use_container_width=True,
            ):

                st.session_state.chat_id = (
                    chat["id"]
                )

                st.session_state.pending_analysis = None

                st.session_state.force_new_chat = False

                st.session_state.messages = []

                st.rerun()


# =========================================================
# MAIN WHATSAPP HEADER
# =========================================================

st.html("""
<div class="whatsapp-header">

    <div class="header-title">
        🌱 Shamba Advisor
    </div>

    <div class="header-subtitle">
        AI farming assistant • Online
    </div>

</div>
""")


# =========================================================
# LOAD EXISTING CHAT HISTORY
# =========================================================

if st.session_state.chat_id:

    try:

        history = get_chat_history(
            st.session_state.chat_id
        )

        for msg in history:

            show_message(
                msg.get("role"),
                msg.get("content"),
            )

    except Exception as e:

        history = []

        st.error(
            "Unable to load this conversation."
        )

        st.exception(e)

else:

    history = []


# =========================================================
# CALL 2
# =========================================================

def run_call_two(
    analysis: dict,
    selected_cause: str = None,
):
    """
    Run Call 2.

    The generated advice is:

    1. displayed in the chat
    2. saved to Supabase
    3. saved as a report
    4. made available for download
    """

    # -----------------------------------------------------
    # SAFETY CHECK
    # -----------------------------------------------------

    if not st.session_state.chat_id:

        st.error(
            "No active conversation was found."
        )

        return

    # -----------------------------------------------------
    # CALL 2
    # -----------------------------------------------------

    with st.spinner(
        "🌱 Preparing your farming advice..."
    ):

        try:

            advice = generate_action_plan(
                analysis,
                selected_cause=selected_cause,
            )

        except Exception as e:

            st.error(
                "I couldn't generate the farming advice."
            )

            st.exception(e)

            return

    # -----------------------------------------------------
    # NORMALIZE ADVICE
    # -----------------------------------------------------

    if advice is None:

        advice = (
            "I couldn't generate advice right now. "
            "Please try again."
        )

    advice = str(advice)

    # -----------------------------------------------------
    # DISPLAY BOT MESSAGE
    # -----------------------------------------------------

    show_message(
        "assistant",
        advice,
    )

    # -----------------------------------------------------
    # SAVE BOT MESSAGE
    # -----------------------------------------------------

    try:

        save_message(
            st.session_state.chat_id,
            "assistant",
            advice,
        )

    except Exception as e:

        st.warning(
            "The advice was generated, "
            "but I couldn't save it to the conversation."
        )

        st.exception(e)

    # -----------------------------------------------------
    # SAVE REPORT
    # -----------------------------------------------------

    try:

        crop = analysis.get("crop")

        saved_path = save_report(
            st.session_state.farmer_name,
            crop,
            advice,
        )

        saved_path = Path(
            saved_path
        )

        # -------------------------------------------------
        # DOWNLOAD BUTTON
        # -------------------------------------------------

        if saved_path.exists():

            with open(
                saved_path,
                "rb",
            ) as report_file:

                st.download_button(
                    label="📥 Download this report",
                    data=report_file,
                    file_name=saved_path.name,
                    mime="text/plain",
                    key=(
                        f"download_"
                        f"{st.session_state.chat_id}_"
                        f"{saved_path.name}"
                    ),
                )

    except Exception as e:

        st.warning(
            "The advice was generated, "
            "but the report could not be saved."
        )

        st.exception(e)


# =========================================================
# PENDING POSSIBLE CAUSE
# =========================================================

if st.session_state.pending_analysis:

    analysis = (
        st.session_state.pending_analysis
    )

    possible_causes = (
        analysis.get("possible_causes")
        or []
    )

    # -----------------------------------------------------
    # BOT QUESTION
    # -----------------------------------------------------

    show_message(
        "assistant",
        "Here are the most likely causes — "
        "which matches what you're seeing?",
    )

    # -----------------------------------------------------
    # CAUSE BUTTONS
    # -----------------------------------------------------

    selected_cause = None

    if possible_causes:

        cols = st.columns(
            len(possible_causes)
        )

        for i, cause in enumerate(
            possible_causes
        ):

            if cols[i].button(
                str(cause),
                key=f"cause_{i}",
                use_container_width=True,
            ):

                selected_cause = str(
                    cause
                )

    # -----------------------------------------------------
    # CUSTOM CAUSE
    # -----------------------------------------------------

    other_input = st.text_input(
        "Or describe it in your own words:",
        key="other_cause_input",
        placeholder="Describe what you are seeing...",
    )

    if st.button(
        "Use my own description",
        key="other_cause_btn",
        use_container_width=True,
    ):

        if other_input.strip():

            selected_cause = (
                other_input.strip()
            )

        else:

            st.warning(
                "Please describe the problem first."
            )

    # -----------------------------------------------------
    # RUN CALL 2
    # -----------------------------------------------------

    if selected_cause:

        # Clear before generating.
        # This prevents duplicate processing
        # during Streamlit reruns.

        st.session_state.pending_analysis = None

        run_call_two(
            analysis,
            selected_cause=selected_cause,
        )

    else:

        # Wait until farmer selects a cause.
        st.stop()


# =========================================================
# CHAT INPUT
# =========================================================

user_message = st.chat_input(
    "Ask about planting, pests, irrigation, harvest..."
)


# =========================================================
# PROCESS NEW FARMER MESSAGE
# =========================================================

if user_message:

    user_message = user_message.strip()

    # -----------------------------------------------------
    # EMPTY MESSAGE
    # -----------------------------------------------------

    if not user_message:

        st.warning(
            "Please type a question."
        )

        st.stop()

    # -----------------------------------------------------
    # CREATE CHAT IF NECESSARY
    # -----------------------------------------------------

    if st.session_state.chat_id is None:

        try:

            st.session_state.chat_id = (
                create_chat(
                    farmer_id,
                    title=user_message[:40],
                )
            )

        except Exception as e:

            st.error(
                "I couldn't create the conversation."
            )

            st.exception(e)

            st.stop()

    # -----------------------------------------------------
    # LOAD PREVIOUS HISTORY BEFORE SAVING
    # CURRENT MESSAGE
    # -----------------------------------------------------

    previous_history = []

    try:

        previous_history = get_chat_history(
            st.session_state.chat_id
        )

    except Exception:

        previous_history = []

    # -----------------------------------------------------
    # SHOW FARMER MESSAGE
    # -----------------------------------------------------

    show_message(
        "user",
        user_message,
    )

    # -----------------------------------------------------
    # SAVE FARMER MESSAGE
    # -----------------------------------------------------

    try:

        save_message(
            st.session_state.chat_id,
            "user",
            user_message,
        )

    except Exception as e:

        st.error(
            "Your message could not be saved."
        )

        st.exception(e)

        st.stop()

    # =====================================================
    # BUILD MEMORY CONTEXT
    # =====================================================

    contextual_message = (
        build_conversation_context(
            previous_history,
            user_message,
        )
    )

    # =====================================================
    # CALL 1
    # =====================================================

    with st.spinner(
        "🌱 Understanding your question..."
    ):

        try:

            analysis = get_full_analysis(
                contextual_message
            )

        except Exception as e:

            st.error(
                "I couldn't analyze your question."
            )

            st.exception(e)

            st.stop()

    # =====================================================
    # CHECK FOR POSSIBLE CAUSES
    # =====================================================

    possible_causes = (
        analysis.get("possible_causes")
        or []
    )

    if possible_causes:

        # -------------------------------------------------
        # Store analysis temporarily.
        #
        # On rerun, the chat history is loaded from
        # Supabase and the cause-selection UI appears.
        # -------------------------------------------------

        st.session_state.pending_analysis = (
            analysis
        )

        st.rerun()

    # =====================================================
    # NORMAL CALL 2
    # =====================================================

    else:

        run_call_two(
            analysis
        )