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
 * Peek (wide only, pointers that can hover): resting on a link to another page of this site shows
 * that page in the rail, level with the link, over the notes and figures, which dim just as they
 * do for a summon. The page is loaded in a sandboxed iframe with scripts off, so it arrives in its
 * narrow layout, and with #peek on its address, so it trims itself: cover, title, subtitle, opening lines. Wikipedia links get a short text summary
 * in the same place. Nothing is fetched until the pointer has rested on a link.
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
    if (layout !== "wide") closePeek(); else if (peek) fitPeek(peek.root);
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
  var peek = null;        // what's showing: { root, link, host }
  var peekEl = null;      // the one box previews are shown in, made on first use
  var peekWait = null, peekTimer = 0, peekLeave = 0, peekSeq = 0, pointerY = 0;
  var wiki = {};          // Wikipedia summaries already fetched, by API address
  var OURS = /^(www\.)?croissanthology\.com$|^croissanthology\.github\.io$/;

  function samePage(path) {
    function norm(p) { return p.replace(/index\.html?$/, "").replace(/\/$/, ""); }
    return norm(path) === norm(location.pathname);
  }

  // what, if anything, hovering this element should preview
  function peekTarget(t) {
    var a = t && t.closest && t.closest("a[href]");
    if (!a || a.hasAttribute("download") || a.closest(".peek, .runhead, .fn-ref")) return null;
    var root = a.closest("[data-wide-root]");
    if (!root || !root.querySelector(".rail")) return null;
    var u;
    try { u = new URL(a.href); } catch (e) { return null; }
    if (u.protocol !== "http:" && u.protocol !== "https:") return null;
    var w = /^([a-z-]+)\.(?:m\.)?wikipedia\.org$/.exec(u.hostname);
    if (w && u.pathname.indexOf("/wiki/") === 0 && u.pathname.length > 6) {
      var title;
      try { title = decodeURIComponent(u.pathname.slice(6)); } catch (e) { return null; }
      return { link: a, root: root, kind: "wiki", src: "https://" + w[1] + ".wikipedia.org/api/rest_v1/page/summary/" + encodeURIComponent(title) };
    }
    var here = u.origin === location.origin || (OURS.test(u.hostname) && OURS.test(location.hostname));
    if (!here || samePage(u.pathname)) return null;
    if (/\.[a-z0-9]+$/i.test(u.pathname) && !/\.html?$/i.test(u.pathname)) return null;  // images, PDFs, feeds
    return { link: a, root: root, kind: "page", src: location.origin + u.pathname + u.search };
  }

  function peekBox(root) {
    if (!peekEl) {
      peekEl = document.createElement("aside");
      peekEl.className = "peek";
      peekEl.setAttribute("aria-hidden", "true");  // it repeats a link that's already in the text
      var go = document.createElement("a");
      go.className = "peek-go";
      go.tabIndex = -1;
      peekEl.appendChild(go);
    }
    if (peekEl.parentNode !== root) root.appendChild(peekEl);
    return peekEl;
  }

  function fitPeek(root) {
    var box = root.getBoundingClientRect();
    var r = root.querySelector(".rail").getBoundingClientRect();
    peekEl.style.left = (r.left - box.left) + "px";
    peekEl.style.width = r.width + "px";
  }

  // the page inside the iframe wears the reader's theme. This site's own pages trim themselves for the
  // margin (facing.css, #peek:target); older pages keep their look but sit on this page's paper.
  function dress(frame) {
    try {
      var d = frame.contentDocument, own = !!d.getElementById("peek");
      var t = doc.getAttribute("data-theme");
      if (!own && !t) t = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";  // older pages always carry one
      if (t) d.documentElement.setAttribute("data-theme", t);
      if (own) return;
      var st = d.createElement("style");
      st.textContent = "html,body{overflow:hidden;background:" + getComputedStyle(doc).getPropertyValue("--page").trim() + "!important}";
      d.head.appendChild(st);
    } catch (e) {}  // can't reach in: the page still shows, in the device's theme
  }

  // call back once the framed page can be shown: parsed and styled, without waiting for every image in it
  function whenReady(frame, cb) {
    var done = false, poll = 0;
    function finish() {
      if (done) return;
      done = true;
      clearInterval(poll);
      cb();
    }
    frame.addEventListener("load", finish);
    poll = setInterval(function () {
      if (!frame.isConnected) { done = true; clearInterval(poll); return; }
      try {
        var d = frame.contentDocument;
        if (!d || d.readyState === "loading" || !d.body || d.URL === "about:blank") return;
        var sheets = d.querySelectorAll('link[rel="stylesheet"]');
        for (var i = 0; i < sheets.length; i++) {
          if (sheets[i].href.indexOf(location.origin) === 0 && sheets[i].media !== "print" && !sheets[i].sheet) return;
        }
        finish();
      } catch (e) { clearInterval(poll); }  // can't look inside: the load event will do
    }, 40);
  }

  function wikiCard(j) {
    var card = document.createElement("div");
    card.className = "peek-wiki";
    function add(tag, cls, text) {
      if (!text) return;
      var el = document.createElement(tag);
      el.className = cls;
      el.textContent = text;
      card.appendChild(el);
    }
    add("p", "peek-kicker", "Wikipedia");
    if (j.thumbnail && j.thumbnail.source) {
      var img = document.createElement("img");
      img.alt = "";
      img.src = j.thumbnail.source;
      if (j.thumbnail.width) { img.width = j.thumbnail.width; img.height = j.thumbnail.height; }
      card.appendChild(img);
    }
    add("p", "peek-title", j.title);
    add("p", "peek-desc", j.description);
    add("p", "peek-extract", j.extract);
    return card;
  }

  // fetch what the link points to, out of sight; show it only if no later hover has overtaken it
  function loadPeek(t) {
    var seq = ++peekSeq;
    var box = peekBox(t.root);
    Array.prototype.slice.call(box.querySelectorAll(".loading")).forEach(function (el) { el.remove(); });
    var cur = box.querySelector(".peek-body");
    if (cur && cur.dataset.src === t.src) { showPeek(t, cur); return; }
    if (!peek) fitPeek(t.root);  // so the page is laid out at the rail's width while it loads
    function ready(body) {
      if (seq !== peekSeq || peekWait !== t.link || !body.isConnected) { body.remove(); return; }
      showPeek(t, body);
    }
    if (t.kind === "page") {
      var frame = document.createElement("iframe");
      frame.className = "peek-body loading";
      frame.dataset.src = t.src;
      frame.setAttribute("sandbox", "allow-same-origin");  // no scripts; same-origin only so dress() can reach in
      frame.setAttribute("scrolling", "no");
      frame.tabIndex = -1;
      frame.title = "Preview";
      frame.src = t.src + "#peek";  // lets the page's own stylesheet know it's being shown as a preview
      box.insertBefore(frame, box.firstChild);
      whenReady(frame, function () { dress(frame); ready(frame); });
    } else {
      var got = wiki[t.src] || (wiki[t.src] = fetch(t.src, { headers: { Accept: "application/json" } }).then(function (r) {
        if (!r.ok) throw 0;
        return r.json();
      }));
      got.then(function (j) {
        if (seq !== peekSeq || peekWait !== t.link || !j || !j.extract) return;
        var card = wikiCard(j);
        card.classList.add("peek-body", "loading");
        card.dataset.src = t.src;
        box.insertBefore(card, box.firstChild);
        ready(card);
      }).catch(function () {});
    }
  }

  function showPeek(t, body) {
    clearTimeout(peekLeave);
    var root = t.root, box = peekEl;
    // a link inside a note or figure that's in the margin: the preview goes right under (or over) it
    var host = t.link.closest(".note, figure.plate");
    while (host && !host.style.top) host = host.parentElement.closest(".note, figure.plate");
    if (summoned && summoned.item !== host) release();
    if (peek && peek.host && peek.host !== host) peek.host.classList.remove("peek-host");

    Array.prototype.slice.call(box.querySelectorAll(".peek-body")).forEach(function (el) { if (el !== body) el.remove(); });
    body.classList.remove("loading");
    box.classList.toggle("wiki", t.kind === "wiki");
    var go = box.querySelector(".peek-go");
    go.href = t.link.href;
    go.target = t.link.target;
    go.rel = t.link.rel;
    fitPeek(root);

    var rbox = root.getBoundingClientRect();
    var railTop = root.querySelector(".rail").getBoundingClientRect().top - rbox.top;
    var h = box.offsetHeight;
    var viewTop = -rbox.top + 12, viewBottom = window.innerHeight - rbox.top - 12;
    var want;
    if (host) {
      var hr = host.getBoundingClientRect();
      want = hr.bottom - rbox.top + GAP;
      var above = hr.top - rbox.top - GAP - h;
      if (want + h > viewBottom && above >= Math.max(viewTop, railTop)) want = above;
    } else {
      // level with the line of the link the pointer is on, but kept on screen
      var rects = t.link.getClientRects(), line = rects[0] || t.link.getBoundingClientRect();
      for (var i = 0; i < rects.length; i++) if (pointerY >= rects[i].top - 2 && pointerY <= rects[i].bottom + 2) line = rects[i];
      var markTop = line.top - rbox.top;
      want = markTop - 4;
      if (want + h > viewBottom) want = Math.max(viewTop, viewBottom - h);
      want = Math.min(want, markTop, root.offsetHeight - h);
      want = Math.max(railTop, want);
      // a link a line or two away from the last one: stay put rather than hop
      var was = peek && !peek.host && peek.root === root ? parseFloat(box.style.top) : NaN;
      if (Math.abs(was - want) < 56 && was >= viewTop && was + h <= viewBottom) want = was;
    }
    box.style.top = want + "px";
    if (host) host.classList.add("peek-host");
    root.classList.remove("releasing");
    root.classList.add("summoning");
    box.classList.add("open");
    peek = { root: root, link: t.link, host: host };
  }

  // put the preview away; anything on its way for the link under the pointer may still arrive
  function hidePeek() {
    clearTimeout(peekLeave);
    if (!peek) return;
    var root = peek.root;
    if (peek.host) peek.host.classList.remove("peek-host");
    peekEl.classList.remove("open");
    peek = null;
    if (!summoned) root.classList.remove("summoning");
  }

  // put it away and drop whatever was still loading
  function closePeek() {
    clearTimeout(peekTimer);
    peekWait = null;
    peekSeq++;
    hidePeek();
  }

  function wirePeek() {
    var canHover = window.matchMedia("(hover: hover)");
    document.addEventListener("mouseover", function (e) {
      if (!canHover.matches || layout !== "wide") return;
      pointerY = e.clientY;
      if (peek && (peekEl.contains(e.target) || peek.link.contains(e.target))) clearTimeout(peekLeave);
      var t = peekTarget(e.target);
      var link = t && t.link;
      if (link === peekWait) return;
      clearTimeout(peekTimer);
      peekWait = link;
      if (!link || (peek && peek.link === link)) return;
      // only once the pointer has rested on the link; passing over it loads nothing
      peekTimer = setTimeout(function () { if (peekWait === link) loadPeek(t); }, 240);
    });
    document.addEventListener("mouseout", function (e) {
      if (!peek) return;
      function inside(n) { return peekEl.contains(n) || peek.link.contains(n); }
      if (e.relatedTarget && inside(e.relatedTarget)) return;
      if (!inside(e.target)) return;
      clearTimeout(peekLeave);
      peekLeave = setTimeout(hidePeek, 320);  // long enough to cross the text to the margin
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
