/* wide.js — the Facing Pages engine.
 *
 * One markup, two layouts:
 *   narrow (phone, folded Duo): notes sit in the text, right after the paragraph that cites them
 *   wide   (unfolded Duo, laptop): notes (and, if asked, figures) move to a rail
 *          beside the text, each level with the line that cites it
 *
 * When the window crosses the breakpoint (folding or unfolding), the page simply switches
 * layout, with no animation.
 *
 * Markup contract:
 *   <html data-layout="narrow|wide">          set by the inline head script, then here
 *   [data-wide-root]                           positioning box for placed items
 *   [data-wide-root] .rail                     empty element whose box is the margin
 *   .fn-ref > a[href="#fn-N"]                  the superscript in the text
 *   aside.note#fn-N > .note-inner              the note, right after its paragraph
 *   figure.plate                               placed in the rail too when the root has data-plates="rail"
 *
 * Summon (wide only): each figure in the rail gets a "fig. N →" marker in the paragraph it sits
 * beside. Hovering that marker or a footnote number slides its figure or note level with it, over
 * the others, which stay where they are and dim. Moving away puts it back. On touch screens a tap
 * does the same, and a tap anywhere else puts it back.
 *
 * Peek (wide only, pointers that can hover): resting on a link opens a box in the rail, level with
 * the link, over the notes and figures, which dim just as they do for a summon. What's in the box
 * depends on the link:
 *   another page of this site, or a site that allows it    the real page, in an iframe that scrolls
 *   Wikipedia                                               the article's lead, set in this site's type
 *   a tweet, a Bluesky post, a Substack post, GitHub        a small card: who, when, what it says
 *   an image                                                the image
 *   a page that refuses to be framed                        its title, description and picture
 * The cards come from previews/<post>.json, which scripts/previews/index.py builds ahead of time
 * (it also notes which pages can be framed). That file is fetched the first time it's needed.
 * Nothing loads until the pointer has rested on a link.
 */
(function () {
  "use strict";
  var doc = document.documentElement;
  var BREAK = parseFloat(getComputedStyle(doc).getPropertyValue("--wide-at")) || 720;
  var GAP = 14;
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  var layout = doc.getAttribute("data-layout");

  function wanted() {
    return window.innerWidth >= BREAK ? "wide" : "narrow";
  }

  /* --- the crease: Viewport Segments API where the browser exposes it --- */
  function readHinge() {
    var segs = window.viewport && window.viewport.segments;
    if (segs && segs.length === 2 && segs[0].right < segs[1].left + 1) {
      doc.style.setProperty("--hinge-x", segs[0].right + "px");
      doc.style.setProperty("--hinge-w", Math.max(0, segs[1].left - segs[0].right) + "px");
      doc.setAttribute("data-hinge", "real");
    } else {
      doc.style.removeProperty("--hinge-x");
      doc.style.removeProperty("--hinge-w");
      doc.removeAttribute("data-hinge");
    }
  }

  /* --- margin placement --- */
  function placed(root) {
    var sel = ".note";
    if (root.dataset.plates === "rail") sel += ", figure.plate";
    // figures inside a footnote travel with their note, not on their own
    return Array.prototype.slice.call(root.querySelectorAll(sel)).filter(function (el) {
      return !el.parentElement.closest(".note");
    });
  }

  function anchorFor(el) {
    if (el.dataset.anchor) return document.querySelector(el.dataset.anchor);
    if (el._marker && layout === "wide") return el._marker;
    if (el.classList.contains("note")) {
      return document.getElementById(el.dataset.for) || el.previousElementSibling;
    }
    var next = el.nextElementSibling;
    while (next && (next.classList.contains("note") || next.classList.contains("plate"))) next = next.nextElementSibling;
    return next || el.previousElementSibling;
  }

  function place() {
    if (summoned) release(false);
    if (layout !== "wide") closePeek(); else if (peek) placePeek(parseFloat(peekEl.style.top));
    document.querySelectorAll("[data-wide-root]").forEach(function (root) {
      var items = placed(root);
      if (layout !== "wide") {
        items.forEach(function (el) { el.style.top = el.style.left = el.style.width = ""; });
        root.style.minHeight = "";
        return;
      }
      var rail = root.querySelector(".rail");
      if (!rail) return;
      var box = root.getBoundingClientRect();
      var r = rail.getBoundingClientRect();
      var left = r.left - box.left, width = r.width;
      var floor = -Infinity;
      items.forEach(function (el) {
        el.style.left = left + "px";
        el.style.width = width + "px";
        var a = anchorFor(el);
        var want = a ? a.getBoundingClientRect().top - box.top : floor;
        if (el.classList.contains("note")) want -= parseFloat(getComputedStyle(el).getPropertyValue("--lift")) || 0;
        var top = Math.max(want, floor + GAP);
        el.style.top = top + "px";
        floor = top + el.offsetHeight;
        el.classList.toggle("bumped", top > want + 2);
      });
      root.style.minHeight = items.length ? Math.ceil(floor + GAP) + "px" : "";
    });
  }

  /* --- summon --- */
  var summoned = null, pinned = false, leaveTimer = 0;

  function markFigures() {
    var n = 0;
    document.querySelectorAll("[data-wide-root]").forEach(function (root) {
      if (root.dataset.plates !== "rail") return;
      placed(root).forEach(function (el, i) {
        if (el.classList.contains("note") || el.classList.contains("cover") || el.dataset.anchor || el.dataset.marked) return;
        // the marker goes at the end of the paragraph the figure followed in the text
        // (or, if there's none, at the start of the next one)
        var prev = el.previousElementSibling;
        while (prev && (prev.classList.contains("note") || prev.classList.contains("plate"))) prev = prev.previousElementSibling;
        var host = null, atEnd = true;
        if (prev && !prev.closest(".note, figure") && !/^H[1-6]$/.test(prev.tagName)) {
          host = prev.matches("ul, ol") ? prev.querySelector(":scope > li:last-child")
               : prev.matches("blockquote, div") ? (Array.prototype.slice.call(prev.querySelectorAll("p")).pop() || prev) : prev;
        }
        if (!host) {
          var a = anchorFor(el);
          if (!a || !root.contains(a) || a.closest(".note, figure")) return;
          host = a.matches("ul, ol") ? a.querySelector("li") : a.matches("blockquote, div") ? (a.querySelector("p") || a) : a;
          atEnd = false;
        }
        if (!host) return;
        if (!el.id) el.id = "plate-" + i;
        el.dataset.marked = "1";
        var label = el.querySelector(".own-card") ? "post" : el.querySelector("blockquote") ? "quote" : "fig. " + (++n);
        var m = document.createElement("button");
        m.type = "button";
        m.className = "fig-ref";
        m.dataset.for = el.id;
        m.setAttribute("aria-label", "Show " + label + " beside this paragraph");
        m.textContent = label + " \u2192";
        // several figures after one paragraph share one holder, in order
        var holder = atEnd ? host.lastElementChild : host.firstElementChild;
        if (!holder || !holder.classList.contains("fig-refs")) {
          holder = document.createElement("span");
          holder.className = "fig-refs";
          if (atEnd) host.appendChild(holder); else host.insertBefore(holder, host.firstChild);
        }
        holder.appendChild(m);
        el._marker = m;
      });
    });
  }

  function triggerFor(t) {
    var a = t && t.closest && t.closest(".fn-ref a, .fig-ref");
    if (!a) return null;
    var id = a.classList.contains("fig-ref") ? a.dataset.for : (a.getAttribute("href") || "").slice(1);
    var item = id && document.getElementById(id);
    if (!item || !item.style.top) return null;  // only things that are actually in the margin
    return { trigger: a, item: item };
  }

  function release(quick) {
    clearTimeout(leaveTimer);
    if (!summoned) return;
    var root = summoned.root;
    if (quick !== false) root.classList.add("releasing");
    placed(root).forEach(function (el) { el.style.transform = ""; el.classList.remove("summoned"); });
    summoned.trigger.classList.remove("hot");
    var item = summoned.item;
    summoned = null;
    pinned = false;
    if (peek && peek.host === item) hidePeek();
    if (!peek) root.classList.remove("summoning");
    setTimeout(function () { root.classList.remove("releasing"); }, 260);
  }

  function summon(trigger, item) {
    clearTimeout(leaveTimer);
    if (layout !== "wide") return;
    if (summoned && summoned.item === item) return;
    if (summoned) release(false);
    var root = item.closest("[data-wide-root]");
    var items = placed(root);
    var idx = items.indexOf(item);
    if (idx < 0) return;
    var box = root.getBoundingClientRect();
    var rail = root.querySelector(".rail").getBoundingClientRect();
    var railTop = rail.top - box.top;
    var top = parseFloat(item.style.top) || 0;
    var h = item.offsetHeight;
    var lift = item.classList.contains("note") ? (parseFloat(getComputedStyle(item).getPropertyValue("--lift")) || 0) : 6;

    // level with the marker, but kept on screen if it's tall; nothing else moves
    var markTop = trigger.getBoundingClientRect().top - box.top;
    var want = markTop - lift;
    var viewTop = -box.top + 12, viewBottom = window.innerHeight - box.top - 12;
    if (want + h > viewBottom) want = Math.max(viewTop, viewBottom - h);
    want = Math.max(railTop, Math.min(want, markTop));

    summoned = { root: root, item: item, trigger: trigger };
    root.classList.remove("releasing");
    root.classList.add("summoning");
    var d = want - top;
    item.style.transform = Math.abs(d) > 0.5 ? "translateY(" + d + "px)" : "";
    item.classList.add("summoned");
    trigger.classList.add("hot");
  }

  // the pointer is on the summoned item, on its marker, or on a preview opened from a link inside the item
  function inSummon(n) {
    return summoned.trigger.contains(n) || summoned.item.contains(n) || !!(peek && peek.host === summoned.item && peekEl.contains(n));
  }

  function wireSummon() {
    var finePointer = window.matchMedia("(hover: hover)");
    document.addEventListener("mouseover", function (e) {
      if (!finePointer.matches || layout !== "wide") return;
      var t = triggerFor(e.target);
      if (t) { summon(t.trigger, t.item); return; }
      if (summoned && inSummon(e.target)) clearTimeout(leaveTimer);
    });
    document.addEventListener("mouseout", function (e) {
      if (!summoned || pinned) return;
      if (e.relatedTarget && inSummon(e.relatedTarget)) return;
      if (!inSummon(e.target)) return;
      clearTimeout(leaveTimer);
      leaveTimer = setTimeout(release, 160);  // long enough to reach a link inside the note
    });
    document.addEventListener("click", function (e) {
      if (layout !== "wide") return;
      var t = triggerFor(e.target);
      if (t) {
        e.preventDefault();
        e.stopImmediatePropagation();
        if (summoned && summoned.item === t.item && pinned) { release(); return; }
        summon(t.trigger, t.item);
        pinned = true;
        return;
      }
      if (summoned && !summoned.item.contains(e.target)) release();
    }, true);
    window.addEventListener("keydown", function (e) { if (e.key === "Escape") release(); });
  }

  /* --- peek: preview on hover --- */

  // Sites that refuse to be shown inside another page (the box would just say "refused to connect").
  // The previews file says, link by link, what can be framed; this list is only for links it hasn't
  // looked up yet. A link here with nothing in the file gets no box.
  var NO_FRAME = [
    "x.com", "twitter.com", "t.co", "github.com", "google.com", "blog.google", "youtube.com", "youtu.be",
    "facebook.com", "instagram.com", "linkedin.com", "reddit.com", "amazon.com", "apple.com", "patreon.com",
    "claude.ai", "claude.com", "openai.com", "goodreads.com", "bsky.app",
    "archive.is", "archive.ph", "archive.today", "imgur.com", "substack.com"
  ];
  var OURS = /^(www\.)?croissanthology\.com$|^croissanthology\.github\.io$/;
  var IMAGES = /\.(png|jpe?g|gif|webp|avif)$/i;
  var FILES = /\.(svg|ico|pdf|zip|gz|mp3|m4a|wav|ogg|mp4|mov|webm|json|xml|rss|csv|txt|epub|docx?|xlsx?|pptx?)$/i;

  var peek = null;        // what's showing: { root, link, host }
  var peekEl = null;      // the one box, made on first use and reused
  var peekWait = null, peekTimer = 0, peekLeave = 0, pointerY = 0;
  var known = null;       // this post's previews file, once asked for (a promise)

  // where this page's links resolve from (normally just its own address)
  function baseURL() {
    try { return new URL(document.baseURI); } catch (e) { return location; }
  }

  function samePage(path) {
    function norm(p) { return p.replace(/index\.html?$/, "").replace(/\/$/, ""); }
    return norm(path) === norm(baseURL().pathname) || norm(path) === norm(location.pathname);
  }

  function tidy(text) { return (text || "").replace(/\s+/g, " ").trim(); }

  // what the indexer found for this post's links, by href; fetched once, on the first hover that needs it
  function previews(root) {
    if (!known) {
      var at = root.getAttribute("data-previews");
      known = !at ? Promise.resolve({}) : fetch(new URL(at, baseURL()).href)
        .then(function (r) { return r.ok ? r.json() : {}; })
        .catch(function () { return {}; });
    }
    return known;
  }

  // what hovering this element might show: { link, root, ours, src, name, image }
  // (src is the address to frame, or "" when the page can't be framed and only a card will do)
  function peekTarget(t) {
    var a = t && t.closest && t.closest("a[href]");
    if (!a || a.hasAttribute("download") || a.closest(".peek, .runhead, .fn-ref")) return null;
    var root = a.closest("[data-wide-root]");
    if (!root || !root.querySelector(".rail")) return null;
    var u;
    try { u = new URL(a.href); } catch (e) { return null; }
    if (u.protocol !== "http:" && u.protocol !== "https:") return null;
    var base = baseURL(), host = u.hostname.replace(/^www\./, "");

    // another page of this site: the page itself
    if (u.origin === base.origin || (OURS.test(u.hostname) && OURS.test(base.hostname))) {
      if (samePage(u.pathname) || IMAGES.test(u.pathname) || FILES.test(u.pathname)) return null;
      var title = a.querySelector(".own-title") || a;
      return { link: a, root: root, ours: true, src: base.origin + u.pathname + u.search + u.hash, name: tidy(title.textContent) };
    }

    var out = { link: a, root: root, ours: false, src: "", name: host, image: false }, m;
    if (IMAGES.test(u.pathname)) {
      out.image = u.protocol === "https:";
    } else if (u.protocol !== "https:" || FILES.test(u.pathname)) {
      // a plain http page can't be shown inside an https one, and a file isn't a page
    } else if ((m = /^([a-z-]+)\.(?:m\.)?(wikipedia|wiktionary)\.org$/.exec(u.hostname))) {
      // Wikipedia not looked up yet, and Wiktionary: the phone version, which fits a narrow box
      out.src = "https://" + m[1] + ".m." + m[2] + ".org" + u.pathname + u.search + u.hash;
    } else if (/^(m\.|music\.)?youtube\.com$/.test(host) && u.pathname === "/watch" && u.searchParams.get("v")) {
      out.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(u.searchParams.get("v"));
    } else if (host === "youtu.be" && u.pathname.length > 1) {
      out.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(u.pathname.slice(1).split("/")[0]);
    } else {
      out.src = u.href;
      for (var i = 0; i < NO_FRAME.length; i++) {
        if (host === NO_FRAME[i] || host.slice(-NO_FRAME[i].length - 1) === "." + NO_FRAME[i]) out.src = "";
      }
      if (/^\/p\/[^/]+\/?$/.test(u.pathname)) out.src = "";  // a Substack on its own domain: posts live at /p/...
    }
    return out;
  }

  function peekBox(root) {
    if (!peekEl) {
      peekEl = document.createElement("aside");
      peekEl.className = "peek";
      peekEl.setAttribute("aria-label", "Preview");
      var bar = document.createElement("header"), name = document.createElement("span"), open = document.createElement("a");
      bar.className = "peek-bar";
      name.className = "peek-name";
      open.className = "peek-open";
      open.textContent = "open ↗";
      bar.appendChild(name);
      bar.appendChild(open);
      peekEl.appendChild(bar);
    }
    if (peekEl.parentNode !== root) root.appendChild(peekEl);
    return peekEl;
  }

  // the real page, in an iframe
  function frameFor(t, src) {
    var frame = document.createElement("iframe");
    frame.className = "peek-body peek-frame";
    frame.title = "Preview: " + t.name;
    // someone else's page may run its scripts, but may not take this page somewhere else
    if (!t.ours) frame.setAttribute("sandbox", "allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-forms");
    else frame.addEventListener("load", function () {
      // one of this site's pages: name the box after the page rather than the link's words
      try {
        var title = tidy(frame.contentDocument.title.replace(/\s*[-·|]\s*Croissanthology\s*$/, ""));
        if (title && frame.isConnected) peekEl.querySelector(".peek-name").textContent = title;
      } catch (e) {}
    });
    frame.src = src;
    return frame;
  }

  // text from the previews file with only its harmless tags kept (it was cleaned when it was stored; this is the second lock)
  function plain(html) {
    var t = document.createElement("template");
    t.innerHTML = html;
    Array.prototype.slice.call(t.content.querySelectorAll("*")).forEach(function (el) {
      if (/^(P|B|I|EM|STRONG|SUB|SUP|UL|OL|LI|BR)$/.test(el.tagName)) {
        while (el.attributes.length) el.removeAttribute(el.attributes[0].name);
      } else if (/^(SCRIPT|STYLE)$/.test(el.tagName)) {
        el.remove();
      } else {
        while (el.firstChild) el.parentNode.insertBefore(el.firstChild, el);
        el.remove();
      }
    });
    return t.content;
  }

  // a card set in this site's own type, from what the indexer stored (or just the image, for an image link)
  function cardFor(rec) {
    var card = document.createElement("div");
    card.className = "peek-body peek-card k-" + rec.kind;
    function add(cls, text) {
      if (!text) return null;
      var el = document.createElement("p");
      el.className = cls;
      el.textContent = text;
      card.appendChild(el);
      return el;
    }
    function picture(cls, src, w, h) {
      if (!/^https:\/\//.test(src || "")) return;
      var img = document.createElement("img");
      img.className = cls;
      img.alt = "";
      img.referrerPolicy = "no-referrer";
      if (w && h) { img.width = w; img.height = h; }
      img.addEventListener("load", function () { if (card.isConnected) placePeek(); });  // it may have grown
      img.addEventListener("error", function () { img.remove(); if (card.isConnected) placePeek(); });
      img.src = src;
      card.appendChild(img);
    }
    var img = rec.img || [];
    if (rec.kind === "image") { picture("peek-image", img[0]); return card; }
    picture(rec.kind === "wiki" ? "peek-thumb" : "peek-cover", img[0], img[1], img[2]);
    add("peek-title", rec.title);
    add("peek-desc", rec.desc);
    add("peek-by", [rec.by, rec.handle, rec.date].filter(Boolean).join(" · "));
    if (rec.html || rec.text) {
      var text = document.createElement("div");
      text.className = "peek-text";
      if (rec.html) text.appendChild(plain(rec.html));
      else rec.text.split("\n").forEach(function (line) {
        var p = document.createElement("p");
        p.textContent = line;
        text.appendChild(p);
      });
      card.appendChild(text);
    }
    (rec.imgs || []).forEach(function (src) { picture("peek-shot", src); });
    add("peek-more", rec.more);
    return card;
  }

  // what to put in the box for this link, given what the indexer found (rec, possibly nothing). null: no box.
  function bodyFor(t, rec) {
    if (t.ours) return frameFor(t, t.src);
    if (t.image) return cardFor({ kind: "image", img: [t.link.href] });
    if (rec && rec.kind === "image") return cardFor(rec);
    if (rec && rec.frame && t.src) return frameFor(t, t.src);          // the indexer saw nothing against framing it
    if (rec && !rec.frame && (rec.title || rec.text || rec.html)) return cardFor(rec);
    if (rec && (rec.title || rec.text)) return cardFor(rec);           // framable on paper, but on the list above
    return t.src ? frameFor(t, t.src) : null;                           // not looked up yet
  }

  // the pointer has rested on a link
  function openPeek(t) {
    if (t.ours || t.image) { showPeek(t, bodyFor(t), t.name); return; }
    previews(t.root).then(function (found) {
      if (peekWait !== t.link) return;  // the pointer has moved on
      var rec = found[t.link.getAttribute("href")];
      var body = bodyFor(t, rec);
      if (body) showPeek(t, body, body.tagName !== "IFRAME" && rec && rec.site || t.name);
    });
  }

  function showPeek(t, body, name) {
    clearTimeout(peekLeave);
    var root = t.root, box = peekBox(root);
    // a link inside a note or figure that's in the margin: the box goes right under (or over) it
    var host = t.link.closest(".note, figure.plate");
    while (host && !host.style.top) host = host.parentElement.closest(".note, figure.plate");
    if (summoned && summoned.item !== host) release();
    if (peek && peek.host && peek.host !== host) peek.host.classList.remove("peek-host");

    var open = box.querySelector(".peek-open");
    box.querySelector(".peek-name").textContent = name;
    open.href = t.link.href;
    open.target = t.link.target;
    open.rel = t.link.rel;
    var old = box.querySelector(".peek-body");
    if (old) old.remove();
    box.appendChild(body);
    box.classList.toggle("card", body.tagName !== "IFRAME");  // a card is only as tall as what's in it
    box.classList.add("open");

    // a link a line or two away from the last one: stay put rather than hop
    var was = peek && !peek.host && !host && peek.root === root ? parseFloat(box.style.top) : NaN;
    peek = { root: root, link: t.link, host: host };
    placePeek(was);
    if (host) host.classList.add("peek-host");
    root.classList.remove("releasing");
    root.classList.add("summoning");
  }

  // level with the line of the link the pointer is on, with the whole box on screen
  function placePeek(was) {
    if (!peek) return;
    var root = peek.root, box = peekEl, host = peek.host;
    var rbox = root.getBoundingClientRect();
    var r = root.querySelector(".rail").getBoundingClientRect();
    box.style.left = (r.left - rbox.left) + "px";
    box.style.width = r.width + "px";
    var railTop = r.top - rbox.top;
    var h = box.offsetHeight;
    var viewTop = -rbox.top + 16, viewBottom = window.innerHeight - rbox.top - 16;
    var want;
    if (host) {
      var hr = host.getBoundingClientRect();
      want = hr.bottom - rbox.top + GAP;
      var above = hr.top - rbox.top - GAP - h;
      if (want + h > viewBottom) want = above >= viewTop ? above : Math.max(viewTop, viewBottom - h);
    } else {
      var rects = peek.link.getClientRects(), line = rects[0] || peek.link.getBoundingClientRect();
      for (var i = 0; i < rects.length; i++) if (pointerY >= rects[i].top - 2 && pointerY <= rects[i].bottom + 2) line = rects[i];
      var markTop = line.top - rbox.top;
      want = markTop - 4;
      if (want + h > viewBottom) want = Math.max(viewTop, viewBottom - h);
      want = Math.min(want, markTop);
      if (Math.abs(was - want) < 56 && was >= viewTop && was + h <= viewBottom) want = was;
    }
    want = Math.max(railTop, Math.min(want, root.offsetHeight - h));  // and inside the page, so it doesn't grow
    box.style.top = want + "px";
  }

  // put the box away; taking out what's in it stops whatever a framed page was doing
  function hidePeek() {
    clearTimeout(peekLeave);
    if (!peek) return;
    var root = peek.root, body = peekEl.querySelector(".peek-body");
    if (body) body.remove();
    if (peek.host) peek.host.classList.remove("peek-host");
    peekEl.classList.remove("open");
    peek = null;
    if (!summoned) root.classList.remove("summoning");
  }

  // put it away and forget the link the pointer was resting on
  function closePeek() {
    clearTimeout(peekTimer);
    peekWait = null;
    hidePeek();
  }

  function wirePeek() {
    var canHover = window.matchMedia("(hover: hover)");
    document.addEventListener("mouseover", function (e) {
      if (!canHover.matches || layout !== "wide") return;
      if (peek && (peekEl.contains(e.target) || peek.link.contains(e.target))) clearTimeout(peekLeave);
      var t = peekTarget(e.target);
      var link = t && t.link;
      if (link === peekWait) return;
      clearTimeout(peekTimer);
      peekWait = link;
      if (!link || (peek && peek.link === link)) return;
      pointerY = e.clientY;
      // only once the pointer has rested on the link; passing over it loads nothing
      peekTimer = setTimeout(function () { if (peekWait === link) openPeek(t); }, 240);
    });
    document.addEventListener("mouseout", function (e) {
      if (!peek) return;
      function inside(n) { return peekEl.contains(n) || peek.link.contains(n); }
      if (e.relatedTarget && inside(e.relatedTarget)) return;
      if (!inside(e.target)) return;
      clearTimeout(peekLeave);
      // long enough to cross the text to the margin; the pointer being in the box (or the page inside it) keeps it
      peekLeave = setTimeout(function () {
        if (peek && (peekEl.matches(":hover") || peek.link.matches(":hover"))) return;
        hidePeek();
      }, 320);
    });
    document.addEventListener("click", function (e) {
      if (peek && !peekEl.contains(e.target)) closePeek();
    }, true);
    window.addEventListener("keydown", function (e) { if (e.key === "Escape") closePeek(); });
    window.addEventListener("pageshow", closePeek);  // coming back with the back button
  }

  /* --- the switch --- */
  function apply(next) {
    layout = next;
    doc.setAttribute("data-layout", next);
    readHinge();
    place();
    document.dispatchEvent(new CustomEvent("wide:layout", { detail: next }));
  }

  function switchTo(next) {
    if (next === layout) { place(); return; }
    apply(next);
  }

  /* --- notes: tap to open when narrow, light up when wide --- */
  function wireNotes() {
    document.addEventListener("click", function (e) {
      var a = e.target.closest && e.target.closest(".fn-ref a");
      if (!a) return;
      var note = document.getElementById(a.getAttribute("href").slice(1));
      if (!note) return;
      e.preventDefault();
      var r = note.getBoundingClientRect();
      if (r.top < 0 || r.bottom > window.innerHeight) {
        note.scrollIntoView({ block: "nearest", behavior: reduce.matches ? "auto" : "smooth" });
      }
      note.classList.remove("flash");
      void note.offsetWidth;
      note.classList.add("flash");
    });
    function hot(e, on) {
      var a = e.target.closest && e.target.closest(".fn-ref a, .note");
      if (!a) return;
      var id = a.classList.contains("note") ? a.id : a.getAttribute("href").slice(1);
      var note = document.getElementById(id);
      var ref = note && document.getElementById(note.dataset.for);
      if (note) note.classList.toggle("hot", on);
      if (ref) ref.classList.toggle("hot", on);
    }
    document.addEventListener("mouseover", function (e) { hot(e, true); });
    document.addEventListener("mouseout", function (e) { hot(e, false); });
  }

  /* --- boot --- */
  var queued = false;
  function onResize() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(function () {
      queued = false;
      switchTo(wanted());
    });
  }

  function boot() {
    markFigures();
    wireNotes();
    wireSummon();
    wirePeek();
    apply(wanted());
    // show the margin once, all at once, after the fonts that decide where everything goes
    var shown = false;
    function show() {
      if (shown) return;
      shown = true;
      place();
      document.querySelectorAll("[data-wide-root]").forEach(function (r) {
        r.classList.add("ready");
      });
    }
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(show);
    setTimeout(show, 900);
    window.addEventListener("load", place);
    window.addEventListener("resize", onResize);
    if (window.ResizeObserver) {
      var ro = new ResizeObserver(function () { if (layout === "wide") place(); });
      document.querySelectorAll("[data-wide-root]").forEach(function (r) { ro.observe(r.querySelector(".flow") || r); });
    }
    document.querySelectorAll("img").forEach(function (img) { img.addEventListener("load", place); });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();

  window.FacingPages = { place: place, layout: function () { return layout; } };
})();
