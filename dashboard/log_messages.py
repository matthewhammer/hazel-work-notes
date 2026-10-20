#!/usr/bin/env python3
"""Each ticket's log, from the session transcripts (^ticket(466)).

agent-instructions.md asks for one log entry per message about a ticket,
appended in the same turn; the closed tickets' metrics are computed from
those entries. Kept by hand, they were not kept: 100 closed tickets said
Matthew had sent nothing, the horse and the outfits among them. So the
entries now come from what the sessions recorded, the transcripts under
~/.claude/projects/-home-matthew-hazel/, and nothing depends on a turn
remembering.

  python3 log_messages.py --backfill [--since 2026-10-15] [--dry-run]
  python3 log_messages.py            (from publish.py: what is new since the last run)

A message of Matthew's is a user record of human origin, or the text of a
message he sent while a turn was running (a queue-operation's enqueue or
remove, or a queued_command attachment: with a screenshot only the latter
two hold its text); the same text twice within an hour is one message. Claude's entry is one per
turn: the length of the text it wrote that turn, and asks when the turn
put a question to Matthew (wrap_up's ask, or AskUserQuestion).

Which ticket a message is about, first rule that applies:
  1. the tickets it names (#ticket-N, ^ticket(N), "ticket N");
  2. the tickets whose text or progress quotes it (the practice is to quote
     Matthew's words there): any of five 24-character pieces of it found;
  3. if it says "mint", the tickets added in the 20 minutes after it;
  4. the dashboard's current ticket at that moment (the published
     data.json's history in ~/localhost-index/notes; live data.json for
     the incremental run).
  (and between 2 and 4: a follow-up within 10 minutes of a message placed
  by 1 to 3 goes where that one went, as "test with a small gnome" did)
Claude's entry is per reply: the text written after one of Matthew's
messages, until the next, goes where that message went.

A hand-kept entry claims the message nearest it in time (within 3 minutes;
Claude's, 5): that message goes to the entry's ticket, with its exact time
and length, in the entry's place (the hand-kept lengths were estimates).
Entries this script wrote carry "note": "from the transcripts", and a rerun
writes them again rather than adding to them. A closed ticket's metrics are
recomputed from its log, as close_ticket.py computes them; open_minutes and
work_minutes are kept."""
import glob, html, json, os, re, subprocess, sys
from datetime import datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data.json")
NOTES = os.path.join(HERE, "notes")
STATE = os.path.join(HERE, "log_messages.state.json")
TRANSCRIPTS = os.path.expanduser("~/.claude/projects/-home-matthew-hazel")
NOTE = "from the transcripts"
# the incremental run leaves a message this long, so the tickets it mints exist
SETTLE = timedelta(minutes=12)
MINT_WINDOW = timedelta(minutes=20)

REF = re.compile(r"#ticket-(\d+)|\^ticket\((\d+)\)|\bticket[s]?\s*#?\s*(\d{2,4})\b", re.I)


def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def iso_local(t):
    return t.astimezone().isoformat(timespec="minutes")


def text_of(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def machine_text(s):
    s = s.lstrip()
    return s.startswith(("<task-notification", "<system-reminder", "[SYSTEM", "<command-", "<local-command", "Caveat:",
                         "This session is being continued from a previous conversation"))


def events(path, start=0):
    """(kind, time, payload) from one transcript, from byte offset [start]:
    ("matthew", t, text), ("turn", t, None) where a turn starts,
    ("text", t, chars) for Claude's text, ("ask", t, None)."""
    with open(path, "rb") as fh:
        fh.seek(start)
        for raw in fh:
            try:
                o = json.loads(raw)
            except ValueError:
                continue
            ts = o.get("timestamp")
            if not ts or o.get("isSidechain"):
                continue
            t = parse_ts(ts)
            kind = o.get("type")
            if kind == "queue-operation" and o.get("operation") in ("enqueue", "remove"):
                # sent while a turn ran: queued, then absorbed into the turn;
                # with a screenshot the enqueue holds no text, the remove does
                c = text_of(o.get("content")).strip()
                if c and not machine_text(c):
                    yield ("matthew", t, c)
            elif kind == "attachment" and (o.get("attachment") or {}).get("type") == "queued_command":
                c = text_of(o["attachment"].get("prompt")).strip()
                if c and not machine_text(c):
                    yield ("matthew", t, c)
            elif kind == "user":
                origin = (o.get("origin") or {}).get("kind")
                if origin == "human":
                    s = text_of(o["message"].get("content")).strip()
                    if s and not machine_text(s):
                        yield ("turn", t, None)
                        yield ("matthew", t, s)
                elif origin == "task-notification":
                    yield ("turn", t, None)
            elif kind == "assistant":
                for b in o.get("message", {}).get("content", []) or []:
                    if not isinstance(b, dict):
                        continue
                    if b.get("type") == "text" and b.get("text", "").strip():
                        yield ("text", t, len(b["text"]))
                    elif b.get("type") == "tool_use":
                        name, inp = b.get("name", ""), b.get("input") or {}
                        if name == "AskUserQuestion" or (name.endswith("__wrap_up") and inp.get("ask")):
                            yield ("ask", t, None)


def messages(paths_offsets, since):
    """Matthew's messages and Claude's turns, in time order, since [since]:
    [("matthew", t, chars, text)], [("claude", t, chars, asks, opening_text)]."""
    mine, turns = [], []
    for path, start in paths_offsets:
        cur = None  # the current turn: [start, chars, asks, last_text_t, opening text]
        def close():
            if cur and cur[1] > 0 and cur[3] >= since:
                turns.append(("claude", cur[3], cur[1], cur[2], cur[4]))
        for kind, t, p in events(path, start):
            if kind == "turn":
                close()
                cur = [t, 0, False, t, None]
            elif kind == "matthew":
                if t >= since:
                    mine.append(("matthew", t, len(p), p))
                # what Claude writes after it, until his next message, is the reply to it
                if cur is not None and cur[1] > 0:
                    close()
                    cur = [t, 0, False, t, p]
                elif cur is not None:
                    cur[4] = cur[4] or p
                else:
                    cur = [t, 0, False, t, p]
            elif kind == "text" and cur is not None:
                cur[1] += p
                cur[3] = t
            elif kind == "ask" and cur is not None:
                cur[2] = True
        close()
    # one message, however many times it was recorded (queued, then delivered)
    mine.sort(key=lambda m: m[1])
    seen, out = {}, []
    for m in mine:
        key = " ".join(m[3].split())
        if key in seen and m[1] - seen[key] < timedelta(hours=1):
            continue
        seen[key] = m[1]
        out.append(m)
    turns.sort(key=lambda m: m[1])
    return out, turns


def current_history():
    """[(time, current_ticket)] from the published data.json's history."""
    log = subprocess.run(["git", "-C", NOTES, "log", "--format=%H %cI", "--since=2026-10-14", "--", "dashboard-data/data.json"],
                         capture_output=True, text=True).stdout.split("\n")
    revs = [l.split() for l in log if l.strip()]
    if not revs:
        return []
    p = subprocess.Popen(["git", "-C", NOTES, "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    hist = []
    for sha, when in revs:
        p.stdin.write(f"{sha}:dashboard-data/data.json\n".encode()); p.stdin.flush()
        header = p.stdout.readline().split()
        if len(header) < 3 or header[1] == b"missing":
            continue
        body = p.stdout.read(int(header[2])); p.stdout.read(1)
        m = re.search(rb'"current_ticket":\s*(null|\d+)', body)
        if m:
            hist.append((parse_ts(when), None if m.group(1) == b"null" else int(m.group(1))))
    p.stdin.close(); p.wait()
    hist.sort()
    return hist


def current_at(hist, t):
    best = None
    for when, cur in hist:
        if when > t:
            break
        best = cur
    return best


def norm(s):
    s = html.unescape(re.sub(r"<[^>]+>", "", s or ""))
    s = s.replace("\u201c", '"').replace("\u201d", '"').replace("\u2019", "'").replace("\u2018", "'")
    return " ".join(s.split()).lower()


QUOTED = {}  # ticket id -> its text and progress, normalized


def probes(text, n=5, k=24):
    s = norm(text)
    if len(s) <= k:
        return [s] if len(s) >= 12 else []
    step = (len(s) - k) / (n - 1)
    return [s[int(i * step):int(i * step) + k] for i in range(n)]


def attribute(text, t, tickets_by_id, added, hist, live_current, why=False):
    ids, how = attribute_how(text, t, tickets_by_id, added, hist, live_current)
    return (ids, how) if why else ids


def attribute_how(text, t, tickets_by_id, added, hist, live_current):
    ids = set()
    for m in REF.finditer(text or ""):
        n = int(next(g for g in m.groups() if g))
        if n in tickets_by_id:
            ids.add(n)
    if ids:
        return ids, "named"
    if text:
        if not QUOTED:
            for i, tk in tickets_by_id.items():
                QUOTED[i] = norm(" ".join(str(tk.get(k) or "") for k in ("text", "progress", "source", "outcome")))
        ps = probes(text)
        if ps:
            quoting = {i for i, q in QUOTED.items() if any(p in q for p in ps)}
            # a quote far from the message's time is a coincidence (a common phrase)
            quoting = {i for i in quoting if i not in added or added[i] - timedelta(days=2) <= t}
            if quoting and len(quoting) <= 4:
                return quoting, "quoted"
    if text and re.search(r"\bmint", text, re.I):
        minted = {i for i, a in added.items() if t - timedelta(minutes=1) <= a <= t + MINT_WINDOW}
        if minted:
            return minted, "minted"
    cur = current_at(hist, t) if hist else live_current
    return ({cur} if cur in tickets_by_id else set()), "current"


def recompute_metrics(t):
    m = dict(t.get("metrics") or {})
    log = sorted(t.get("log", []), key=lambda e: e["at"])
    ts = [datetime.fromisoformat(e["at"]) for e in log]
    gaps = [(b - a).total_seconds() / 60 for a, b in zip(ts, ts[1:])]
    m["matthew_messages"] = sum(e.get("from") == "matthew" for e in log)
    m["questions_to_matthew"] = sum(e.get("from") == "claude" and bool(e.get("asks")) for e in log)
    m["chars_exchanged"] = sum(e.get("chars", 0) for e in log)
    m["tokens_est"] = m["chars_exchanged"] // 4
    m["sync_minutes_est"] = round(sum(g for g in gaps if g < 10), 1)
    t["metrics"] = m


def merge(d, mine, turns, hist, opened_since, dry, since=None):
    """Put each message on its tickets. A hand-kept entry claims the message
    nearest it in time (within 3 minutes; Claude's, 5): the message goes to
    that entry's ticket, with its exact time and length, in the entry's
    place. The rest are placed by attribute(). Entries this script wrote
    before, from [since] on, are written again, so a rerun does not double
    them."""
    everyone = d["tickets"] + d["closed_tickets"]
    by_id = {t["id"]: t for t in everyone}
    added = {}
    for t in everyone:
        a = t.get("opened") or t.get("added")
        if a and len(a) >= 16:
            try:
                added[t["id"]] = datetime.fromisoformat(a)
            except ValueError:
                pass
    in_scope = lambda tid: not opened_since or (tid in added and added[tid] >= opened_since)
    lo = since or min([m[1] for m in mine] + [m[1] for m in turns], default=None)
    if lo is None:
        return {}
    def claims(sender, msgs, window):
        out, used = {}, set()
        for tid, t in by_id.items():
            if not in_scope(tid):
                continue
            for e in t.get("log", []):
                if e.get("from") != sender or e.get("note") == NOTE:
                    continue
                at = datetime.fromisoformat(e["at"])
                if at < lo - window:
                    continue
                near = min(((abs(m[1] - at), k) for k, m in enumerate(msgs) if abs(m[1] - at) <= window), default=None)
                if near:
                    out.setdefault(near[1], set()).add(tid)
                    used.add(id(e))
        return out, used
    mine_claims, used_m = claims("matthew", mine, timedelta(minutes=3))
    turn_claims, used_c = claims("claude", turns, timedelta(minutes=5))
    live_current = d.get("current_ticket")
    where, new = {}, {}
    last_placed = None  # (time, ids) of the last message placed by rules 1-3
    for k, (_, t, chars, text) in enumerate(mine):
        if k in mine_claims:
            ids, how = mine_claims[k], "hand"
        else:
            ids, how = attribute(text, t, by_id, added, hist, live_current, why=True)
            if how == "current" and last_placed and t - last_placed[0] <= timedelta(minutes=10):
                ids = last_placed[1]
        if how != "current":
            last_placed = (t, ids)
        where[" ".join(text.split())] = ids
        for tid in ids:
            if in_scope(tid):
                new.setdefault(tid, []).append({"at": iso_local(t), "from": "matthew", "chars": chars, "asks": False, "note": NOTE})
    for k, (_, t, chars, asks, opening) in enumerate(turns):
        ids = turn_claims.get(k) or (where.get(" ".join(opening.split())) if opening else None)
        if not ids:
            ids = attribute(None, t, by_id, added, hist, live_current)
        for tid in ids:
            if in_scope(tid):
                new.setdefault(tid, []).append({"at": iso_local(t), "from": "claude", "chars": chars, "asks": asks, "note": NOTE})
    touched = set(new)
    for tid, t in by_id.items():
        if not in_scope(tid):
            continue
        old = t.get("log", [])
        keep = [e for e in old
                if id(e) not in used_m and id(e) not in used_c
                and not (e.get("note") == NOTE and datetime.fromisoformat(e["at"]) >= lo)]
        if len(keep) != len(old) or tid in new:
            touched.add(tid)
            t["log"] = sorted(keep + new.get(tid, []), key=lambda e: e["at"])
            if t in d["closed_tickets"] and t.get("metrics"):
                recompute_metrics(t)
    return {tid: new.get(tid, []) for tid in touched}


def main():
    """Parse first, then read data.json, merge and write at once: the parse
    takes seconds, and an edit made meanwhile (now.py, a ticket) must not be
    overwritten. Under publish.py's lock: publish.py holds it already when it
    calls this with --locked; otherwise this takes it."""
    dry = "--dry-run" in sys.argv
    backfill = "--backfill" in sys.argv
    state = json.load(open(STATE)) if os.path.exists(STATE) else {"through": None}
    paths = sorted(glob.glob(os.path.join(TRANSCRIPTS, "*.jsonl")), key=os.path.getmtime)
    now = datetime.now(timezone.utc)
    through = now - SETTLE
    if backfill:
        since = parse_ts((sys.argv[sys.argv.index("--since") + 1] if "--since" in sys.argv else "2026-10-15") + "T00:00:00-06:00")
        paths = [p for p in paths if datetime.fromtimestamp(os.path.getmtime(p), timezone.utc) >= since]
        mine, turns = messages([(p, 0) for p in paths], since)
        hist, opened_since, lo = current_history(), since, None
    else:
        # what is new: messages settled (SETTLE old) since the last run
        last = parse_ts(state["through"]) if state.get("through") else now - timedelta(hours=1)
        if through <= last:
            return
        recent = [p for p in paths if datetime.fromtimestamp(os.path.getmtime(p), timezone.utc) >= last - timedelta(hours=3)]
        mine, turns = messages([(p, 0) for p in recent], last)
        mine = [m for m in mine if m[1] < through]
        turns = [m for m in turns if m[1] < through]
        hist, opened_since, lo = [], None, last
    lock = None
    if "--locked" not in sys.argv and not dry:
        import fcntl
        lock = open(os.path.join(HERE, ".publish.lock"), "w")
        fcntl.flock(lock, fcntl.LOCK_EX)
    d = json.load(open(DATA))
    new = merge(d, mine, turns, hist, opened_since, dry, since=lo)
    n = sum(len(v) for v in new.values())
    print(f"log_messages: {len(mine)} messages, {len(turns)} replies; {n} entries on {len(new)} tickets" + (" (dry run)" if dry else ""))
    if dry:
        return
    if n or new:
        tmp = DATA + ".log_messages.tmp"
        json.dump(d, open(tmp, "w"), indent=1, ensure_ascii=False)
        os.replace(tmp, DATA)
    state["through"] = through.isoformat()
    json.dump(state, open(STATE, "w"))


if __name__ == "__main__":
    main()
