import os

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

You are Shamba Advisor's action-plan writer.

You receive structured farming information from Call 1.

Your job is to turn that information into a practical
farming action plan for the farmer.

Call 1 has already analyzed the farmer's question.

Do NOT re-analyze the question.

Do NOT answer non-farming questions.

Do NOT invent missing information.

Do NOT invent weather information.

Do NOT invent pesticide names or chemical doses.

Only use information provided by Call 1.


FARMING AREAS:

The farmer may ask about:

- Land preparation
- Planting
- Pests
- Diseases
- Irrigation
- Harvesting
- Storage
- General farming


PLAN REQUIREMENTS:

1. Use simple language.

2. Give practical actions the farmer can actually follow.

3. Prefer affordable and locally available solutions.

4. Do not recommend expensive products unnecessarily.

5. If chemicals are relevant, tell the farmer to follow
   the product label and local agricultural guidance.

6. Tell farmers to keep people and animals away from
   areas being sprayed.

7. Focus on what the farmer should DO.

8. Use a 2-4 week plan when appropriate.

9. Do not make the response unnecessarily long.


OUTPUT FORMAT:

Start with a short introduction.

Then use:

Week 1:
- Action
- Action
- Action

Week 2:
- Action
- Action

Week 3:
- Action
- Action

Week 4:
- Action
- Action

Only include weeks that are useful.

Finish with:

Monitoring tip:
- One short monitoring instruction.

"""


# =========================================================
# GENERATE ACTION PLAN
# =========================================================

def generate_action_plan(analysis):
    """
    Generate a farming action plan from Call 1's analysis.
    """

    # -----------------------------------------------------
    # SAFETY CHECK
    # -----------------------------------------------------

    intent = analysis.get("intent")


    # Do not create plans for off-topic questions.

    if intent == "off_topic":

        return None


    # Do not create a plan if Call 1 needs more information.

    if analysis.get(
        "clarification_required"
    ):

        return None


    # -----------------------------------------------------
    # PREPARE CALL 1 INFORMATION
    # -----------------------------------------------------

    context = f"""

FARMER'S FARMING REQUEST

Intent:
{analysis.get('intent')}

Farmer's goal:
{analysis.get('user_goal')}

Crop:
{analysis.get('crop')}

Location:
{analysis.get('location')}

Farm size:
{analysis.get('farm_size')}

Growth stage:
{analysis.get('growth_stage')}

Symptoms:
{analysis.get('symptoms')}

Timeline:
{analysis.get('timeline')}

Weather required:
{analysis.get('weather_required')}

"""


    # -----------------------------------------------------
    # CALL OPENAI
    # -----------------------------------------------------

    try:

        response = client.responses.create(

            model=MODEL_NAME,

            instructions=SYSTEM_PROMPT,

            input=context
        )


        # -------------------------------------------------
        # GET ACTION PLAN
        # -------------------------------------------------

        action_plan = response.output_text.strip()


        return action_plan


    except Exception as error:

        print()
        print(
            f"Call 2 error: {error}"
        )


        return (
            "I'm sorry, I could not create the "
            "action plan right now. Please try again."
        )


# =========================================================
# TEST CALL 2 DIRECTLY
# =========================================================

if __name__ == "__main__":

    sample_analysis = {

        "intent": "planting",

        "user_goal": (
            "Find out what crop to plant "
            "during this season."
        ),

        "crop": "maize",

        "location": "Nairobi",

        "farm_size": "2 acres",

        "growth_stage": None,

        "symptoms": [],

        "timeline": None,

        "clarification_required": False,

        "clarification_question": None,

        "weather_required": True
    }


    print()
    print("=" * 60)
    print("             CALL 2 TEST")
    print("=" * 60)
    print()


    plan = generate_action_plan(
        sample_analysis
    )


    print(plan)

    print()