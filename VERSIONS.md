# Hazel Work Dashboard: versions

Each version lists the dashboard's features as of that version. The newest version is first. The version number is `VERSION` in [`dashboard/update.py`](dashboard/update.py), and the page shows it in its History line.

## Unreleased

Changes since 0.0.3, for the next version, which waits for Matthew's go-ahead.

- **Published at matthewhammer.org/hazel/dashboard/** (Matthew's, 2026-10-16, ^ticket(181)): the public copy moved from this repository's root (matthewhammer.org/hazel-work-notes/) into the homepage's repository, and every link with it. `dashboard/site_publish.py` makes it and commits it to the homepage's master by git's plumbing, at most once every ten minutes, since that site's Pages build takes about two; a change inside the ten minutes waits, and `publish.py` sends it when they end. The old addresses, this repository's root and /hazel/work-dashboard/, redirect to the new one, `#ticket-N` and all.
- **🌙 Long runs** (Matthew's, 2026-10-15, ^ticket(114)): a ticket can carry tags (`tags` in `data.json`), and "long run" marks one to do while Matthew is away from the keyboard (archive renders, big sweeps). It shows as a 🌙 chip on the ticket's row, in the current ticket's box and in the queue, a 🌙 before it in the outline, and the long runs at the end of the queue sit together under a line of their own.
- **🪷 Blocked on Matthew** (Matthew's, 2026-10-15, ^ticket(115); the lotus his pick, "pur-fect"): a second tag, for a ticket waiting on his response. A teal 🪷 chip, and a category of its own at the very end of the queue, after the long runs (`QUEUE_GROUPS` in `update.py` says the categories and their order).
- **Each ticket's metrics** (Matthew's, 2026-10-15): when it opened and closed, to the minute; the messages about it, his and Claude's, with their lengths and which put him a question; and on closing, the minutes it was open, the minutes of work when timed, his messages, the questions to him, the characters (and tokens) exchanged, and the minutes spent together. The closed tickets' page shows them in a line under each outcome. The rules are in `agent-instructions.md`.
- **Closing a ticket by script:** `dashboard/close_ticket.py <id> <status> <outcome> [--work-minutes M]` moves a ticket from `tickets` to `closed_tickets` with its status, outcome and closing time, computes its metrics from its log (and its timed work, when it has some), takes it out of the queue, and, if it was current, makes the queue's front current. In use since 2026-10-15, through the `~/localhost-index/close_ticket.py` symlink; in the repository since 2026-10-16.
- **Our numbers in our own syntax:** a ticket is `^ticket(N)` and a report of the performance analysis series is `^report(N)` (Matthew's, 2026-10-14): in `data.json`, on the page and in chat, with no leading zeros, so numbers can grow into the thousands without passing for a PR. Shown in monospace, `^ticket(` / `^report(` and `)` in bold, each a link; the old `#45` and "issue 013" in a text still read the same way. The series' items are now **reports**: "issue" is GitHub's word.
- **Hover cards:** every GitHub PR or issue number is a link with a card on hover or focus, asked of GitHub live (title, state, author, dates, comments; `prlinks.py`), with what GitHub said at the last publish as the fallback; every `^ticket` link has a card from the tickets carried in the page (area, status, its first line), and every `^report` link a card read live from the report's page (title, date, opening; `refcards.py`).
- **Working notes made like the rest:** `dashboard/notes_page.py` gives a notes page the same chips, links and cards, and its Next steps a link and "copy link" / "copy for a ticket" chips.
- Fixed: "issue 010" and later did not link (only 001 to 009 did).
- **A link to the reports, first in the outline:** "Performance reports" opens the performance analysis series, and the series index links back (Matthew's, 2026-10-14). Local pages link local pages (http://localhost:8000/ and http://localhost:8131/series/); the published dashboard and the published series link each other.
- **Its repository, linked both ways:** the outline's "On GitHub" opens matthewhammer/hazel-work-notes, and the repository's new README links the dashboard's address, http://matthewhammer.org/hazel/work-dashboard/, first.

- **The page keeps itself current:** every 90 seconds while it is open and in view, and as soon as its tab comes back into view, the page fetches itself and reloads if it changed, keeping its scroll position and any `#ticket-N`. Each page carries a version (`<meta name="dashboard-version">`, a hash of the page without its Updated line). The current ticket's elapsed time is now filled in only by the browser, so the page does not change, and is not snapshotted or republished, just because time passed.
- **Published, publicly:** the repository is public, and `log_notes.py` writes a copy of the page and of the closed tickets to its root whenever either changes, which its Pages site serves at http://matthewhammer.org/hazel-work-notes/ (http://matthewhammer.org/hazel/work-dashboard/ redirects there, and the homepage's Hazel menu has a "work-dashboard" chip). The copy says what it is, links the history on GitHub instead of on localhost, and is marked noindex: findable by its link, not by search. The History line says so.
- **A theme switch:** a button, top right, on the page and on the closed tickets, cycles Auto / Light / Dark. Auto follows the system; a choice is remembered by the browser for the site (localStorage `theme`), so the published copy and http://localhost:8000/ each keep their own. It is the same switch as on the performance analysis series and matthewhammer.org/hazel/.
- **A work queue, and the backlog:** a short, ordered list of the tickets we mean to do next, **Work Queue (Active Tickets)**, right after the current ticket (`queue` in `data.json`, front first), each a line linking to its row; the Tickets section is now **Full Backlog (All Tickets)**, every open ticket, a ticket in the queue marked with a "queued" chip, the status beside "current" (one ticket is current; the others in line are queued). The outline lists both. Old `#tickets` links land on the backlog.
- **Published within a minute of a change:** cron runs `dashboard/publish.py` every minute. It republishes as soon as `data.json` differs from what was last published (a ticket made current or closed, ✋❔ raised or lowered, a note, a port), and on the quarter hour for PR status and deploys, which come from GitHub. Before, everything waited for the quarter hour unless the agent remembered to run the scripts by hand. A lock keeps a by-hand run (`publish.py --now`) and cron from colliding, and `update.log` says why each run ran.
- **Waiting on Matthew, at a glance:** when the current ticket waits on him (`current_waiting` in `data.json`, `true` or a line saying what for), a raised hand and a question mark, ✋❔, in a bold, high-contrast rounded box, follow the current ticket's heading, its row in the Tickets table and its outline entry, and lead the page's title, so a browser tab shows it without being opened. The line, if any, is the badge's tooltip.

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
