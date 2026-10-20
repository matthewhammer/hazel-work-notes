# Hazel work notes

**▶ See the Hazel Work Dashboard at https://matthewhammer.org/hazel/work-dashboard/**

Matthew Hammer's working record for his [Hazel](https://hazel.org) work, kept with Claude. The dashboard shows the PRs we track, which branch is on which local port, our tickets, the work queue and the current ticket. Alongside it are its history and our dated work notes. The repository is public, but it is written for the two of us. The write-ups for other readers are the [Hazel performance analysis](http://matthewhammer.org/hazel/performance-analysis/) series.

## What's here

- The published dashboard, and its closed tickets, are at https://matthewhammer.org/hazel/dashboard/, beside the series at https://matthewhammer.org/hazel/performance-analysis/, in the homepage's repository (since 2026-10-16). `dashboard/site_publish.py` republishes them at most ten minutes after each change to the dashboard's data, and to the status from GitHub, read every 15 minutes.
- `index.html` and `closed.html`: redirects to that address, keeping any `#ticket-N`: until 2026-10-16 the dashboard was published here, at http://matthewhammer.org/hazel-work-notes/ (and http://matthewhammer.org/hazel/work-dashboard/ redirected here; it now goes to the new address too).
- `dashboard/`: the code that makes the dashboard from its data and publishes it:
  - `update.py` makes the dashboard;
  - `publish.py`, `log_notes.py` and `site_publish.py` publish it;
  - `notes_page.py`, `prlinks.py` and `refcards.py` give a notes page the same links and hover cards.
- `dashboard-data/data.json` and `dashboard-data/closed/<YYYY-MM>.json`: the data the dashboard is made from, as last published, split since ^ticket(428) (2026-10-19): all but the closed tickets' full records (each is there as its hover card's summary, which the published reports' cards read), and the closed tickets by the month each was closed, so a change to an open ticket no longer copies the closed ones, and a closing rewrites only its month. `python3 dashboard/data_whole.py [commit]` prints the whole data.json, now or at any commit.
- `dashboard-snapshots/index.html` and `closed.html`: the dashboard and its closed tickets' page, one file each; every change is a commit of them (since 2026-10-19, ^ticket(417)). Since ^ticket(428) a publish is one commit, the closed page is kept only when a ticket closes or a closed one changes, and the page when its data changes or at most hourly otherwise; `versions.html` (the last 30 days of versions, made from git log on every run) is no longer committed: GitHub's history of each file is the same list. The dated files from before, a folder per day, are in git's history (the tree of `df072c9d`).
- `work-notes/YYYY/MM/DD/`: dated work notes, as HTML.
- `agent-instructions.md`: how we work with the dashboard.
- `VERSIONS.md`: the dashboard's features, version by version.
