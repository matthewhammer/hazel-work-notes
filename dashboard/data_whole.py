#!/usr/bin/env python3
"""Print data.json as the dashboard used it, from the files kept since ^ticket(428): dashboard-data/data.json (all but the
closed tickets) with "closed_tickets" set to the months of dashboard-data/closed/<YYYY-MM>.json, newest month first (a
closing goes to the front of the list). For the first hour of ^ticket(428) they were one file, closed_tickets.json.

  python3 dashboard/data_whole.py              # from the working tree
  python3 dashboard/data_whole.py <commit>     # as it was at a commit (before ^ticket(428), data.json was whole)"""
import json, os, subprocess, sys

NOTES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def git(*args):
    r = subprocess.run(["git", "-C", NOTES, *args], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None

def read(path, rev):
    if rev is None:
        full = os.path.join(NOTES, path)
        return open(full).read() if os.path.exists(full) else None
    return git("show", f"{rev}:{path}")

def months(rev):
    if rev is None:
        folder = os.path.join(NOTES, "dashboard-data", "closed")
        return sorted(os.listdir(folder)) if os.path.isdir(folder) else []
    return sorted(os.path.basename(p) for p in (git("ls-tree", "--name-only", f"{rev}:dashboard-data/closed") or "").split())

rev = sys.argv[1] if len(sys.argv) > 1 else None
d = json.loads(read("dashboard-data/data.json", rev))
if "closed_tickets" not in d:
    one = read("dashboard-data/closed_tickets.json", rev)
    if one is not None:
        d["closed_tickets"] = json.loads(one)
    else:
        names = months(rev)
        # (the months newest first; "undated" sorts after the digits, so it goes last)
        names = sorted([n for n in names if n[0].isdigit()], reverse=True) + [n for n in names if not n[0].isdigit()]
        d["closed_tickets"] = [t for n in names for t in json.loads(read(f"dashboard-data/closed/{n}", rev))]
sys.stdout.write(json.dumps(d, indent=1, ensure_ascii=False))
