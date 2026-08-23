"""
Call 1 — Intake Analysis
--------------------------------
Reads the farmer's current message together with the previous
conversation history and turns it into structured JSON that
Call 2 can act on.

This file NEVER generates farming advice itself — only analysis.

Conversation memory:
- Previous messages are supplied by the Streamlit app.
- The model uses previous messages to understand references such as:
    "What should I plant?"
    "How often should I water it?"
    "What about the yellow leaves?"
- Known farmer details from previous messages can be carried forward.
"""

import os
import json

from openai import OpenAI
from dotenv import load_dotenv


# =========================================================
# SETUP
# =========================================================

load_dotenv()

# Check Streamlit Cloud Secrets first, then fall back to local .env
api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)


# =========================================================
# MODEL
# =========================================================

MODEL_NAME = "gpt-5.6-luna"


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """
ROLE:
You are Shamba Advisor's intake analyst.

You understand small-scale Kenyan farming across the whole
farming cycle:

- land preparation
- planting
- crop selection
- crop care
- pests and diseases
- fertilizer and soil
- irrigation
- weather
- harvesting
- storage

You are used to messages from farmers with limited formal
literacy. Spelling mistakes, mixed English/Swahili, shorthand,
and incomplete sentences are normal and must not be treated
as errors.

============================================================
MOST IMPORTANT RULE: CONVERSATION MEMORY
============================================================

This is an ONGOING conversation with a farmer.

The farmer's current message must NOT automatically be treated
as a completely new conversation.

Use the previous conversation to understand references and
follow-up questions.

For example:

Previous conversation:
Farmer: Nakuru, 3 ha
Shamba Advisor: What farming help do you need?
Farmer: What should I plant?

The current question:

"What should I plant?"

must be understood as:

"What should I plant on my 3-hectare farm in Nakuru?"

Do NOT ask the farmer to repeat information that is already
available in the conversation.

Another example:

Previous:
Farmer: I planted maize two weeks ago.
Farmer: The leaves are turning yellow.

Current:
"Should I add fertilizer?"

Understand that "the crop" and the situation refer to the
maize already discussed.

Another example:

Previous:
Farmer: I have tomatoes.
Farmer: There are spots on the leaves.

Current:
"What should I spray?"

Understand that "I" and "the crop" refer to the same farmer
and tomato crop discussed previously.

============================================================
WHAT COUNTS AS CONVERSATION CONTEXT
============================================================

Previous messages may contain important information such as:

- farmer location
- farm size
- crops
- crop variety
- growth stage
- planting date
- symptoms
- weather conditions
- soil information
- irrigation method
- pest/disease observations
- previous questions
- previous answers
- farmer goals
- timelines

Use these details when interpreting the current message.

Previous conversation information is NOT considered invented
information. It is established context.

============================================================
TASK
============================================================

Read:

1. The previous conversation, if available.
2. The farmer's current message.
3. Any quick option selected by the farmer.

Then:

1. Identify the farmer's current intent.
2. Understand the current user goal.
3. Extract relevant farming details.
4. Carry forward relevant known details from the conversation.
5. Resolve references such as:
   - it
   - this
   - that
   - there
   - my farm
   - my crop
   - the leaves
   - the plants
   - them
6. Produce a lightly cleaned-up version of the current message.
7. Determine whether current/recent weather is genuinely needed.
8. Flag if the message is unrelated to farming.
9. If the farming question is too vague to act on, request
   clarification.

IMPORTANT:

The analysis describes the farmer's CURRENT request while
using previous conversation as context.

Do not generate farming advice.

Call 2 is responsible for advice.

============================================================
CONSTRAINTS
============================================================

- Never invent details.
- Details explicitly established earlier in the conversation
  may be used as known context.
- If a detail has never been provided, use null.
- Do not guess the farmer's location.
- Do not guess farm size.
- Do not guess a crop.
- Do not guess symptoms.
- Do not guess dates.
- Do not guess weather.
- Do not give farming advice.
- Do not recommend products.
- Do not diagnose beyond identifying possible causes.
- Do not force unrelated messages into farming categories.

If the message is unrelated to farming:

    intent = "off_topic"

If the message is farming-related but genuinely too vague
to act on:

    clarification_required = true

and provide ONE short clarification question.

If enough information exists in the current conversation,
do not ask for information that has already been provided.

============================================================
CORRECTED MESSAGE
============================================================

corrected_message must represent the farmer's CURRENT message.

Fix spelling and grammar only.

Do NOT add information from previous messages into
corrected_message.

Example:

Previous:
Farmer: Nakuru, 3 ha

Current:
"What should i plant"

corrected_message:

"What should I plant?"

NOT:

"What should I plant on my 3-hectare farm in Nakuru?"

The contextual information belongs in the structured fields,
not in corrected_message.

============================================================
WEATHER
============================================================

Set weather_required to true ONLY when current or recent
weather would genuinely change the response.

Examples where weather may be required:

- planting timing
- rain-dependent planting
- irrigation decisions
- rainfall concerns
- drought
- flooding
- disease risk related to rain/humidity
- frost or extreme temperatures
- current weather affecting farm operations

Examples where weather is usually NOT required:

- general crop information
- crop varieties
- storage
- general fertilizer information
- general pest information
- harvest information that does not depend on current weather

If weather is required and a location is known from the current
message OR previous conversation, use that location.

If weather is required but no location is known, do not invent one.

============================================================
POSSIBLE CAUSES
============================================================

If the intent is:

- pest_disease
OR
- fertilizer_soil

and there are multiple plausible causes for what the farmer
describes:

list 2-4 short, distinct possible causes.

Examples:

- Fungal disease
- Nitrogen deficiency
- Overwatering
- Pest damage

If there is only one clear cause, leave possible_causes empty.

If the question does not involve diagnosing a cause,
leave possible_causes empty.

============================================================
OUTPUT FORMAT
============================================================

Reply ONLY with valid JSON.

No markdown.

No explanation.

Use exactly this structure:

{
  "intent": "crop_selection | pest_disease | fertilizer_soil | irrigation_weather | harvest_storage | general | off_topic",
  "user_goal": string or null,
  "location": string or null,
  "crop": string or null,
  "farm_size": string or null,
  "growth_stage": string or null,
  "symptoms": [array of strings, empty if none],
  "timeline": string or null,
  "clarification_required": true or false,
  "clarification_question": string or null,
  "corrected_message": string,
  "weather_required": true or false,
  "possible_causes": [array of strings, empty if not applicable]
}

============================================================
IMPORTANT FIELD RULE
============================================================

The structured fields should represent information that is
relevant to understanding the CURRENT request, including
relevant information already established in the conversation.

For example:

Previous:
"Nakuru, 3 ha"

Current:
"What should I plant?"

A good analysis may contain:

{
  "intent": "crop_selection",
  "user_goal": "Choose crops to plant",
  "location": "Nakuru",
  "crop": null,
  "farm_size": "3 ha"
}

Do not ask the farmer for location or farm size again merely
because they were provided in an earlier message.
"""


# =========================================================
# FORMAT CONVERSATION HISTORY
# =========================================================

def _build_conversation_context(
    conversation_history,
    current_message,
):
    """
    Convert database chat history into a readable conversation
    for the model.

    The function also prevents the current user message from
    being duplicated if app.py saved it before calling Call 1.
    """

    if not conversation_history:
        return "(No previous conversation.)"

    lines = []

    current_normalized = (
        current_message.strip().lower()
        if current_message
        else ""
    )

    for message in conversation_history:

        role = message.get("role")
        content = message.get("content")

        if not content:
            continue

        content = str(content).strip()

        if not content:
            continue

        if (
            role == "user"
            and content.lower() == current_normalized
        ):
            continue

        if role == "user":
            lines.append(
                f"Farmer: {content}"
            )

        elif role == "assistant":
            lines.append(
                f"Shamba Advisor: {content}"
            )

    if not lines:
        return "(No previous conversation.)"

    return "\n".join(lines)


# =========================================================
# CALL 1 ANALYSIS
# =========================================================

def analyze_message(
    farmer_message: str,
    quick_option: str = None,
    conversation_history=None,
) -> dict:
    """
    Runs Call 1 on the farmer's current message plus the
    previous conversation.

    Returns a dict matching the JSON contract.

    Always returns a usable dict and never intentionally raises
    an exception to the Streamlit app.
    """

    if not farmer_message or not farmer_message.strip():

        return _fallback_response(
            error="empty_input",
            clarification_question=(
                "Please tell me what farming help you need today."
            ),
        )

    user_content = farmer_message.strip()

    if quick_option:

        user_content = (
            f"[Quick option selected: {quick_option}] "
            f"{user_content}"
        )

    conversation_context = _build_conversation_context(
        conversation_history,
        farmer_message,
    )

    analysis_prompt = f"""
PREVIOUS CONVERSATION
=====================

{conversation_context}


CURRENT FARMER MESSAGE
======================

Farmer:
{user_content}


TASK
====

Analyze the CURRENT farmer message while using the previous
conversation as context.

Remember:

- This is an ongoing conversation.
- Do not treat the current message as a new farmer.
- Carry forward relevant known details.
- Resolve references such as "it", "there", "my farm",
  "the crop", "the leaves", etc.
- Do not ask the farmer to repeat information already known.
- Do not give farming advice.
- Return ONLY the required JSON object.
"""

    response = None
    last_error = None

    for attempt in range(2):

        try:

            response = client.chat.completions.create(
                model=MODEL_NAME,
                response_format={
                    "type": "json_object"
                },
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt,
                    },
                ],
            )

            break

        except Exception as api_error:

            last_error = api_error

    if response is None:

        return _fallback_response(
            error=f"api_call_failed: {last_error}",
            clarification_question=(
                "I'm having trouble connecting right now. "
                "Please try again in a moment."
            ),
        )

    try:

        raw_text = (
            response
            .choices[0]
            .message
            .content
        )

    except Exception as error:

        return _fallback_response(
            error=f"invalid_api_response: {error}",
            clarification_question=(
                "Sorry, I didn't quite understand that. "
                "Could you rephrase?"
            ),
        )

    try:

        data = json.loads(raw_text)

    except (
        json.JSONDecodeError,
        TypeError,
    ):

        return _fallback_response(
            error="invalid_json_from_model",
            clarification_question=(
                "Sorry, I didn't quite understand that. "
                "Could you rephrase?"
            ),
        )

    data = _ensure_analysis_shape(data)

    return data


# =========================================================
# ENSURE ANALYSIS SHAPE
# =========================================================

def _ensure_analysis_shape(data: dict) -> dict:
    """
    Makes sure Call 1 always returns the fields expected by
    the rest of the application.
    """

    if not isinstance(data, dict):

        return _fallback_response(
            error="model_returned_non_dict",
            clarification_question=(
                "Sorry, I didn't quite understand that. "
                "Could you rephrase?"
            ),
        )

    defaults = {
        "intent": "general",
        "user_goal": None,
        "location": None,
        "crop": None,
        "farm_size": None,
        "growth_stage": None,
        "symptoms": [],
        "timeline": None,
        "clarification_required": False,
        "clarification_question": None,
        "corrected_message": "",
        "weather_required": False,
        "possible_causes": [],
    }

    for key, default_value in defaults.items():

        if key not in data:
            data[key] = default_value

    if not isinstance(
        data.get("symptoms"),
        list,
    ):
        data["symptoms"] = []

    if not isinstance(
        data.get("possible_causes"),
        list,
    ):
        data["possible_causes"] = []

    return data


# =========================================================
# FALLBACK RESPONSE
# =========================================================

def _fallback_response(
    error: str,
    clarification_question: str,
) -> dict:
    """
    Consistent response whenever something goes wrong.
    """

    return {
        "intent": "off_topic",
        "user_goal": None,
        "location": None,
        "crop": None,
        "farm_size": None,
        "growth_stage": None,
        "symptoms": [],
        "timeline": None,
        "clarification_required": True,
        "clarification_question": clarification_question,
        "corrected_message": "",
        "weather_required": False,
        "possible_causes": [],
        "error": error,
        "weather": None,
    }


# =========================================================
# FULL ANALYSIS + WEATHER
# =========================================================

def get_full_analysis(
    farmer_message: str,
    quick_option: str = None,
    conversation_history=None,
) -> dict:
    """
    Runs Call 1 using the current farmer message plus
    conversation history.

    Then attaches live weather data if:

    1. weather_required is true
    2. a location is known

    This is the function that app.py should call.
    """

    analysis = analyze_message(
        farmer_message=farmer_message,
        quick_option=quick_option,
        conversation_history=conversation_history,
    )

    needs_weather = (
        analysis.get("weather_required")
        and analysis.get("location")
    )

    if needs_weather:

        try:

            from weather.open_meteo import get_weather

            analysis["weather"] = get_weather(
                analysis["location"]
            )

        except Exception as weather_error:

            analysis["weather"] = None

            analysis["weather_error"] = str(
                weather_error
            )

    else:

        analysis["weather"] = None

    return analysis


# =========================================================
# COMMAND-LINE TEST — maintains conversation memory across turns
# =========================================================

if __name__ == "__main__":

    print("Shamba Advisor — Call 1 conversation-memory test")
    print("Type 'exit' to quit.\n")

    conversation_history = []

    while True:

        test_message = input("You: ").strip()

        if test_message.lower() == "exit":
            print("Goodbye!")
            break

        result = get_full_analysis(
            test_message,
            conversation_history=conversation_history,
        )

        print("\nCall 1 + weather output:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print()

        # --- Update history so the NEXT turn has real context ---
        conversation_history.append(
            {"role": "user", "content": test_message}
        )

        if result.get("clarification_required") and result.get("clarification_question"):
            conversation_history.append(
                {"role": "assistant", "content": result["clarification_question"]}
            )