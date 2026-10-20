#!/usr/bin/env python3
"""Regenerate index.html from data.json, with live PR status from GitHub (gh).

  python3 ~/localhost-index/update.py

Run by publish.py (cron, every minute: within a minute of any change to
data.json, and on the quarter hour), followed by log_notes.py, which commits
the page to ~/hazel-work-notes and pushes it; the last run's output is in
update.log.

data.json holds what only we know: which ports serve what, which PRs are
against the performance tracking issue, and our tickets: the open ones, the
current one, and the closed ones, which go on a page of their own,
closed.html. Titles, state, CI, review and mergeability come from GitHub each
run."""
import html, json, os, re, subprocess, sys
from datetime import datetime
from zoneinfo import ZoneInfo

# Times on the page are Matthew's local time: Mountain Time, Colorado.
LOCAL = ZoneInfo("America/Denver")

# The dashboard's version: what each version adds is in VERSIONS.md, next to this file's folder.
VERSION = "0.0.3"

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "data.json")))
REPO = "hazelgrove/hazel"

def gh_pr(n):
    fields = "number,title,url,state,isDraft,baseRefName,headRefName,statusCheckRollup,reviewDecision,mergeable,updatedAt"
    r = subprocess.run(["gh", "pr", "view", str(n), "--repo", REPO, "--json", fields],
                       capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        # no page rather than a page of unknowns: the last good one stays
        sys.exit(f"gh could not read #{n}: {r.stderr.strip()[:200]}")
    return json.loads(r.stdout)

prs = {}
def pr(n):
    if n not in prs:
        prs[n] = gh_pr(n)
    return prs[n]

e = html.escape

# Links made the same way everywhere on the page: a report of the
# Hazel reports series (^report(N)), a hazelgrove/hazel issue or PR (#NNNN), and a
# commit (10 hex digits). Text already inside a link is left alone.
SERIES_PUBLIC = "https://matthewhammer.org/hazel/reports/"
SERIES_LOCAL = "http://localhost:8131/series/"
PUBLISHED = os.path.expanduser("~/matthewhammer.github.io/hazel/reports")

def series_url(n):
    nnn = f"{int(n):03d}"
    if os.path.isdir(os.path.join(PUBLISHED, nnn)):
        return SERIES_PUBLIC + nnn + "/"
    return SERIES_LOCAL + nnn + "/"

LINKABLE = re.compile(
    r"(?P<tk>\^ticket\((?P<tid>\d+)\))"
    r"|(?P<rep>\^(?:report|issue)\((?P<rn>\d+)\))"
    r"|(?P<series>\b(?:[Ii]ssues?|[Rr]eports?) (?P<n>0\d\d)\b)"
    r"|(?P<gh>(?<![\w/#&])#(?P<num>\d{4})\b)"
    r"|(?P<sha>\b(?=[0-9a-f]*\d)(?=[0-9a-f]*[a-f])[0-9a-f]{10}\b)"
    r"|(?P<step>(?<![\w/#&])#(?P<sid>\d{1,3})\b)")

# Our tickets, by number: "^ticket(10)" links to its row, on this page while
# it is open and on closed.html once it is closed. Numbers are never reused.
# (Matthew's syntax since 2026-10-14, as our numbers will reach the
# thousands, past where "#1000" could pass for a PR; an old "#10" in a text
# reads as ^ticket(10) too.) Shown in monospace, "^ticket(" and ")" bold.
# The same for the reports of the Hazel reports series: ^report(13)
# links to its page (a report is never "issue 013" now: "issue" is GitHub's).
def chip(kind, n):
    return f'<code class="ref"><b>^{kind}(</b>{int(n)}<b>)</b></code>'
def tk(n):
    return chip("ticket", n)
def tk_plain(n):
    return f"^ticket({n})"
TICKETS = sorted(data["tickets"], key=lambda t: t["id"])
CLOSED = sorted(data.get("closed_tickets", []), key=lambda t: t["id"])
OPEN_IDS = {t["id"] for t in TICKETS}
CLOSED_IDS = {t["id"] for t in CLOSED}
# (^ticket(428), 2026-10-19: the closed page had reached 1.1 MB, a new copy in two repositories' history at every closing, and
# grew ~120 KB a day) The closed tickets by the month each was closed: closed.html holds this month's, and each earlier month
# has a page of its own, closed-<YYYY-MM>.html, which stops changing once its month is over. closed-where.json maps each
# ticket on an earlier month's page to that page, so a link made before it moved (closed.html#ticket-N) still finds it.
# DASHBOARD_MONTH (YYYY-MM) stands in for this month, to try a month to come.
def closed_month(t):
    w = str(t.get("closed_at") or t.get("closed") or "")
    return w[:7] if re.match(r"\d{4}-\d\d", w) else None
THIS_MONTH = os.environ.get("DASHBOARD_MONTH") or datetime.now(LOCAL).strftime("%Y-%m")
def closed_page_of(t):
    m = closed_month(t)
    return f"closed-{m}.html" if m and m < THIS_MONTH else "closed.html"
CLOSED_PAGE = {t["id"]: closed_page_of(t) for t in CLOSED}
CURRENT = next((t for t in TICKETS if t["id"] == data.get("current_ticket")), None)
# The work queue: a few open tickets, in the order we mean to take them
# (data.json's "queue", ticket numbers, front first). Short on purpose: the
# whole backlog is below it. A closed or unknown number is left out, and said.
BY_ID = {t["id"]: t for t in TICKETS}
QUEUE = [BY_ID[n] for n in data.get("queue", []) if n in BY_ID]
# (^ticket(487), Matthew 2026-10-20: "the 'blocked on Matthew' list seems inaccurate -- it has tickets with no such tag.") the
# queue's categories at its end, whatever data.json's order: a line is drawn above a category's first ticket, so a ticket
# tagged in the middle of the queue put every untagged one after it under "Blocked on Matthew". A stable sort: the untagged
# in data.json's order, then the long runs, then the blocked (QUEUE_GROUPS' order), so the numbers, the table and the
# outline all agree.
QUEUE_CATEGORIES = ["long run", "blocked on Matthew"]
QUEUE = sorted(QUEUE, key=lambda t: next((i for i, g in enumerate(QUEUE_CATEGORIES) if g in t.get("tags", [])), -1))
for n in data.get("queue", []):
    if n not in BY_ID:
        print(f"queue: ^ticket({n}) is not an open ticket; left out", file=sys.stderr)
QPOS = {t["id"]: i + 1 for i, t in enumerate(QUEUE)}
# The current ticket waits on Matthew (current_waiting: true, or a line saying
# what for): a raised hand and a question mark, boxed, wherever it is named,
# and in the page's title, so a tab shows it unopened.
WAITING = bool(CURRENT and data.get("current_waiting"))
WAITING_FOR = data.get("current_waiting") if isinstance(data.get("current_waiting"), str) else ""
HAND = "\u270b\u2754"
def hand():
    tip = "Waiting on Matthew" + (": " + WAITING_FOR if WAITING_FOR else "")
    return f'<span class="waiting" title="{e(tip)}" aria-label="{e(tip)}">{HAND}</span>' if WAITING else ""

def ticket_href(n, on):
    """The link to ticket n from the page `on` ("index", or a closed page's file name: closed.html, closed-<YYYY-MM>.html)."""
    if n in OPEN_IDS:
        return f"#ticket-{n}" if on == "index" else f"./#ticket-{n}"
    if n in CLOSED_IDS:
        page = CLOSED_PAGE.get(n, "closed.html")
        return f"#ticket-{n}" if on == page else f"{page}#ticket-{n}"
    return None

def linkify(text, on="index"):
    out, pos, depth = [], 0, 0
    # walk tags; only text outside <a>...</a> and outside tags gets links
    for m in re.finditer(r"<[^>]+>", text):
        out.append(link_text(text[pos:m.start()], on) if depth == 0 else text[pos:m.start()])
        tag = m.group(0)
        if re.match(r"<a[\s>]", tag):
            depth += 1
        elif tag.startswith("</a"):
            depth = max(0, depth - 1)
        out.append(tag)
        pos = m.end()
    out.append(link_text(text[pos:], on) if depth == 0 else text[pos:])
    return "".join(out)

def link_text(t, on="index"):
    def sub(m):
        if m.group("rep") or m.group("series"):
            n = int(m.group("rn") or m.group("n"))
            return f'<a href="{series_url(n)}">{chip("report", n)}</a>'
        if m.group("gh"):
            return f'<a href="https://github.com/{REPO}/issues/{m.group("num")}">{m.group("gh")}</a>'
        if m.group("sha"):
            return f'<a href="https://github.com/{REPO}/commit/{m.group("sha")}"><code>{m.group("sha")}</code></a>'
        n = int(m.group("tid") or m.group("sid"))
        href = ticket_href(n, on)
        return f'<a href="{href}">{tk(n)}</a>' if href else tk(n)
    return LINKABLE.sub(sub, t)

def pr_cell(p):
    return f'<a href="{e(p["url"])}">#{p["number"]}</a> {e(p.get("title", ""))}'

def state(p):
    s = (p.get("state") or "").lower()
    if s == "open" and p.get("isDraft"):
        return "draft"
    return s or "?"

def ci(p):
    checks = p.get("statusCheckRollup") or []
    if not checks:
        return "no checks"
    ok, bad, wait, skip = [], [], [], []
    for c in checks:
        name = c.get("name") or c.get("context") or "?"
        concl = (c.get("conclusion") or c.get("state") or "").upper()
        status = (c.get("status") or "").upper()
        if status and status != "COMPLETED":
            wait.append(name)
        elif concl in ("SUCCESS", "NEUTRAL"):
            ok.append(name)
        elif concl == "SKIPPED":
            skip.append(name)
        elif concl in ("PENDING", "EXPECTED", "QUEUED", ""):
            wait.append(name)
        else:
            bad.append(f"{name} ({concl.lower()})")
    out = []
    if bad:
        out.append(f'<span class="bad">✗ {len(bad)} failing</span>: ' + e(", ".join(bad)))
    if wait:
        out.append(f'<span class="wait">… {len(wait)} pending</span>')
    if ok:
        out.append(f'<span class="good">✓ {len(ok)} passed</span>')
    return "; ".join(out) or e(f"{len(skip)} skipped")

def review(p):
    r = p.get("reviewDecision") or ""
    return {"APPROVED": "approved", "CHANGES_REQUESTED": "changes requested",
            "REVIEW_REQUIRED": "review required"}.get(r, "no review yet")

# Changes requested is the one review state that waits on Matthew: a bright
# chip, hard to miss (his ask, 2026-10-14), linking to the PR's reviews.
def review_cell(p):
    if (p.get("reviewDecision") or "") == "CHANGES_REQUESTED":
        url = p.get("url", "") + "/files"
        return (f'<a class="changes-chip" href="{e(url)}" title="A reviewer asked for changes: they wait on Matthew">'
                f'⚠️ changes requested</a>')
    return e(review(p))

def merge(p):
    m = p.get("mergeable") or ""
    return {"MERGEABLE": "mergeable", "CONFLICTING": '<span class="bad">conflicts</span>'}.get(m, e(m.lower() or "?"))

def date(p):
    d = p.get("updatedAt") or ""
    return d[:10]

rows = []
for r in data["ports"]:
    if "pr" in r:
        p = pr(r["pr"])
        first = pr_cell(p)
        repo = e(r["repo"])
        branch = f'<code>{e(r["branch"])}</code>' + (f' (into <code>{e(r["base"])}</code>)' if r.get("base") else "")
    else:
        first = "— " + e(r["name"])
        repo = r["repo_html"]
        branch = f'<code>{e(r["branch"])}</code>' + (f' {e(r["branch_note"])}' if r.get("branch_note") else "")
    links = "<br>".join(f'<a href="{e(u)}">{e(t)}</a>' for t, u in r["links"]) or "not served"
    rows.append(f"<tr><td>{first}</td><td>{repo}<br>{branch}</td><td>{links}</td></tr>")

def status_rows(ns, notes=None):
    out = []
    for n in ns:
        p = pr(n)
        note = f"<td>{linkify(e(notes.get(n, '')))}</td>" if notes is not None else ""
        out.append(
            f"<tr><td>{pr_cell(p)}</td><td><code>{e(p.get('headRefName', ''))}</code> → <code>{e(p.get('baseRefName', ''))}</code></td>"
            f"<td>{e(state(p))}</td><td>{ci(p)}</td><td>{review_cell(p)}</td><td>{merge(p)}</td><td>{date(p)}</td>{note}</tr>")
    return "\n".join(out)

def gh_json(args, what, missing_ok=False):
    r = subprocess.run(["gh", *args], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        if missing_ok and "HTTP 404" in r.stderr:
            return None
        # as for a PR: no page rather than a page of unknowns
        sys.exit(f"gh could not read {what}: {r.stderr.strip()[:200]}")
    return r.stdout

# Repositories we deploy by pushing to a branch, not through PRs: the
# branch's latest commit, each project's version (the newest "## X.Y.Z
# (date)" heading of its VERSIONS.md), and whether GitHub Pages has
# deployed that very commit yet.
VERSION_HEAD = re.compile(r"^## (\S+) \((\d{4}-\d{2}-\d{2})\)", re.M)

def repo_row(r):
    name, branch = r["repo"], r["branch"]
    url = f"https://github.com/{name}"
    head = json.loads(gh_json(["api", f"repos/{name}/commits/{branch}"], f"{name}@{branch}"))
    sha, c = head["sha"], head["commit"]
    latest = (f'<a href="{url}/commit/{sha}"><code>{sha[:7]}</code></a> {e(c["message"].splitlines()[0])} '
              f'<span class="note">({c["committer"]["date"][:10]})</span>')
    versions = []
    for label, path in r.get("versions", []):
        text = gh_json(["api", "-H", "Accept: application/vnd.github.raw", f"repos/{name}/contents/{path}?ref={branch}"],
                       f"{name}/{path}")
        m = VERSION_HEAD.search(text)
        versions.append(f'{e(label)} <a href="{url}/blob/{branch}/{path}">{e(m.group(1) if m else "?")}</a>'
                        + (f' <span class="note">({m.group(2)})</span>' if m else ""))
    out = gh_json(["api", f"repos/{name}/pages/builds/latest"], f"{name}'s Pages", missing_ok=True)
    if out is None:
        deployed = "no Pages site"
    else:
        b = json.loads(out)
        status, at = b.get("status") or "?", (b.get("commit") or "")[:7]
        if status == "built" and b.get("commit") == sha:
            deployed = f'<span class="good">✓ deployed</span> <code>{at}</code>'
        elif status == "errored":
            deployed = f'<span class="bad">✗ build failed</span> <code>{at}</code>'
        elif status == "built":
            deployed = f'<span class="wait">… not yet</span>: live is <code>{at}</code>'
        else:
            deployed = f'<span class="wait">… {e(status)}</span> <code>{at}</code>'
    live = "".join(f'<br><a href="{e(u)}">{e(t)}</a>' for t, u in r.get("live", []))
    prs_open = json.loads(gh_json(["pr", "list", "--repo", name, "--state", "open", "--json", "number,title,url"],
                                  f"{name}'s PRs"))
    prs_cell = "<br>".join(f'<a href="{e(p["url"])}">#{p["number"]}</a> {e(p["title"])}' for p in prs_open) or "none"
    return (f'<tr><td><a href="{url}">{e(name)}</a><br><code>{e(branch)}</code></td><td>{latest}</td>'
            f'<td>{"<br>".join(versions) or "—"}</td><td>{deployed}{live}</td><td>{prs_cell}</td>'
            f'<td>{linkify(r.get("note", ""))}</td></tr>')

repo_rows = "\n".join(repo_row(r) for r in data.get("repos", []))

other = [o["pr"] for o in data.get("other_prs", [])]
other_notes = {o["pr"]: o.get("note", "") for o in data.get("other_prs", [])}

# A link into the local report sources becomes the public page once that
# report is published (^report(1) is the sources' root), so a step's From and
# its text point at the same place.
def series_link(url):
    m = re.match(r"http://localhost:8131/(?:series/)?(?:(\d{3})/)?(.*)$", url)
    if not m:
        return url
    return series_url(m.group(1) or "001") + m.group(2)

def from_cell(s, on="index"):
    text = e(s["source"])
    return f'<a href="{e(series_link(s["url"]))}">{text}</a>' if s.get("url") else linkify(text, on)

def num_cell(t):
    return (f'<td class="num"><a class="anchor" href="#ticket-{t["id"]}">{tk(t["id"])}</a>'
            f'<button class="copy" type="button" data-anchor="ticket-{t["id"]}" title="Copy a link to {tk_plain(t["id"])}">copy link</button></td>')

# a ticket's tags (data.json: a ticket's "tags"), each a chip: "long run", a
# ticket to do while Matthew is away (^ticket(114)); "blocked on Matthew", one
# that waits for his response (^ticket(115)); any other tag as itself
TAG_CHIPS = {"long run": ("longrun", "🌙 long run", "A long run: to do while Matthew is away from the keyboard"),
             "blocked on Matthew": ("blocked", "🪷 blocked on Matthew", "Blocked on Matthew's response: nothing to do until he answers")}
# the queue's own categories, at its end, in this order: each tag's tickets under a line of their own
QUEUE_GROUPS = [("long run", "🌙 <b>Long runs</b>: for when Matthew is away from the keyboard"),
                ("blocked on Matthew", "🪷 <b>Blocked on Matthew</b>: waiting for his response")]
assert [g for g, _ in QUEUE_GROUPS] == QUEUE_CATEGORIES   # (the sort above, in the same order)
def group_of(t):
    return next((g for g, _ in QUEUE_GROUPS if g in t.get("tags", [])), None)
TAG_ICON = lambda t: "".join(TAG_CHIPS[g][1].split(" ")[0] + " " for g in t.get("tags", []) if g in TAG_CHIPS)
def tag_chips(t, sep="<br>"):
    return "".join(f'{sep}<span class="badge {TAG_CHIPS.get(g, ("tag",))[0]}" title="{e(TAG_CHIPS.get(g, (0, 0, g))[2])}">'
                   f'{e(TAG_CHIPS.get(g, (0, g))[1])}</span>' for g in t.get("tags", []))

# (^ticket(190), Matthew 2026-10-17) what a ticket is about, as chips: hazel,
# dress-up, performance, dashboard, operations (one, several or none), from its area
# (data.json's "chips" on a ticket, when given, instead); and a filter bar of
# them over the work queue and the backlog
ABOUT = [("hazel", "hazel", r"hazel|#2\d{3}|livelit|\bseries\b"), ("dress-up", "dress-up", r"dress[ -]?up"),
         ("performance", "performance", r"\bperf"), ("dashboard", "dashboard", r"dashboard"),
         # (Matthew 2026-10-19) operations: the machines and services the work runs on, such as the laptop's battery
         ("operations", "operations", r"\boperations\b")]
# (Matthew 2026-10-20) and the next meeting's tickets: those tagged "meeting <its date>" (data.json's next_meeting)
_NM = data.get("next_meeting") or {}
MEETING_TAG = f'meeting {_NM["date"]}' if _NM.get("date") else None
if MEETING_TAG:
    ABOUT.append(("meeting", f'🤝 meeting {_NM["date"][5:]}' + (f' ({_NM["with"]})' if _NM.get("with") else ""), None))
def about(t):
    # (^ticket(196): a ticket's own "chips" add to those its area gives, as hazel on 16-19, whose areas say only CI or performance)
    a, own = t.get("area", "").lower(), t.get("chips") if isinstance(t.get("chips"), list) else []
    out = [c for c, _, rx in ABOUT if rx and (c in own or re.search(rx, a))]
    if MEETING_TAG and MEETING_TAG in (t.get("tags") or []):
        out.append("meeting")
    return out
def about_chips(t, sep="<br>"):
    return "".join(f'{sep}<span class="badge about about-{c}" title="about {c}">{c}</span>' for c in about(t))
def about_filter(table):
    return (f'<div class="about-filter" data-for="{table}"><span class="note">show:</span> ' +
            "".join(f'<button type="button" data-about="{c}" aria-pressed="false">{label}</button>' for c, label, _ in ABOUT) +
            ' <button type="button" data-about="" class="about-all" aria-pressed="true">all</button></div>')

# a ticket's status chip beside "current": "queued", for a ticket in the work
# queue that is not the current one (its place in line is its tooltip)
def queue_badge(t):
    if t["id"] not in QPOS or t is CURRENT:
        return ""
    return f'<br><a class="badge queued" href="#queue" title="number {QPOS[t["id"]]} in the work queue">queued</a>'

# Our tickets: data.json's next_ticket is never reused, so a number names one
# ticket for good, open or closed.
ticket_rows = "\n".join(
    f'<tr id="ticket-{t["id"]}" data-about="{" ".join(about(t))}"{" class=\"current\"" if t is CURRENT else ""}>{num_cell(t)}'
    f'<td>{e(t.get("area", ""))}{"<br><span class=\"badge\">current</span>" + (" " + hand() if WAITING else "") if t is CURRENT else ""}'
    f'{queue_badge(t)}{tag_chips(t)}{about_chips(t)}</td>'
    f'<td>{linkify(t["text"])}</td><td>{from_cell(t)}</td></tr>'
    for t in TICKETS)

def elapsed(minutes):
    d, h, m = minutes // 1440, minutes % 1440 // 60, minutes % 60
    return (f"{d} d " if d else "") + (f"{h} h " if d or h else "") + f"{m} min"

# The current ticket: the one we are working on, first on the page, with when
# we started it (current_since) and how long ago that was, kept up to date in
# the browser between regenerations.
current_section = ""
if CURRENT:
    t = CURRENT
    note = data.get("current_note", "")
    since_line = ""
    if data.get("current_since"):
        since = datetime.fromisoformat(data["current_since"])
        mins = max(0, int((datetime.now(LOCAL) - since).total_seconds() // 60))
        since_line = (f'<p class="since">Started <b>{e(since.astimezone(LOCAL).strftime("%a %b %-d, %-I:%M %p %Z"))}</b>'
                      f' · elapsed <b data-since="{e(since.isoformat())}"></b></p>')
    current_section = f"""<h2 id="current">Current ticket: <a href="#ticket-{t["id"]}">{tk(t["id"])}</a> {hand()}</h2>
<div class="current-box">
<p class="note">{e(t.get("area", ""))} · from {from_cell(t)}{tag_chips(t, " ")}</p>
{since_line}
<p>{linkify(t["text"])}</p>
{f'<p><b>Now:</b> {linkify(note)}</p>' if note else ""}
</div>
"""

# The side outline (as on fumola.org): the sections, and under Next steps
# every step by its number, so a step is one click away.
def short(html_text, n=46):
    t = re.sub(r"<[^>]+>", "", html_text)
    t = html.unescape(t)
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"

# The work queue: its tickets in order, each a line, linking to its full row
# in the backlog. Short on purpose; we push to its front or its back, and
# reorder it, as we go.
def queue_row(i, t):
    tag = ' <span class="badge">current</span>' + (" " + hand() if WAITING else "") if t is CURRENT else ""
    return (f'<tr data-about="{" ".join(about(t))}"><td class="num">{i}</td><td class="tkcell"><a href="#ticket-{t["id"]}">{tk(t["id"])}</a>{tag}{tag_chips(t)}{about_chips(t)}</td>'
            f'<td>{e(t.get("area", ""))}</td><td>{e(short(t["text"], 140))}</td></tr>')
# (the queue's categories, at its end, each under a line of its own: the long runs, the work for when
# Matthew is away; then the tickets blocked on his response. Shown in data.json's order: a line goes
# above a category's first ticket)
def queue_rows():
    rows, last = [], None
    for i, t in enumerate(QUEUE):
        g = group_of(t)
        if g and g != last:
            rows.append(f'<tr class="group-head {TAG_CHIPS[g][0]}-head"><td colspan="4">{dict(QUEUE_GROUPS)[g]}</td></tr>')
        last = g
        rows.append(queue_row(i + 1, t))
    return "\n".join(rows)

queue_section = f"""<h2 id="queue">Work Queue (Active Tickets)</h2>
<p class="note">What we mean to do next, in order: a few tickets, not the backlog. We push a ticket onto the front or the back, and reorder as we go; a ticket leaves the queue when it closes. Each links to its full row in <a href="#backlog">the backlog</a>.</p>
""" + (about_filter("queue") + f"""<table class="queue" data-about-table="queue">
<tr><th class="num">Next</th><th class="tkcell">Ticket</th><th class="area">Area</th><th>Ticket</th></tr>
{queue_rows()}
</table>
""" if QUEUE else '<p><i>Empty: push a ticket onto it.</i></p>\n')

def entry(href, text, sub=False, n=None):
    # (n: a ticket, shown as its chip before the text)
    label = (tk(n) + " " if n is not None else "") + e(text)
    return f'<li{" class=\"sub\"" if sub else ""}><a href="{href}">{label}</a></li>'

# (^ticket(292), Matthew 2026-10-18: "so I don't have to click so much") every
# URL in the last column of Localhost ports, just before the current ticket
LOCAL_URLS = {}
for r in data["ports"]:
    for t, u in r["links"]: LOCAL_URLS.setdefault(u, t)   # (in the table's order, each URL once)
LOCAL_URLS = list(LOCAL_URLS.items())
# (^ticket(390), Matthew 2026-10-19: "add indentation to: local ports served list, work queue, full backlog"; "work queue and local
# ports list are open by default, but can be collapsed with those triangles"; "full backlog is collapsed by default, but can be
# expanded") a list in the outline as a group: its heading with a triangle, its entries indented under it, folded or not as it
# starts (open: data-open), each reader's choice kept in their browser ("dash-grp-<name>"), whether beside the page or in the nav bar
def group(name, href, text, kids, open_default):
    on = "true" if open_default else "false"
    return (f'<li class="grp" data-grp="{name}" data-open="{on}"><div class="grp-row"><button type="button" class="grp-tw" aria-expanded="{on}" '
            f'aria-label="{"Fold" if open_default else "Unfold"} {e(text)}">{"▾" if open_default else "▸"}</button><a href="{href}">{text}</a></div>'
            f'<ul class="kids"{"" if open_default else " hidden"}>' + "".join(kids) + '</ul></li>')
local_entries = [group("local", "#ports", e(f"Local URLs ({len(LOCAL_URLS)})"),
                       [f'<li><a href="{e(u)}">{e(t)}</a></li>' for u, t in LOCAL_URLS], True)] if LOCAL_URLS else []

# (Matthew, 2026-10-19: "put the 'next meeting agenda, WIP' link into the nav bar ... near the top", public, to share with
# Cyrus) data.json's next_meeting {report, with, date}: the agenda report for the next meeting, first in the outline's links
NEXT_MEETING = data.get("next_meeting")
agenda_entry = (f'<li><a href="{series_url(NEXT_MEETING["report"])}" title="{e("With " + NEXT_MEETING["with"] + ", " + NEXT_MEETING["date"])}">'
                f'Next meeting agenda, WIP&nbsp;<span aria-hidden="true">↗</span></a></li>\n') if NEXT_MEETING else ""

outline = "\n".join(local_entries +
    ([f'<li><a href="#current">Current ticket: {tk(CURRENT["id"])}' + (f" {HAND}" if WAITING else "") + '</a></li>'] if CURRENT else []) + [
    group("queue", "#queue", e(f"Work Queue ({len(QUEUE)})"), [f'<li><a href="#ticket-{t["id"]}">{i + 1}. {tk(t["id"])} {TAG_ICON(t)}{e(short(t["text"]))}</a></li>' for i, t in enumerate(QUEUE)], True),
] + [
    entry("#ports", "Localhost ports"),
    entry("#other", "Other PRs we are tracking"),
    entry("#repos", "Repositories we deploy"),
    entry("#perf", "Performance Analysis and Improvement"),
    entry("#perf-prs", "Performance PRs", sub=True),
    entry("#integration", "Integration branches", sub=True),
    group("backlog", "#backlog", e(f"Full Backlog ({len(TICKETS)})"), [entry(f'#ticket-{t["id"]}', short(t["text"]), n=t["id"]) for t in TICKETS], False),
] + [entry("closed.html", f"Closed tickets ({len(CLOSED)})")])

issue = data["tracking_issue"]
now = datetime.now(LOCAL).strftime("%Y-%m-%d %H:%M %Z")
page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{HAND + ' ' if WAITING else ''}Hazel Work Dashboard</title>
<style>
  :root {{ color-scheme: light dark; --line: #d0d0d0; --muted: #666; --good: #1a7f37; --bad: #cf222e; --wait: #9a6700; --ops: #c2410c; }}
  @media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --line: #444; --muted: #aaa; --good: #3fb950; --bad: #f85149; --wait: #d29922; --ops: #fb923c; }} }}
  :root[data-theme="light"] {{ color-scheme: light; }}
  :root[data-theme="dark"] {{ color-scheme: dark; --line: #444; --muted: #aaa; --good: #3fb950; --bad: #f85149; --wait: #d29922; --ops: #fb923c; }}
  body {{ font: 15px/1.45 system-ui, sans-serif; margin: 0; background: Canvas; color: CanvasText; }}
  code.ref {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.9em; white-space: nowrap; }}
  code.ref b {{ font-weight: 800; }}
  main {{ padding: 24px 16px 60px; }}
  h2, h3, tr[id] {{ scroll-margin-top: 12px; }}
  /* The outline, as on fumola.org: beside the page when there is room
     (48rem and up), and behind a button at the top left when there is not. */
  :root {{ --outline-w: 15rem; }}
  .outline {{ display: none; position: fixed; top: 0; left: 0; width: var(--outline-w); height: 100vh; box-sizing: border-box;
    padding: 1.5rem 0.75rem 3rem 1rem; overflow-y: auto; overscroll-behavior: contain; background: Canvas;
    border-right: 1px solid var(--line); font-size: 0.82rem; line-height: 1.4; z-index: 15; scrollbar-width: thin; }}
  .outline.is-open {{ display: block; width: auto; right: 0; padding: 4rem 1.25rem 3rem; font-size: 0.95rem; }}
  body.outline-open {{ overflow: hidden; }}
  .outline-label {{ font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); margin: 0 0 0.5rem; }}
  .outline ul {{ list-style: none; margin: 0 0 1.4rem; padding: 0; border-left: 1px solid var(--line); }}
  .outline a {{ display: block; padding: 0.18rem 0.6rem; margin-left: -1px; border-left: 2px solid transparent;
    color: var(--muted); text-decoration: none; }}
  .outline a:hover {{ color: CanvasText; }}
  .outline ul.outline-out {{ margin-bottom: 0.9rem; }}
  .outline li.sub a {{ padding-left: 1.4rem; font-size: 0.95em; }}
  /* (^ticket(390)) a list as a group: a triangle before its heading, its entries indented under it, folding */
  .outline .grp-row {{ display: flex; align-items: baseline; }}
  .outline .grp-row > a {{ flex: 1; min-width: 0; }}
  .outline .grp-tw {{ flex: none; width: 1.1em; padding: 0; border: 0; background: none; color: var(--muted); cursor: pointer; font: inherit; line-height: 1.4; }}
  .outline .grp-tw:hover {{ color: CanvasText; }}
  .outline ul.kids {{ margin: 0 0 0.4rem 1.6em; padding: 0 0 0 0.5em; border-left: 1px solid var(--line); font-size: 0.95em; }}
  .outline ul.kids[hidden] {{ display: none; }}
  #cnav #outline ul.kids {{ margin: 0 0 0.3rem 1.6em; padding-left: 0.5em; }}   /* (in the nav bar too: its own lists' rule is #cnav ul ul) */
  #cnav #outline ul.kids[hidden] {{ display: none; }}
  .outline a[aria-current="true"] {{ color: CanvasText; border-left-color: var(--good); }}
  .outline-toggle {{ display: flex; position: fixed; top: 0.6rem; left: 0.6rem; z-index: 20; width: 2.4rem; height: 2.4rem;
    align-items: center; justify-content: center; padding: 0; background: Canvas; color: CanvasText;
    border: 1px solid var(--line); border-radius: 5px; cursor: pointer; }}
  .outline-toggle svg {{ width: 1.1rem; height: 1.1rem; }}
  .outline-toggle .ex {{ display: none; }}
  .outline-toggle[aria-expanded="true"] .bars {{ display: none; }}
  .outline-toggle[aria-expanded="true"] .ex {{ display: block; }}
  @media (max-width: 47.99rem) {{ main {{ padding-top: 3.6rem; }} }}
  /* (Matthew, 2026-10-16) beside the page, the outline can be hidden (« at
     its top right, » to bring it back) and made wider or narrower by
     dragging its right edge (double-click: as it was); this browser keeps both */
  .outline-grip, .outline-hide, .outline-show {{ display: none; }}
  .outline-hide, .outline-show {{ position: fixed; top: 0.6rem; z-index: 20; width: 2rem; height: 2rem; align-items: center; justify-content: center;
    padding: 0; background: Canvas; color: var(--muted); border: 1px solid var(--line); border-radius: 5px; cursor: pointer; font: 1.05rem/1 system-ui, sans-serif; }}
  .outline-hide:hover, .outline-show:hover {{ color: CanvasText; }}
  @media (min-width: 48rem) {{
    .outline {{ display: block; }}
    .outline-toggle {{ display: none; }}
    main {{ margin-left: var(--outline-w); padding: 24px 24px 60px; }}
    .outline-grip {{ display: block; position: fixed; top: 0; left: calc(var(--outline-w) - 3px); width: 7px; height: 100vh; z-index: 16; cursor: col-resize; touch-action: none; }}
    .outline-grip:hover, .outline-grip.dragging {{ background: color-mix(in srgb, var(--line) 70%, transparent); }}
    .outline-hide {{ display: flex; left: calc(var(--outline-w) - 2.6rem); }}
    html.outline-collapsed .outline, html.outline-collapsed .outline-grip, html.outline-collapsed .outline-hide {{ display: none; }}
    html.outline-collapsed main {{ margin-left: 0; padding-left: 3.4rem; }}
    html.outline-collapsed .outline-show {{ display: flex; left: 0.6rem; }}
    body.dragging-outline {{ cursor: col-resize; user-select: none; }}
  }}
  table {{ border-collapse: collapse; width: 100%; max-width: 1200px; margin-bottom: 8px; }}
  /* words wrap whole; only long code names (branches) may break anywhere,
     or a column can shrink to one character and break every word */
  td {{ overflow-wrap: break-word; }}
  th, td {{ text-align: left; vertical-align: top; padding: 6px 10px; border: 1px solid var(--line); }}
  th {{ font-weight: 600; }}
  h2 {{ margin-top: 36px; }}
  code {{ overflow-wrap: anywhere; }}
  .note {{ color: var(--muted); font-size: 0.9em; }}
  .scroll {{ overflow-x: auto; max-width: 1200px; margin-bottom: 8px; }}
  .scroll > table {{ margin-bottom: 0; }}
  th.num, td.num {{ white-space: nowrap; width: 3em; }}
  th.area {{ width: 8.5em; }}
  td.num a.anchor {{ color: inherit; text-decoration: none; font-weight: 600; }}
  td.num a.anchor:hover {{ text-decoration: underline; }}
  button.copy {{ display: block; margin-top: 6px; font: inherit; font-size: 0.75em; padding: 1px 6px; cursor: pointer;
    border: 1px solid var(--line); border-radius: 4px; background: transparent; color: var(--muted); }}
  button.copy:hover {{ color: inherit; }}
  button.copy.done {{ color: var(--good); border-color: var(--good); }}
  tr:target td {{ background: color-mix(in srgb, var(--good) 14%, transparent); }}
  th.from {{ width: 11em; }}
  /* six columns of sentences: scroll sideways before they squeeze to a word a line */
  table.repos {{ min-width: 56rem; }}
  .good {{ color: var(--good); }} .bad {{ color: var(--bad); }} .wait {{ color: var(--wait); }}
  .current-box {{ max-width: 1200px; box-sizing: border-box; padding: 4px 16px; border: 1px solid var(--good); border-left-width: 4px; border-radius: 4px; }}
  .waiting {{ display: inline-block; margin-left: 0.3em; padding: 0.05em 0.4em; border: 3px solid CanvasText; border-radius: 999px; background: Canvas; color: CanvasText; font-weight: 800; line-height: 1.25; vertical-align: 0.05em; white-space: nowrap; }}
  h2 .waiting {{ font-size: 0.85em; }}
  .changes-chip {{ display: inline-block; padding: 0.15em 0.6em; border-radius: 999px; font-weight: 800; white-space: nowrap;
    background: #ff3b30; color: #fff; text-decoration: none; box-shadow: 0 0 0 3px color-mix(in srgb, #ff3b30 35%, transparent);
    animation: changes-pulse 1.6s ease-in-out infinite; }}
  .changes-chip:hover {{ background: #d70015; color: #fff; }}
  @keyframes changes-pulse {{ 50% {{ box-shadow: 0 0 0 7px color-mix(in srgb, #ff3b30 10%, transparent); }} }}
  @media (prefers-reduced-motion: reduce) {{ .changes-chip {{ animation: none; }} }}
  .badge {{ display: inline-block; margin-top: 4px; padding: 0 6px; font-size: 0.8em; border-radius: 4px; color: var(--good); border: 1px solid var(--good); }}
  .badge.queued {{ color: var(--wait); border-color: var(--wait); text-decoration: none; }}
  /* (^ticket(190)) what a ticket is about, and the filter bars */
  .badge.about {{ color: var(--muted); border-color: var(--line); }}
  /* (^ticket(196), Matthew: hazel and dress-up solid, bright, black text) */
  .badge.about-hazel {{ background: #facc15; color: #000; border-color: #eab308; font-weight: 600; }}
  .badge.about-dress-up {{ background: #f472b6; color: #000; border-color: #ec4899; font-weight: 600; }}
  .badge.about-meeting {{ background: #93c5fd; color: #000; border-color: #3b82f6; font-weight: 600; }}
  .badge.about-performance {{ color: #0f766e; border-color: #0f766e; }}
  .badge.about-dashboard {{ color: #4f46e5; border-color: #4f46e5; }}
  .badge.about-operations {{ color: var(--ops); border-color: var(--ops); }}
  .about-filter {{ display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin: 6px 0 8px; }}
  .about-filter button {{ font: inherit; font-size: 0.85em; padding: 1px 10px; border-radius: 999px; border: 1px solid var(--line); background: Canvas; color: CanvasText; cursor: pointer; }}
  .about-filter button[aria-pressed="true"] {{ background: color-mix(in srgb, var(--good) 18%, Canvas); border-color: var(--good); }}
  tr.about-hidden {{ display: none; }}
  .badge.longrun, .badge.tag {{ color: #8b5cf6; border-color: #8b5cf6; }}
  .badge.blocked {{ color: #0f9f8f; border-color: #0f9f8f; }}
  tr.longrun-head td {{ background: color-mix(in srgb, #8b5cf6 9%, transparent); }}
  tr.blocked-head td {{ background: color-mix(in srgb, #0f9f8f 9%, transparent); }}
  table.queue td:first-child {{ font-weight: 700; }}
  /* (Matthew, 2026-10-16: the ticket column was too wide; its chips wrap, one to a line, under the ticket, and the description gets the room) */
  table.queue th.tkcell, table.queue td.tkcell {{ white-space: normal; width: 9.5em; }}
  tr.current td {{ background: color-mix(in srgb, var(--good) 7%, transparent); }}
  td.status {{ white-space: nowrap; }}
  .since {{ margin: 6px 0; }}
</style>
<script>try {{ var w = localStorage.getItem("dash-outline-w"); if (w) document.documentElement.style.setProperty("--outline-w", w);
  if (localStorage.getItem("dash-outline-collapsed") === "1") document.documentElement.classList.add("outline-collapsed"); }} catch (e) {{}}</script>
</head>
<body>
<button class="outline-toggle" id="outline-toggle" type="button" aria-controls="outline" aria-expanded="false" aria-label="Open the outline">
  <svg class="bars" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M2 4h12M2 8h12M2 12h12"/></svg>
  <svg class="ex" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M3.5 3.5l9 9M12.5 3.5l-9 9"/></svg>
</button>
<nav class="outline" id="outline" aria-label="Outline">
<p class="outline-label">Hazel Work Dashboard</p>
<ul class="outline-out">
{agenda_entry}<li><a href="https://matthewhammer.org/hazel/dress-up/">Messed Up Dress Up&nbsp;<span aria-hidden="true">↗</span></a></li>
<li><a href="{SERIES_PUBLIC}">Hazel reports&nbsp;<span aria-hidden="true">↗</span></a></li>
<li><a href="https://github.com/matthewhammer/hazel-work-notes">On GitHub&nbsp;<span aria-hidden="true">↗</span></a></li>
</ul>
<ul id="outline-list">
{outline}
</ul>
</nav>
<div class="outline-grip" id="outline-grip" role="separator" aria-orientation="vertical" aria-controls="outline" title="Drag to make the outline wider or narrower (double-click: as it was)"></div>
<button class="outline-hide" id="outline-hide" type="button" title="Hide the outline" aria-label="Hide the outline">«</button>
<button class="outline-show" id="outline-show" type="button" title="Show the outline" aria-label="Show the outline">»</button>
<main>
<h1>Hazel Work Dashboard</h1>
<p class="note">Updated {e(now)}, by <code>~/localhost-index/update.py</code> (PR titles and status from GitHub).</p>
<p class="note">History: <a href="http://localhost:8000/notes/dashboard-snapshots/versions.html">every change to this page</a>, each a commit of one file (^ticket(417): no longer a file a change), also pushed to <a href="https://github.com/matthewhammer/hazel-work-notes">matthewhammer/hazel-work-notes</a> (public). Published at most ten minutes after each change to our notes, and to the status from GitHub (read every 15 minutes): <a href="https://matthewhammer.org/hazel/dashboard/">matthewhammer.org/hazel/dashboard/</a>. How we work with this page: <a href="https://github.com/matthewhammer/hazel-work-notes/blob/main/agent-instructions.md">agent-instructions.md</a> (<a href="http://localhost:8000/notes/agent-instructions.md">local</a>). This is version {VERSION}: <a href="https://github.com/matthewhammer/hazel-work-notes/blob/main/VERSIONS.md">VERSIONS.md</a> lists what each version has. Closed tickets: <a href="closed.html">their own page</a>. This page reloads itself when it changes (checked every 90 s while it is open).</p>

{current_section}
{queue_section}
<h2 id="ports">Localhost ports</h2>
<table>
<tr><th>PR # and title</th><th>Repo and branch</th><th>Localhost</th></tr>
{chr(10).join(rows)}
</table>

<h2 id="other">Other PRs we are tracking</h2>
<p class="note">Not about performance: features, fixes, docs, CI.</p>
<table>
<tr><th>PR # and title</th><th>Branch → base</th><th>State</th><th>CI</th><th>Review</th><th>Merge</th><th>Updated</th><th>Note</th></tr>
{status_rows(other, other_notes)}
</table>

<h2 id="repos">Repositories we deploy</h2>
<p class="note">Pushed to directly, without PRs. The version is the newest in each project's VERSIONS.md. Deployed means Pages has built the branch's latest commit; a repository without a Pages site runs where its links point.</p>
<div class="scroll"><table class="repos">
<tr><th>Repository and branch</th><th>Latest commit</th><th>Version</th><th>Deployed</th><th>Open PRs</th><th>Note</th></tr>
{repo_rows}
</table></div>

<h2 id="perf">Performance Analysis and Improvement</h2>
<p>Tracked in <a href="https://github.com/{REPO}/issues/{issue}">hazelgrove/hazel#{issue}</a> (performance challenges). Write-ups: <a href="http://localhost:8131/series/">the performance analysis series</a> (local sources).</p>

<h3 id="perf-prs">Performance PRs</h3>
<p class="note">Against #{issue}; the last three (#2606, #2603, #2490) are from before it.</p>
<table>
<tr><th>PR # and title</th><th>Branch → base</th><th>State</th><th>CI</th><th>Review</th><th>Merge</th><th>Updated</th></tr>
{status_rows(data["perf_prs"])}
</table>
<p class="note" id="integration">The integration branches also carry these fixes:</p>
<table>
<tr><th>PR # and title</th><th>Branch → base</th><th>State</th><th>CI</th><th>Review</th><th>Merge</th><th>Updated</th></tr>
{status_rows(data["integration_prs"])}
</table>

<h2 id="backlog"><span id="tickets"></span>Full Backlog (All Tickets)</h2>
<p class="note">All our open tickets: important and not done; the few we mean to do next are in <a href="#queue">the work queue</a>. Numbered in our own sequence from #1; a number is never reused. A closed ticket moves to <a href="closed.html">the closed tickets</a>, with how it ended.</p>
{about_filter("backlog")}
<table data-about-table="backlog">
<tr><th class="num">Ticket</th><th class="area">Area</th><th>Text</th><th class="from">From</th></tr>
{ticket_rows}
</table>
<script>
/* (^ticket(190)) The filter bars over the work queue and the backlog: a chip
   pressed shows the tickets about it (several pressed, any of them); "all",
   or none pressed, shows every ticket. A table's group lines stay. This
   browser keeps each table's choice. */
(() => {{
  for (const bar of document.querySelectorAll(".about-filter")) {{
    const name = bar.dataset.for, table = document.querySelector('table[data-about-table="' + name + '"]'), key = "dash-about-" + name;
    if (!table) continue;
    let on = [];
    try {{ on = JSON.parse(localStorage.getItem(key) || "[]"); }} catch (_) {{}}
    const show = () => {{
      for (const b of bar.querySelectorAll("button[data-about]")) b.setAttribute("aria-pressed", String(b.dataset.about ? on.includes(b.dataset.about) : !on.length));
      for (const tr of table.querySelectorAll("tr[data-about]")) {{
        const mine = tr.dataset.about.split(" ").filter(Boolean);
        tr.classList.toggle("about-hidden", on.length > 0 && !mine.some(c => on.includes(c)));
      }}
      try {{ on.length ? localStorage.setItem(key, JSON.stringify(on)) : localStorage.removeItem(key); }} catch (_) {{}}
    }};
    bar.addEventListener("click", e => {{
      const b = e.target.closest("button[data-about]");
      if (!b) return;
      const c = b.dataset.about;
      on = !c ? [] : on.includes(c) ? on.filter(x => x !== c) : [...on, c];
      show();
    }});
    show();
  }}
}})();
/* Old links (#next-N, from before tickets had the name) and links to a
   ticket that has closed since: find the ticket where it is now. */
(() => {{
  const find = () => {{
    const m = location.hash.match(/^#(?:next|ticket)-(\\d+)$/);
    if (!m) return;
    if (document.getElementById("ticket-" + m[1])) {{
      if (location.hash !== "#ticket-" + m[1]) location.replace("#ticket-" + m[1]);
    }} else {{
      location.replace("closed.html#ticket-" + m[1]);
    }}
  }};
  find();
  window.addEventListener("hashchange", find);
}})();
/* #34: stay current. Every 90 s while the page is in view, and on coming
   back to it, fetch this page and reload if its version changed (a hash of
   the page without its Updated line), keeping the scroll position. */
(() => {{
  const mine = document.querySelector('meta[name="dashboard-version"]');
  if (!mine) return;
  try {{
    const y = sessionStorage.getItem("dashboard-scroll");
    if (y !== null) {{ sessionStorage.removeItem("dashboard-scroll"); if (!location.hash) window.scrollTo(0, Number(y)); }}
  }} catch (_) {{}}
  let busy = false;
  const check = async () => {{
    if (busy || document.visibilityState !== "visible") return;
    busy = true;
    try {{
      const r = await fetch(location.pathname + "?v=" + Date.now(), {{ cache: "no-store" }});
      if (r.ok) {{
        const m = (await r.text()).match(/<meta name="dashboard-version" content="([^"]+)"/);
        if (m && m[1] !== mine.content) {{
          try {{ sessionStorage.setItem("dashboard-scroll", String(window.scrollY)); }} catch (_) {{}}
          location.reload();
        }}
      }}
    }} catch (_) {{}}
    busy = false;
  }};
  setInterval(check, 90000);
  document.addEventListener("visibilitychange", () => {{ if (document.visibilityState === "visible") check(); }});
}})();
/* The current ticket's elapsed time, kept up to date between regenerations. */
for (const el of document.querySelectorAll("[data-since]")) {{
  const t0 = Date.parse(el.dataset.since);
  const tick = () => {{
    const m = Math.max(0, Math.floor((Date.now() - t0) / 60000));
    const d = Math.floor(m / 1440), h = Math.floor(m % 1440 / 60);
    el.textContent = (d ? d + " d " : "") + (d || h ? h + " h " : "") + (m % 60) + " min";
  }};
  tick(); setInterval(tick, 30000);
}}
/* Each ticket's "copy link" puts its full URL, with its anchor, on the
   clipboard: a way to name a step exactly when talking about it. */
for (const b of document.querySelectorAll("button.copy")) {{
  b.addEventListener("click", async () => {{
    const url = location.origin + location.pathname + "#" + b.dataset.anchor;
    try {{ await navigator.clipboard.writeText(url); }}
    catch (_) {{
      const t = document.createElement("textarea"); t.value = url; document.body.append(t);
      t.select(); document.execCommand("copy"); t.remove();
    }}
    b.textContent = "copied"; b.classList.add("done");
    setTimeout(() => {{ b.textContent = "copy link"; b.classList.remove("done"); }}, 1500);
  }});
}}

/* (^ticket(390)) The outline's groups: each folds and unfolds by its triangle, as it starts unless this
   reader chose otherwise (kept in this browser), beside the page or in the nav bar alike. */
(() => {{
  const set = (li, on) => {{ const b = li.querySelector(":scope > .grp-row > .grp-tw"), ul = li.querySelector(":scope > ul.kids"); if (!b || !ul) return;
    b.setAttribute("aria-expanded", on ? "true" : "false"); b.textContent = on ? "▾" : "▸"; ul.hidden = !on;
    b.setAttribute("aria-label", (on ? "Fold " : "Unfold ") + ((li.querySelector(":scope > .grp-row > a") || {{}}).textContent || "")); }};
  for (const li of document.querySelectorAll("#outline li.grp")) {{ let v = null; try {{ v = localStorage.getItem("dash-grp-" + li.dataset.grp); }} catch (e) {{}}
    if (v === "open" || v === "closed") set(li, v === "open"); }}
  document.addEventListener("click", ev => {{ const b = ev.target.closest && ev.target.closest("#outline .grp-tw"); if (!b) return;
    const li = b.closest("li.grp"), on = b.getAttribute("aria-expanded") !== "true"; set(li, on);
    try {{ localStorage.setItem("dash-grp-" + li.dataset.grp, on ? "open" : "closed"); }} catch (e) {{}} }});
}})();

/* The outline: the entry for where the reader is (the last target above a
   line a third of the way down), and opening it on a narrow screen. */
(() => {{
  const nav = document.getElementById("outline");
  const links = [...nav.querySelectorAll("a")].map(a => ({{ a, el: document.getElementById(a.getAttribute("href").slice(1)) }})).filter(l => l.el);
  let current = null;
  const mark = () => {{
    const line = window.innerHeight * 0.33;
    let found = links[0];
    for (const l of links) {{ if (l.el.getBoundingClientRect().top <= line) found = l; }}
    if (window.scrollY + window.innerHeight >= document.body.scrollHeight - 4) {{
      found = links.reduce((best, l) => l.el.getBoundingClientRect().top <= window.innerHeight ? l : best, found);
    }}
    if (found === current) return;
    if (current) current.a.removeAttribute("aria-current");
    if (found) found.a.setAttribute("aria-current", "true");
    current = found;
    if (found && nav.scrollHeight > nav.clientHeight) {{
      const r = found.a.getBoundingClientRect(), n = nav.getBoundingClientRect();
      if (r.top < n.top + 8 || r.bottom > n.bottom - 8) found.a.scrollIntoView({{ block: "nearest" }});
    }}
  }};
  let ticking = false;
  const onScroll = () => {{ if (ticking) return; ticking = true; requestAnimationFrame(() => {{ ticking = false; mark(); }}); }};
  window.addEventListener("scroll", onScroll, {{ passive: true }});
  window.addEventListener("resize", onScroll, {{ passive: true }});
  mark();
  const toggle = document.getElementById("outline-toggle");
  const setOpen = open => {{
    nav.classList.toggle("is-open", open);
    document.body.classList.toggle("outline-open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.setAttribute("aria-label", open ? "Close the outline" : "Open the outline");
  }};
  toggle.addEventListener("click", () => setOpen(!nav.classList.contains("is-open")));
  nav.addEventListener("click", ev => {{ if (ev.target.closest("a") && nav.classList.contains("is-open")) setOpen(false); }});
  document.addEventListener("keydown", ev => {{ if (ev.key === "Escape" && nav.classList.contains("is-open")) {{ setOpen(false); toggle.focus(); }} }});
  const wide = window.matchMedia("(min-width: 48rem)");
  wide.addEventListener("change", () => {{ if (wide.matches) setOpen(false); }});
  // (Matthew, 2026-10-16) hide or show the outline beside the page, and drag its width; kept in this browser
  const root = document.documentElement, grip = document.getElementById("outline-grip");
  const keep = (k, v) => {{ try {{ if (v == null) localStorage.removeItem(k); else localStorage.setItem(k, v); }} catch (e) {{}} }};
  document.getElementById("outline-hide").addEventListener("click", () => {{ root.classList.add("outline-collapsed"); keep("dash-outline-collapsed", "1"); }});
  document.getElementById("outline-show").addEventListener("click", () => {{ root.classList.remove("outline-collapsed"); keep("dash-outline-collapsed", null); }});
  grip.addEventListener("pointerdown", ev => {{ ev.preventDefault(); grip.setPointerCapture(ev.pointerId); grip.classList.add("dragging"); document.body.classList.add("dragging-outline"); }});
  grip.addEventListener("pointermove", ev => {{
    if (!grip.classList.contains("dragging")) return;
    root.style.setProperty("--outline-w", Math.round(Math.max(140, Math.min(window.innerWidth * 0.6, ev.clientX))) + "px");
  }});
  const letGo = () => {{
    if (!grip.classList.contains("dragging")) return;
    grip.classList.remove("dragging"); document.body.classList.remove("dragging-outline");
    keep("dash-outline-w", root.style.getPropertyValue("--outline-w"));
  }};
  grip.addEventListener("pointerup", letGo); grip.addEventListener("pointercancel", letGo);
  grip.addEventListener("dblclick", () => {{ root.style.removeProperty("--outline-w"); keep("dash-outline-w", null); }});
}})();
</script>
</main>
</body>
</html>
"""
THEME_HEAD = '<!-- theme: head begin -->\n<script>try { var t = localStorage.getItem("theme"); if (t === "light" || t === "dark") document.documentElement.setAttribute("data-theme", t); } catch (e) {}</script>\n<!-- theme: head end -->'
THEME_BODY = '<!-- theme: begin -->\n<style>\n  .theme-toggle { position: fixed; top: 10px; right: 10px; z-index: 30; font: 13px system-ui, sans-serif; padding: 3px 10px;\n    border-radius: 999px; border: 1px solid var(--line, #ccc); background: var(--paper, Canvas); color: var(--muted, GrayText);\n    cursor: pointer; opacity: 0.85; }\n  .theme-toggle:hover { opacity: 1; color: var(--ink, CanvasText); }\n  @media print { .theme-toggle { display: none; } }\n</style>\n<script>\n/* The theme switch: Auto (the system\'s choice), Light, Dark; remembered for this site. */\n(() => {\n  const order = ["auto", "light", "dark"], label = { auto: "◐ auto", light: "☀ light", dark: "☾ dark" };\n  const get = () => { try { return localStorage.getItem("theme") || "auto"; } catch (_) { return "auto"; } };\n  const apply = m => m === "auto" ? document.documentElement.removeAttribute("data-theme")\n                                  : document.documentElement.setAttribute("data-theme", m);\n  const b = document.createElement("button");\n  b.type = "button"; b.className = "theme-toggle";\n  const show = () => { const m = get(); b.textContent = label[m] || label.auto;\n    b.title = "Theme: " + m + ". Click for " + order[(order.indexOf(m) + 1) % 3] + "; remembered on this site."; };\n  b.addEventListener("click", () => {\n    const m = order[(order.indexOf(get()) + 1) % 3];\n    try { m === "auto" ? localStorage.removeItem("theme") : localStorage.setItem("theme", m); } catch (_) {}\n    apply(m); show();\n  });\n  window.addEventListener("storage", e => { if (e.key === "theme") { apply(get()); show(); } });\n  show(); document.body.append(b);\n})();\n</script>\n<!-- theme: end -->'
# (ticket 296) the constellation's nav bar, on every reachable page: ~/matthewhammer.github.io/nav/agent-instructions.md
NAV_HEAD = '<!-- nav: begin --><meta name="theme-support" content="data-theme"><script src="https://matthewhammer.org/nav/nav.js"></script><!-- nav: end -->'
def themed(text):
    """The theme switch (Auto / Light / Dark, remembered per site), as on the series' pages; and the nav bar."""
    text = text.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + NAV_HEAD + '\n' + THEME_HEAD, 1)
    return text.replace("</body>", THEME_BODY + "\n</body>", 1)

import hashlib
# every PR or issue number a link, with a card on hover (prlinks.py)
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import prlinks, refcards
PRLINKS_CACHE = os.path.join(HERE, ".prlinks-cache.json")
UPDATED_LINE = re.compile(r'<p class="note">Updated [^<]*<code>[^<]*</code>[^<]*</p>')
def versioned(text):
    token = hashlib.sha1(UPDATED_LINE.sub("", text).encode()).hexdigest()[:12]
    return text.replace('<meta charset="utf-8">', f'<meta charset="utf-8">\n<meta name="dashboard-version" content="{token}">', 1)

# A table wider than the window scrolls by itself; the page never does.
page = page.replace("<table>", '<div class="scroll"><table>').replace("</table>", "</table></div>")
# written whole, then renamed into place: a reader never sees half a page
tmp = os.path.join(HERE, ".index.html.tmp")
open(tmp, "w").write(versioned(themed(refcards.process(prlinks.process(page, PRLINKS_CACHE), data))))
os.replace(tmp, os.path.join(HERE, "index.html"))

# The closed tickets, on a page of their own: how each ended (done, or closed
# for another reason, such as not needed or dropped), when, and where the
# outcome is.
STATUS_CLASS = {"done": "good", "not needed": "wait", "dropped": "bad", "superseded": "wait"}
# (from 2026-10-15: a ticket's metrics, kept as agent-instructions.md says,
# shown in a line under its outcome)
def metrics_line(t):
    m = t.get("metrics")
    if not m:
        return ""
    hm = lambda iso: iso[11:16] if iso and len(iso) >= 16 else "?"
    bits = []
    if t.get("opened") and t.get("closed_at"):
        bits.append(f'opened {e(t["opened"][:10])} {hm(t["opened"])}, closed {hm(t["closed_at"])}'
                    + (f' ({m["open_minutes"]:,} min)' if m.get("open_minutes") is not None else ""))
    if m.get("work_minutes") is not None:
        bits.append(f'{m["work_minutes"]} min of work, timed')
    if m.get("matthew_messages") is not None:
        n, q = m["matthew_messages"], m.get("questions_to_matthew", 0)
        bits.append(f'{n} message{"" if n == 1 else "s"} from Matthew, {q} question{"" if q == 1 else "s"} to him')
    if m.get("chars_exchanged") is not None:
        bits.append(f'~{m["chars_exchanged"]:,} chars (~{m.get("tokens_est", m["chars_exchanged"] // 4):,} tokens)')
    if m.get("sync_minutes_est") is not None:
        bits.append(f'~{m["sync_minutes_est"]} min together')
    return '<br><span class="note">\u23f1 ' + " \u00b7 ".join(bits) + "</span>"
def outcome_cell(t, on):
    out = linkify(t.get("outcome", ""), on=on)
    if t.get("outcome_url"):
        out += f' <a href="{e(series_link(t["outcome_url"]))}">(where)</a>'
    return out + metrics_line(t)
def closed_rows(page):
    return "\n".join(
        f'<tr id="ticket-{t["id"]}">{num_cell(t)}<td>{e(t.get("area", ""))}</td>'
        f'<td class="status"><span class="{STATUS_CLASS.get(t["status"], "")}">{e(t["status"])}</span><br>'
        f'<span class="note">{e(t["closed"])}</span></td>'
        f'<td>{outcome_cell(t, page)}</td>'
        f'<td>{linkify(t["text"], on=page)}'
        f'{"<br><span class=" + chr(34) + "note" + chr(34) + ">from " + from_cell(t, on=page) + "</span>" if t.get("source") else ""}</td></tr>'
        for t in sorted(CLOSED, key=lambda t: (t["closed"], t["id"]), reverse=True) if CLOSED_PAGE[t["id"]] == page)
# (each closed page's line of months: this month's page, then each earlier month's, newest first, with how many each holds)
CLOSED_PAGES = ["closed.html"] + sorted({p for p in CLOSED_PAGE.values() if p != "closed.html"}, reverse=True)
def months_line(page):
    count = lambda p: sum(1 for q in CLOSED_PAGE.values() if q == p)
    name = lambda p: f"this month, {THIS_MONTH}" if p == "closed.html" else p[len("closed-"):-len(".html")]
    bits = [f"<b>{e(name(p))}</b> ({count(p)})" if p == page else f'<a href="{p}">{e(name(p))}</a> ({count(p)})' for p in CLOSED_PAGES]
    return '<p class="note">By the month they were closed: ' + " · ".join(bits) + ".</p>" if len(CLOSED_PAGES) > 1 else ""
style = page.split("<style>", 1)[1].split("</style>", 1)[0]
# the copy-link buttons' code only (the index's own redirects stay there)
script = "/* Each ticket" + page.split("/* Each ticket", 1)[1].split("/* The outline:", 1)[0]
def closed_page(page):
    month = "" if page == "closed.html" else page[len("closed-"):-len(".html")]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Closed Tickets{", " + month if month else ""}</title>
<style>{style}  main {{ margin-left: 0 !important; padding-top: 24px !important; }}
</style>
</head>
<body>
<main>
<h1>Closed tickets</h1>
<p class="note"><a href="./">← the Hazel Work Dashboard</a>. Updated {e(now)}.{" Closed in " + e(month) + "." if month else ""} Our tickets once closed, newest first: done, or closed for another reason (not needed, dropped, superseded), with what came of each. A number is never reused; the open tickets are on the dashboard: <a href="./#queue">the work queue</a> and <a href="./#backlog">the full backlog</a>.</p>
<div class="scroll"><table>
{months_line(page)}
<tr><th class="num">Ticket</th><th class="area">Area</th><th>Status, closed</th><th>Outcome</th><th>The ticket, as it last read</th></tr>
{closed_rows(page)}
</table></div>
<script>
/* A link to a ticket that is open again, or never closed: the dashboard. One closed in an earlier month (^ticket(428)): its
   month's page, from closed-where.json (this month's page asks it; an earlier month's page sends the link here first). */
(() => {{
  const find = async () => {{
    const m = location.hash.match(/^#(?:next|ticket)-(\\d+)$/);
    if (!m) return;
    if (!document.getElementById("ticket-" + m[1])) {{
      if ({"true" if page != "closed.html" else "false"}) return location.replace("closed.html#ticket-" + m[1]);
      let where = null;
      try {{ const r = await fetch("closed-where.json", {{ cache: "no-store" }}); if (r.ok) where = (await r.json())[m[1]]; }} catch (_) {{}}
      location.replace((where || "./") + "#ticket-" + m[1]);
    }}
    else if (location.hash !== "#ticket-" + m[1]) location.replace("#ticket-" + m[1]);
  }};
  find();
  window.addEventListener("hashchange", find);
}})();
/* #34: stay current. Every 90 s while the page is in view, and on coming
   back to it, fetch this page and reload if its version changed (a hash of
   the page without its Updated line), keeping the scroll position. */
(() => {{
  const mine = document.querySelector('meta[name="dashboard-version"]');
  if (!mine) return;
  try {{
    const y = sessionStorage.getItem("dashboard-scroll");
    if (y !== null) {{ sessionStorage.removeItem("dashboard-scroll"); if (!location.hash) window.scrollTo(0, Number(y)); }}
  }} catch (_) {{}}
  let busy = false;
  const check = async () => {{
    if (busy || document.visibilityState !== "visible") return;
    busy = true;
    try {{
      const r = await fetch(location.pathname + "?v=" + Date.now(), {{ cache: "no-store" }});
      if (r.ok) {{
        const m = (await r.text()).match(/<meta name="dashboard-version" content="([^"]+)"/);
        if (m && m[1] !== mine.content) {{
          try {{ sessionStorage.setItem("dashboard-scroll", String(window.scrollY)); }} catch (_) {{}}
          location.reload();
        }}
      }}
    }} catch (_) {{}}
    busy = false;
  }};
  setInterval(check, 90000);
  document.addEventListener("visibilitychange", () => {{ if (document.visibilityState === "visible") check(); }});
}})();
{script}</script>
</main>
</body>
</html>
"""
for page in CLOSED_PAGES:
    tmp = os.path.join(HERE, "." + page + ".tmp")
    open(tmp, "w").write(versioned(themed(refcards.process(prlinks.process(closed_page(page), PRLINKS_CACHE), data))))
    os.replace(tmp, os.path.join(HERE, page))
# (a month's page no longer made, as when its tickets were all reopened, goes)
for old in os.listdir(HERE):
    if re.fullmatch(r"closed-\d{4}-\d\d\.html", old) and old not in CLOSED_PAGES:
        os.remove(os.path.join(HERE, old))
tmp = os.path.join(HERE, ".closed-where.json.tmp")
json.dump({str(n): p for n, p in sorted(CLOSED_PAGE.items()) if p != "closed.html"}, open(tmp, "w"))
os.replace(tmp, os.path.join(HERE, "closed-where.json"))
print(f"wrote index.html: {len(rows)} ports, {len(other)} other + {len(data['perf_prs'])} perf + {len(data['integration_prs'])} integration PRs, {len(data.get('repos', []))} repos, {len(TICKETS)} tickets"
      + (f" (current ^ticket({CURRENT['id']}))" if CURRENT else "") + f"; closed.html: {len(CLOSED)} closed tickets" + (f", and {len(CLOSED_PAGES) - 1} earlier month{chr(39) + 's page' if len(CLOSED_PAGES) == 2 else 's' + chr(39) + ' pages'}" if len(CLOSED_PAGES) > 1 else ""))
