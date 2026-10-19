#!/usr/bin/env python3
"""Publish the dashboard at matthewhammer.org/hazel/dashboard/ (^ticket(181), Matthew's,
2026-10-16): the page and the closed tickets as served locally, made public, committed
into the homepage's repository (~/matthewhammer.github.io, branch master, folder
hazel/dashboard/) and pushed.

  python3 ~/localhost-index/site_publish.py

Run by log_notes.py after each publish, and by publish.py each minute while a copy
waits. Until 2026-10-16 the copy was at the root of hazel-work-notes, served at
matthewhammer.org/hazel-work-notes/; that address now redirects here, ticket anchors
and all.

The homepage's Pages build takes about two minutes and GitHub allows about ten builds an
hour, so a copy goes up at most once every ten minutes: a change inside that window
waits (.site-pending says so), and goes up when the window ends.

The commit is made without the homepage's checkout: the pages go into git's objects, a
tree is made from origin/master with them replaced, and that commit is pushed to master.
The checkout (its working tree, index and branch) never changes, so whatever is being
done there is safe; it falls behind origin by the dashboard's commits, so pull before
pushing from it. A push that loses a race is tried again a minute later."""
import hashlib, json, os, re, subprocess, sys, tempfile, time
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))   # ~/localhost-index, through the symlink
SITE = os.path.expanduser("~/matthewhammer.github.io")
FOLDER = "hazel/dashboard"
EVERY = 600   # seconds between pushes
RECORD = os.path.join(HERE, ".site-published.json")
PENDING = os.path.join(HERE, ".site-pending")
UPDATED = re.compile(r'<p class="note">Updated [^<]*<code>')

REPO = "https://github.com/matthewhammer/hazel-work-notes"
NOTE = ('<p class="note">A copy of the Hazel Work Dashboard that Matthew runs on his laptop, published at most ten minutes '
        'after each change to its notes, and to the status from GitHub, which it reads every 15 minutes. Its <code>localhost</code> links work only there.</p>')

def public(text):
    """The page as served locally, made public: a line saying what it is, links to the
    history on GitHub instead of on localhost, and noindex (findable by its link, not by search)."""
    text = text.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<meta name="robots" content="noindex">', 1)
    # (^ticket(417): the history is the page's own git log since 2026-10-19, not a folder of dated files)
    text = text.replace("http://localhost:8000/notes/dashboard-snapshots/versions.html", REPO + "/commits/main/dashboard-snapshots/index.html")
    text = text.replace("http://localhost:8000/notes/dashboard-snapshots/", REPO + "/commits/main/dashboard-snapshots/index.html")
    text = text.replace(' (<a href="http://localhost:8000/notes/agent-instructions.md">local</a>)', "")
    text = text.replace("http://localhost:8000/notes/agent-instructions.md", REPO + "/blob/main/agent-instructions.md")
    # The outline's link to the series: the published reports, as the local page links the local ones.
    text = text.replace('<ul class="outline-out">\n<li><a href="http://localhost:8131/series/">',
                        '<ul class="outline-out">\n<li><a href="https://matthewhammer.org/hazel/reports/">', 1)
    for h1 in ("<h1>Hazel Work Dashboard</h1>", "<h1>Closed tickets</h1>"):
        text = text.replace(h1, h1 + "\n" + NOTE, 1)
    return text

def digest(text):
    return hashlib.sha256(UPDATED.sub("", text).encode()).hexdigest()

def git(*args, env=None, data=None):
    r = subprocess.run(["git", "-C", SITE, *args], capture_output=True, timeout=120,
                       env=env, input=data, text=data is None or isinstance(data, str))
    if r.returncode != 0:
        err = r.stderr if isinstance(r.stderr, str) else r.stderr.decode(errors="replace")
        raise RuntimeError(f"git {' '.join(args[:2])}: {err.strip()[:300]}")
    return r.stdout.strip() if isinstance(r.stdout, str) else r.stdout

def main():
    copies = {}
    for name in ("index.html", "closed.html"):
        src = os.path.join(HERE, name)
        if os.path.exists(src):
            copies[name] = public(open(src).read())
    try:
        rec = json.load(open(RECORD))
    except (FileNotFoundError, ValueError):
        rec = {}
    changed = [n for n, t in copies.items() if rec.get(n) != digest(t)]
    if not changed:
        if os.path.exists(PENDING):
            os.remove(PENDING)
        return
    wait = int(EVERY - (time.time() - rec.get("at", 0)))
    if wait > 0:
        open(PENDING, "w").write(", ".join(changed) + "\n")
        print(f"site: {', '.join(changed)} changed; goes up in {wait} s")
        return
    try:
        git("fetch", "-q", "origin", "master")
        base = git("rev-parse", "origin/master")
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, GIT_INDEX_FILE=os.path.join(tmp, "index"))
            git("read-tree", base, env=env)
            for name, text in copies.items():
                blob = git("hash-object", "-w", "--stdin", data=text)
                git("update-index", "--add", "--cacheinfo", f"100644,{blob},{FOLDER}/{name}", env=env)
            tree = git("write-tree", env=env)
        if tree != git("rev-parse", base + "^{tree}"):
            when = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
            commit = git("commit-tree", tree, "-p", base, "-m",
                         f"Hazel Work Dashboard, {when}: {', '.join(changed)}\n\n"
                         "Published by ~/localhost-index/site_publish.py (hazel-work-notes/dashboard/).")
            git("push", "-q", "origin", f"{commit}:refs/heads/master")
            print(f"site: published {', '.join(changed)} ({commit[:7]})")
        else:
            print("site: already published")
    except (RuntimeError, subprocess.TimeoutExpired) as e:
        open(PENDING, "w").write(", ".join(changed) + "\n")
        print(f"site: not published, tried again next minute: {e}")
        return
    rec = {"at": int(time.time()), **{n: digest(t) for n, t in copies.items()}}
    json.dump(rec, open(RECORD, "w"))
    if os.path.exists(PENDING):
        os.remove(PENDING)

main()
