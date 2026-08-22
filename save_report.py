import os
import re
from datetime import datetime


OUTPUT_DIR = "outputs"


def make_safe_filename(value, default):
    """
    Convert a name or crop into a safe filename.
    """

    if not value:
        value = default

    value = value.strip().lower()

    value = value.replace(" ", "_")

    value = re.sub(r"[^a-zA-Z0-9_-]", "", value)

    return value or default


def save_report(farmer_name, crop, content):
    """
    Save the action plan into the outputs folder.
    """

    # Create outputs folder
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Create timestamp
    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H%M%S"
    )

    # Make safe names
    safe_name = make_safe_filename(
        farmer_name,
        "farmer"
    )

    safe_crop = make_safe_filename(
        crop,
        "advice"
    )

    # Create filename
    filename = (
        f"{safe_name}_{safe_crop}_{timestamp}.txt"
    )

    filepath = os.path.join(
        OUTPUT_DIR,
        filename
    )

    # Write file
    with open(
        filepath,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            f"Shamba Advisor — Report for "
            f"{farmer_name or 'Farmer'}\n"
        )

        file.write(
            f"Generated: "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        )

        file.write("-" * 40 + "\n\n")

        file.write(content)

    return filepath