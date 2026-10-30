"""
Copy every Croiss Lite post from Substack onto croissanthology.com.

Run by .github/workflows/sync-substack.yml every day (and by hand: python scripts/substack/sync.py).
It rewrites every post each run, so changes to translate.py or the layout reach old posts too,
but it only touches files whose content actually changed.

Writes:
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
        batch = get_json(f"/api/v1/archive?sort=new&search=&offset={offset}&limit=12")
        if not batch:
            break
        posts.extend(batch)
        offset += len(batch)
        if len(batch) < 12 or offset > 2000:
            break
    keep = [p for p in posts if p.get("type", "newsletter") == "newsletter" and p.get("slug")]
    seen, out = set(), []
    for p in keep:
        if p["slug"] not in seen:
            seen.add(p["slug"])
            out.append(p)
    return out


def front_matter(fields):
    lines = ["---"]
    for k, v in fields.items():
        if v is None or v == "":
            continue
        if isinstance(v, list):
            lines.append(f"{k}:")
            lines.extend(f"  - {json.dumps(x, ensure_ascii=False)}" for x in v)
        elif isinstance(v, (int, float)):
            lines.append(f"{k}: {v}")
        else:
            lines.append(f"{k}: {json.dumps(str(v), ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines)


def main():
    try:
        posts = list_posts()
    except Exception as e:  # noqa: BLE001
        log("error", f"Substack's archive could not be read ({e}). Nothing was changed.")
        sys.exit(1)
    if not posts:
        log("error", "Substack returned no posts. Nothing was changed.")
        sys.exit(1)
    log("notice", f"{len(posts)} posts on Substack")

    # pass 1: covers (embeds of one post inside another use them as thumbnails)
    covers = {}
    for p in posts:
        covers[p["slug"]] = save_image(p.get("cover_image"), IMAGES / p["slug"], name="cover", max_w=1400, as_jpeg=True)
    slugs = {p["slug"] for p in posts}

    def local_href(slug):
        return f"/subslop/{slug}/" if slug in slugs else None

    def thumb_for(slug):
        return covers.get(slug)

    index, changed, failed = [], 0, 0
    for p in posts:
        slug = p["slug"]
        try:
            full = get_json(f"/api/v1/posts/{urllib.parse.quote(slug)}")
        except Exception as e:  # noqa: BLE001
            log("warning", f"{slug}: could not fetch the post ({e}); kept the existing page")
            failed += 1
            if (PAGES / slug / "index.html").exists():
                index.append(None)  # placeholder keeps order; filled below from the archive entry
                index[-1] = {"slug": slug, "title": p.get("title", "").strip(), "subtitle": (p.get("subtitle") or "").strip(),
                             "date": (p.get("post_date") or "")[:10], "url": f"/subslop/{slug}/", "cover": covers.get(slug)}
            continue
        body = full.get("body_html") or ""
        if not body.strip():
            log("warning", f"{slug}: no body (paid-only or empty?); skipped")
            continue
        title = (full.get("title") or "").strip()
        subtitle = (full.get("subtitle") or "").strip()
        date = (full.get("post_date") or "")[:10]
        cover = covers.get(slug)
        cw, ch = image_size(cover)

        html = translate(body,
                         download_image=lambda u, s=slug: save_image(u, IMAGES / s),
                         local_href=local_href, thumb_for=thumb_for)
        html = html.replace("{%", "{&#37;").replace("{{", "{&#123;")  # nothing in a post is Liquid

        redirects = []
        old = old_slug(title)
        if old and old != slug:
            redirects.append(f"/subslop/{old}/")
            if (PAGES / old).is_dir():
                shutil.rmtree(PAGES / old)
                changed += 1

        page = front_matter({
            "layout": "facing-post",
            "title": title,
            "dek": subtitle,
            "description": subtitle or (full.get("description") or ""),
            "date": date,
            "substack_url": full.get("canonical_url") or f"{BASE}/p/{slug}",
            "cover": cover,
            "cover_width": cw,
            "cover_height": ch,
            "permalink": f"/subslop/{slug}/",
            "redirect_from": redirects,
        }) + "\n" + html + "\n"
        if write_if_changed(PAGES / slug / "index.html", page):
            changed += 1
            log("notice", f"updated {slug}")
        index.append({"slug": slug, "title": title, "subtitle": subtitle, "date": date,
                      "url": f"/subslop/{slug}/", "cover": cover})

    index = [x for x in index if x]
    index.sort(key=lambda x: x["date"], reverse=True)
    if write_if_changed(DATA, json.dumps(index, ensure_ascii=False, indent=1) + "\n"):
        changed += 1
    log("notice", f"{len(index)} posts on the site, {changed} files changed, {failed} could not be fetched")


if __name__ == "__main__":
    main()
