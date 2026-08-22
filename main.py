from call1_analysis import analyze_farmer_message
from call2 import generate_action_plan
from save_report import save_report

from farmer_profile import (
    create_database,
    get_or_create_farmer,
    update_farmer_profile
)


# =========================================================
# HEADER
# =========================================================

def show_header():

    print()
    print("=" * 60)
    print("                 SHAMBA ADVISOR")
    print("=" * 60)
    print("Your AI farming assistant")
    print()

    print("Ask about:")

    print("- Planting")
    print("- Pests and diseases")
    print("- Irrigation")
    print("- Harvesting")
    print("- Storage")
    print("- General farming")

    print()

    print("Type 'exit' to quit.")

    print("=" * 60)
    print()


# =========================================================
# MAIN PROGRAM
# =========================================================

def main():

    # -----------------------------------------------------
    # CREATE DATABASE
    # -----------------------------------------------------

    create_database()


    # -----------------------------------------------------
    # SHOW HEADER
    # -----------------------------------------------------

    show_header()


    # -----------------------------------------------------
    # FARMER NAME
    # -----------------------------------------------------

    farmer_name = input(
        "Farmer name: "
    ).strip()


    if not farmer_name:

        farmer_name = "Farmer"


    # -----------------------------------------------------
    # LOAD FARMER PROFILE
    # -----------------------------------------------------

    farmer_profile = get_or_create_farmer(
        farmer_name
    )


    print()


    if farmer_profile.get("location"):

        print(
            f"Welcome back, {farmer_name}!"
        )

        print(
            f"I remember your farm is in "
            f"{farmer_profile['location']}."
        )


    else:

        print(
            f"Welcome to Shamba Advisor, "
            f"{farmer_name}!"
        )


    # -----------------------------------------------------
    # CURRENT CONVERSATION
    # -----------------------------------------------------

    conversation = ""


    # =====================================================
    # CHAT LOOP
    # =====================================================

    while True:

        print()


        farmer_message = input(
            "You: "
        ).strip()


        # =================================================
        # EXIT
        # =================================================

        if farmer_message.lower() == "exit":

            print()

            print(
                "Thank you for using Shamba Advisor."
            )

            print(
                "Goodbye!"
            )

            break


        # =================================================
        # EMPTY MESSAGE
        # =================================================

        if not farmer_message:

            print(
                "Please enter a farming question."
            )

            continue


        # =================================================
        # ADD FARMER MESSAGE TO CONVERSATION
        # =================================================

        if conversation:

            conversation += (
                f"\nFarmer: {farmer_message}"
            )

        else:

            conversation = (
                f"Farmer: {farmer_message}"
            )


        # =================================================
        # CALL 1 — ANALYSIS
        # =================================================

        print()

        print(
            "Analyzing your question..."
        )


        analysis = analyze_farmer_message(

            conversation,

            farmer_profile
        )


        # =================================================
        # OFF-TOPIC CHECK
        # =================================================

        if analysis.get(
            "intent"
        ) == "off_topic":

            print()

            print(
                "Shamba Advisor:"
            )

            print(
                "I'm here to help with farming "
                "questions such as planting, pests, "
                "irrigation, harvesting, and storage."
            )

            print(
                "Please ask me a farming-related "
                "question."
            )


            # Start a fresh question

            conversation = ""


            continue


        # =================================================
        # CLARIFICATION CHECK
        # =================================================

        if analysis.get(
            "clarification_required"
        ):

            question = analysis.get(
                "clarification_question"
            )


            print()

            print(
                "Shamba Advisor:"
            )

            print(
                question
            )


            # Remember the bot's question

            conversation += (
                f"\nShamba Advisor: {question}"
            )


            continue


        # =================================================
        # UPDATE FARMER PROFILE
        # =================================================

        farmer_profile = update_farmer_profile(

            farmer_name,

            location=analysis.get(
                "location"
            ),

            farm_size=analysis.get(
                "farm_size"
            ),

            crop=analysis.get(
                "crop"
            )
        )


        # =================================================
        # CALL 2 — ACTION PLAN
        # =================================================

        print()

        print(
            "Creating your action plan..."
        )


        action_plan = generate_action_plan(
            analysis
        )


        # =================================================
        # CHECK THAT A PLAN WAS ACTUALLY CREATED
        # =================================================

        if not action_plan:

            print()

            print(
                "Shamba Advisor:"
            )

            print(
                "I need a little more information "
                "before I can create a farming plan."
            )

            continue


        # =================================================
        # DISPLAY ACTION PLAN
        # =================================================

        print()

        print(
            "=" * 60
        )

        print(
            "                  ACTION PLAN"
        )

        print(
            "=" * 60
        )

        print()

        print(
            action_plan
        )

        print()

        print(
            "=" * 60
        )


        # =================================================
        # SAVE REPORT
        # =================================================

        crop = analysis.get(
            "crop"
        )


        if not crop:

            crop = "general_farming"


        filepath = save_report(

            farmer_name,

            crop,

            action_plan
        )


        print()

        print(
            f"Report saved to: {filepath}"
        )


        # =================================================
        # RESET CONVERSATION
        # =================================================

        conversation = ""


# =========================================================
# START PROGRAM
# =========================================================

if __name__ == "__main__":

    main()