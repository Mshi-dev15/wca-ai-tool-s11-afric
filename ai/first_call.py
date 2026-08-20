"""
Call 1 — Intake Analysis
--------------------------------
Reads the farmer's raw message and turns it into structured JSON
that Call 2 (the advice-generation step) can act on.

This file NEVER generates farming advice itself — only analysis.
"""

import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# --- Setup: load API key securely from .env, never hardcoded ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Cheapest suitable model tier for this task — confirm the exact
# model string available on your account before running.
MODEL_NAME = "gpt-5.6-luna"

# --- The R-T-C-C-O system prompt for Call 1 ---
SYSTEM_PROMPT = """
ROLE:
You are Shamba Advisor's intake analyst. You understand small-scale
Kenyan farming across the whole farming cycle: land preparation,
planting, crop care, pests and disease, irrigation, harvest, and
storage. You are used to messages from farmers with limited formal
literacy — spelling mistakes, mixed English/Swahili, and incomplete
sentences are all normal and never a reason to reject a message.

TASK:
Read the farmer's message (and any quick-option they selected) and:
1. Identify their intent.
2. Extract whatever details they've given.
3. Produce a lightly cleaned-up version of their message.
4. Flag if the message is not actually about farming at all.

CONTEXT:
This is the analysis step only — you never give farming advice
yourself, that happens in a separate step. Interpret the farmer's
meaning generously even if spelling or grammar is imperfect.

CONSTRAINTS:
- Never invent details the farmer didn't give. Use null instead.
- If the message is unrelated to farming (jokes, testing you, random
  chat), set intent to "off_topic" — do not force it into a farming
  category.
- If it's farming-related but too vague to act on, set
  clarification_required to true with one short clarification_question.
- corrected_message must stay faithful to the original meaning — fix
  spelling/grammar only, never add new information.
- Set weather_required to true only if current or recent weather
  conditions would genuinely change the advice (e.g. planting timing,
  irrigation, disease risk from rain). Routine questions (storage,
  general crop info) should be false.

OUTPUT FORMAT:
Reply ONLY with valid JSON, no extra commentary, matching exactly:
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
  "weather_required": true or false
}
"""


def analyze_message(farmer_message: str, quick_option: str = None) -> dict:
    """
    Runs Call 1 on a single farmer message.
    Returns a dict matching the JSON contract above.
    Always returns a usable dict — never raises — so the app never crashes.
    """

    # --- Error case 1: empty input ---
    if not farmer_message or not farmer_message.strip():
        return _fallback_response(
            error="empty_input",
            clarification_question="Please tell me what farming help you need today.",
        )

    # Combine the quick-option context (if any) with the free-text message
    user_content = farmer_message.strip()
    if quick_option:
        user_content = f"[Quick option selected: {quick_option}] {user_content}"

    # --- Error case 2: the API call itself fails (no internet, bad key, etc.) ---
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            response_format={"type": "json_object"},  # forces valid JSON output
            
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
        )
    except Exception as api_error:
        return _fallback_response(
            error=f"api_call_failed: {api_error}",
            clarification_question="I'm having trouble connecting right now. Please try again in a moment.",
        )

    raw_text = response.choices[0].message.content

    # --- Error case 3: model returns malformed JSON (rare, since JSON mode
    # is enabled above, but we still guard against it) ---
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        return _fallback_response(
            error="invalid_json_from_model",
            clarification_question="Sorry, I didn't quite understand that. Could you rephrase?",
        )

    return data


def _fallback_response(error: str, clarification_question: str) -> dict:
    """
    A single, consistent shape returned whenever something goes wrong,
    so Call 2 and the UI never have to guess what fields exist.
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
        "error": error,  # extra field, not part of the strict contract,
                          # useful for logging/debugging during testing
    }


def get_full_analysis(farmer_message: str, quick_option: str = None) -> dict:
    """
    Runs Call 1, then attaches live weather data if the analysis says
    it's relevant and a location was given.

    This is the function Call 2 (the partner's code) should actually
    call — not analyze_message() directly — since this is the fully
    enriched handoff, weather included when relevant.
    """
    from weather.open_meteo import get_weather  # local import avoids a
                                                  # hard dependency if
                                                  # weather isn't needed

    analysis = analyze_message(farmer_message, quick_option)

    needs_weather = analysis.get("weather_required") and analysis.get("location")
    analysis["weather"] = get_weather(analysis["location"]) if needs_weather else None

    return analysis


# --- Quick manual test from the command line ---
if __name__ == "__main__":
    print("Shamba Advisor — Call 1 test\n")
    test_message = input("Type a farmer message to test: ")
    result = get_full_analysis(test_message)
    print("\nCall 1 + weather output:")
    print(json.dumps(result, indent=2))