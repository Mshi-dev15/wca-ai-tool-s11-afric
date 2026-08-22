"""
Call 2 — Action Plan Generation
--------------------------------
Takes Call 1's structured analysis (and weather, if available) and
writes a practical, low-cost action plan the farmer can follow.

This file NEVER re-analyzes the farmer's message — that's Call 1's
job. This only writes the advice.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODEL_NAME = "gpt-5.6-luna"

SYSTEM_PROMPT = """
ROLE:
You are Shamba Advisor's action-plan writer. You turn analysis into
a simple, practical plan for a Kenyan smallholder farmer, who may
have limited formal literacy.

TASK:
Using the structured analysis provided (intent, crop, location,
symptoms, weather if available), write a clear, step-by-step action
plan the farmer can follow.

CONTEXT:
The farmer may not have access to expensive inputs. Weather data may
or may not be available — only reference it if it is marked as
available. Match the plan to whichever stage of the farming cycle
the intent falls under (land prep, planting, pest/disease,
irrigation, harvest, storage).

CONSTRAINTS:
- Plain, simple language, short sentences.
- Structure the plan week-by-week (Week 1, Week 2, etc.) — not just
  a generic numbered list. Most plans should span 2-4 weeks.
- Prioritize free or cheap, locally available solutions before
  anything that costs money.
- No jargon.
- Keep it to roughly 150-250 words.
- Don't repeat the diagnosis back to the farmer — focus on action.

OUTPUT FORMAT:
Plain text only (not JSON): one short intro line, then the plan
broken into "Week 1: ...", "Week 2: ...", etc., ending with one
short monitoring tip.
"""


def generate_action_plan(analysis: dict, selected_cause: str = None) -> str:
    """
    Takes Call 1's analysis dict and returns a plain-text action plan.
    If the farmer selected a specific cause (from possible_causes,
    or typed their own), the plan focuses on addressing that cause
    specifically rather than the general symptom picture.
    Always returns a usable string — never raises — so the app never crashes.
    """

    # --- Skip the API call entirely for cases that don't need advice ---
    if analysis.get("intent") == "off_topic":
        return "I'm here to help with farming questions — land prep, planting, pests, irrigation, and harvest. What would you like help with?"

    if analysis.get("clarification_required"):
        question = analysis.get("clarification_question") or "Could you tell me a bit more about what you need?"
        return question

    # --- Build the context block Call 2 reasons over ---
    context_lines = [
        f"Intent: {analysis.get('intent')}",
        f"Farmer's goal: {analysis.get('user_goal')}",
        f"Crop: {analysis.get('crop')}",
        f"Location: {analysis.get('location')}",
        f"Farm size: {analysis.get('farm_size')}",
        f"Growth stage: {analysis.get('growth_stage')}",
        f"Symptoms: {analysis.get('symptoms')}",
        f"Timeline: {analysis.get('timeline')}",
    ]

    weather = analysis.get("weather")
    if weather and weather.get("available"):
        context_lines.append(
            f"Current weather in {weather.get('location')}: "
            f"{weather.get('temperature_c')}°C, "
            f"{weather.get('humidity_percent')}% humidity, "
            f"{weather.get('precipitation_mm')}mm precipitation."
        )

    if selected_cause:
        context_lines.append(
            f"The farmer has confirmed the cause is: {selected_cause}. "
            f"Build the plan specifically around addressing this cause."
        )

    user_content = "\n".join(context_lines)

    # --- Error case: the API call fails — retry once, then fall back ---
    response = None
    last_error = None

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
            )
            break
        except Exception as api_error:
            last_error = api_error

    if response is None:
        return (
            "Sorry, I'm temporarily unable to generate advice right now. "
            "Please try again in a moment."
        )

    return response.choices[0].message.content


# --- Quick manual test from the command line ---
if __name__ == "__main__":
    # A sample analysis dict, as if it came straight from Call 1
    sample_analysis = {
        "intent": "pest_disease",
        "user_goal": "Find out what to do about holes in maize leaves",
        "crop": "maize",
        "location": "Kiserian",
        "farm_size": None,
        "growth_stage": None,
        "symptoms": ["Holes in the maize leaves"],
        "timeline": None,
        "clarification_required": False,
        "clarification_question": None,
        "weather_required": False,
        "weather": None,
    }

    plan = generate_action_plan(sample_analysis)
    print("Call 2 output:\n")
    print(plan)