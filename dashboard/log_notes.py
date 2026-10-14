#!/usr/bin/env python3
"""Save index.html, and data.json, into ~/hazel-work-notes, commit them, publish a public copy, and push to GitHub.

  python3 ~/localhost-index/log_notes.py

Run by publish.py right after update.py. Each snapshot is the page
exactly as served on http://localhost:8000/, at

  dashboard-snapshots/<YYYY>/<MM>/<DD>/<YYYY-MM-DD>T<HHMM><+-hhmm>.html

a folder for each year, month and day, and a file name that says when it was
taken even outside its folder. data.json is kept at dashboard-data/data.json,
committed whenever it changes: the tickets, closed ones included, live only
there.

A snapshot is written only when the page differs from the last one in more than
its "Updated" line; a quiet run writes nothing. Pushing is tried on every run,
so commits made while offline go up on the next run that has a network."""
import os, re, subprocess, sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
NOTES = os.path.expanduser("~/hazel-work-notes")
SNAPS = os.path.join(NOTES, "dashboard-snapshots")
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
    # the newest by name: names begin with the date and time
    snaps = [os.path.join(root, f) for root, _, files in os.walk(SNAPS) for f in files if f.endswith(".html")]
    return max(snaps, key=os.path.basename) if snaps else None

page = open(PAGE).read()
last = last_snapshot()
if last and body(open(last).read()) == body(page):
    print(f"unchanged since {os.path.relpath(last, NOTES)}")
else:
    now = datetime.now().astimezone()
    day = now.strftime("%Y/%m/%d")
    name = now.strftime("%Y-%m-%dT%H%M%z") + ".html"
    os.makedirs(os.path.join(SNAPS, day), exist_ok=True)
    path = os.path.join(SNAPS, day, name)
    open(path, "w").write(page)
    git("add", os.path.relpath(path, NOTES))
    git("commit", "-q", "-m", f"Snapshot {now.strftime('%Y-%m-%d %H:%M %Z')}")
    print(f"wrote dashboard-snapshots/{day}/{name}")

# data.json too: the tickets, closed ones included, are only there, so it gets
# a history of its own, committed whenever it changes.
DATA = os.path.join(HERE, "data.json")
KEPT = os.path.join(NOTES, "dashboard-data", "data.json")
data = open(DATA).read()
if not os.path.exists(KEPT) or open(KEPT).read() != data:
    os.makedirs(os.path.dirname(KEPT), exist_ok=True)
    open(KEPT, "w").write(data)
    git("add", os.path.relpath(KEPT, NOTES))
    git("commit", "-q", "-m", f"Data {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}")
    print("wrote dashboard-data/data.json")

# The public copy, at the repository's root, served by its Pages site
# (matthewhammer.org/hazel-work-notes/, and matthewhammer.org/hazel/work-dashboard/
# redirects there): the page and the closed tickets as served locally, with a
# line saying what it is, links to the history on GitHub instead of on
# localhost, and noindex (findable by its link, not by search). Written when
# a page changed in more than its "Updated" line.
REPO = "https://github.com/matthewhammer/hazel-work-notes"
NOTE = ('<p class="note">A copy of the Hazel Work Dashboard that Matthew runs on his laptop, published within a minute or '
        'two of each change to its notes, and every 15 minutes for the status from GitHub. Its <code>localhost</code> links work only there.</p>')

def public(text):
    text = text.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<meta name="robots" content="noindex">', 1)
    text = text.replace("http://localhost:8000/notes/dashboard-snapshots/", REPO + "/tree/main/dashboard-snapshots")
    text = text.replace(' (<a href="http://localhost:8000/notes/agent-instructions.md">local</a>)', "")
    text = text.replace("http://localhost:8000/notes/agent-instructions.md", REPO + "/blob/main/agent-instructions.md")
    for h1 in ("<h1>Hazel Work Dashboard</h1>", "<h1>Closed tickets</h1>"):
        text = text.replace(h1, h1 + "\n" + NOTE, 1)
    return text

published = []
for name in ("index.html", "closed.html"):
    src = os.path.join(HERE, name)
    if not os.path.exists(src):
        continue
    out = os.path.join(NOTES, name)
    copy = public(open(src).read())
    if not os.path.exists(out) or body(open(out).read()) != body(copy):
        open(out, "w").write(copy)
        git("add", name)
        published.append(name)
if published:
    git("commit", "-q", "-m", f"Publish {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}: {', '.join(published)}")
    print("published " + ", ".join(published))

upstream = subprocess.run(["git", "-C", NOTES, "rev-parse", "-q", "--verify", "@{u}"], capture_output=True).returncode == 0
if not upstream:
    git("push", "-q", "-u", "origin", "HEAD")
    print("pushed, and set the upstream")
elif (ahead := git("rev-list", "--count", "@{u}..HEAD").strip()) != "0":
    git("push", "-q")
    print(f"pushed {ahead} commit(s)")
