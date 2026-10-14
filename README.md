# Hazel work notes

**▶ See the Hazel Work Dashboard at http://matthewhammer.org/hazel/work-dashboard/** (HTTP only, for now).

Matthew Hammer's working record for his [Hazel](https://hazel.org) work, kept with Claude. The dashboard shows the PRs we track, which branch is on which local port, our tickets, the work queue and the current ticket. Alongside it are its history and our dated work notes. The repository is public, but it is written for the two of us. The write-ups for other readers are the [Hazel performance analysis](http://matthewhammer.org/hazel/performance-analysis/) series.

## What's here

- `index.html` and `closed.html`: the published copy of the dashboard and of its closed tickets. Their address is http://matthewhammer.org/hazel/work-dashboard/, beside the series at http://matthewhammer.org/hazel/performance-analysis/; it redirects to this repository's own Pages site, http://matthewhammer.org/hazel-work-notes/, keeping any `#ticket-N`. They are republished within a minute of each change to the dashboard's data, and every 15 minutes for the status from GitHub.
- `dashboard/`: the code that makes the dashboard from its data and publishes it:
  - `update.py` makes the dashboard;
  - `publish.py` and `log_notes.py` publish it;
  - `notes_page.py`, `prlinks.py` and `refcards.py` give a notes page the same links and hover cards.
- `dashboard-data/data.json`: the data the dashboard is made from, as last published.
- `dashboard-snapshots/YYYY/MM/DD/`: every change to the dashboard, a folder per day.
- `work-notes/YYYY/MM/DD/`: dated work notes, as HTML.
- `agent-instructions.md`: how we work with the dashboard.
- `VERSIONS.md`: the dashboard's features, version by version.
