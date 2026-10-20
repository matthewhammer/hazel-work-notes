#!/usr/bin/env python3
"""Print data.json as the dashboard used it, from the two files kept since ^ticket(428): dashboard-data/data.json (all but
the closed tickets) with "closed_tickets" set to dashboard-data/closed_tickets.json.

  python3 dashboard/data_whole.py              # from the working tree
  python3 dashboard/data_whole.py <commit>     # as it was at a commit (before ^ticket(428), data.json was whole)"""
import json, os, subprocess, sys

NOTES = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def read(path, rev):
    if rev is None:
        full = os.path.join(NOTES, path)
        return open(full).read() if os.path.exists(full) else None
    r = subprocess.run(["git", "-C", NOTES, "show", f"{rev}:{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None

rev = sys.argv[1] if len(sys.argv) > 1 else None
d = json.loads(read("dashboard-data/data.json", rev))
closed = read("dashboard-data/closed_tickets.json", rev)
if closed is not None and "closed_tickets" not in d:
    d["closed_tickets"] = json.loads(closed)
sys.stdout.write(json.dumps(d, indent=1, ensure_ascii=False))
