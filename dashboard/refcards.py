"""Hover cards for ^ticket(N) and ^report(N) links (Matthew, 2026-10-14):
ref_cards.html, put before </body> between "ref-cards" markers when a page
has such a chip. The dashboard's own pages carry their tickets in it (made
with the page, so they change together); other pages pass no tickets, and
the card reads the published data live. A report's card always reads the
report's page live.

Since ^ticket(428) (2026-10-19) a dashboard page carries only the tickets it
names (its ^ticket(N) chips): all of them were 202 KB in every page, growing
with every ticket ever made. A chip added in the browser (the nav bar's) for
a ticket the page does not carry reads the data live, as other pages do."""
import json, os, re, html

DIR = os.path.dirname(os.path.realpath(__file__))
CARDS = open(os.path.join(DIR, "ref_cards.html"), encoding="utf-8").read()

def plain(h):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h or ""))).strip()

def cut(t, n):
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"

def lead(h):
    m = re.match(r"\s*<b>(.*?)</b>", h or "", flags=re.S)
    return plain(m.group(1)) if m else cut(plain(h), 200)

REF = re.compile(r"\^ticket\(</b>(\d+)<b>\)")

def tickets(data, only=None):
    """What the cards need of data.json, small: each ticket's lead line (only those numbered in `only`, if given)."""
    keep = (lambda t: True) if only is None else (lambda t: t["id"] in only)
    one = lambda t, closed: {k: v for k, v in {
        "id": t["id"], "area": t.get("area", ""), "added": t.get("added", ""), "text": lead(t.get("text", "")),
        "source": cut(plain(t.get("source", "")), 120),
        **({"status": t.get("status", ""), "closed": t.get("closed", ""), "outcome": cut(plain(t.get("outcome", "")), 180)} if closed else {}),
    }.items() if v != ""}
    return {"tickets": [one(t, False) for t in data.get("tickets", []) if keep(t)],
            "closed_tickets": [one(t, True) for t in data.get("closed_tickets", []) if keep(t)],
            "current_ticket": data.get("current_ticket"), "current_waiting": data.get("current_waiting") or False,
            "queue": data.get("queue", [])}

def process(page, data=None):
    page = re.sub(r"\s*<!-- ref-cards: begin -->.*?<!-- ref-cards: end -->", "", page, flags=re.S)
    if 'class="ref"' not in page:
        return page
    embed = json.dumps(tickets(data, {int(n) for n in REF.findall(page)}), ensure_ascii=False).replace("</", "<\\/") if data else "null"
    block = CARDS.replace("__TICKETS__", embed)
    i = page.rfind("</body>")
    return page[:i].rstrip() + "\n" + block + "\n" + page[i:] if i >= 0 else page + block
