"""A working-notes page, made like the dashboard and the series (Matthew,
2026-10-14). Idempotent; run it on every new or changed page under
work-notes/:

- each step of the list after <h2 id="next"> gets a link to itself, a
  "copy link" chip and a "copy for a ticket" chip (the copied request names
  the page, the step and its URL, for Matthew to paste to Claude);
- tickets and reports in the text become ^ticket(N) and ^report(N) chips,
  each a link to its public page (the dashboard's row, open or closed; the
  series' report): "Ticket #45", "#45" (one to three digits), "issue 013" or
  "report 013"; each chip's link gets a hover card (refcards.py), read live;
- GitHub PR and issue numbers become links with live hover cards
  (prlinks.py, as on the dashboard).

  python3 dashboard/notes_page.py work-notes/YYYY/MM/DD/<stamp>.html ..."""
import json, os, re, sys

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, DIR)
import prlinks, refcards

DATA = os.path.expanduser("~/localhost-index/data.json")
CACHE = os.path.expanduser("~/localhost-index/.prlinks-cache.json")
DASH = "https://matthewhammer.org/hazel/dashboard/"   # (until 2026-10-16: /hazel-work-notes/, which redirects)
SERIES = "https://matthewhammer.org/hazel/reports/"
data = json.load(open(DATA))
OPEN = {t["id"] for t in data["tickets"]}
CLOSED = {t["id"] for t in data.get("closed_tickets", [])}

def chip(kind, n):
    return f'<code class="ref"><b>^{kind}(</b>{int(n)}<b>)</b></code>'
def ticket(n, linked):
    n = int(n)
    href = DASH + f"#ticket-{n}" if n in OPEN else DASH + f"closed.html#ticket-{n}" if n in CLOSED else None
    return chip("ticket", n) if linked or not href else f'<a href="{href}">{chip("ticket", n)}</a>'
def report(n, linked):
    return chip("report", n) if linked else f'<a href="{SERIES}{int(n):03d}/">{chip("report", n)}</a>'

def refs_text(t, linked):
    t = re.sub(r"(?<![\w^/])(?:[Ii]ssues?|[Rr]eports?)\s+(\d{3})\s*([–-])\s*(\d{3})\b",
               lambda m: report(m.group(1), linked) + m.group(2) + report(m.group(3), linked), t)
    t = re.sub(r"(?<![\w^/])(?:[Ii]ssue|[Rr]eport)\s+(\d{3})\b", lambda m: report(m.group(1), linked), t)
    t = re.sub(r"(?<![\w^/])(?:[Tt]ickets?\s+)?#(\d{1,3})\b", lambda m: ticket(m.group(1), linked), t)
    return t.replace("<b>^issue(</b>", "<b>^report(</b>")

SKIP = {"head", "script", "style", "svg", "title"}
def refs(page):
    parts = re.split(r"(<!--.*?-->|<[^>]+>)", page, flags=re.S)
    depth, a, out = {t: 0 for t in SKIP}, 0, []
    for p in parts:
        m = re.match(r"<(/?)([a-zA-Z][\w-]*)", p)
        if m and not p.startswith("<!--"):
            name = m.group(2).lower()
            if name in SKIP and not p.endswith("/>"):
                depth[name] += -1 if m.group(1) else 1
            if name == "a":
                a += -1 if m.group(1) else 1
            out.append(p)
        elif p.startswith("<") or any(depth.values()):
            out.append(p)
        else:
            out.append(refs_text(p, a > 0))
    return "".join(out)

BLOCK_BEGIN, BLOCK_END = "<!-- notes: begin -->", "<!-- notes: end -->"
BLOCK = BLOCK_BEGIN + r'''
<style>
  code.ref { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.9em; white-space: nowrap; }
  code.ref b { font-weight: 800; }
  button.mint { margin-left: 4px; font: inherit; font-size: 0.75em; padding: 0 6px; border: 1px solid var(--line, #ccc);
    border-radius: 4px; background: transparent; color: var(--muted, #666); cursor: pointer; vertical-align: 1px; }
  button.mint:hover { color: inherit; }
  button.mint.done { color: var(--good, #15803d); border-color: var(--good, #15803d); }
  a.step-link { color: var(--muted, #666); text-decoration: none; font-size: 0.85em; margin-left: 4px; }
  a.step-link:hover { text-decoration: underline; }
  li:target { background: color-mix(in srgb, var(--good, #15803d) 12%, transparent); border-radius: 6px; }
</style>
<script>
/* Each step under "Next": a link to it, a chip copying that link, and a
   chip copying a request to mint a ticket for it (to paste to Claude). */
(() => {
  const h = document.getElementById("next");
  if (!h) return;
  let list = h.nextElementSibling;
  while (list && !/^(OL|UL)$/.test(list.tagName)) {
    if (list.tagName === "H2") return;
    list = list.nextElementSibling;
  }
  if (!list) return;
  const page = location.origin + location.pathname, name = document.title;
  const copy = async (b, text) => {
    try { await navigator.clipboard.writeText(text); }
    catch (_) { const t = document.createElement("textarea"); t.value = text; document.body.append(t); t.select(); document.execCommand("copy"); t.remove(); }
    const was = b.textContent; b.textContent = "copied"; b.classList.add("done");
    setTimeout(() => { b.textContent = was; b.classList.remove("done"); }, 1500);
  };
  [...list.children].filter(li => li.tagName === "LI").forEach((li, i) => {
    const n = i + 1;
    if (!li.id) li.id = "step-" + n;
    const url = page + "#" + li.id;
    const b = li.querySelector("b, strong");
    const title = (b ? b.textContent : li.textContent).replace(/\s+/g, " ").trim().replace(/[:.,;]$/, "").slice(0, 160);
    const a = document.createElement("a");
    a.href = "#" + li.id; a.className = "step-link"; a.textContent = "#" + n; a.title = "A link to this step";
    const link = document.createElement("button");
    link.type = "button"; link.className = "mint"; link.textContent = "copy link"; link.title = "Copies a link to this step";
    link.addEventListener("click", () => copy(link, url));
    const mint = document.createElement("button");
    mint.type = "button"; mint.className = "mint"; mint.textContent = "copy for a ticket";
    mint.title = "Copies a request to mint a ticket for this step, to paste to Claude";
    mint.addEventListener("click", () => copy(mint, "Mint a ticket for this step: " + name + ", Next, step " + n + ': "' + title + '". ' + url));
    li.append(" ", a, " ", link, " ", mint);
  });
  if (location.hash) { const t = document.getElementById(location.hash.slice(1)); if (t) t.scrollIntoView(); }
})();
</script>
''' + BLOCK_END

def run(path):
    src = open(path, encoding="utf-8").read()
    page = re.sub(r"\s*" + re.escape(BLOCK_BEGIN) + r".*?" + re.escape(BLOCK_END), "", src, flags=re.S)
    page = refs(page)
    page = refcards.process(prlinks.process(page, CACHE))
    i = page.rfind("</body>")
    page = page[:i].rstrip() + "\n" + BLOCK + "\n" + page[i:]
    if page != src:
        open(path, "w", encoding="utf-8").write(page)
    print(f"{path}: chips {page.count('class=\"ref\"')}, GitHub links {len(re.findall(r'github.com/[^\"]+/(?:pull|issues)/', page))}, cards {'pr-cards: begin' in page}")

for p in sys.argv[1:]:
    run(p)
