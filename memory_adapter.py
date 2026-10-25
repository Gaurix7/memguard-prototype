"""Connects Agent B to YOUR real shared memory (memory_store.py -> memguard.db, table memory_entries).
Run all scripts from the repo folder so the same memguard.db file is found."""
import math, re, collections
from memory_store import init_db, get_all_memories

init_db()  # creates the table if missing (prints "Database ready.")

def _tokens(text):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words]   # crude plural handling

def _cos(a, b):
    a, b = collections.Counter(a), collections.Counter(b)
    num = sum(a[w] * b[w] for w in a)
    den = math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values()))
    return num / den if den else 0.0

def _normalize(row):
    return {"id": str(row["id"]), "text": row["content"], "source_trust": row["source_trust"],
            "written_by": row["source_agent"], "timestamp": row["created_at"],
            "origin_document": row.get("origin_document"), "sim_day": row.get("sim_day", 0)}

def retrieve(query, k=3, include_untrusted=True):
    """Top-k memories most similar to the query. include_untrusted=False is used only to build the clean baseline."""
    q = _tokens(query)
    rows = [_normalize(r) for r in get_all_memories()]
    if not include_untrusted:
        rows = [r for r in rows if r["source_trust"] == "trusted"]
    for r in rows:
        r["score"] = _cos(q, _tokens(r["text"]))
    rows.sort(key=lambda r: (r["score"], int(r["id"])), reverse=True)
    return rows[:k]