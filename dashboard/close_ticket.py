#!/usr/bin/env python3
"""Close a ticket the way agent-instructions.md says: move it from tickets to
closed_tickets with its status and outcome, stamp closed_at, and compute its
metrics from its log (and its timed work, when it has some).

  python3 close_ticket.py <id> <status> <outcome> [--work-minutes M]"""
import json, os, sys
from datetime import datetime
DATA = os.path.expanduser("~/localhost-index/data.json")
tid, status, outcome = int(sys.argv[1]), sys.argv[2], sys.argv[3]
work = float(sys.argv[sys.argv.index("--work-minutes") + 1]) if "--work-minutes" in sys.argv else None
d = json.load(open(DATA))
t = next(t for t in d["tickets"] if t["id"] == tid)
now = datetime.now().astimezone()
t.update(status=status, closed=now.date().isoformat(), closed_at=now.isoformat(timespec="minutes"), outcome=outcome)
log = sorted(t.get("log", []), key=lambda e: e["at"])
ts = [datetime.fromisoformat(e["at"]) for e in log]
gaps = [(b - a).total_seconds() / 60 for a, b in zip(ts, ts[1:])]
m = {"open_minutes": round((now - datetime.fromisoformat(t["opened"])).total_seconds() / 60) if t.get("opened") else None,
     "matthew_messages": sum(e.get("from") == "matthew" for e in log),
     "questions_to_matthew": sum(e.get("from") == "claude" and bool(e.get("asks")) for e in log),
     "chars_exchanged": sum(e.get("chars", 0) for e in log)}
m["tokens_est"] = m["chars_exchanged"] // 4
m["sync_minutes_est"] = round(sum(g for g in gaps if g < 10), 1)
# (^ticket(489)) Claude's replies on it, and the time to read them or hear them (log_messages.py keeps the rates)
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
from log_messages import reading_metrics, model_label, shares, agent_models
m.update(reading_metrics(log))
# (Matthew 2026-10-21: the model and effort used, "some average for each") the replies' share per "model · effort",
# and the workflow agents' share
c = {}
for e in log:
    if e.get("from") == "claude" and e.get("model"):
        k = model_label(e["model"], e.get("effort")); c[k] = c.get(k, 0) + 1
if c:
    m["models"] = shares(c)
a = agent_models().get(tid)
if a:
    m["agents_models"] = shares(a)
if work is None and isinstance(t.get("work"), dict): work = t["work"].get("work_minutes")
if work is not None: m["work_minutes"] = work
t["metrics"] = m
d["tickets"].remove(t); d["closed_tickets"].insert(0, t)
d["queue"] = [q for q in d["queue"] if q != tid]
# (closing the current ticket makes the queue's next one current AS OF NOW: it
# kept the closed ticket's start and note, and now.py then left them in place)
if d.get("current_ticket") == tid:
    tags = {x["id"]: x.get("tags") or [] for x in d["tickets"]}
    nxt = next((q for q in d["queue"] if "blocked on Matthew" not in tags.get(q, [])), None)
    d["current_ticket"], d["current_since"] = nxt, now.isoformat(timespec="minutes")
    d["current_note"] = f"{now:%H:%M}: ^ticket({tid}) closed ({status}); " + (f"^ticket({nxt}) is next in the queue" if nxt else "the rest of the queue is blocked on Matthew" if d["queue"] else "the queue is empty")
    d.pop("current_waiting", None)
json.dump(d, open(DATA, "w"), indent=1, ensure_ascii=False)
print(tid, status, m)
