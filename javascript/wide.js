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
 *   Wikipedia                                               the lead at once, then the whole article, fetched
 *                                                           from Wikipedia and set in this site's type
 *   a tweet, a Bluesky post, a profile                      the same card tweets get inside a post
 *   a Substack post, GitHub                                 a small card: who, when, how it opens
 *   an image                                                the image
 *   a page that refuses to be framed                        its title, description and picture
 * The cards come from previews/<post>.json, which scripts/previews/index.py builds ahead of time
 * (it also notes which pages can be framed). That file is fetched the first time it's needed.
 * A link inside the box (in a Wikipedia article, or in one of this site's pages shown there) opens
 * right under it, the two sharing the box. Go deeper and the pair slides along: always the pane you
 * came from and the one you opened, with "back" to step up. Nothing loads until the pointer has
 * rested on a link.
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
  // what a Wikipedia article is shown without: boxes, tables, pictures, footnote marks, and its closing lists
  var WIKI_JUNK = "style, link, meta, script, table, figure, img, audio, video, .infobox, .navbox, .sidebar, .hatnote, .ambox, " +
    ".metadata, .mw-editsection, .mw-ref, .reference, .reflist, .refbegin, .noprint, .mw-empty-elt, .thumb, .gallery, .navbar, .shortdescription";
  var WIKI_ENDS = /^(see also|notes|references|footnotes|citations|sources|works cited|bibliography|further reading|external links)$/i;
  var WIKI_OTHER = /^(File|Special|Category|Help|Talk|Wikipedia|User|Template|Portal|Draft|Module|MediaWiki):/i;

  var peek = null;        // what's showing: { root, link, host }
  var peekEl = null;      // the one box, made on first use and reused
  var peekWait = null, peekTimer = 0, peekLeave = 0, pointerY = 0, asked = 0;
  var swapped = false;    // the box's contents just changed under the pointer; where the pointer is isn't known until it moves
  var deep = false;       // the box has held two panes since it opened
  var stale = false, anchor = null;  // after such a change, a link that lands under a still pointer mustn't open: wait for the pointer to move
  var trail = [];         // what the box holds, oldest first; the last two are shown: { pane, body, name, href, target, rel }
  var files = {};         // previews files already asked for, by address (promises)
  var articles = {};      // Wikipedia articles already fetched (promises)

  // where this page's links resolve from (normally just its own address)
  function baseURL() {
    try { return new URL(document.baseURI); } catch (e) { return location; }
  }

  function samePage(path) {
    function norm(p) { return p.replace(/index\.html?$/, "").replace(/\/$/, ""); }
    return norm(path) === norm(baseURL().pathname) || norm(path) === norm(location.pathname);
  }

  function tidy(text) { return (text || "").replace(/\s+/g, " ").trim(); }

  // what the indexer found for a post's links, by href; fetched once, on the first hover that needs it
  function previewsAt(at) {
    if (!at) return Promise.resolve({});
    if (!files[at]) {
      files[at] = fetch(at).then(function (r) { return r.ok ? r.json() : {}; }).catch(function () { return {}; });
    }
    return files[at];
  }

  function previewsOf(root) {
    var at = root.getAttribute("data-previews");
    return at ? new URL(at, baseURL()).href : "";
  }

  // what a link might show: { link, root, ours, src, name, image, wiki, short }
  // (src is the address to frame, or "" when the page can't be framed and only a card will do)
  function targetOf(a, root) {
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
      // the phone version fits a narrow box: Wiktionary always gets it, Wikipedia only if its article can't be fetched
      out.src = "https://" + m[1] + ".m." + m[2] + ".org" + u.pathname + u.search + u.hash;
      if (m[2] === "wikipedia" && u.pathname.indexOf("/wiki/") === 0 && u.pathname.length > 6 && !WIKI_OTHER.test(u.pathname.slice(6))) {
        try { out.wiki = { lang: m[1], title: decodeURIComponent(u.pathname.slice(6)) }; out.name = "Wikipedia"; } catch (e) {}
      }
    } else if (/^(m\.|music\.)?youtube\.com$/.test(host) && u.pathname === "/watch" && u.searchParams.get("v")) {
      out.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(u.searchParams.get("v"));
    } else if (host === "youtu.be" && u.pathname.length > 1) {
      out.src = "https://www.youtube-nocookie.com/embed/" + encodeURIComponent(u.pathname.slice(1).split("/")[0]);
    } else if (/\.substack\.com$/.test(host) && /^\/p\/[^/]+\/?$/.test(u.pathname)) {
      // Substack won't let its posts be framed, but it offers this small embed of each one
      out.src = "https://" + u.hostname + "/embed" + u.pathname.replace(/\/$/, "");
      out.short = true;
    } else {
      out.src = u.href;
      for (var i = 0; i < NO_FRAME.length; i++) {
        if (host === NO_FRAME[i] || host.slice(-NO_FRAME[i].length - 1) === "." + NO_FRAME[i]) out.src = "";
      }
      if (/^\/p\/[^/]+\/?$/.test(u.pathname)) out.src = "";  // a Substack on its own domain: posts live at /p/...
    }
    return out;
  }

  // the same, for whatever is under the pointer. Links inside the box count too (nested: they open in the box).
  function peekTarget(el) {
    var a = el && el.closest && el.closest("a[href]");
    if (!a || a.hasAttribute("download") || a.closest(".runhead, .fn-ref, .peek-bar")) return null;
    if (a.closest(".bsky")) return null;  // a tweet or Bluesky card already in the margin is its own preview
    var root = a.closest("[data-wide-root]");
    if (!root || !root.querySelector(".rail")) return null;
    var t = targetOf(a, root);
    var pane = a.closest(".peek-pane");
    if (t && pane) {
      t.nested = true;
      for (var i = 0; i < trail.length; i++) if (trail[i].pane === pane) t.from = i;  // which pane the link is in
    }
    return t;
  }

  function peekBox(root) {
    if (!peekEl) {
      peekEl = document.createElement("aside");
      peekEl.className = "peek";
      peekEl.setAttribute("aria-label", "Preview");
    }
    if (peekEl.parentNode !== root) root.appendChild(peekEl);
    return peekEl;
  }

  // one thing in the box: a small top line (open, back, what it is), then the page or card itself
  function makePane(entry) {
    var pane = document.createElement("div"), bar = document.createElement("header");
    var name = document.createElement("span"), open = document.createElement("a"), back = document.createElement("button");
    pane.className = "peek-pane";
    bar.className = "peek-bar";
    name.className = "peek-name";
    open.className = "peek-open";
    open.textContent = "open ↗";
    back.className = "peek-back";
    back.type = "button";
    back.hidden = true;
    back.addEventListener("click", stepBack);
    bar.appendChild(open);  // the way out comes first, nearest the text
    bar.appendChild(back);
    bar.appendChild(name);
    pane.appendChild(bar);
    pane.appendChild(entry.body);
    return pane;
  }

  // The box shows the last two things on the trail, one above the other, sharing its height: where you came from
  // and what you opened from it. Anything older is kept, out of sight, for "back". So however deep the trail
  // goes, the margin holds the same two panes in the same space.
  function layoutPeek() {
    var n = trail.length, last = trail[n - 1];
    trail.forEach(function (e, i) {
      var hide = i < n - 2, pane = e.pane, back = pane.querySelector(".peek-back"), open = pane.querySelector(".peek-open");
      if (hide && !pane.classList.contains("under")) e.scroll = e.body.scrollTop;  // a hidden card forgets how far it was scrolled
      pane.classList.toggle("under", hide);
      pane.querySelector(".peek-name").textContent = e.name;
      open.href = e.href;
      open.target = e.target;
      open.rel = e.rel;
      back.hidden = !(i === n - 1 && i > 0);
      back.textContent = "← back" + (i > 1 ? " · " + (i + 1) + " deep" : "");
      if (!hide && e.scroll) { e.body.scrollTop = e.scroll; e.scroll = 0; }
    });
    if (n > 1) deep = true;  // once it has held two it keeps that height, so it never shrinks away from under the pointer
    peekEl.classList.toggle("two", deep);
    peekEl.classList.toggle("card", !deep && last.body.tagName !== "IFRAME");  // alone, a card is only as tall as what's in it
    peekEl.classList.toggle("short", !deep && !!last.short);
    if (peek) fitPeek();
  }

  // "back": drop the newest pane; the one before it comes back into view, as it was left
  function stepBack() {
    if (trail.length < 2) return;
    clearTimeout(peekLeave);
    swapped = stale = true; anchor = null;
    trail.pop().pane.remove();
    layoutPeek();
  }

  // the real page, in an iframe
  function frameFor(t, src) {
    var frame = document.createElement("iframe");
    frame.className = "peek-body peek-frame";
    frame.title = "Preview: " + t.name;
    // someone else's page may run its scripts, but may not take this page somewhere else
    if (!t.ours) frame.setAttribute("sandbox", "allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox allow-forms");
    frame.src = src;
    return frame;
  }

  // a piece of someone else's HTML with only its harmless tags kept and every attribute dropped. With wiki set
  // (a language code), links to other Wikipedia articles are kept too, pointed at Wikipedia.
  function plain(holder, wiki) {
    Array.prototype.slice.call(holder.querySelectorAll("*")).forEach(function (el) {
      var href = el.tagName === "A" && wiki && el.getAttribute("rel") === "mw:WikiLink" ? el.getAttribute("href") || "" : "";
      if (/^\.\/[^#]/.test(href) && !WIKI_OTHER.test(href.slice(2))) {
        while (el.attributes.length) el.removeAttribute(el.attributes[0].name);
        el.href = "https://" + wiki + ".wikipedia.org/wiki/" + href.slice(2);
        el.target = "_blank";
        el.rel = "noopener";
      } else if (/^(P|B|I|EM|STRONG|SUB|SUP|UL|OL|LI|DL|DT|DD|BLOCKQUOTE|H3|H4|BR)$/.test(el.tagName)) {
        while (el.attributes.length) el.removeAttribute(el.attributes[0].name);
      } else if (/^(SCRIPT|STYLE)$/.test(el.tagName)) {
        el.remove();
      } else {
        while (el.firstChild) el.parentNode.insertBefore(el.firstChild, el);
        el.remove();
      }
    });
    Array.prototype.slice.call(holder.querySelectorAll("p, li, h3, h4")).forEach(function (el) {
      if (!el.textContent.trim()) el.remove();
    });
    return holder;
  }

  // a whole Wikipedia article, fetched from Wikipedia when a box needs it: { title, lead, sections: [{ title, body }] }
  function wikiArticle(w) {
    var key = w.lang + ":" + w.title;
    if (!articles[key]) {
      articles[key] = fetch("https://" + w.lang + ".wikipedia.org/api/rest_v1/page/html/" + encodeURIComponent(w.title.replace(/ /g, "_")))
        .then(function (r) { if (!r.ok) throw 0; return r.text(); })
        .then(function (html) {
          var d = new DOMParser().parseFromString(html, "text/html");
          var art = { title: tidy(d.title), lead: null, sections: [] };
          Array.prototype.slice.call(d.querySelectorAll(WIKI_JUNK)).forEach(function (el) { el.remove(); });
          Array.prototype.slice.call(d.body.children).forEach(function (sec) {
            if (sec.tagName !== "SECTION") return;
            var h = sec.querySelector("h2");
            if (h && h.parentNode !== sec) h = null;
            var title = h ? tidy(h.textContent) : "";
            if (h) h.remove();
            if (h && WIKI_ENDS.test(title)) return;
            var body = plain(sec, w.lang);
            if (!body.textContent.trim()) return;
            if (!h && !art.lead) art.lead = body;
            else if (h) art.sections.push({ title: title, body: body });
          });
          if (!art.lead && !art.sections.length) throw 0;
          return art;
        });
      articles[key].catch(function () { delete articles[key]; });
    }
    return articles[key];
  }

  // put the article into its card: the lead (now with its links), then each section, closed, under its title
  function growWiki(card, art) {
    function pour(from, into) {
      Array.prototype.slice.call(from.childNodes).forEach(function (n) { into.appendChild(document.importNode(n, true)); });
    }
    var text = card.querySelector(".peek-text");
    if (!text) {
      text = document.createElement("div");
      text.className = "peek-text";
      card.appendChild(text);
    }
    if (art.lead) {
      while (text.firstChild) text.removeChild(text.firstChild);
      pour(art.lead, text);
    }
    if (art.sections.length) {
      var rest = document.createElement("div");
      rest.className = "peek-secs";
      art.sections.forEach(function (sec) {
        var d = document.createElement("details"), sum = document.createElement("summary"), body = document.createElement("div");
        sum.textContent = sec.title;
        body.className = "peek-text";
        pour(sec.body, body);
        d.appendChild(sum);
        d.appendChild(body);
        d.addEventListener("toggle", fitPeek);
        rest.appendChild(d);
      });
      card.appendChild(rest);
    }
    if (card.isConnected) fitPeek();
  }

  function picture(card, cls, src, w, h) {
    if (!/^https:\/\//.test(src || "")) return null;
    var img = document.createElement("img");
    img.className = cls;
    img.alt = "";
    img.referrerPolicy = "no-referrer";
    if (w && h) { img.width = w; img.height = h; }
    img.addEventListener("load", function () { if (card.isConnected) fitPeek(); });  // the box may have grown
    img.addEventListener("error", function () { img.remove(); if (card.isConnected) fitPeek(); });
    img.src = src;
    return img;
  }

  // a tweet, a Bluesky post or a profile, in the same markup (and so the same look) as the tweets inside a post
  function tweetCard(card, rec) {
    function el(tag, cls, text) {
      var e = document.createElement(tag);
      e.className = cls;
      if (text) e.textContent = text;
      return e;
    }
    function who(r, tag) {
      var w = el(tag, "who"), face = r.avatar && picture(card, "avatar", r.avatar, 36, 36);
      if (face) w.appendChild(face);
      w.appendChild(el("span", "name", r.by || ""));
      w.appendChild(document.createTextNode(" "));
      w.appendChild(el("span", "handle", r.handle || ""));
      return w;
    }
    var bq = el("blockquote", "bsky");
    bq.appendChild(who(rec, "p"));
    if (rec.replying) bq.appendChild(el("p", "reply", "Replying to " + rec.replying));
    if (rec.text) bq.appendChild(el("p", "said", rec.text));
    var shots = (rec.imgs || []).concat(rec.poster ? [rec.poster] : []);
    if (shots.length) {
      var row = el("span", "shots");
      shots.forEach(function (src) { var img = picture(card, "", src); if (img) row.appendChild(img); });
      bq.appendChild(row);
    }
    if (rec.video) bq.appendChild(el("p", "video", "▶ " + rec.video));
    if (rec.link) bq.appendChild(el("p", "video", "↗ " + [rec.link.title, rec.link.site].filter(Boolean).join(" · ")));
    if (rec.quoted) {
      var q = el("span", "quoted");
      q.appendChild(who(rec.quoted, "span"));
      q.appendChild(el("span", "said", rec.quoted.text || ""));
      bq.appendChild(q);
    }
    if (rec.more) bq.appendChild(el("p", "video", rec.more));
    bq.appendChild(el("p", "when", rec.kind === "profile"
      ? rec.site + " keeps profiles to itself: open it to see the rest"
      : [rec.site, rec.date].filter(Boolean).join(" · ")));
    card.appendChild(bq);
    return card;
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
    function show(cls, src, w, h) {
      var img = picture(card, cls, src, w, h);
      if (img) card.appendChild(img);
    }
    var img = rec.img || [];
    if (rec.kind === "image") { show("peek-image", img[0]); return card; }
    if (rec.kind === "tweet" || rec.kind === "profile") return tweetCard(card, rec);
    show(rec.kind === "wiki" ? "peek-thumb" : "peek-cover", img[0], img[1], img[2]);
    add("peek-title", rec.title);
    add("peek-desc", rec.desc);
    add("peek-by", [rec.by, rec.handle, rec.date].filter(Boolean).join(" · "));
    if (rec.html || rec.text) {
      var text = document.createElement("div");
      text.className = "peek-text";
      if (rec.html) {
        var t = document.createElement("template");
        t.innerHTML = rec.html;  // cleaned when it was stored; plain() is the second lock
        text.appendChild(plain(t.content));
      } else rec.text.split("\n").forEach(function (line) {
        var p = document.createElement("p");
        p.textContent = line;
        text.appendChild(p);
      });
      card.appendChild(text);
    }
    (rec.imgs || []).forEach(function (src) { show("peek-shot", src); });
    add("peek-more", rec.more);
    return card;
  }

  // Wikipedia: the stored lead at once, the rest of the article when it arrives. With nothing stored (a link
  // inside another article, say) the box waits for the article, and failing that shows Wikipedia's phone page.
  function wikiCard(t, rec) {
    var whole = wikiArticle(t.wiki);
    if (rec) {
      var card = cardFor(rec);
      whole.then(function (art) { growWiki(card, art); }).catch(function () {});
      return card;
    }
    return whole.then(function (art) {
      var made = cardFor({ kind: "wiki", title: art.title.replace(/ - Wikipedia$/, "") });
      growWiki(made, art);
      return made;
    }).catch(function () { return frameFor(t, t.src); });
  }

  // what to put in the box for this link, given what the indexer found (rec, possibly nothing).
  // null: no box. For Wikipedia it may be a promise.
  function bodyFor(t, rec) {
    if (t.ours) return frameFor(t, t.src);
    if (t.image) return cardFor({ kind: "image", img: [t.link.href] });
    if (rec && rec.kind === "image") return cardFor(rec);
    if (t.wiki) return wikiCard(t, rec && rec.kind === "wiki" ? rec : null);
    if (rec && rec.kind === "profile") return cardFor(rec);
    if (rec && rec.frame && t.src && !t.short) return frameFor(t, t.src);  // the indexer saw nothing against framing it
    if (rec && !rec.frame && (rec.title || rec.text || rec.html)) return cardFor(rec);
    if (rec && (rec.title || rec.text)) return cardFor(rec);           // framable on paper, but on the list above
    return t.src ? frameFor(t, t.src) : null;                           // not looked up yet
  }

  // the pointer has rested on a link. found: the previews file to look it up in (a promise); key: its href there.
  function openPeek(t, found, key, stillWanted) {
    var mine = ++asked;
    function show(body, rec) {
      if (!body || mine !== asked || !stillWanted() || (t.nested && !peek)) return;  // overtaken, or the pointer has moved on
      showPeek(t, body, body.tagName !== "IFRAME" && rec && rec.site || t.name);
    }
    if (t.ours || t.image) { show(bodyFor(t)); return; }
    found.then(function (recs) {
      var rec = recs[key];
      Promise.resolve(bodyFor(t, rec)).then(function (body) { show(body, rec); });
    });
  }

  function showPeek(t, body, name) {
    clearTimeout(peekLeave);
    var root = t.root, box = peekBox(root);
    var entry = { body: body, name: name, href: t.link.href, target: t.link.target, rel: t.link.rel, short: t.short };
    entry.pane = makePane(entry);
    if (t.ours) body.addEventListener("load", function () {
      // one of this site's pages: name the pane after the page rather than the link's words
      try {
        var title = tidy(body.contentDocument.title.replace(/\s*[-·|]\s*Croissanthology\s*$/, ""));
        if (title) { entry.name = title; entry.pane.querySelector(".peek-name").textContent = title; }
      } catch (e) {}
    });

    if (t.nested && peek) {
      // a link inside the box: what it opens goes right under the pane it's in. Anything that pane had
      // opened before is replaced, and the pane above it steps out of sight.
      if (t.from == null || t.from >= trail.length) return;
      while (trail.length > t.from + 1) trail.pop().pane.remove();
      if (trail.length >= 40) trail.shift().pane.remove();
      swapped = stale = true; anchor = null;
      trail.push(entry);
      box.appendChild(entry.pane);
      layoutPeek();
      return;
    }

    // a link inside a note or figure that's in the margin: the box goes right under (or over) it
    var host = t.link.closest(".note, figure.plate");
    while (host && !host.style.top) host = host.parentElement.closest(".note, figure.plate");
    if (summoned && summoned.item !== host) release();
    if (peek && peek.host && peek.host !== host) peek.host.classList.remove("peek-host");

    trail.forEach(function (old) { old.pane.remove(); });
    trail = [entry];
    deep = false;
    box.appendChild(entry.pane);
    box.classList.add("open");
    var was = peek && !peek.host && !host && peek.root === root ? parseFloat(box.style.top) : NaN;
    peek = null;  // (so layoutPeek leaves the placing to placePeek, below)
    layoutPeek();

    // a link a line or two away from the last one: stay put rather than hop
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

  // what's in the box has changed size: the box stays where it is, moving up only as far as it must to stay on screen
  function fitPeek() {
    if (!peek) return;
    var root = peek.root, rbox = root.getBoundingClientRect();
    var railTop = root.querySelector(".rail").getBoundingClientRect().top - rbox.top;
    var top = parseFloat(peekEl.style.top) || 0, h = peekEl.offsetHeight;
    var viewTop = -rbox.top + 16, viewBottom = window.innerHeight - rbox.top - 16;
    if (top + h > viewBottom) top = Math.max(viewTop, viewBottom - h);
    peekEl.style.top = Math.max(railTop, Math.min(top, root.offsetHeight - h)) + "px";
  }

  // put the box away; taking out what's in it stops whatever a framed page was doing
  function hidePeek() {
    clearTimeout(peekLeave);
    if (!peek) return;
    var root = peek.root;
    trail.forEach(function (old) { old.pane.remove(); });
    trail = [];
    swapped = deep = stale = false;
    if (peek.host) peek.host.classList.remove("peek-host");
    peekEl.classList.remove("open");
    peek = null;
    if (!summoned) root.classList.remove("summoning");
  }

  // put it away and forget the link the pointer was resting on
  function closePeek() {
    clearTimeout(peekTimer);
    peekWait = null;
    asked++;
    hidePeek();
  }

  // This page is itself being shown in a box on another of the site's pages: that page's wide.js, if so.
  function upstairs() {
    try {
      var f = window.frameElement, up = window.parent.FacingPages;
      return f && f.classList.contains("peek-frame") && up && up.nest ? up : null;
    } catch (e) { return null; }
  }

  // ...and a link in it has been rested on: ask the page upstairs to open it in the box, on top of this one
  function askUpstairs(e, up) {
    var a = e.target.closest && e.target.closest("a[href]");
    if (a === peekWait) return;
    clearTimeout(peekTimer);
    peekWait = a;
    if (!a || a.hasAttribute("download") || a.closest(".runhead, .fn-ref, .bsky") || !/^https?:$/.test(a.protocol)) return;
    if (a.origin === location.origin && a.pathname === location.pathname) return;  // a link within this page
    var root = a.closest("[data-wide-root]");
    peekTimer = setTimeout(function () {
      if (peekWait !== a) return;
      up.nest({ frame: window.frameElement, href: a.href, key: a.getAttribute("href"), text: tidy((a.querySelector(".own-title") || a).textContent),
                target: a.target, rel: a.rel, previews: root ? previewsOf(root) : "" });
    }, 600);
  }

  // (upstairs) a page shown in the box passes on a link of its own
  function nest(info) {
    if (!peek || layout !== "wide") return;
    var a = document.createElement("a");
    a.href = info.href;
    a.target = info.target || "";
    a.rel = info.rel || "";
    a.textContent = info.text || "";
    var t = targetOf(a, peek.root);
    if (!t) return;
    t.nested = true;
    for (var i = 0; i < trail.length; i++) if (trail[i].body === info.frame) t.from = i;  // which pane that page is in
    openPeek(t, previewsAt(info.previews), info.key, function () { return true; });
  }

  // the pointer has left the link and the box: put the box away, after long enough to cross the text to the margin.
  // The pointer being in the box (or the page inside it) keeps it, and so does a change of contents under a still pointer.
  function leaveSoon() {
    clearTimeout(peekLeave);
    peekLeave = setTimeout(function () {
      if (!peek || swapped || peekEl.matches(":hover") || peek.link.matches(":hover")) return;
      hidePeek();
    }, 320);
  }

  function wirePeek() {
    var canHover = window.matchMedia("(hover: hover)");
    function hover(e) {
      if (!canHover.matches) return;
      if (layout !== "wide") {
        var up = upstairs();
        if (up) askUpstairs(e, up);
        return;
      }
      if (stale) {
        // the box has just changed, and a link may simply have appeared under the pointer: it has to move first
        if (!anchor) anchor = [e.clientX, e.clientY];
        else if (Math.abs(e.clientX - anchor[0]) + Math.abs(e.clientY - anchor[1]) >= 6) stale = false;
      }
      if (peek && (peekEl.contains(e.target) || peek.link.contains(e.target))) clearTimeout(peekLeave);
      else if (peek && swapped) leaveSoon();  // it moved, and it's outside
      swapped = false;
      var t = peekTarget(e.target);
      var link = t && t.link;
      if (link === peekWait) return;
      clearTimeout(peekTimer);
      peekWait = link;
      if (!link || (peek && peek.link === link) || (t.nested && !peek)) return;
      if (stale && t.nested) { peekWait = null; return; }  // (it has only just appeared under the pointer)
      if (!t.nested) pointerY = e.clientY;
      // only once the pointer has rested on the link; passing over it loads nothing.
      // Inside the box the wait is longer, so reading with the pointer on the text doesn't turn the page.
      peekTimer = setTimeout(function () {
        if (peekWait === link) openPeek(t, previewsAt(previewsOf(t.root)), link.getAttribute("href"), function () { return peekWait === link; });
      }, t.nested ? 600 : 240);
    }
    document.addEventListener("mouseover", hover);
    document.addEventListener("mousemove", function (e) { if (stale && peek) hover(e); });
    document.addEventListener("mouseout", function (e) {
      if (!peek) return;
      function inside(n) { return peekEl.contains(n) || peek.link.contains(n); }
      if (e.relatedTarget && inside(e.relatedTarget)) return;
      if (!inside(e.target)) return;
      leaveSoon();
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

  window.FacingPages = { place: place, layout: function () { return layout; }, nest: nest };
})();
