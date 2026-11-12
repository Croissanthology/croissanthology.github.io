#!/usr/bin/env python3
"""Link previews: looks up every outside link in the posts ahead of time, so hovering one can show
something better than "refused to connect".

For each link it stores only what a preview needs:
  Wikipedia      the article's lead section, description and a small thumbnail (Wikipedia's API)
  tweets         text, author and date (publish.twitter.com/oembed, the official embed service)
  Bluesky posts  text, author, date, images (Bluesky's public API)
  Substack       title, subtitle, cover, author, date, opening (Substack's public post API)
  GitHub         repo description, or an issue's title and opening (GitHub's API)
  anything else  title, description and image from the page's own <meta> tags, and whether the
                 page allows being shown inside another page (X-Frame-Options / frame-ancestors)
  images         a link straight to an image is just noted as one

Files:
  _previews/links.json    everything it knows, by link, with the date it last looked (not published)
  _previews/report.json   what the last run did
  previews/<post>.json    what each post's page needs, by the link's href; wide.js reads this

Manners: it says who it is, obeys robots.txt, waits between requests to the same site, gives up on a
site that refuses, never pretends to be a browser, and only looks again when a link is new or stale.

  python3 scripts/previews/index.py            # look up new and stale links, write the files
  python3 scripts/previews/index.py --limit 50 # at most 50 lookups this run
  python3 scripts/previews/index.py --offline  # just rewrite previews/*.json from what's known
"""
import argparse
import datetime
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.robotparser
import zlib
from pathlib import Path

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "_previews" / "links.json"
REPORT = ROOT / "_previews" / "report.json"
OUT = ROOT / "previews"
UA = "croissanthology-link-previews/1.0 (+https://croissanthology.com)"
OURS = {"croissanthology.com", "www.croissanthology.com", "croissanthology.github.io"}
FRESH_DAYS, RETRY_DAYS = 45, 6      # look again at a good answer after 45 days, at a failure after 6
GAP = 1.5                           # seconds between two requests to the same site
TIMEOUT = 15
MAX_PAGE = 400_000                  # bytes of a page read for its <meta> tags
TODAY = datetime.date.today()

session = requests.Session()
session.headers.update({"User-Agent": UA, "Accept-Language": "en"})
last_hit, robots, refused = {}, {}, {}


class Skip(Exception):
    """This link gets no preview (and why)."""


# ---------------------------------------------------------------- fetching, politely

def wait_for(host):
    since = time.time() - last_hit.get(host, 0)
    if since < GAP:
        time.sleep(GAP - since)
    last_hit[host] = time.time()


def allowed(url):
    """robots.txt, for the name this script goes by."""
    p = urllib.parse.urlsplit(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            wait_for(p.netloc)
            r = session.get(base + "/robots.txt", timeout=TIMEOUT)
            if r.status_code == 200 and "text" in r.headers.get("content-type", "text"):
                rp.parse(r.text.splitlines())
            else:
                rp = None       # no robots.txt (or it couldn't be read): nothing is forbidden
        except requests.RequestException:
            rp = None
        robots[base] = rp
    rp = robots[base]
    return True if rp is None else rp.can_fetch(UA, url)


def get(url, *, check_robots=True, headers=None, stream=False):
    host = urllib.parse.urlsplit(url).netloc
    if refused.get(host, 0) >= 2:
        raise Skip("site refused earlier in this run")
    if check_robots and not allowed(url):
        raise Skip("robots.txt says no")
    wait_for(host)
    try:
        r = session.get(url, timeout=TIMEOUT, headers=headers or {}, stream=stream)
    except requests.RequestException as e:
        raise Skip(f"couldn't connect ({type(e).__name__})")
    if r.status_code in (401, 403, 429, 451, 503):
        refused[host] = refused.get(host, 0) + 1
        r.close()
        raise Skip(f"refused ({r.status_code})")
    if r.status_code != 200:
        r.close()
        raise Skip(f"status {r.status_code}")
    return r


# ---------------------------------------------------------------- small helpers

def squash(text):
    return re.sub(r"\s+", " ", text or "").strip()


def clip(text, n=700):
    """The opening of a text, cut at a word, keeping paragraph breaks."""
    text = "\n".join(squash(line) for line in (text or "").splitlines() if squash(line))
    if len(text) <= n:
        return text
    cut = text[:n].rsplit(" ", 1)[0].rstrip(",;:—-")
    return cut + "…"


def nice_date(iso):
    try:
        d = datetime.datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return f"{d.day} {d.strftime('%b %Y')}"
    except (ValueError, AttributeError):
        return ""


def https_only(url):
    return url if isinstance(url, str) and url.startswith("https://") else ""


def tidy(rec):
    return {k: v for k, v in rec.items() if v not in ("", None, False, [], {})}


def can_frame(headers):
    """Does the page let itself be shown inside another site's page?"""
    if headers.get("x-frame-options"):
        return False
    for part in headers.get("content-security-policy", "").split(";"):
        words = part.split()
        if words and words[0].lower() == "frame-ancestors":
            return any(w in ("*", "https:") for w in words[1:])
    return True


# ---------------------------------------------------------------- one kind of link each

WIKI_TAGS = {"p", "b", "i", "em", "strong", "sub", "sup", "ul", "ol", "li", "br"}


def clean_lead(extract):
    """Wikipedia's intro as plain paragraphs: only a few harmless tags, no attributes."""
    soup = BeautifulSoup(extract or "", "html.parser")
    for junk in soup.select("style, link, script, .mw-empty-elt, .noexcerpt, .mw-ref, table, figure, img"):
        junk.decompose()
    for el in list(soup.find_all(True)):
        if el.name in WIKI_TAGS:
            el.attrs = {}
        else:
            el.unwrap()
    out, size = [], 0
    for el in soup.contents:
        if isinstance(el, NavigableString):
            continue
        if not squash(el.get_text()):
            continue
        out.append(str(el))
        size += len(el.get_text())
        if len(out) >= 8 or size > 5000:
            break
    return "".join(out)


def wikipedia(url, p):
    m = re.fullmatch(r"([a-z-]+)\.(?:m\.)?wikipedia\.org", p.hostname)
    title = urllib.parse.unquote(p.path[len("/wiki/"):])
    if not m or not p.path.startswith("/wiki/") or not title or re.match(r"(File|Special|Category|Help|Talk|Wikipedia|User|Template):", title):
        raise Skip("not an article")
    api = f"https://{m.group(1)}.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "format": "json", "formatversion": "2", "redirects": "1",
        "prop": "extracts|pageimages|description", "exintro": "1", "pithumbsize": "320", "titles": title})
    pages = get(api, check_robots=False).json().get("query", {}).get("pages", [])   # the API is there to be asked
    if not pages or pages[0].get("missing") or not pages[0].get("extract"):
        raise Skip("no such article")
    page = pages[0]
    lead = clean_lead(page["extract"])
    if not lead:
        raise Skip("empty lead")
    thumb = page.get("thumbnail") or {}
    img = [thumb["source"], thumb.get("width"), thumb.get("height")] if https_only(thumb.get("source")) else None
    return tidy({"kind": "wiki", "site": "Wikipedia", "title": page.get("title"), "desc": page.get("description"),
                 "html": lead, "img": img})


def tweet(url, p):
    m = re.fullmatch(r"/([A-Za-z0-9_]+)/status(?:es)?/(\d+).*", p.path)
    if not m:
        raise Skip("not a tweet")
    canon = f"https://twitter.com/{m.group(1)}/status/{m.group(2)}"
    api = "https://publish.twitter.com/oembed?" + urllib.parse.urlencode(
        {"url": canon, "omit_script": "1", "dnt": "1", "hide_thread": "1", "lang": "en"})
    data = get(api, check_robots=False).json()
    soup = BeautifulSoup(data.get("html", ""), "html.parser")
    para = soup.select_one("blockquote > p")
    if para is None:
        raise Skip("no text in the embed")
    for br in para.find_all("br"):
        br.replace_with("\n")
    media = False
    for a in para.find_all("a"):
        if a.get_text().startswith("pic.twitter.com") or re.match(r"https://t\.co/\w+$", a.get_text()):
            media = media or a.get_text().startswith("pic.twitter.com")
            a.decompose()
    when = soup.select("blockquote > a")
    handle = (data.get("author_url") or "").rstrip("/").rsplit("/", 1)[-1]
    return tidy({"kind": "tweet", "site": "X", "by": squash(data.get("author_name")), "handle": "@" + handle if handle else "",
                 "date": squash(when[-1].get_text()) if when else "", "text": clip(para.get_text(), 1200),
                 "more": "with an image or video" if media else ""})


def bluesky(url, p):
    m = re.fullmatch(r"/profile/([^/]+)/post/([A-Za-z0-9]+)/?", p.path)
    if not m:
        raise Skip("not a post")
    api = "https://public.api.bsky.app/xrpc/app.bsky.feed.getPostThread?" + urllib.parse.urlencode(
        {"uri": f"at://{m.group(1)}/app.bsky.feed.post/{m.group(2)}", "depth": "0", "parentHeight": "0"})
    post = get(api, check_robots=False).json().get("thread", {}).get("post") or {}
    record, author = post.get("record") or {}, post.get("author") or {}
    if not record.get("text") and not post.get("embed"):
        raise Skip("empty post")
    imgs = [https_only(i.get("thumb")) for i in (post.get("embed") or {}).get("images", [])]
    return tidy({"kind": "tweet", "site": "Bluesky", "by": squash(author.get("displayName")) or author.get("handle"),
                 "handle": "@" + author["handle"] if author.get("handle") else "", "date": nice_date(record.get("createdAt")),
                 "text": clip(record.get("text"), 1200), "imgs": [i for i in imgs if i][:4]})


def substack(url, p):
    m = re.fullmatch(r"/p/([^/]+)/?", p.path)
    if not m:
        raise Skip("not a post")
    data = get(f"https://{p.netloc}/api/v1/posts/{m.group(1)}").json()
    if not data.get("title"):
        raise Skip("no title")
    by = ", ".join(b.get("name", "") for b in data.get("publishedBylines") or [] if b.get("name"))
    return tidy({"kind": "post", "site": p.hostname.removeprefix("www."), "title": squash(data.get("title")),
                 "desc": squash(data.get("subtitle")), "by": by, "date": nice_date(data.get("post_date")),
                 "text": clip(data.get("truncated_body_text") or data.get("description")),
                 "img": [https_only(data.get("cover_image"))] if https_only(data.get("cover_image")) else None})


def github(url, p):
    parts = [x for x in p.path.split("/") if x]
    if len(parts) < 2:
        raise Skip("not a repository")
    owner, repo = parts[0], parts[1]
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    if len(parts) >= 4 and parts[2] in ("issues", "pull") and parts[3].isdigit():
        d = get(f"https://api.github.com/repos/{owner}/{repo}/issues/{parts[3]}", check_robots=False, headers=headers).json()
        return tidy({"kind": "repo", "site": "GitHub", "title": f"{squash(d.get('title'))} #{parts[3]}",
                     "desc": f"{owner}/{repo} · {d.get('state', '')}", "by": (d.get("user") or {}).get("login"),
                     "date": nice_date(d.get("created_at")), "text": clip(d.get("body"), 600)})
    d = get(f"https://api.github.com/repos/{owner}/{repo}", check_robots=False, headers=headers).json()
    bits = [d.get("language"), f"★ {d['stargazers_count']:,}" if d.get("stargazers_count") else "",
            "updated " + nice_date(d.get("pushed_at")) if d.get("pushed_at") else ""]
    return tidy({"kind": "repo", "site": "GitHub", "title": d.get("full_name") or f"{owner}/{repo}",
                 "desc": squash(d.get("description")), "text": " · ".join(b for b in bits if b)})


def page(url, p):
    """Any other page: its own <meta> tags, and whether it can be framed."""
    r = get(url, stream=True)
    try:
        ctype = r.headers.get("content-type", "").lower()
        frame = can_frame(r.headers)
        if ctype.startswith("image/"):
            return {"kind": "image", "img": [r.url if r.url.startswith("https://") else url]}
        if "html" not in ctype:
            raise Skip(f"not a page ({ctype.split(';')[0] or 'unknown type'})")
        raw = b""
        for chunk in r.iter_content(65536):
            raw += chunk
            if len(raw) >= MAX_PAGE:
                break
    finally:
        r.close()
    soup = BeautifulSoup(raw, "html.parser", from_encoding=r.encoding if "charset" in ctype else None)

    def meta(*names):
        for n in names:
            el = soup.find("meta", attrs={"property": n}) or soup.find("meta", attrs={"name": n})
            if el and squash(el.get("content")):
                return squash(html.unescape(el["content"]))
        return ""

    title = meta("og:title", "twitter:title") or squash(soup.title.get_text() if soup.title else "")
    host = p.hostname.removeprefix("www.")
    frame = frame and urllib.parse.urlsplit(r.url).scheme == "https"
    if not title and not frame:
        raise Skip("no title, and it can't be framed")
    img = meta("og:image", "og:image:secure_url", "twitter:image")
    img = https_only(urllib.parse.urljoin(r.url, img)) if img else ""
    if re.search(r"favicon|logo|\.(svg|ico)(\?|$)", img, re.I):
        img = ""                                          # a site's badge isn't a picture of the page
    desc = clip(meta("og:description", "description", "twitter:description"), 500)
    # frame: the box can show the page itself. The card is kept anyway, for when it turns out it can't.
    return tidy({"kind": "page", "frame": frame, "site": meta("og:site_name") or host, "title": clip(title, 200),
                 "desc": desc if desc.lower() != title.lower() else "",
                 "by": meta("author", "article:author") if not meta("author", "article:author").startswith("http") else "",
                 "date": nice_date(meta("article:published_time", "date")), "img": [img] if img else None})


def look_up(url):
    p = urllib.parse.urlsplit(url)
    host = (p.hostname or "").removeprefix("www.")
    if host.endswith("wikipedia.org"):
        return wikipedia(url, p)
    if host in ("x.com", "twitter.com", "mobile.twitter.com"):
        return tweet(url, p)
    if host == "bsky.app":
        return bluesky(url, p)
    if host == "github.com":
        return github(url, p)
    if host in ("youtube.com", "m.youtube.com", "youtu.be", "t.co"):
        raise Skip("handled on the page")           # videos open the embed player
    if re.fullmatch(r"/p/[^/]+/?", p.path):
        try:
            return substack(url, p)                 # a Substack, on substack.com or its own domain
        except (Skip, ValueError):
            pass                                    # not one after all (or it said no): read the page
    return page(url, p)


# ---------------------------------------------------------------- the posts and the files

def links_in(post):
    """The outside links in one post, as their href appears on the page."""
    text = post.read_text()
    body = text.split("---", 2)[2] if text.startswith("---") else text
    seen = []
    for a in BeautifulSoup(body, "html.parser").find_all("a", href=True):
        href = a["href"]
        p = urllib.parse.urlsplit(href)
        if p.scheme in ("http", "https") and p.hostname and p.hostname not in OURS and href not in seen:
            seen.append(href)
    return seen


def key_of(href):
    return urllib.parse.urldefrag(href)[0]


def due(entry, url):
    if entry is None:
        return True
    try:
        age = (TODAY - datetime.date.fromisoformat(entry["at"])).days
    except (KeyError, ValueError):
        return True
    if entry.get("rec") == {"kind": "page", "frame": True}:
        return True                             # stored before framed pages kept their title too
    spread = zlib.crc32(url.encode()) % 10      # so they don't all come due on the same morning
    return age >= (FRESH_DAYS + spread if entry.get("rec") else RETRY_DAYS + spread % 3)


def dump(obj):
    lines = [f"{json.dumps(k, ensure_ascii=False)}: {json.dumps(v, ensure_ascii=False, separators=(',', ':'))}"
             for k, v in sorted(obj.items())]
    return "{\n" + ",\n".join(lines) + "\n}\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=500)
    ap.add_argument("--offline", action="store_true")
    args = ap.parse_args()

    master = json.loads(MASTER.read_text()) if MASTER.exists() else {}
    posts = {p.parent.name: links_in(p) for p in sorted((ROOT / "subslop").glob("*/index.html"))}
    wanted = []
    for hrefs in posts.values():
        for h in hrefs:
            if key_of(h) not in wanted:
                wanted.append(key_of(h))
    todo = [] if args.offline else [u for u in wanted if due(master.get(u), u)][:args.limit]
    print(f"{len(posts)} posts, {len(wanted)} outside links, {len(todo)} to look up", flush=True)

    counts, skips = {}, {}
    for i, url in enumerate(todo, 1):
        try:
            rec = look_up(url)
            master[url] = {"at": TODAY.isoformat(), "rec": rec}
            what = rec["kind"] + (" (framed)" if rec.get("frame") else "")
            counts[what] = counts.get(what, 0) + 1
            print(f"[{i}/{len(todo)}] {what}: {url}", flush=True)
        except Skip as why:
            master[url] = {"at": TODAY.isoformat(), "skip": str(why)}
            skips[str(why)] = skips.get(str(why), 0) + 1
            print(f"[{i}/{len(todo)}] skipped, {why}: {url}", flush=True)
        except Exception as e:      # one odd page mustn't stop the rest
            master[url] = {"at": TODAY.isoformat(), "skip": f"error ({type(e).__name__})"}
            skips["error"] = skips.get("error", 0) + 1
            print(f"[{i}/{len(todo)}] error {type(e).__name__}: {e}: {url}", flush=True)

    MASTER.parent.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    MASTER.write_text(dump(master))
    for slug, hrefs in posts.items():
        recs = {h: master[key_of(h)]["rec"] for h in hrefs if master.get(key_of(h), {}).get("rec")}
        (OUT / f"{slug}.json").write_text(dump(recs))
    for old in OUT.glob("*.json"):
        if old.stem not in posts:
            old.unlink()
    if todo:
        known = [master[u] for u in wanted if u in master]
        kinds = {}
        for e in known:
            k = (e["rec"]["kind"] + (" (framed)" if e["rec"].get("frame") else "")) if e.get("rec") else "no preview"
            kinds[k] = kinds.get(k, 0) + 1
        REPORT.write_text(json.dumps({"date": TODAY.isoformat(), "looked_up": len(todo), "this_run": counts,
                                      "skipped_this_run": skips, "all_links": kinds,
                                      "sites_that_refused": sorted(h for h, n in refused.items() if n)}, indent=1) + "\n")
    print("done:", counts, skips, flush=True)


if __name__ == "__main__":
    sys.exit(main())
