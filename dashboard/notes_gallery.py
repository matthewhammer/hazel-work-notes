#!/usr/bin/env python3
"""The working notes as a gallery (^ticket(182), Matthew's, 2026-10-16): a card
per note in work-notes/, newest first, each with a picture drawn for it, a
short summary of what it records, its next steps and a link to the note;
tickets, reports and Dress Up reports as chips, GitHub numbers as links, each
with a hover card, as on the dashboard. Published at
https://matthewhammer.org/hazel/work-notes/, in the homepage's repository,
beside the dashboard.

  python3 dashboard/notes_gallery.py [out.html]
      (default ~/matthewhammer.github.io/hazel/work-notes/index.html)

The cards come from work-notes/gallery.json, one entry per note, kept by
hand (by Claude) when a note is added: path, title, when, why, summary, next
(a few short steps), and art, the card's picture: an SVG drawn for that note
(viewBox 0 0 240 150; no two alike), in the house style, ink on cream with
hatching and a little oxblood, ochre or green. In a summary, ^ticket(N),
^report(N) and ^du_report(N) become chips, #NNNN and owner/repo#N links. A
note with no entry still gets a card (its title, a plain picture), and the
script says so. Then commit and push the homepage (pull first: the dashboard
publishes there too)."""
import html, json, os, re, sys

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, DIR)
import prlinks, refcards

NOTES = os.path.dirname(DIR)
DATA = os.path.expanduser("~/localhost-index/data.json")
CACHE = os.path.expanduser("~/localhost-index/.prlinks-cache.json")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/matthewhammer.github.io/hazel/work-notes/index.html")
DASH = "https://matthewhammer.org/hazel/dashboard/"
SERIES = "https://matthewhammer.org/hazel/reports/"
DU_REPORTS = "https://matthewhammer.org/kids-choice-games/dress-up/reports/"
PUBLIC = "https://matthewhammer.org/hazel-work-notes/"
REPO = "https://github.com/matthewhammer/hazel-work-notes"

data = json.load(open(DATA))
OPEN = {t["id"] for t in data["tickets"]}
CLOSED = {t["id"] for t in data.get("closed_tickets", [])}

def chip(kind, n):
    return f'<code class="ref"><b>^{kind}(</b>{int(n)}<b>)</b></code>'

def chips(text):
    def ticket(m):
        n = int(m.group(1))
        href = DASH + f"#ticket-{n}" if n in OPEN else DASH + f"closed.html#ticket-{n}" if n in CLOSED else None
        return f'<a href="{href}">{chip("ticket", n)}</a>' if href else chip("ticket", n)
    text = re.sub(r"\^ticket\((\d+)\)", ticket, text)
    text = re.sub(r"\^report\((\d+)\)", lambda m: f'<a href="{SERIES}{int(m.group(1)):03d}/">{chip("report", m.group(1))}</a>', text)
    text = re.sub(r"\^du_report\((\d+)\)", lambda m: f'<a href="{DU_REPORTS}{int(m.group(1)):03d}/">{chip("du_report", m.group(1))}</a>', text)
    return text

def notes():
    found = []
    for root, _, files in os.walk(os.path.join(NOTES, "work-notes")):
        for f in files:
            if re.match(r"\d{4}-\d{2}-\d{2}T\d{4}[+-]\d{4}\.html$", f):
                found.append(os.path.relpath(os.path.join(root, f), NOTES))
    return sorted(found, key=os.path.basename, reverse=True)

def title_of(path):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", open(os.path.join(NOTES, path), encoding="utf-8").read(), re.S)
    return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else os.path.basename(path)

PLAIN = ('<svg viewBox="0 0 240 150" role="img" aria-label="a page of notes"><rect width="240" height="150" fill="#f3ead6"/>'
         '<g stroke="#2b2118" stroke-width="1.2" opacity="0.7">' + "".join(f'<line x1="70" y1="{y}" x2="{170 if y % 20 else 150}" y2="{y}"/>' for y in range(40, 120, 10)) +
         '</g><rect x="60" y="25" width="120" height="105" fill="none" stroke="#2b2118" stroke-width="1.5"/></svg>')

def card(path, e):
    stamp = os.path.basename(path)[:15]
    when = f"{stamp[:10]} {stamp[11:13]}:{stamp[13:15]}"
    title = e.get("title") or title_of(path)
    art = e.get("art") or PLAIN
    why = f' <span class="why">{html.escape(e["why"])}</span>' if e.get("why") else ""
    nxt = e.get("next") or []
    nxt_html = ("<p class=\"next-h\">Next, then</p><ul class=\"next\">" + "".join(f"<li>{chips(html.escape(s, quote=False))}</li>" for s in nxt) + "</ul>") if nxt else ""
    summary = chips(html.escape(e.get("summary", ""), quote=False)) if e else '<span class="dim">No summary yet.</span>'
    url = PUBLIC + path
    return (f'<article class="note" id="n-{stamp}">\n'
            f'  <a class="art" href="{url}" aria-label="{html.escape(title)}">{art}</a>\n'
            f'  <p class="when"><time datetime="{stamp[:10]}">{when}</time>{why}</p>\n'
            f'  <h2><a href="{url}">{html.escape(title)}</a></h2>\n'
            f'  <p class="summary">{summary}</p>\n'
            f'  {nxt_html}\n'
            f'</article>')

def page(cards, count):
    THEME_HEAD = ('<!-- theme: head begin -->\n<script>try { var t = localStorage.getItem("theme"); if (t === "light" || t === "dark") '
                  'document.documentElement.setAttribute("data-theme", t); } catch (e) {}</script>\n<!-- theme: head end -->')
    NAV_HEAD = '<!-- nav: begin --><meta name="theme-support" content="data-theme"><script src="https://matthewhammer.org/nav/nav.js"></script><!-- nav: end -->'   # (ticket 296: the nav bar; ~/matthewhammer.github.io/nav/agent-instructions.md)
    THEME = open(os.path.expanduser("~/matthewhammer.github.io/hazel/dress-up/index.html"), encoding="utf-8").read()
    THEME = THEME[THEME.index("<!-- theme: begin -->"):THEME.index("<!-- theme: end -->") + len("<!-- theme: end -->")]
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
{NAV_HEAD}
{THEME_HEAD}
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="noindex">
  <title>Hazel Work Notes</title>
  <meta name="color-scheme" content="light dark">
  <meta name="description" content="Matthew Hammer's dated working notes on Hazel, kept with Claude: what each records, at a glance, with a link to the note.">
  <link rel="icon" href="../../favicon.ico">
  <link rel="stylesheet" href="../../style.css">
  <script src="../../outline.js" defer></script>
  <style>
    /* The homepage's look, plus a dark palette for the theme switch. */
    @media (prefers-color-scheme: dark) {{
      :root:not([data-theme="light"]) {{ --bg: #15171a; --panel: #1d2024; --rule: #33373d; --fg: #d9d7d2; --dim: #a2a9b3;
        --blue: #93c5fd; --ink: #f2f0ea; --accent: #f0a48f; --sym: #c4a5d0; }}
      :root:not([data-theme="light"]) a {{ border-bottom-color: #3b5573; }}
    }}
    :root[data-theme="dark"] {{ --bg: #15171a; --panel: #1d2024; --rule: #33373d; --fg: #d9d7d2; --dim: #a2a9b3;
      --blue: #93c5fd; --ink: #f2f0ea; --accent: #f0a48f; --sym: #c4a5d0; }}
    :root[data-theme="dark"] a {{ border-bottom-color: #3b5573; }}
    /* a gallery uses the window's width beside the outline; the header keeps its reading width */
    main {{ max-width: none; margin: 0; padding: 3.5rem clamp(1rem, 2.5vw, 2rem) 4rem; }}
    @media (min-width: 48rem) {{ main {{ margin-left: 15rem; }} }}   /* (beside the outline, at every width: style.css centers a narrow main from 78rem) */
    header {{ max-width: 45rem; margin-bottom: 1.6rem; }}
    .gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 19rem), 1fr)); gap: 1.1rem; }}
    .note {{ border: 1px solid var(--rule); border-radius: 8px; background: var(--panel); padding: 0.75rem 0.85rem 0.9rem; min-width: 0; }}
    .note .art {{ display: block; border: 0; margin: -0.1rem 0 0.6rem; }}
    .note .art svg {{ display: block; width: 100%; height: auto; border-radius: 5px; border: 1px solid var(--rule); }}
    .note .when {{ margin: 0; font-size: 0.8rem; color: var(--dim); }}
    .note .why {{ display: inline-block; margin-left: 0.4rem; padding: 0 0.5rem; border-radius: 999px; border: 1px solid var(--rule); font-size: 0.74rem; }}
    .note h2 {{ font-size: 1.02rem; line-height: 1.35; margin: 0.25rem 0 0.4rem; }}
    .note h2 a {{ border-bottom: 0; }}
    .note .summary {{ font-size: 0.9rem; line-height: 1.5; margin: 0 0 0.4rem; overflow-wrap: anywhere; }}
    .note .next-h {{ font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--dim); margin: 0.5rem 0 0.15rem; }}
    .note ul.next {{ margin: 0; padding-left: 1.1rem; font-size: 0.84rem; color: var(--dim); }}
    .dim {{ color: var(--dim); }}
  </style>
</head>
<body>
  <button class="outline-toggle" id="outline-toggle" type="button"
          aria-controls="outline" aria-expanded="false" aria-label="Open page outline">
    <svg class="bars" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
      <path d="M2 4h12M2 8h12M2 12h12"/>
    </svg>
    <svg class="ex" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
      <path d="M3.5 3.5l9 9M12.5 3.5l-9 9"/>
    </svg>
  </button>
  <nav class="outline" id="outline" aria-label="Page outline">
    <p class="outline-label">Pages</p>
    <ul class="outline-pages">
      <li><a href="../../">Home</a></li>
      <li><a href="../">Hazel</a></li>
      <li><a href="../dashboard/">Work dashboard</a></li>
      <li><span class="here">Work notes</span></li>
      <li><a href="../reports/">Hazel reports</a></li>
      <li><a href="../dress-up/">Dress Up</a></li>
    </ul>
  </nav>
  <main>
    <header>
      <h1>Hazel Work Notes</h1>
      <p class="tagline">What each of our working notes records, at a glance</p>
      <p>When a session with Claude pauses (a shutdown, a crash, the end of a long stretch), it writes a dated note: what was done, where things are, and what is next. Here are all {count} of them, newest first, each with a picture drawn for it. The notes themselves are in <a href="{REPO}/tree/main/work-notes">matthewhammer/hazel-work-notes</a>, beside the <a href="../dashboard/">work dashboard</a>'s history. They are written in shorthand, for the two of us; the write-ups for other readers are the <a href="../reports/">Hazel reports</a> and the <a href="../dress-up/reports/">Dress Up reports</a>.</p>
    </header>
    <section class="gallery" aria-label="The notes, newest first">
{cards}
    </section>
    <footer>
      &copy; 2026 Matthew Hammer &mdash; Built with plain HTML + CSS on GitHub Pages. Made by <a href="{REPO}/blob/main/dashboard/notes_gallery.py">notes_gallery.py</a>.
    </footer>
  </main>
{THEME}
</body>
</html>
'''

entries = {e["path"]: e for e in json.load(open(os.path.join(NOTES, "work-notes", "gallery.json"), encoding="utf-8"))}
paths = notes()
missing = [p for p in paths if p not in entries]
out = page("\n".join(card(p, entries.get(p, {})) for p in paths), len(paths))
out = refcards.process(prlinks.process(out, CACHE))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write(out)
print(f"{OUT}: {len(paths)} notes, {len(paths) - len(missing)} with a summary and a picture"
      + (f"; no entry yet for {', '.join(missing)}" if missing else ""))
