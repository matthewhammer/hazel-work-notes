# Hazel Work Dashboard: versions

Each version lists the dashboard's features as of that version. The newest version is first. The version number is `VERSION` in [`dashboard/update.py`](dashboard/update.py), and the page shows it in its History line.

## 0.0.3 (2026-10-13)

Everything in 0.0.2, plus:

- **The history is organized by date:** the snapshots now live in `dashboard-snapshots/<YYYY>/<MM>/<DD>/`, a folder for each year, month and day, instead of one folder per day at the top of the repository. Their names are unchanged, and `git mv` kept their history. The page's History line links there.
- **The agent instructions say what this repository is for:** our working record, for the two of us. The performance analysis series is separate, written for outside readers, in its own repository.
- **Tickets, not next steps:** our own numbered items are now called tickets, so they are not confused with GitHub issues. The section is "Tickets", each row's anchor is `#ticket-N` (with a "copy link" button), and old `#next-N` links still find their ticket. In `data.json`: `tickets` and `next_ticket`, in place of `next_steps` and `next_id`.
- **The current ticket, first on the page:** when there is one (`current_ticket`), a first section shows it in full, with a line on what is next on it (`current_note`). Its row in the Tickets table is marked "current", and the outline lists it first.
- **The current ticket's clock:** the section says when we started the ticket (`current_since`) in Mountain Time, and the time elapsed since, which the browser keeps up to date between regenerations. The page's "Updated" time is Mountain Time too.
- **Closed tickets have a page:** http://localhost:8000/closed.html, newest first. Each row gives the status (done, not needed, dropped or superseded), the date it closed, what came of it (with a link to where), and its text as it last read. Closing a ticket moves it to `closed_tickets` in `data.json`; nothing is deleted. A `#N` reference links to a ticket wherever it is, and a link to a closed ticket's old anchor lands on its row there. The nine tickets closed before this (#1, #3, #6, #8, #9, #11, #20, #21, #26) were reconstructed from the snapshots.
- **`data.json` has a history:** `log_notes.py` also copies it to `dashboard-data/data.json` and commits it whenever it changes, since the closed tickets live only there.

## 0.0.2 (2026-10-12)

Everything in 0.0.1, plus:

- **Repositories we deploy:** a new section after "Other PRs we are tracking", for the repositories that deploy on a push to a branch, with no PRs. The first is matthewhammer/kids-choice-games. Each row gives:
  - the repository and branch;
  - the branch's latest commit, with its message and date;
  - each project's version, the newest `## X.Y.Z (date)` heading of its `VERSIONS.md`, linked to that file;
  - whether GitHub Pages has deployed that very commit ("✓ deployed", "… not yet" with the commit that is live, "… building", or "✗ build failed"), with links to where it is live and served locally;
  - the repository's open PRs, if any, and a note.
- The table keeps a readable width and scrolls sideways on a narrow screen.

## 0.0.1 (2026-10-12)

The dashboard as it was when it got its first version number, built from 2026-09-28 to 2026-10-12.

### The page

- One page, at http://localhost:8000/, titled **Hazel Work Dashboard**.
- An outline at the side lists the sections and every next step by its number, and marks where you are as you scroll. On a wide window it stays fixed at the left. On a narrow one it sits at the top, behind a button.
- Four sections, in order:
  1. **Localhost ports:** what is served where. One row per PR or project: the repository, the branch (and the branch it merges into), and localhost links, with deep links such as `?slide=...`. A row with nothing served says "not served".
  2. **Other PRs we are tracking:** the PRs that are not about performance, with a note on each.
  3. **Performance Analysis and Improvement:** the PRs against hazelgrove/hazel#2609, and the integration PRs (#2635, #2597) that carry their fixes.
  4. **Next steps:** our own numbered issues.
- Each PR row gives its status from GitHub: title, state, CI, review, whether it merges cleanly, and the date of its last update.
- Tables keep their column widths, wrap long text and code, and scroll sideways on their own on a narrow screen, never the whole page.

### Next steps

- Each step has a number, `#N`, which is never reused. A done step leaves the list, and its number is retired. A parked step stays, marked PARKED.
- Each step has its area, the date it was added, the step, and where it came from.
- Each step's row has an anchor, `#next-N`, and a **copy link** button that copies the page's address with that anchor. The step a link points to is highlighted.

### Links

References are written plainly in `data.json`, and the page links them the same way everywhere:

- "issue 00N" links to that issue of the performance analysis series: the public page once it is published, the local draft until then. Links to a local draft switch to the public page when it is published.
- `#NNNN` (four digits) links to that hazelgrove/hazel issue or PR.
- `#N` (one to three digits) links to that next step while it is listed.
- A 10-character commit id links to that commit.
- Text already inside a link is left alone.

### How it is made

- `data.json` (in `~/localhost-index`) holds what only we know: the ports, the PRs we track, the notes and the next steps. `update.py` reads it, asks GitHub (`gh`) about each PR, and writes the page.
- The page is written whole or not at all: if GitHub can't be reached, the last good page stays.
- Cron runs `update.py` every 15 minutes.

### History

- `log_notes.py` runs after each update and saves the page, exactly as served, to this repository: `<YYYY-MM-DD>/<YYYY-MM-DD>T<HHMM><+-hhmm>.html`, one folder per day, each name carrying its full date and time zone.
- A page that changed only in its "Updated" line is not saved.
- Each snapshot is committed and pushed to `matthewhammer/hazel-work-notes` (private). A push that fails is retried on the next run.
- The page links its history, browsable at http://localhost:8000/notes/, and this repository.
- [`agent-instructions.md`](agent-instructions.md) describes how we work with the dashboard.
