import os
import json

from openai import OpenAI
from dotenv import load_dotenv


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError(
        "OPENAI_API_KEY is missing. "
        "Make sure your .env file contains your API key."
    )


# =========================================================
# OPENAI CLIENT
# =========================================================

client = OpenAI(
    api_key=API_KEY
)


# =========================================================
# MODEL
# =========================================================

MODEL_NAME = "gpt-5.6-luna"


# =========================================================
# SYSTEM PROMPT
# =========================================================

SYSTEM_PROMPT = """

ROLE:

You are Shamba Advisor's farmer-message analysis assistant.

Your job is to understand a Kenyan smallholder farmer's
conversation and convert it into structured information.

You are NOT responsible for writing the final farming advice.

Call 2 will use your analysis to create the action plan.


CONVERSATION CONTEXT:

The input may contain:

- the farmer's original question
- questions asked by Shamba Advisor
- answers given by the farmer
- information provided earlier in the conversation

Use the entire conversation to understand the farmer's
current farming request.

If the farmer answers a previous clarification question,
use that answer to update the missing information.

Do NOT treat an answer to a clarification question
as a completely new farming problem.


STORED FARMER INFORMATION:

The conversation may also include information saved
from previous sessions.

Use stored farmer information when it is relevant.

If the farmer gives newer information, prefer the
new information.

Do not reveal database information unnecessarily.

Do not invent information that is not in the profile
or conversation.


TASK:

Identify the following information:

- intent
- user_goal
- crop
- location
- farm_size
- growth_stage
- symptoms
- timeline
- clarification_required
- clarification_question
- weather_required


INTENT OPTIONS:

- land_preparation
- planting
- pest_disease
- irrigation
- harvest
- storage
- general_farming
- off_topic


RULES:

1. Do not invent information.

2. If information is missing, use null.

3. If the farmer's conversation is unclear,
   set clarification_required to true.

4. If clarification is required,
   provide ONE simple question.

5. If the farmer has already answered a previous
   clarification question, use that answer.

6. Do not ask the same clarification question again
   if the information has already been provided.

7. Keep information from earlier messages
   in the conversation.

8. Keep the language simple.

9. Return ONLY valid JSON.

10. Do not include markdown.

11. Do not provide farming advice.

12. Do not generate the action plan.

13. Do not guess the farmer's location,
    crop, farm size, or other missing information.

14. If the farmer asks something unrelated to farming,
    use the intent "off_topic".

15. A question about a non-farming product, company,
    person, entertainment, technology, politics,
    cars, or general knowledge is off-topic.

16. If the farmer asks about planting, crops,
    pests, diseases, irrigation, harvesting,
    storage, soil, farm tools, or other farming
    activities, it is farming-related.


OUTPUT FORMAT:

{
    "intent": "...",
    "user_goal": "...",
    "crop": "...",
    "location": "...",
    "farm_size": "...",
    "growth_stage": "...",
    "symptoms": [],
    "timeline": "...",
    "clarification_required": false,
    "clarification_question": null,
    "weather_required": false
}

"""


# =========================================================
# ANALYZE FARMER CONVERSATION
# =========================================================

def analyze_farmer_message(
    message,
    farmer_profile=None
):
    """
    Analyze the farmer's current conversation.

    The analysis also uses the farmer's stored profile
    when one exists.
    """

    try:

        # -------------------------------------------------
        # BUILD FARMER PROFILE CONTEXT
        # -------------------------------------------------

        profile_context = ""

        if farmer_profile:

            profile_context = f"""

STORED FARMER PROFILE:

Name: {farmer_profile.get('name')}
Location: {farmer_profile.get('location')}
Farm size: {farmer_profile.get('farm_size')}
Known crops: {farmer_profile.get('crops')}

Use this stored information when relevant.

If the farmer provides newer information that conflicts
with the stored profile, prefer the farmer's newest
information.

"""


        # -------------------------------------------------
        # COMBINE PROFILE + CONVERSATION
        # -------------------------------------------------

        full_input = f"""

{profile_context}

CURRENT CONVERSATION:

{message}

"""


        # -------------------------------------------------
        # CALL OPENAI
        # -------------------------------------------------

        response = client.responses.create(
            model=MODEL_NAME,
            instructions=SYSTEM_PROMPT,
            input=full_input
        )


        # -------------------------------------------------
        # GET RESPONSE
        # -------------------------------------------------

        result = response.output_text.strip()


        # -------------------------------------------------
        # CONVERT JSON TEXT TO PYTHON DICTIONARY
        # -------------------------------------------------

        analysis = json.loads(result)


        return analysis


    except Exception as error:

        print(f"Call 1 error: {error}")

        return {
            "intent": "general_farming",
            "user_goal": message,
            "crop": None,
            "location": None,
            "farm_size": None,
            "growth_stage": None,
            "symptoms": [],
            "timeline": None,
            "clarification_required": True,
            "clarification_question": (
                "Could you please give me a little more "
                "information about your farming problem?"
            ),
            "weather_required": False
        }


# =========================================================
# MANUAL TEST
# =========================================================

if __name__ == "__main__":

    print()
    print("=" * 50)
    print("        CALL 1 - SHAMBA ADVISOR")
    print("=" * 50)

    message = input(
        "\nEnter a farmer's question: "
    )

    analysis = analyze_farmer_message(
        message
    )

    print()
    print("Call 1 Analysis:")
    print()

    print(
        json.dumps(
            analysis,
            indent=4
        )
    )