"""Run ONCE. Adds the two normal company rules to the real DB as TRUSTED notes (written by a human).
Without them the baseline has no 'normal rules' to follow. Safe to re-run: it skips notes that already exist."""
from memory_store import init_db, add_memory, get_all_memories

RULES = ["Refunds over $500 require manager approval before payout.",
         "Refunds are returned to the customer's original payment account."]

init_db()
existing = {m["content"] for m in get_all_memories()}
for rule in RULES:
    if rule in existing:
        print("already there:", rule)
    else:
        add_memory(rule, "human", "trusted", "company_policy_handbook", 0)
        print("added:", rule)