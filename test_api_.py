from dotenv import load_dotenv
from openai import OpenAI

# Load variables from .env
load_dotenv()

# Create the OpenAI client
client = OpenAI()

# Send a request
response = client.responses.create(
    model="gpt-5.6-luna",
    input="Hello! Introduce yourself in one short sentence."
)

# Print the AI's response
print(response.output_text)
