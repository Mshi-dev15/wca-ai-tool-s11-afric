import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_or_create_farmer(name: str) -> int:
    try:
        existing = supabase.table("farmers").select("id").eq("name", name).execute()
        if existing.data:
            return existing.data[0]["id"]
        created = supabase.table("farmers").insert({"name": name}).execute()
        return created.data[0]["id"]
    except Exception as db_error:
        print(f"[database] get_or_create_farmer failed: {db_error}")
        return None


def create_chat(farmer_id: int, title: str = "New chat") -> int:
    try:
        result = supabase.table("chats").insert({"farmer_id": farmer_id, "title": title}).execute()
        return result.data[0]["id"]
    except Exception as db_error:
        print(f"[database] create_chat failed: {db_error}")
        return None


def save_message(chat_id: int, role: str, content: str, intent_json: str = None):
    if chat_id is None:
        return
    try:
        supabase.table("messages").insert({
            "chat_id": chat_id, "role": role, "content": content, "intent_json": intent_json,
        }).execute()
    except Exception as db_error:
        print(f"[database] save_message failed: {db_error}")


def get_recent_chats(farmer_id: int, limit: int = 10) -> list:
    try:
        result = (supabase.table("chats").select("id, title, started_at")
                  .eq("farmer_id", farmer_id).order("started_at", desc=True).limit(limit).execute())
        return result.data
    except Exception as db_error:
        print(f"[database] get_recent_chats failed: {db_error}")
        return []


def get_chat_history(chat_id: int) -> list:
    try:
        result = (supabase.table("messages").select("role, content, created_at")
                  .eq("chat_id", chat_id).order("created_at", desc=False).execute())
        return result.data
    except Exception as db_error:
        print(f"[database] get_chat_history failed: {db_error}")
        return []


if __name__ == "__main__":
    fid = get_or_create_farmer("Test Farmer")
    print("Farmer id:", fid)
    cid = create_chat(fid, title="Maize planting question")
    print("Chat id:", cid)
    save_message(cid, "user", "Is it a good time to plant maize in Kiserian?")
    save_message(cid, "assistant", "Based on current rainfall, yes.")
    print("Recent chats:", get_recent_chats(fid))
    print("Chat history:", get_chat_history(cid))
