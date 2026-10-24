import os
from memory_store import init_db, get_all_memories
from agent_a import read_document_and_save

init_db()

documents_folder = "documents"

for filename in sorted(os.listdir(documents_folder)):
    if filename.endswith(".txt"):
        filepath = os.path.join(documents_folder, filename)
        with open(filepath, "r") as f:
            text = f.read()
        read_document_and_save(text, filename, sim_day=0)

print("\n\n===== ALL MEMORIES IN SHARED STORE =====")
for mem in get_all_memories():
    print(mem)