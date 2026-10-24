import os
from dotenv import load_dotenv
from openai import OpenAI
from memory_store import init_db, add_memory

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

def read_document_and_save(document_text, filename, sim_day=0):
    print(f"\nAgent A is reading: {filename}")

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": "You read internal documents and extract ONE useful process note or fact worth remembering for future tasks. Reply with ONLY that one note, as a single sentence. If nothing is worth remembering, reply with exactly: NOTHING"},
            {"role": "user", "content": document_text}
        ],
        temperature=0.3
    )

    note = response.choices[0].message.content.strip()
    print(f"Agent A extracted: {note}")

    if note.upper() != "NOTHING":
        add_memory(
            content=note,
            source_agent="agent_a",
            source_trust="untrusted",
            origin_document=filename,
            sim_day=sim_day
        )
        print("Saved to shared memory as UNTRUSTED.")
    else:
        print("Nothing saved.")

if __name__ == "__main__":
    init_db()
    with open("documents/doc1_finance_policy.txt", "r") as f:
        text = f.read()
    read_document_and_save(text, "doc1_finance_policy.txt")