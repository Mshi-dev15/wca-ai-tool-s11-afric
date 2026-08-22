# 🌱 Shamba Advisor

An AI-powered decision assistant for smallholder farmers in Kenya — covering the whole farming cycle, from land preparation and planting, through pest and disease problems, to harvest and storage.

**Group:** AFRIC
**Author:** Faith Mshiki
**Course:** WeCan Academy — AI & Chatbot Course, Season 11

---

## What it does

A farmer types a question in plain language — misspellings, mixed English/Swahili, and incomplete sentences are all fine. The tool then:

1. **Analyzes** the message to figure out what the farmer actually needs (Call 1)
2. **Pulls in live weather data** automatically, if it's relevant to the question
3. **Generates a practical, low-cost action plan** based on that analysis (Call 2)
4. **Saves the advice to a file** and lets the farmer download their own copy
5. **Remembers the conversation** — recent chats appear in a sidebar and can be reopened

## How it works — the pipeline

```
Farmer types a message
        │
        ▼
   CALL 1 (ai/first_call.py)
   Analyzes intent, crop, location, symptoms, etc.
   Returns structured JSON
        │
        ▼
   Weather lookup (weather/open_meteo.py)
   Only runs if the analysis says weather matters
        │
        ▼
   CALL 2 (ai/second_call.py)
   Turns the analysis + weather into a real action plan
        │
        ▼
   Saved to a .txt file + shown in the chat
   Conversation stored in Supabase (models/database_supabase.py)
```

Both AI calls use OpenAI's API and are written following the **R-T-C-C-O** prompt framework (Role, Task, Context, Constraints, Output format) — full prompts are documented in the project report.

## Project structure

```
shamba-advisor/
│
├── app.py                       # Main Streamlit app — run this
├── requirements.txt
├── .env                         # Your API keys (never committed)
├── .gitignore
│
├── ai/
│   ├── first_call.py            # Call 1 — intake analysis
│   └── second_call.py           # Call 2 — action plan generation
│
├── weather/
│   └── open_meteo.py            # Live weather lookup (no API key needed)
│
├── models/
│   ├── database_supabase.py     # Chat/farmer storage (Supabase)
│   └── supabase_schema.sql      # Run this in Supabase's SQL Editor once
│
├── utils/
│   └── file_saver.py            # Saves the final advice to a .txt file
│
└── outputs/                     # Where saved reports land
```

## Setup — how to run this yourself

### 1. Clone the repo
```bash
git clone https://github.com/Mshi-dev15/wca-ai-tool-s11-afric.git
cd wca-ai-tool-s11-afric
```

### 2. Create a virtual environment
```bash
python -m venv my-env
source my-env/Scripts/activate      # Git Bash / Windows
# or: source my-env/bin/activate    # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up your API keys

Create a `.env` file in the project root (this file is git-ignored and never gets pushed):
```
OPENAI_API_KEY=your_openai_key_here
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

**Getting an OpenAI key:** platform.openai.com → API keys → Create new secret key.
**Getting Supabase credentials:** create a project at supabase.com, run `models/supabase_schema.sql` in its SQL Editor to create the tables, then copy your Project URL and anon key from Settings → API.

### 5. Run the app
```bash
streamlit run app.py
```
This opens automatically in your browser at `http://localhost:8501`.

## Testing individual pieces

Each part can be tested on its own from the command line:

```bash
python -m ai.first_call        # Test Call 1 alone — type a message, see the JSON
python -m ai.second_call       # Test Call 2 with a built-in sample analysis
python weather/open_meteo.py   # Test the weather lookup with a location name
python models/database_supabase.py   # Test the database connection
```

## Error handling

The tool handles three required failure cases without crashing:
- **Empty input** — caught before any API call is made
- **Failed API call** (no internet, timeout) — retries once automatically, then shows a friendly message
- **Invalid JSON from the model** — caught and handled with a fallback response

## Deployment

Deployed via **Streamlit Community Cloud**, connected directly to this GitHub repo. API keys are set in the app's **Secrets** manager on Streamlit Cloud (not in `.env`, since that file never leaves your local machine).

## Notes for graders

- API key is never hardcoded — loaded from `.env` locally / Streamlit Secrets when deployed
- Both R-T-C-C-O prompts are documented in full in the written report
- Chat history and farmer records persist in Supabase, so they survive app restarts and redeploys (unlike a local file, which would reset on Streamlit Cloud)