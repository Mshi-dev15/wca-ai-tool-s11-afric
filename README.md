# 🌱 Shamba Advisor

An AI-powered decision assistant for smallholder farmers in Kenya — covering the whole farming cycle, from land preparation and planting, through pest and disease problems, to harvest and storage.

**Group:** AFRIC
**Members:** Faith Mshiki, Simon Gatuku
**Course:** WeCan Academy — AI & Chatbot Course, Season 11

---

## What it does

A farmer types a question in plain language — misspellings, mixed English/Swahili, and incomplete sentences are all fine. Shamba Advisor then:

1. **Understands the question** using conversation memory — follow-up messages like "what should I plant?" are correctly understood using earlier context (location, farm size, crop) without the farmer repeating themselves (Call 1)
2. **Pulls in live weather data** automatically, when relevant to the question
3. If multiple causes are plausible (e.g. a pest problem), **asks the farmer to pick one** from quick-select buttons, or type their own description if none fit
4. **Generates a practical, low-cost, week-by-week action plan** based on the analysis (Call 2)
5. **Saves the advice to a file**, downloadable directly from the chat
6. **Remembers the farmer** — returning to the same link signs them back in automatically, with recent chats available in the sidebar to reopen at any time

## How it works — the pipeline

```
Farmer types a message
        │
        ▼
   CALL 1 (ai/first_call.py)
   Analyzes intent, crop, location, symptoms, possible causes, etc.
   Uses conversation history to understand follow-up questions
   Returns structured JSON
        │
        ▼
   Weather lookup (weather/open_meteo.py)
   Only runs if the analysis says weather matters
        │
        ▼
   [If ambiguous] Farmer picks a cause via buttons, or types their own
        │
        ▼
   CALL 2 (ai/second_call.py)
   Turns the analysis + weather + selected cause into a real action plan
        │
        ▼
   Saved to a .txt file + shown in the chat
   Conversation stored in Supabase (encrypted at rest)
```

Both AI calls use OpenAI's API and are written following the **R-T-C-C-O** prompt framework (Role, Task, Context, Constraints, Output format) — full prompts are documented in the written report.

## Project structure

```
wca-ai-tool-s11-afric/
│
├── app.py                       # Main Streamlit app — run this
├── requirements.txt
├── .env                         # Your API keys (never committed)
├── .gitignore
│
├── ai/
│   ├── first_call.py            # Call 1 — intake analysis + conversation memory
│   └── second_call.py           # Call 2 — action plan generation
│
├── weather/
│   └── open_meteo.py            # Live weather lookup (no API key needed)
│
├── models/
│   ├── database_supabase.py     # Chat/farmer storage (Supabase)
│   ├── supabase_schema.sql      # Run once in Supabase's SQL Editor
│
├── utility/ (or utils/)
│   ├── file_saver.py            # Saves the final advice to a .txt file
│   └── encryption.py            # Encrypts message content before storage
│
└── outputs/                     
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
ENCRYPTION_KEY=your_generated_encryption_key
```

**Getting an OpenAI key:** platform.openai.com → API keys → Create new secret key.

**Getting Supabase credentials:** create a project at supabase.com, run `models/supabase_schema.sql` in its SQL Editor to create/update the tables, then copy your Project URL and anon key from Settings → API.

**Generating an encryption key:**
```bash
python utils/encryption.py
```
This prints a new key the first time — copy it into `.env` as shown above.

### 5. Run the app
```bash
streamlit run app.py
```
This opens automatically in your browser at `http://localhost:8501`.

## Testing individual pieces

Each part can be tested on its own from the command line:

```bash
python -m ai.first_call        # Test Call 1 — supports an ongoing multi-turn conversation, type 'exit' to quit
python -m ai.second_call       # Test Call 2 with a built-in sample analysis
python weather/open_meteo.py   # Test the weather lookup with a location name
python models/database_supabase.py   # Test the database connection
python utils/encryption.py     # Generate a key, or test encrypt/decrypt with an existing one
```

## Key features

- **Conversation memory** — Call 1 uses recent chat history to understand follow-up questions without the farmer repeating themselves
- **Cause selection** — when a symptom has multiple likely causes, the farmer picks one via quick buttons, or describes it themselves if none fit
- **Weather-aware advice** — Call 1 decides when current weather is actually relevant, and only then fetches it via Open-Meteo
- **Persistent sign-in** — a farmer's name is saved in the page URL, so returning to that link signs them back in without retyping
- **Encrypted storage** — message content is encrypted before being saved to Supabase, and decrypted only when displayed back to the farmer
- **Safety-conscious advice** — Call 2 is instructed never to invent pesticide names or doses, and always tells farmers to follow product labels and keep people/animals away from sprayed areas

## Error handling

The tool handles the required failure cases without crashing:
- **Empty input** — caught before any API call is made
- **Failed API call** (no internet, timeout) — retries once automatically, then shows a friendly message
- **Invalid JSON from the model** — caught and handled with a fallback response
- **Missing/invalid data at any stage** (weather lookup failure, database errors) — degrades gracefully rather than crashing the app


## Notes for graders

- Both R-T-C-C-O prompts are documented in full in the written report
- Chat history and farmer records persist in Supabase (not local SQLite), so they survive app restarts and redeploys on Streamlit Cloud
- Message content is encrypted at rest as an added privacy measure

## Group members and contributions

- **Faith Mshiki** — Call 1 (intake analysis, conversation memory), weather integration, Supabase database, encryption, Streamlit UI, deployment
- **Simon Gatuku** — Call 2 (action plan generation), farmer profile persistence, safety constraints for chemical/pesticide advice