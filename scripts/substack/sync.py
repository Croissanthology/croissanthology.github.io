"""
Copy every Croiss Lite post from Substack onto croissanthology.com.

Runs once a day from your Mac (scripts/substack/install-mac.sh sets that up), or by hand:
    python3 scripts/substack/sync.py            # new and recently edited posts
    python3 scripts/substack/sync.py --refresh  # re-download every post

Substack refuses requests from GitHub's servers, so this can't run in GitHub Actions.

How few requests it makes: it reads the archive list (one or two requests), and only downloads a
post that is new, changed in the list, or published in the last 14 days. Everything it downloads is
kept in _substack/<slug>.json (a raw copy of each post, which Jekyll doesn't publish), and every page
is rebuilt from those copies on every run, so changes to translate.py or the layout reach old posts
without asking Substack again. Files are only written when their content changes.

Writes:
  _substack/<slug>.json                raw copy of each post from Substack's API
  subslop/<substack-slug>/index.html   one page per post (layout: facing-post)
  images/subslop/<slug>/...            the cover and every image, copied home
  _data/subslop.json                   the list the homepage contents and /all read
Old addresses (/subslop/<slug-from-the-title>/) redirect to the new ones.
"""
import hashlib
import io
import json
import os
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from translate import translate  # noqa: E402

BASE = "https://croissanthology.substack.com"
ROOT = Path(__file__).resolve().parents[2]
PAGES = ROOT / "subslop"
IMAGES = ROOT / "images" / "subslop"
DATA = ROOT / "_data" / "subslop.json"
RAW = ROOT / "_substack"
RECENT_DAYS = 14
LIST_FIELDS = ("title", "subtitle", "cover_image", "post_date", "wordcount")
UA = "croissanthology.com archive sync (+https://croissanthology.com)"

try:
    from PIL import Image
except ImportError:  # still works without Pillow, just keeps images as they are
    Image = None


def log(kind, msg):
    """kind: notice | warning | error (shows up as an annotation on the Actions run)"""
    print(f"::{kind}::{msg}" if os.environ.get("GITHUB_ACTIONS") else f"{kind}: {msg}", flush=True)


def fetch(url, tries=4, binary=False):
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                data = r.read()
                return data if binary else data.decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(4 * (attempt + 1))
                continue
            raise
        except urllib.error.URLError:
            if attempt < tries - 1:
                time.sleep(4 * (attempt + 1))
                continue
            raise
    raise RuntimeError("unreachable")


def get_json(path):
    time.sleep(0.4)  # be polite to Substack
    return json.loads(fetch(BASE + path))


def old_slug(title):
    """The address the previous sync used, built from the title."""
    s = title.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return s.strip("-")


def original_url(url):
    """substackcdn 'fetch' URLs wrap the original upload; ask for the original."""
    m = re.search(r"/(https?%3A%2F%2F.+)$", url or "")
    return urllib.parse.unquote(m.group(1)) if m else url


def write_if_changed(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = content.encode("utf-8") if isinstance(content, str) else content
    if path.exists() and path.read_bytes() == data:
        return False
    path.write_bytes(data)
    return True


def save_image(remote, dest_dir, name=None, max_w=1600, as_jpeg=False):
    """Download once; returns the site path (/images/...) or None."""
    if not remote or remote.startswith("data:"):
        return None
    url = original_url(remote)
    ext = (re.search(r"\.(png|jpe?g|webp|gif)(?:$|\?)", url.lower()) or [None, "jpg"])[1].replace("jpeg", "jpg")
    stem = name or hashlib.sha1(url.encode()).hexdigest()[:12]
    for existing in dest_dir.glob(stem + ".*"):
        return "/" + existing.relative_to(ROOT).as_posix()
    try:
        raw = fetch(url, binary=True)
    except Exception as e:  # noqa: BLE001
        log("warning", f"could not download {url[:120]}: {e}")
        return None
    out_ext, out = ext, raw
    if Image is not None and ext in ("png", "jpg", "webp"):
        try:
            im = Image.open(io.BytesIO(raw))
            im.load()
            alpha = im.mode in ("RGBA", "LA", "P") and ("transparency" in im.info or im.mode != "P")
            if im.width > max_w:
                im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
            buf = io.BytesIO()
            if as_jpeg or (not alpha and ext != "png") or (ext == "png" and not alpha and len(raw) > 400_000):
                im.convert("RGB").save(buf, "JPEG", quality=84, optimize=True, progressive=True)
                out_ext = "jpg"
            elif ext == "webp":
                im.save(buf, "WEBP", quality=86)
            else:
                im.save(buf, "PNG", optimize=True)
                out_ext = "png"
            out = buf.getvalue()
        except Exception as e:  # noqa: BLE001
            log("warning", f"kept {url[:80]} unprocessed ({e})")
    dest = dest_dir / f"{stem}.{out_ext}"
    write_if_changed(dest, out)
    return "/" + dest.relative_to(ROOT).as_posix()


def image_size(site_path):
    if not site_path or Image is None:
        return None, None
    try:
        with Image.open(ROOT / site_path.lstrip("/")) as im:
            return im.width, im.height
    except Exception:  # noqa: BLE001
        return None, None


def list_posts():
    posts, offset = [], 0
    while True:
        batch = get_json(f"/api/v1/archive?sort=new&search=&offset={offset}&limit=50")
        if not batch:
            break
        posts.extend(batch)
        offset += len(batch)
        if offset > 2000:
            break
    keep = [p for p in posts if p.get("type", "newsletter") == "newsletter" and p.get("slug")]
    seen, out = set(), []
    for p in keep:
        if p["slug"] not in seen:
            seen.add(p["slug"])
            out.append(p)
    return out


def image_key(url):
    """The upload behind a Substack image URL (one picture reaches posts through several CDN URLs)."""
    u = original_url(url or "")
    m = re.search(r"/images/([0-9a-f]{8}-[0-9a-f-]{27})", u)
    return m.group(1) if m else u


def fingerprint(site_path):
    """A 16x16 light/dark pattern of a saved image, to spot the same picture uploaded twice."""
    if Image is None or not site_path:
        return None
    try:
        with Image.open(ROOT / site_path.lstrip("/")) as im:
            px = im.convert("L").resize((16, 16)).tobytes()
    except Exception:  # noqa: BLE001
        return None
    mean = sum(px) / len(px)
    return [p > mean for p in px]


def cover_in_body(cover_url, cover_path, body_images):
    """True when the post shows its cover image itself, so the page shouldn't show it twice.
    body_images: (remote url, local path) for every image in the post."""
    if not cover_path:
        return False
    if any(image_key(u) == image_key(cover_url) for u, _ in body_images):
        return True
    fp = fingerprint(cover_path)
    return fp is not None and any(
        (other := fingerprint(p)) is not None and sum(a != b for a, b in zip(fp, other)) <= 12
        for _, p in body_images)


def front_matter(fields):
    lines = ["---"]
    for k, v in fields.items():
        if v is None or v == "":
            continue
        if isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        elif isinstance(v, list):
            lines.append(f"{k}:")
            lines.extend(f"  - {json.dumps(x, ensure_ascii=False)}" for x in v)
        elif isinstance(v, (int, float)):
            lines.append(f"{k}: {v}")
        else:
            lines.append(f"{k}: {json.dumps(str(v), ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines)


def needs_download(entry, cached, refresh):
    if refresh or cached is None:
        return True
    if any((entry.get(k) or "") != (cached.get(k) or "") for k in LIST_FIELDS):
        return True
    try:
        published = time.mktime(time.strptime((entry.get("post_date") or "")[:10], "%Y-%m-%d"))
        return time.time() - published < RECENT_DAYS * 86400
    except ValueError:
        return False


def main():
    refresh = "--refresh" in sys.argv
    try:
        posts = list_posts()
    except Exception as e:  # noqa: BLE001
        log("error", f"Substack's archive could not be read ({e}). Nothing was changed.")
        sys.exit(1)
    if not posts:
        log("error", "Substack returned no posts. Nothing was changed.")
        sys.exit(1)

    # 1. download only what is new or changed; keep a raw copy of each post
    downloaded, failed = 0, 0
    raws = {}
    for entry in posts:
        slug = entry["slug"]
        cache = RAW / f"{slug}.json"
        cached = json.loads(cache.read_text()) if cache.exists() else None
        if needs_download(entry, cached, refresh):
            try:
                full = get_json(f"/api/v1/posts/{urllib.parse.quote(slug)}")
                keep = {k: full.get(k) for k in ("slug", "title", "subtitle", "description", "post_date",
                                                 "cover_image", "canonical_url", "wordcount", "audience", "body_html")}
                keep.update({k: entry.get(k) for k in LIST_FIELDS})  # compare like with like next time
                write_if_changed(cache, json.dumps(keep, ensure_ascii=False, indent=1) + "\n")
                cached = keep
                downloaded += 1
            except Exception as e:  # noqa: BLE001
                log("warning", f"{slug}: could not fetch the post ({e}); kept the previous copy")
                failed += 1
        if cached:
            raws[slug] = cached
    log("notice", f"{len(posts)} posts on Substack, {downloaded} downloaded, {failed} failed")

    # 2. covers (embeds of one post inside another use them as thumbnails)
    covers = {s: save_image(r.get("cover_image"), IMAGES / s, name="cover", max_w=1400, as_jpeg=True)
              for s, r in raws.items()}

    def local_href(slug):
        return f"/subslop/{slug}/" if slug in raws else None

    def thumb_for(slug):
        return covers.get(slug)

    # 3. rebuild every page from the raw copies
    index, changed = [], 0
    for slug, raw in raws.items():
        body = raw.get("body_html") or ""
        if not body.strip():
            log("warning", f"{slug}: no body (paid-only or empty?); skipped")
            continue
        title = (raw.get("title") or "").strip()
        subtitle = (raw.get("subtitle") or "").strip()
        date = (raw.get("post_date") or "")[:10]
        cover = covers.get(slug)
        cw, ch = image_size(cover)

        body_images = []

        def grab(u, s=slug, seen=body_images):
            local = save_image(u, IMAGES / s)
            seen.append((u, local))
            return local

        html = translate(body, download_image=grab, local_href=local_href, thumb_for=thumb_for)
        html = html.replace("{%", "{&#37;").replace("{{", "{&#123;")  # nothing in a post is Liquid

        redirects = []
        old = old_slug(title)
        if old and old != slug:
            redirects.append(f"/subslop/{old}/")
            if (PAGES / old).is_dir() and old not in raws:
                shutil.rmtree(PAGES / old)
                changed += 1

        page = front_matter({
            "layout": "facing-post",
            "title": title,
            "dek": subtitle,
            "description": subtitle or (raw.get("description") or ""),
            "date": date,
            "substack_url": raw.get("canonical_url") or f"{BASE}/p/{slug}",
            "cover": cover,
            "cover_width": cw,
            "cover_height": ch,
            "cover_in_body": cover_in_body(raw.get("cover_image"), cover, body_images) or None,
            "permalink": f"/subslop/{slug}/",
            "redirect_from": redirects,
        }) + "\n" + html + "\n"
        if write_if_changed(PAGES / slug / "index.html", page):
            changed += 1
            log("notice", f"updated {slug}")
        index.append({"slug": slug, "title": title, "subtitle": subtitle, "date": date,
                      "url": f"/subslop/{slug}/", "cover": cover})

    index.sort(key=lambda x: x["date"], reverse=True)
    if write_if_changed(DATA, json.dumps(index, ensure_ascii=False, indent=1) + "\n"):
        changed += 1
    log("notice", f"{len(index)} posts on the site, {changed} files changed")


if __name__ == "__main__":
    main()
