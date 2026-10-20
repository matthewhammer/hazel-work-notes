"""Every PR or issue number on the dashboard is a link, with a card on
hover (Matthew's rule, 2026-10-14, as in the performance series: see its
tools/link_prs.py). A bare `#N` of four digits or more is a hazelgrove/hazel
PR or issue; `owner/repo#N` names its repository; a short `#45` is one of
the dashboard's own tickets and is left alone. Text already in a link, and
<head>, <script>, <style> and <svg>, are left alone too.

The card (pr_cards.html) asks GitHub live when it shows; what GitHub said
when the page was made is its fallback, kept here for 15 minutes so that
the every-minute publish does not ask GitHub each time."""
import json, os, re, subprocess, time

DIR = os.path.dirname(os.path.realpath(__file__))
CARDS = open(os.path.join(DIR, "pr_cards.html"), encoding="utf-8").read()
TTL = 15 * 60
REF = re.compile(r"(?<![\w&/#])(?:([A-Za-z0-9_-]+/[A-Za-z0-9_.-]+))?#(\d{1,6})\b")
LINK = re.compile(r'href="https://github\.com/([A-Za-z0-9_-]+/[A-Za-z0-9_.-]+)/(?:pull|issues)/(\d+)"')
SKIP = {"a", "head", "script", "style", "svg", "title"}

class Cache:
    def __init__(self, path):
        self.path = path
        try:
            self.data = json.load(open(path))
        except (OSError, ValueError):
            self.data = {}
    def get(self, repo, n):
        key, now = f"{repo}#{n}", time.time()
        e = self.data.get(key)
        if e and now - e.get("at", 0) < TTL:
            return e["info"]
        out = subprocess.run(["gh", "api", f"repos/{repo}/issues/{n}", "--jq",
            '{title, state: (if .pull_request.merged_at then "merged" elif .draft then "draft" else .state end), '
            'author: .user.login, created: .created_at, updated: .updated_at, comments, '
            'kind: (if .pull_request then "pull" else "issues" end)}'], capture_output=True, text=True)
        try:
            info = json.loads(out.stdout)
        except ValueError:
            return e["info"] if e else None   # GitHub unreachable: the last known
        # (^ticket(478)) a PR's base branch, which the card shows: dev or not
        if info.get("kind") == "pull":
            base = subprocess.run(["gh", "api", f"repos/{repo}/pulls/{n}", "--jq", ".base.ref"], capture_output=True, text=True).stdout.strip()
            if base:
                info["base"] = base
        self.data[key] = {"at": now, "info": info}
        return info
    def save(self):
        tmp = self.path + ".tmp"
        json.dump(self.data, open(tmp, "w"), indent=1, sort_keys=True)
        os.replace(tmp, self.path)

def process(page, cache_path):
    # (a page processed before has the card block: take it out first, so
    # a second run gives the same page)
    page = re.sub(r"\s*<!-- pr-cards: begin -->.*?<!-- pr-cards: end -->", "", page, flags=re.S)
    cache = Cache(cache_path)
    def sub(m):
        repo, n = m.group(1) or "hazelgrove/hazel", m.group(2)
        if not m.group(1) and len(n) < 4:
            return m.group(0)            # a dashboard ticket, #45
        info = cache.get(repo, n)
        if info is None:
            return m.group(0)
        return f'<a href="https://github.com/{repo}/{info["kind"]}/{n}">{m.group(0)}</a>'
    parts = re.split(r"(<!--.*?-->|<[^>]+>)", page, flags=re.S)
    depth = {t: 0 for t in SKIP}
    out = []
    for p in parts:
        m = re.match(r"<(/?)([a-zA-Z][\w-]*)", p)
        if m and not p.startswith("<!--"):
            name = m.group(2).lower()
            if name in SKIP and not p.endswith("/>"):
                depth[name] += -1 if m.group(1) else 1
            out.append(p)
        elif p.startswith("<") or any(depth.values()):
            out.append(p)
        else:
            out.append(REF.sub(sub, p))
    page = "".join(out)
    keys = sorted(set(LINK.findall(page)), key=lambda k: (k[0], int(k[1])))
    cached = {}
    for r, n in keys:
        info = cache.get(r, n)
        if info is not None:
            cached[f"{r}#{n}"] = info
    cache.save()
    if cached:
        block = CARDS.replace("__CACHED__", json.dumps(cached, ensure_ascii=False).replace("</", "<\\/")) \
                     .replace("__BUILT__", time.strftime("%Y-%m-%d"))
        i = page.rfind("</body>")
        page = page[:i].rstrip() + "\n" + block + "\n" + page[i:] if i >= 0 else page + block
    return page
