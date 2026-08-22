"""
File Saving — Output Persistence
--------------------------------
Saves the final action plan to a .txt file, so the farmer keeps a
record after the program closes. This ALWAYS runs, regardless of
whether the advice is also shown on screen.
"""

import os
from datetime import datetime

OUTPUT_DIR = "outputs"


def save_report(farmer_name: str, crop: str, content: str) -> str:
    """
    Saves the action plan to a .txt file inside outputs/.
    Returns the file path so the app can tell the user where it went.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    safe_crop = (crop or "advice").replace(" ", "_").lower()
    safe_name = (farmer_name or "farmer").replace(" ", "_").lower()

    filename = f"{safe_name}_{safe_crop}_{timestamp}.txt"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"Shamba Advisor — Report for {farmer_name or 'Farmer'}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("-" * 40 + "\n\n")
        f.write(content)

    return filepath


# --- Quick manual test from the command line ---
if __name__ == "__main__":
    path = save_report("Test Farmer", "maize", "1. Do this.\n2. Then this.\n3. Monitor weekly.")
    print(f"Saved to: {path}")