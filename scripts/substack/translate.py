"""
Turn one Substack post's body_html into croissanthology.com "Facing Pages" markup.

What comes out:
  * footnotes become <aside class="note"> right after the paragraph that cites them;
    the layout shows them inline when folded / on phones, and in the right margin when wide
  * images become <figure class="plate"> with a local copy (download_image is passed in)
  * embedded posts of yours become small cards (thumbnail, title, date) linking to the
    copy on this site; other people's posts become plain cards linking out
  * Bluesky and Twitter/X embeds become static quote cards (no third-party iframes)
  * @mentions keep their names (Substack stores them in data-attrs)
  * subscribe widgets, share buttons and Substack's image chrome are dropped
  * the first paragraph is marked .opening for the drop cap
"""
import html
import json
import re

from bs4 import BeautifulSoup, NavigableString, Tag

MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
OWN_HOSTS = ("croissanthology.substack.com",)


def nice_date(iso):
    """'2026-01-13...' -> '13 Jan 2026'"""
    if not iso or len(iso) < 10:
        return ""
    y, m, d = iso[:10].split("-")
    return f"{int(d)} {MONTHS[int(m) - 1]} {y}"


def _attrs(el):
    raw = el.get("data-attrs")
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except ValueError:
        return {}


def own_slug(url):
    """Slug of one of your own Substack posts, or None."""
    m = re.match(r"https?://(?:www\.)?([^/]+)/p/([^/?#]+)", url or "")
    if m and m.group(1) in OWN_HOSTS:
        return m.group(2)
    return None


def _top_block(tag, root):
    node = tag
    while node.parent is not None and node.parent is not root:
        node = node.parent
    return node


def _card(soup, href, title, date_text, thumb=None, kicker=None):
    a = soup.new_tag("a", attrs={"class": "own-card", "href": href})
    if thumb:
        a.append(soup.new_tag("img", attrs={"class": "own-thumb", "src": thumb, "alt": "",
                                            "width": "240", "height": "240"}))
    text = soup.new_tag("span", attrs={"class": "own-text"})
    t = soup.new_tag("span", attrs={"class": "own-title"})
    t.string = title or href
    text.append(t)
    if kicker or date_text:
        d = soup.new_tag("span", attrs={"class": "own-date"})
        d.string = " · ".join(x for x in (kicker, date_text) if x)
        text.append(d)
    r = soup.new_tag("span", attrs={"class": "own-read"})
    r.string = "Read →"
    text.append(r)
    a.append(text)
    return a


def _quote_card(soup, name, handle, text, href, where, date, images=()):
    fig = soup.new_tag("figure", attrs={"class": "plate embed"})
    bq = soup.new_tag("blockquote", attrs={"class": "bsky"})
    who = soup.new_tag("p", attrs={"class": "who"})
    n = soup.new_tag("span", attrs={"class": "name"})
    n.string = name or ""
    h = soup.new_tag("span", attrs={"class": "handle"})
    h.string = ("@" + handle) if handle else ""
    who.append(n)
    who.append(" ")
    who.append(h)
    said = soup.new_tag("p", attrs={"class": "said"})
    said.string = text or ""
    src = soup.new_tag("a", attrs={"class": "src", "href": href})
    src.string = f"{where} · {nice_date(date)} ↗" if date else f"{where} ↗"
    bq.append(who)
    bq.append(said)
    if images:
        shots = soup.new_tag("span", attrs={"class": "shots"})
        for src_url in images:
            shots.append(soup.new_tag("img", attrs={"src": src_url, "alt": ""}))
        bq.append(shots)
    bq.append(src)
    fig.append(bq)
    return fig


def _mark_opening(soup, root):
    """Mark the first paragraph for the drop cap (CSS ::first-letter + initial-letter, wide screens only).
    If the post opens inside a link, the first letter moves just before it, so the drop cap isn't underlined."""
    first_p = None
    for el in root.children:
        if isinstance(el, Tag) and el.name == "p" and el.get_text(strip=True):
            first_p = el
            break
    if first_p is None:
        return
    first_p["class"] = (first_p.get("class") or []) + ["opening"]
    for node in first_p.descendants:
        if isinstance(node, NavigableString) and node.strip():
            link = node.find_parent("a")
            if link is None or not first_p in link.parents:
                return
            text = str(node)
            m = re.match(r"(\s*)([\u201c\u2018\"'(\[]?[A-Za-z0-9\u00c0-\u024f])", text)
            if not m:
                return
            node.replace_with(NavigableString(text[:m.start(2)] + text[m.end(2):]))
            link.insert_before(NavigableString(m.group(2)))
            return


def translate(body_html, *, download_image=None, local_href=None, thumb_for=None):
    """
    body_html      Substack's body_html for the post
    download_image f(remote_url) -> local path or None (keeps the remote URL on failure)
    local_href     f(slug) -> URL on this site for one of your posts, or None
    thumb_for      f(slug) -> local thumbnail path for one of your posts, or None
    """
    download_image = download_image or (lambda u: None)
    local_href = local_href or (lambda s: None)
    thumb_for = thumb_for or (lambda s: None)

    soup = BeautifulSoup(f"<div id='root'>{body_html}</div>", "html.parser")
    root = soup.find(id="root")

    # 1. chrome we never want
    for sel in (".subscription-widget-wrap-editor", ".subscription-widget-wrap", ".subscription-widget",
                ".button-wrapper", ".image-link-expand", "source", ".share-dialog", ".captioned-button-wrap",
                ".paywall-jump", ".community-chat"):
        for el in root.select(sel):
            el.decompose()

    # 2. @mentions
    for span in root.select("span.mention-wrap"):
        at = _attrs(span)
        name = at.get("name")
        if name:
            a = soup.new_tag("a", attrs={"class": "mention", "href": at.get("url") or "#"})
            a.string = name
            span.replace_with(a)
        else:
            span.decompose()

    # 3. embeds of posts (yours become local cards with your cover as thumbnail)
    for emb in root.select(".embedded-post-wrap, .digest-post-embed"):
        at = _attrs(emb)
        # embedded-post-wrap names the post in "url"/"date"; the newer digest-post-embed in
        # "canonical_url"/"post_date" (and carries the cover)
        url = (at.get("url") or at.get("canonical_url") or "").split("?")[0]
        link = emb.find("a", href=True)
        if not url and link:
            url = link["href"].split("?")[0]
        title = (at.get("title") or (emb.get_text(" ", strip=True)[:120] if emb else "")).strip()
        date = nice_date(at.get("date") or at.get("post_date") or "")
        slug = own_slug(url)
        if slug:
            thumb = thumb_for(slug) or (download_image(at["cover_image"]) if at.get("cover_image") else None)
            card = _card(soup, local_href(slug) or url, title, date, thumb)
        else:
            pic = at.get("cover_image") or at.get("publication_logo_url")
            card = _card(soup, url, title, date, download_image(pic) if pic else None,
                         kicker=at.get("publication_name") or None)
        holder = soup.new_tag("figure", attrs={"class": "plate embed own"})
        holder.append(card)
        emb.replace_with(holder)

    # 4. Bluesky and Twitter/X embeds -> static quote cards
    for wrap in root.select(".bluesky-wrap"):
        at = _attrs(wrap)
        handle = at.get("authorHandle", "")
        imgs = at.get("imageUrls") or []
        if isinstance(imgs, str):
            imgs = [imgs]
        local_imgs = [download_image(u) or u for u in imgs if isinstance(u, str) and u]
        wrap.replace_with(_quote_card(soup, at.get("authorName", ""), handle, at.get("text", ""),
                                      f"https://bsky.app/profile/{handle}/post/{at.get('postId', '')}",
                                      "Bluesky", at.get("createdAt", ""), local_imgs))
    for wrap in root.select(".tweet, .twitter-embed, .tweet-wrap"):
        at = _attrs(wrap)
        if not at:
            continue
        wrap.replace_with(_quote_card(soup, at.get("name", ""), at.get("username", ""),
                                      at.get("full_text") or at.get("text", ""),
                                      (at.get("url") or "").split("?")[0], "X", at.get("date", "")))
    for yt in root.select(".youtube-wrap"):
        at = _attrs(yt)
        vid = at.get("videoId") or (yt.get("id", "").replace("youtube2-", ""))
        p = soup.new_tag("p", attrs={"class": "embed-link"})
        a = soup.new_tag("a", attrs={"href": f"https://www.youtube.com/watch?v={vid}"})
        a.string = "Video on YouTube ↗"
        p.append(a)
        yt.replace_with(p)
    for fr in root.find_all("iframe"):
        src = (fr.get("src") or "").split("?")[0]
        a = soup.new_tag("a", attrs={"href": src or "#"})
        a.string = "Embedded content ↗"
        wrapper = fr.find_parent("div")
        if wrapper is not None and wrapper.parent is root and not wrapper.find("p"):
            p = soup.new_tag("p", attrs={"class": "embed-link"})
            p.append(a)
            wrapper.replace_with(p)
        else:
            fr.replace_with(a)

    # 5. images -> <figure class="plate"> with a local copy
    for box in root.select("div.captioned-image-container, div.image-gallery-embed"):
        imgs = box.find_all("img")
        if not imgs:
            box.decompose()
            continue
        fig = box.find("figure")
        cap = fig.find("figcaption") if fig else box.find("figcaption")
        new_fig = soup.new_tag("figure", attrs={"class": "plate"})
        for img in imgs:
            remote = img.get("src", "")
            local = download_image(remote)
            w, h = img.get("width"), img.get("height")
            m = re.search(r"_(\d+)x(\d+)\.(?:png|jpe?g|webp|gif|heic)", remote)
            if m:
                w, h = m.group(1), m.group(2)
            new_img = soup.new_tag("img", attrs={"src": local or remote, "alt": img.get("alt", "") or "",
                                                 "decoding": "async"})
            if w and h:
                try:
                    new_img["width"], new_img["height"] = str(int(float(w))), str(int(float(h)))
                except ValueError:
                    pass
            new_fig.append(new_img)
        if cap and cap.get_text(strip=True):
            new_cap = soup.new_tag("figcaption")
            for child in list(cap.contents):
                new_cap.append(child)
            new_fig.append(new_cap)
        box.replace_with(new_fig)
    # stray images not in a captioned container
    for img in root.find_all("img"):
        if img.find_parent("figure") is not None:
            continue
        local = download_image(img.get("src", ""))
        if local:
            img["src"] = local
        for a in ("srcset", "sizes", "data-attrs"):
            if a in img.attrs:
                del img[a]

    # 6. footnotes -> sidenotes after the citing paragraph
    notes = {}
    for fn in root.select("div.footnote"):
        num = fn.select_one("a.footnote-number")
        content = fn.select_one("div.footnote-content")
        if not num or not content:
            continue
        for p in content.find_all("p"):
            if not p.get_text(strip=True) and not p.find(["img", "a", "figure"]):
                p.decompose()
        notes[num.get_text(strip=True)] = content.extract()
        fn.decompose()

    for ref in root.select("a.footnote-anchor"):
        n = ref.get_text(strip=True)
        if n not in notes:
            ref.decompose()
            continue
        sup = soup.new_tag("sup", attrs={"class": "fn-ref"})
        a = soup.new_tag("a", attrs={"href": f"#fn-{n}", "id": f"fnref-{n}", "role": "doc-noteref",
                                     "aria-describedby": f"fn-{n}"})
        a.string = n
        sup.append(a)
        block = _top_block(ref, root)
        ref.replace_with(sup)

        aside = soup.new_tag("aside", attrs={"class": "note", "id": f"fn-{n}", "role": "doc-footnote",
                                             "data-n": n, "data-for": f"fnref-{n}"})
        clip = soup.new_tag("div", attrs={"class": "note-inner"})
        body = soup.new_tag("div", attrs={"class": "note-body"})
        for child in list(notes[n].contents):
            if isinstance(child, Tag) and child.name == "figure" and "own" in (child.get("class") or []):
                p = soup.new_tag("p", attrs={"class": "own-ref"})
                card = child.find("a")
                if card:
                    p.append(card)
                body.append(p)
                child.decompose()
            else:
                body.append(child)
        num = soup.new_tag("span", attrs={"class": "note-n"})
        num.string = n
        first = body.find("p")
        (first if first is not None else body).insert(0, num)
        clip.append(body)
        aside.append(clip)
        anchor = block
        while anchor.next_sibling is not None and getattr(anchor.next_sibling, "name", None) == "aside":
            anchor = anchor.next_sibling
        anchor.insert_after(aside)

    # 7. links: footnote links into Substack's feed, links to your other posts
    for a in root.find_all("a", href=True):
        href = a["href"]
        if "substack.com/feed#" in href or re.match(r"https?://[^/]+/p/[^#]*#footnote", href):
            a["href"] = "#" + href.split("#", 1)[1]
            continue
        slug = own_slug(href)
        if slug and local_href(slug):
            a["href"] = local_href(slug)
            a["class"] = (a.get("class") or []) + ["internal"]
        if a.get("target") == "_self":
            del a["target"]

    # 8. a blank line typed inside a paragraph on Substack (<br><br>) starts a new paragraph here
    for p in list(root.find_all("p", recursive=False)):
        if len(p.find_all("br", recursive=False)) < 2:
            continue
        parts, current, pending_br = [], [], None
        for child in list(p.contents):
            if isinstance(child, Tag) and child.name == "br":
                if pending_br is not None:
                    parts.append(current)
                    current, pending_br = [], None
                else:
                    pending_br = child
                continue
            if isinstance(child, NavigableString) and not child.strip() and pending_br is not None:
                continue
            if pending_br is not None:
                current.append(pending_br)
                pending_br = None
            current.append(child)
        parts.append(current)
        if len(parts) < 2:
            continue
        for chunk in parts:
            if not any((c.get_text(strip=True) if isinstance(c, Tag) else str(c).strip()) for c in chunk):
                continue
            np_ = soup.new_tag("p")
            for c in chunk:
                np_.append(c.extract() if c.parent is not None else c)
            p.insert_before(np_)
        p.decompose()

    # 9. tidy: empty paragraphs, Substack data attributes
    for p in root.find_all("p"):
        if not p.get_text(strip=True) and not p.find(["img", "a", "figure"]):
            p.decompose()
    for el in root.find_all(True):
        for k in list(el.attrs):
            if k.startswith("data-") and k not in ("data-n", "data-for"):
                del el[k]
            elif k in ("contenteditable", "style"):
                del el[k]

    _mark_opening(soup, root)
    return "".join(str(c) for c in root.contents if not (isinstance(c, NavigableString) and not c.strip()))
