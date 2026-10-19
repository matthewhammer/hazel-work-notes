#!/usr/bin/env python3
"""Save index.html and closed.html, and data.json, into ~/hazel-work-notes, commit them, publish a public copy (site_publish.py), and push to GitHub.

  python3 ~/localhost-index/log_notes.py

Run by publish.py right after update.py. Since ^ticket(417) (2026-10-19, Matthew: "revise the dashboard repo so that the
current dashboard is kept, and no prior snapshots are kept as separate files, but only as part of the git history"; the
dated files had reached 1,793 and 341 MB on the laptop, ~95 MB a day, ^ticket(391)) each page is one path,

  dashboard-snapshots/index.html    the page exactly as served on http://localhost:8000/
  dashboard-snapshots/closed.html   the closed tickets' page

and every earlier version is in git's history: each commit that changes one is a snapshot, its time the commit's. Beside
them, dashboard-snapshots/versions.html lists the versions from git log, newest first, with links to each on GitHub. The
dated files from before (dashboard-snapshots/<YYYY>/<MM>/<DD>/...) left the tree in that change and are still in history:
versions.html links the last tree that held them. data.json is kept at dashboard-data/data.json, committed whenever it
changes: the tickets, closed ones included, live only there.

A page is written only when it differs from the kept one in more than its "Updated" line; a quiet run writes nothing.
Pushing is tried on every run, so commits made while offline go up on the next run that has a network."""
import html, os, re, subprocess, sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
NOTES = os.path.expanduser("~/hazel-work-notes")
SNAPS = os.path.join(NOTES, "dashboard-snapshots")
REPO = "https://github.com/matthewhammer/hazel-work-notes"
UPDATED = re.compile(r'<p class="note">Updated [^<]*<code>')
# (the last commit whose tree held the dated snapshot files, before ^ticket(417) took them out)
DATED_UNTIL = os.path.join(SNAPS, ".dated-until")

def git(*args):
    r = subprocess.run(["git", "-C", NOTES, *args], capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        sys.exit(f"git {' '.join(args)}: {(r.stderr or r.stdout).strip()[:300]}")
    return r.stdout

def body(text):
    return UPDATED.sub("", text)

def versions_page():
    """The versions of the two pages, from git log: when, which, and links to each on GitHub."""
    rows, PAGES = [], ("dashboard-snapshots/index.html", "dashboard-snapshots/closed.html")
    # (one pass: each commit's hash and time, then the files it changed; a commit per line of git show was too slow for long)
    for block in git("log", "--format=%x00%H %cI", "--name-only", "--", *PAGES).split("\0")[1:]:
        lines = [l for l in block.splitlines() if l.strip()]
        sha, when = lines[0].split(" ", 1)
        t, files = datetime.fromisoformat(when), [f for f in lines[1:] if f in PAGES]
        links = " · ".join(f'<a href="{REPO}/blob/{sha}/{f}">{"the page" if f.endswith("index.html") else "the closed page"}</a>' for f in files)
        rows.append(f'<tr><td>{t.strftime("%Y-%m-%d %H:%M")}</td><td><a href="{REPO}/commit/{sha}"><code>{sha[:10]}</code></a></td><td>{links}</td></tr>')
    dated = open(DATED_UNTIL).read().strip() if os.path.exists(DATED_UNTIL) else ""
    before = (f'<p>Before {html.escape(dated.split()[1]) if len(dated.split()) > 1 else "then"}, each version was a file of its own, dated, in a folder per day: '
              f'they are all in <a href="{REPO}/tree/{dated.split()[0]}/dashboard-snapshots">the last tree that held them</a>, and in git\'s history.</p>') if dated else ""
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>Dashboard Versions</title><style>:root{{--bg:#fbfaf7;--ink:#1f2328;--muted:#5b6470;--line:#e6e2da}}@media (prefers-color-scheme:dark){{:root{{--bg:#16181d;--ink:#e6e6e6;--muted:#9aa3ad;--line:#2d3139}}}}
body{{background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,sans-serif;margin:0 auto;max-width:900px;padding:16px}}a{{color:inherit}}td{{border-top:1px solid var(--line);padding:3px 8px;vertical-align:top}}p{{color:var(--muted)}}</style></head><body>
<h1>The dashboard's versions</h1>
<p>Each change to the Hazel Work Dashboard (the page, and its closed tickets' page) is a commit to <code>dashboard-snapshots/index.html</code> or <code>closed.html</code>, its time the commit's, newest first. To see one as it was: <code>git show &lt;commit&gt;:dashboard-snapshots/index.html &gt; then.html</code>, then open it.</p>
{before}
<table><tbody>{"".join(rows)}</tbody></table></body></html>
"""

wrote = []
for name, src in (("index.html", os.path.join(HERE, "index.html")), ("closed.html", os.path.join(HERE, "closed.html"))):
    if not os.path.exists(src):
        continue
    page, kept = open(src).read(), os.path.join(SNAPS, name)
    if os.path.exists(kept) and body(open(kept).read()) == body(page):
        continue
    os.makedirs(SNAPS, exist_ok=True)
    open(kept, "w").write(page)
    git("add", os.path.relpath(kept, NOTES))
    wrote.append(name)
if wrote:
    now = datetime.now().astimezone()
    git("commit", "-q", "-m", f"Snapshot {now.strftime('%Y-%m-%d %H:%M %Z')}: {', '.join(wrote)}")
    # (the versions list, from the log including this commit, in a commit of its own)
    open(os.path.join(SNAPS, "versions.html"), "w").write(versions_page())
    git("add", "dashboard-snapshots/versions.html")
    if git("diff", "--cached", "--name-only").strip():
        git("commit", "-q", "-m", f"Versions {now.strftime('%Y-%m-%d %H:%M %Z')}")
    print(f"wrote dashboard-snapshots/{', '.join(wrote)}")
else:
    print("unchanged")

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

# The public copy: matthewhammer.org/hazel/dashboard/, in the homepage's repository,
# by site_publish.py (^ticket(181), 2026-10-16). Until then it was written here, at
# this repository's root, served at matthewhammer.org/hazel-work-notes/; the root's
# index.html and closed.html now redirect to the new address.
r = subprocess.run([sys.executable, os.path.join(HERE, "site_publish.py")], capture_output=True, text=True, timeout=300)
if (r.stdout + r.stderr).strip():
    print((r.stdout + r.stderr).strip())

upstream = subprocess.run(["git", "-C", NOTES, "rev-parse", "-q", "--verify", "@{u}"], capture_output=True).returncode == 0
if not upstream:
    git("push", "-q", "-u", "origin", "HEAD")
    print("pushed, and set the upstream")
elif (ahead := git("rev-list", "--count", "@{u}..HEAD").strip()) != "0":
    git("push", "-q")
    print(f"pushed {ahead} commit(s)")
