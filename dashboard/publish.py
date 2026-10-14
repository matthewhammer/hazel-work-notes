#!/usr/bin/env python3
"""Run update.py, then log_notes.py, when data.json has changed since the last
publish, and on the quarter hour.

  python3 ~/localhost-index/publish.py          # what cron runs, every minute
  python3 ~/localhost-index/publish.py --now    # by hand, after a change

data.json changes only when we edit it: a ticket opened, made current, closed
or parked, current_waiting raised or lowered, a note, a port, a PR. Each such
edit is published within a minute, without waiting for anyone to remember to.
What comes from GitHub (PR status, deploys) is not in data.json, so it is
refreshed on the quarter hour, as before.

A lock keeps two runs from overlapping: a cron run that finds one in progress
skips, and --now waits for it. The hash of the data.json a run rendered is
kept in .published-data.sha256 once both scripts succeed, so a failed run is
retried a minute later. Each run that does anything writes update.log; a quiet
minute writes nothing."""
import fcntl, hashlib, os, subprocess, sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data.json")
STAMP = os.path.join(HERE, ".published-data.sha256")
LOG = os.path.join(HERE, "update.log")
now_flag = "--now" in sys.argv[1:]

lock = open(os.path.join(HERE, ".publish.lock"), "w")
try:
    fcntl.flock(lock, fcntl.LOCK_EX | (0 if now_flag else fcntl.LOCK_NB))
except BlockingIOError:
    sys.exit(0)

digest = hashlib.sha256(open(DATA, "rb").read()).hexdigest()
try:
    last = open(STAMP).read().strip()
except FileNotFoundError:
    last = ""
minute = datetime.now().minute
if now_flag:
    why = "by hand (--now)"
elif digest != last:
    why = "data.json changed"
elif minute % 15 == 0:
    why = "quarter hour"
else:
    sys.exit(0)

out = [f"{datetime.now().astimezone():%Y-%m-%d %H:%M:%S %Z}: {why}"]
ok = True
for script in ("update.py", "log_notes.py"):
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, script)], cwd=HERE,
                           capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        out.append(f"{script} took over 10 minutes")
        ok = False
        break
    out.append((r.stdout + r.stderr).rstrip())
    if r.returncode != 0:
        out.append(f"{script} exited {r.returncode}")
        ok = False
        break
if ok:
    open(STAMP, "w").write(digest + "\n")
open(LOG, "w").write("\n".join(s for s in out if s) + "\n")
print("\n".join(s for s in out if s))
sys.exit(0 if ok else 1)
