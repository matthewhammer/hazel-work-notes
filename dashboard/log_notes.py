#!/usr/bin/env python3
"""Save index.html into ~/hazel-work-notes, commit it, and push to GitHub.

  python3 ~/localhost-index/log_notes.py

Run by cron right after update.py, every 15 minutes. Each snapshot is the page
exactly as served on http://localhost:8000/, at

  <YYYY-MM-DD>/<YYYY-MM-DD>T<HHMM><+-hhmm>.html

so a file's name says when it was taken even outside its day's folder.

A snapshot is written only when the page differs from the last one in more than
its "Updated" line; a quiet run writes nothing. Pushing is tried on every run,
so commits made while offline go up on the next run that has a network."""
import os, re, subprocess, sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
NOTES = os.path.expanduser("~/hazel-work-notes")
PAGE = os.path.join(HERE, "index.html")
UPDATED = re.compile(r'<p class="note">Updated [^<]*<code>')

def git(*args):
    r = subprocess.run(["git", "-C", NOTES, *args], capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        sys.exit(f"git {' '.join(args)}: {(r.stderr or r.stdout).strip()[:300]}")
    return r.stdout

def body(text):
    return UPDATED.sub("", text)

def last_snapshot():
    days = sorted(d for d in os.listdir(NOTES) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d))
    for d in reversed(days):
        files = sorted(f for f in os.listdir(os.path.join(NOTES, d)) if f.endswith(".html"))
        if files:
            return os.path.join(NOTES, d, files[-1])
    return None

page = open(PAGE).read()
last = last_snapshot()
if last and body(open(last).read()) == body(page):
    print(f"unchanged since {os.path.relpath(last, NOTES)}")
else:
    now = datetime.now().astimezone()
    day = now.strftime("%Y-%m-%d")
    name = now.strftime("%Y-%m-%dT%H%M%z") + ".html"
    os.makedirs(os.path.join(NOTES, day), exist_ok=True)
    path = os.path.join(NOTES, day, name)
    open(path, "w").write(page)
    git("add", os.path.relpath(path, NOTES))
    git("commit", "-q", "-m", f"Snapshot {now.strftime('%Y-%m-%d %H:%M %Z')}")
    print(f"wrote {day}/{name}")

upstream = subprocess.run(["git", "-C", NOTES, "rev-parse", "-q", "--verify", "@{u}"], capture_output=True).returncode == 0
if not upstream:
    git("push", "-q", "-u", "origin", "HEAD")
    print("pushed, and set the upstream")
elif (ahead := git("rev-list", "--count", "@{u}..HEAD").strip()) != "0":
    git("push", "-q")
    print(f"pushed {ahead} commit(s)")
