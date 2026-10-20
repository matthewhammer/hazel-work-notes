#!/usr/bin/env python3
"""Save index.html and closed.html, and data.json, into ~/hazel-work-notes, commit them, publish a public copy (site_publish.py), and push to GitHub.

  python3 ~/localhost-index/log_notes.py

Run by publish.py right after update.py. Since ^ticket(417) (2026-10-19, Matthew: "revise the dashboard repo so that the
current dashboard is kept, and no prior snapshots are kept as separate files, but only as part of the git history"; the
dated files had reached 1,793 and 341 MB on the laptop, ~95 MB a day, ^ticket(391)) each page is one path,

  dashboard-snapshots/index.html    the page exactly as served on http://localhost:8000/
  dashboard-snapshots/closed.html   the closed tickets' page

and every earlier version is in git's history: each commit that changes one is a snapshot, its time the commit's. The dated
files from before (dashboard-snapshots/<YYYY>/<MM>/<DD>/...) left the tree in that change and are still in history.

Since ^ticket(428) (2026-10-19, Matthew: "re-org of dashboard repo so that it scales locally as a checked out copy, and in GH,
over time") the history grows by real changes only. Measured that evening: packed, it grew ~2.9 MB a day (633 commits on
10-18), and most of it was full copies of the two big files, closed.html and data.json (1.1 MB each): git stores a file's
versions as deltas, but a chain is at most ~50 long, so every ~50 versions of a big file cost a full copy again. And most
versions were not changes: closed.html was rewritten on 22 of 31 publishes that closed nothing (its version meta, its own
"Updated" time, and the hover cards' scripts, which carry every ticket's and PR's summary), and data.json's 1 MB of closed
tickets was copied with every change to the open ones. So, one commit per publish, holding:

  - a page, when it differs from the kept one in more than what changes on every publish (`VOLATILE`: the "Updated" lines,
    the dashboard-version meta, the hover cards' scripts); index.html besides only when the data changed, or an hour after
    its last snapshot (the quarter-hour runs refresh only what comes from GitHub, and the next snapshot has it);
  - the data, each file when it changes: dashboard-data/data.json, all but the closed tickets, and the closed tickets by
    the month each was closed, dashboard-data/closed/<YYYY-MM>.json (each in the order of the list `closed_tickets`), so a
    closing rewrites only its month's file, never a list that grows for years. data.json as served is the first with
    "closed_tickets" set to the months, newest first: `python3 dashboard/data_whole.py` prints it, from the working tree
    or any commit.

dashboard-snapshots/versions.html, the list of the pages' versions with links to each on GitHub, is made here on every run
from the last 30 days of git log, and is no longer committed (it is in .gitignore): GitHub's history of each file is the
same list, and the public copy links to it.

Pushing is tried on every run, so commits made while offline go up on the next run that has a network."""
import html, json, os, re, subprocess, sys, time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
NOTES = os.path.expanduser("~/hazel-work-notes")
SNAPS = os.path.join(NOTES, "dashboard-snapshots")
REPO = "https://github.com/matthewhammer/hazel-work-notes"
# (what changes on every publish, left out when deciding whether a page changed)
VOLATILE = re.compile(r'<p class="note">Updated [^<]*<code>'
                      r'|Updated \d{4}-\d\d-\d\d \d\d:\d\d [A-Z]{2,5}'
                      r'|<meta name="dashboard-version" content="[^"]*">'
                      r'|<script> /\* A card for each [\s\S]*?</script>')
INDEX_EVERY = 3600   # (seconds: index.html with no change to the data, at most this often)
VERSIONS_DAYS = 30
# (the last commit whose tree held the dated snapshot files, before ^ticket(417) took them out)
DATED_UNTIL = os.path.join(SNAPS, ".dated-until")

def git(*args):
    r = subprocess.run(["git", "-C", NOTES, *args], capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        sys.exit(f"git {' '.join(args)}: {(r.stderr or r.stdout).strip()[:300]}")
    return r.stdout

def body(text):
    return VOLATILE.sub("", text)

def versions_page():
    """The versions of the two pages in the last VERSIONS_DAYS days, from git log: when, which, and links to each on GitHub."""
    rows, PAGES = [], ("dashboard-snapshots/index.html", "dashboard-snapshots/closed.html")
    # (one pass: each commit's hash and time, then the files it changed; a commit per line of git show was too slow for long)
    for block in git("log", f"--since={VERSIONS_DAYS} days ago", "--format=%x00%H %cI", "--name-only", "--", *PAGES).split("\0")[1:]:
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
<p>Each change to the Hazel Work Dashboard (the page, and its closed tickets' page) is a commit to <code>dashboard-snapshots/index.html</code> or <code>closed.html</code>, its time the commit's, newest first: the last {VERSIONS_DAYS} days here, and all of them in GitHub's history of <a href="{REPO}/commits/main/dashboard-snapshots/index.html">the page</a> and <a href="{REPO}/commits/main/dashboard-snapshots/closed.html">the closed page</a>. The page is kept when the data behind it changes, and at most hourly otherwise; the closed page when a ticket is closed or a closed one changes. To see one as it was: <code>git show &lt;commit&gt;:dashboard-snapshots/index.html &gt; then.html</code>, then open it.</p>
{before}
<table><tbody>{"".join(rows)}</tbody></table></body></html>
"""

def write(path, text):
    """Write a kept file when its text changed; say whether it did."""
    full = os.path.join(NOTES, path)
    if os.path.exists(full) and open(full).read() == text:
        return False
    os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, "w").write(text)
    git("add", path)
    return True

wrote = []
# The data first (whether it changed decides index.html): all but the closed tickets, and the closed tickets by month.
live = json.load(open(os.path.join(HERE, "data.json")))
months = {}
for t in live.pop("closed_tickets", []):
    when = str(t.get("closed_at") or t.get("closed") or "")
    months.setdefault(when[:7] if re.match(r"\d{4}-\d\d", when) else "undated", []).append(t)
data_changed = False
parts = [("dashboard-data/data.json", live, "data")] + [(f"dashboard-data/closed/{m}.json", ts, f"closed {m}") for m, ts in sorted(months.items())]
for path, part, name in parts:
    if write(path, json.dumps(part, indent=1, ensure_ascii=False)):
        wrote.append(name)
        data_changed = True
# (a month no longer in the list, its file gone; and closed_tickets.json, the one file of the evening before the months)
for path in git("ls-files", "dashboard-data/closed/", "dashboard-data/closed_tickets.json").split():
    if path not in [p for p, _, _ in parts]:
        git("rm", "-q", path)
        wrote.append("- " + os.path.basename(path))
        data_changed = True

last_index = git("log", "-1", "--format=%ct", "--", "dashboard-snapshots/index.html").strip()
index_due = data_changed or not last_index or time.time() - int(last_index) >= INDEX_EVERY
for name, src in (("index.html", os.path.join(HERE, "index.html")), ("closed.html", os.path.join(HERE, "closed.html"))):
    if not os.path.exists(src) or (name == "index.html" and not index_due):
        continue
    page, kept = open(src).read(), os.path.join(SNAPS, name)
    if os.path.exists(kept) and body(open(kept).read()) == body(page):
        continue
    write(os.path.relpath(kept, NOTES), page)
    wrote.append(name)

# (versions.html: made here, never committed; taken out of the index once, in the first commit after ^ticket(428))
if git("ls-files", "dashboard-snapshots/versions.html").strip():
    git("rm", "-q", "--cached", "dashboard-snapshots/versions.html")
    wrote.append("versions.html untracked")
if wrote:
    git("commit", "-q", "-m", f"Dashboard {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M %Z')}: {', '.join(wrote)}")
    print(f"committed: {', '.join(wrote)}")
else:
    print("unchanged")
os.makedirs(SNAPS, exist_ok=True)
open(os.path.join(SNAPS, "versions.html"), "w").write(versions_page())

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
