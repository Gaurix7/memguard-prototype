"""STEP 9 prototype - the timeline dashboard.
Reads the shared memory (memguard.db) and the detector's log (detector_log.jsonl) and writes timeline.html.
Run order first: seed_trusted.py -> baseline.py -> plant_poison.py -> detector.py / compare_demo.py (these write the log)."""
import json, html, os, webbrowser
from memory_store import get_all_memories

def load_log(path="detector_log.jsonl"):
    out = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
    return out

def esc(x):
    return html.escape(str(x))

def short(text, n=150):
    text = str(text)
    return esc(text if len(text) <= n else text[:n].rstrip() + "...")

log = load_log()
mems = sorted(get_all_memories(), key=lambda m: int(m["id"]))
untrusted = [m for m in mems if m["source_trust"] != "trusted"]
high = [e for e in log if e["risk"] == "HIGH"]
calm = [e for e in log if e["risk"] != "HIGH"]
ev = high[-1] if high else None                       # the event we tell the story about
guilty = {str(s["memory_id"]) for s in ev["untrusted_memories_used"]} if ev else set()

THR = 500
if os.path.exists("baseline_profile.json"):
    THR = json.load(open("baseline_profile.json")).get("approval_threshold", 500)

def approval_text(d):
    """'NO' only counts as alarming above the approval threshold; below it, no approval is normal."""
    if d.get("approval_required"):
        return "yes"
    return "<b>NO</b>" if float(d.get("amount", 0)) > THR else "not needed"

BADGE = {"HIGH": "#c62828", "WATCH": "#ef6c00", "OK": "#2e7d32"}
def badge(risk):
    return f"<span class='badge' style='background:{BADGE.get(risk, '#555')}'>{esc(risk)}</span>"

# ---- the four stages ----
notes_html = ""
for m in untrusted[:6]:
    tag = "<span class='tag bad'>implicated</span>" if str(m["id"]) in guilty else "<span class='tag'>untrusted</span>"
    notes_html += (f"<div class='note'>{tag} <b>[{esc(m['id'])}]</b> from <i>{esc(m['origin_document'] or '?')}</i><br>"
                   f"<span class='quote'>{short(m['content'])}</span></div>")
stage1 = notes_html or "<p class='muted'>No untrusted notes in memory yet. Run plant_poison.py.</p>"

stage2 = (f"<p><b>{len(calm)}</b> logged request(s) went through without a block.</p>"
          "<p class='muted'>The poisoned notes sit in the shared notebook. Nothing looks wrong until the right request retrieves them.</p>")

if ev:
    d = ev.get("decision", {})
    stage3 = (f"<p>Request <b>{esc(ev['request_id'])}</b>, <b>${float(d.get('amount', 0)):.0f}</b>.</p>"
              f"<p>Agent B retrieved the poisoned notes and decided:</p>"
              f"<ul><li>manager approval: <b>{approval_text(d)}</b></li>"
              f"<li>money sent to: <b>{esc(d.get('destination_account', '?'))}</b> "
              f"(customer's own account: {esc(d.get('original_account', '?'))})</li></ul>"
              f"<p class='muted'>{esc(ev['time'])}</p>")
    proof = ""
    if "attribution" in ev:
        a = ev["attribution"]
        proof = (f"<p>Replay proof: memories {esc(', '.join(a['removed_memory_ids']))} removed, request re-run {a['trials']}x, "
                 f"bad behaviour returned {a['drifted_without_suspects']}/{a['trials']} times.<br><b>"
                 + ("CONFIRMED: these memories caused it." if a["caused_by_suspects"] else "NOT CONFIRMED.") + "</b></p>")
    stage4 = (f"<p>{badge('HIGH')}</p><p><b>{esc(ev['action'])}</b></p>"
              f"<p>Traced back to: " + ", ".join(sorted({esc(s['origin_document'] or '?') for s in ev['untrusted_memories_used']})) + "</p>" + proof)
else:
    stage3 = "<p class='muted'>No attack has been logged yet. Run detector.py or compare_demo.py.</p>"
    stage4 = "<p class='muted'>Nothing detected yet.</p>"

# ---- evidence panel ----
evidence = ""
if ev:
    drift = "".join(f"<li>{esc(v)}</li>" for v in ev["drift_violations"])
    sus = "".join(f"<tr><td>{esc(s['memory_id'])}</td><td>{esc(s['origin_document'] or '?')}</td><td>{short(s['text'], 220)}</td></tr>"
                  for s in ev["untrusted_memories_used"])
    evidence = (f"<div class='card'><h2>Evidence for the latest alert</h2>"
                f"<h3>How Agent B broke from its baseline</h3><ul>{drift}</ul>"
                f"<h3>Untrusted memories it relied on</h3>"
                f"<table><tr><th>Memory</th><th>Source document</th><th>Text</th></tr>{sus}</table></div>")

# ---- log table ----
rows = ""
for e in reversed(log[-15:]):
    d = e.get("decision", {})
    src = ", ".join(sorted({esc(s['origin_document'] or '?') for s in e["untrusted_memories_used"]})) or "-"
    rows += (f"<tr><td>{esc(e['time'])}</td><td>{esc(e['request_id'])}</td><td>${float(d.get('amount', 0)):.0f}</td>"
             f"<td>{approval_text(d)}</td><td>{esc(d.get('destination_account', '?'))}</td>"
             f"<td>{badge(e['risk'])}</td><td>{src}</td></tr>")
log_table = (f"<div class='card'><h2>Detector log (newest first)</h2><table><tr><th>Time</th><th>Request</th><th>Amount</th>"
             f"<th>Approval?</th><th>Sent to</th><th>Verdict</th><th>Untrusted source used</th></tr>{rows}</table></div>") if rows else ""

page = f"""<!doctype html><html><head><meta charset="utf-8"><title>MemWatch timeline</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#fff;color:#222;max-width:1100px;margin:28px auto;padding:0 16px}}
h1{{font-size:22px;margin-bottom:4px}} h2{{font-size:16px;margin:0 0 8px}} h3{{font-size:14px;margin:12px 0 4px}}
.sub{{color:#666;font-size:13px;margin:0 0 16px}} .muted{{color:#777;font-size:13px}}
.timeline{{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;margin:12px 0 18px}}
.stage{{border:1px solid #ddd;border-radius:10px;padding:14px;position:relative}}
.stage .n{{font-size:11px;letter-spacing:.06em;color:#888;text-transform:uppercase}}
.stage h2{{margin:2px 0 8px}} .s1{{border-top:4px solid #ef6c00}} .s2{{border-top:4px solid #9e9e9e}}
.s3{{border-top:4px solid #c62828}} .s4{{border-top:4px solid #2e7d32}}
.note{{font-size:12.5px;margin:8px 0;padding:6px 8px;background:#fafafa;border-radius:6px}} .quote{{color:#555}}
.tag{{font-size:10.5px;background:#eee;border-radius:4px;padding:1px 6px}} .tag.bad{{background:#ffcdd2;color:#b71c1c}}
.card{{border:1px solid #ddd;border-radius:10px;padding:16px;margin:14px 0}}
table{{border-collapse:collapse;width:100%;font-size:13px}} th,td{{border-bottom:1px solid #e5e5e5;padding:6px 8px;text-align:left;vertical-align:top}}
.badge{{color:#fff;border-radius:4px;padding:2px 8px;font-weight:600;font-size:12px}}
ul{{margin:4px 0 4px 18px;padding:0;font-size:13.5px}} p{{margin:6px 0;font-size:13.5px}}
</style></head><body>
<h1>MemWatch: from a poisoned note to a blocked payout</h1>
<p class="sub">Timestamps are real, from this prototype's database and detector log. "Day 1" and "Day X" are illustrative: the prototype runs in one session, but a real poison can sit dormant for days.</p>
<div class="timeline">
<div class="stage s1"><div class="n">Day 1</div><h2>Poison enters memory</h2>{stage1}</div>
<div class="stage s2"><div class="n">Dormant period</div><h2>Nothing looks wrong</h2>{stage2}</div>
<div class="stage s3"><div class="n">Day X</div><h2>Agent B uses the memory</h2>{stage3}</div>
<div class="stage s4"><div class="n">Detection</div><h2>Detector fires</h2>{stage4}</div>
</div>
{evidence}
{log_table}
</body></html>"""
open("timeline.html", "w", encoding="utf-8").write(page)
path = os.path.abspath("timeline.html")
print("saved:", path)
webbrowser.open("file:///" + path.replace("\\", "/"))