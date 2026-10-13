# Hazel Work Dashboard: agent instructions

The Hazel Work Dashboard is how Matthew and his agent keep track of Hazel work, across sessions, machines and time: what is served where, which PRs are open and how they stand, and what to do next. It is one page, http://localhost:8000/, and this repository is its history.

Read this before working with Matthew on Hazel. Keep the dashboard current as you go: it is the shared memory between sessions.

**This repository is our working record, for the two of us:** what is served where, how the PRs stand, what to do next, and the dashboard's history. It is written in shorthand, for people who were there.

**The Hazel performance analysis series is separate,** in its own repository, [`hazel-performance-analysis`](https://github.com/matthewhammer/hazel-performance-analysis), with its own agent instructions. It is written for readers outside the loop: Cyrus, the Hazel team and others. The dashboard links to the series ("issue 007"), but working notes never go into an issue. When work here answers a question worth sharing, that answer becomes an issue there.

## Where things are

| What | Where |
|---|---|
| The page | `~/localhost-index/index.html`, served at http://localhost:8000/ by the launch entry `localhost-index` in `~/hazel/.claude/launch.json` (`python3 -m http.server 8000`). If 8000 is taken, use 8080. The old `#2492 hazel-dev` entry also names 8000: never run both. |
| What only we know | `~/localhost-index/data.json`: the ports, which PRs are tracked, and our tickets (open, current and closed). **Edit this, never `index.html` or `closed.html`.** |
| The generator | `update.py`: reads `data.json`, asks GitHub (`gh`) for each PR's title, state, CI, review and mergeability, and writes the page, and the closed tickets' page `closed.html`, atomically. If `gh` fails, it writes nothing, and the last good pages stay. |
| The code | `update.py` and `log_notes.py` live in this repository's `dashboard/` folder. `~/localhost-index/update.py` and `~/localhost-index/log_notes.py` are symlinks to them, so the scripts still read and write `~/localhost-index`. |
| The history | This repository: `~/hazel-work-notes`, pushed to `matthewhammer/hazel-work-notes` (private). `~/localhost-index/log_notes.py` copies the page here verbatim, and `data.json` to `dashboard-data/data.json`, so the tickets, closed ones included, have a history too. Browse it at http://localhost:8000/notes/, or clone it. GitHub shows HTML as source. |
| The schedule | `crontab -l`: every 15 minutes, `update.py`, then `log_notes.py`. The last run's output is in `~/localhost-index/update.log`. |

## The page

The title is **Hazel Work Dashboard**. An outline on the side lists the sections, every open ticket by its number, and the closed tickets' page. The sections, in order:

0. **Current ticket,** when there is one: the ticket we are working on now, in full, with a line on what is next on it (`current_note`).

1. **Localhost ports.** One row per thing served or worked on: the PR number and title, linked; the repo and branch; and the localhost link, with deep links where they help, such as `?slide=...`. A row without a PR gets a dash and a short name.
2. **Other PRs we are tracking.** The PRs that are not about performance (features, fixes, docs, CI), with live status and a note.
3. **Repositories we deploy.** Repositories that deploy on a push to a branch, without PRs, such as matthewhammer/kids-choice-games: the latest commit, each project's version from its `VERSIONS.md`, whether Pages has deployed that commit, and open PRs.
4. **Performance Analysis and Improvement.** The PRs against hazelgrove/hazel#2609 (performance challenges), with live status, and the integration PRs (#2635, #2597) that carry their fixes.
5. **Tickets.** Our own numbered tickets (below); the current one is marked.

The **closed tickets** have a page of their own, http://localhost:8000/closed.html, newest first: each with its status, the date it closed, what came of it, and its text as it last read.

## Tickets: our own numbers

We call them **tickets**, not issues: an issue is a GitHub issue (or an issue of the performance analysis series).

- Each ticket has a number, `#N`, from `data.json`'s `next_ticket`. **A number is never reused.** Take `next_ticket` for a new ticket, then increment it.
- **When Matthew calls something important and it is not started, open a ticket right away,** in `tickets`, with an area, its text, where it came from (`source`, and a `url` when there is a real one) and the date (`added`).
- **The current ticket** is the one we are working on now: `current_ticket` is its number, and `current_note` says in a line what is next on it. The page shows it first. Set it when Matthew starts one ("let's do #N", or a pasted ticket link); keep the note up to date as the work moves; set it to `null` when no ticket is in hand. Only an open ticket can be current.
- **Closing a ticket moves it** from `tickets` to `closed_tickets`, never deletes it. Keep its `text` as it last read, and add:
  - `closed`: the date;
  - `status`: **done**; **not needed** (its premise turned out wrong, or there was nothing to do); **dropped** (we decided not to, and why); or **superseded** (another ticket took it over: name it);
  - `outcome`: what came of it, with its commits, PRs, issues of the series or other tickets; and `outcome_url` when one page holds it.
  If it was the current ticket, choose the next current one, or `null`.
- **A parked ticket stays open,** with "PARKED", the date, and the measurement that parked it.
- Each ticket's row has the anchor `#ticket-N`, and a "copy link" button that copies http://localhost:8000/#ticket-N. Old links, `#next-N`, still work, and a link to a closed ticket takes the reader to its row on the closed page. **When Matthew pastes such a link, he means exactly that ticket:** read the ticket with that number in `data.json`, in `tickets` or `closed_tickets`. Never guess from the wording.

## Links

Write references plainly in `data.json`, and `update.py` links them the same way everywhere:

- "issue 006" links to that issue of the performance analysis series. That is the public page once it is published (`~/matthewhammer.github.io/hazel/performance-analysis/006/` exists), and the local draft at http://localhost:8131/series/006/ until then.
- `#2161`, any four digits, links to hazelgrove/hazel on GitHub.
- `#10`, one to three digits, links to that ticket: its row on the dashboard while it is open, and on the closed page once it is closed.
- A 10-character commit id, such as `bd90642654`, links to the commit.

Text already inside a link is left alone. Give a ticket a `url` only when it has a real source; otherwise leave `url` empty, and its "From" is plain text.

## Keeping it current

- **Update in the same turn as the change:** a server started, stopped or moved to another port; a PR opened, retitled, merged or closed; a worktree switched to another branch; a ticket opened, made current, closed or parked. Then run `python3 ~/localhost-index/update.py && python3 ~/localhost-index/log_notes.py` by hand. Don't wait for cron.
- At the start of a session, run `update.py` once, and make sure the `localhost-index` server is up.
- **Launch entries are named with their PR,** such as `#2635 hazel-livelits-modular` or `fumola#129 fumola-pages-wt`. Rename an entry when its worktree's branch, and so its PR, changes. The app runs at most 5 preview servers per worktree, so stopping one may be needed to start another.
- **Always tell Matthew the port, and what build it serves,** in chat. Never put local ports in a PR description: there, say "in the browser".

## Versions

The dashboard's code has a version number, `VERSION` in `dashboard/update.py`, which the page shows in its History line. [`VERSIONS.md`](VERSIONS.md) lists the features of each version, newest first. It started at 0.0.1 on 2026-10-12.

- **When a change to the code adds or changes a feature,** bump `VERSION`, add the new version to `VERSIONS.md` with its date and what it changed, and commit the code with it. `log_notes.py` commits only snapshots, so the code is committed by hand.
- A change to `data.json` alone (a port, a PR, a step) is content, not a new version.

## The history

`log_notes.py` writes the page to `dashboard-snapshots/<YYYY>/<MM>/<DD>/<YYYY-MM-DD>T<HHMM><+-hhmm>.html`: a folder for each year, month and day, and a file name that carries the whole date and time zone, so a file still says when it was taken if the folders are ever reorganized (as they were on 2026-10-12, from one folder per day at the top). It writes nothing when the page changed only in its "Updated" line, then commits and pushes, retrying the push on every run. The files are exactly the page as served, in HTML.

## Related practice

- **The performance analysis series:** http://matthewhammer.org/hazel/performance-analysis/, issues 001–006. The sources are in `~/hazel-perf-report`, served at http://localhost:8131/series/.
  - Write an issue as a draft. Matthew reviews it, then publish: copy it to `~/matthewhammer.github.io/hazel/performance-analysis/`, push, wait for the Pages run, and check the live page.
  - A correction to a published issue is a dated update box under the short answers, a note after each claim it supersedes, and an "Update" section. The original text stays as written.
- **Performance is the highest priority.** Profile, and measure before and after. One heavy job at a time: the laptop crashes under load.
- **PRs:**
  - Ask before merging; a PR to `dev` also needs an approving review.
  - Only touch Matthew's own PRs.
  - Work on #2597's branch (`integration/livelits-splicerefs-full`) first, then cherry-pick to #2635 and push both.
  - Turn on auto-fix for a PR when Matthew asks.

## `data.json` fields

- `ports`: rows with `pr`, `repo`, `branch`, optional `base`, and `links` as `[text, url]` pairs. A row without a PR has `name`, `repo_html`, `branch`, an optional `branch_note`, and `links`.
- `tracking_issue`: 2609.
- `perf_prs`, `integration_prs`: PR numbers.
- `other_prs`: `{pr, note}`.
- `repos`: `{repo, branch, versions, live, note}`. `versions` is `[label, path of a VERSIONS.md]` pairs; `live` is `[text, url]` pairs; `note` may hold HTML. A project's version heading must read `## X.Y.Z (YYYY-MM-DD)`.
- `tickets`: the open tickets, `{id, area, added, text, source, url}`. `text` may hold HTML.
- `current_ticket`: the number of the ticket we are working on, or `null`; `current_note`: a line on what is next on it, may hold HTML.
- `closed_tickets`: `{id, area, text, source, listed, closed, status, outcome, outcome_url}`. `status` is `done`, `not needed`, `dropped` or `superseded`; `outcome` may hold HTML; `listed` is the date it was first seen on the page, where `added` was not recorded.
- `next_ticket`: the next number to give. Never reuse one.

These fields replaced `next_steps` and `next_id` on 2026-10-13. Tickets #1–#27 were numbered before then; the nine closed by then (#1, #3, #6, #8, #9, #11, #20, #21, #26) were reconstructed from the snapshots and this session's record, with their status and outcome.
