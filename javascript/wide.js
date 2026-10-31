/* wide.js — the Facing Pages engine.
 *
 * One markup, two layouts:
 *   narrow (phone, folded Duo): notes sit in the text, right after the paragraph that cites them
 *   wide   (unfolded Duo, laptop): notes (and, if asked, figures) move to a rail
 *          beside the text, each level with the line that cites it
 *
 * When the window crosses the breakpoint (unfolding), the switch runs inside a
 * View Transition, so every note travels from its spot in the text to the margin.
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

  /* --- name everything that should travel, only for the unfold itself; with no names at rest,
         moving to another page is one soft crossfade instead of pieces flying about --- */
  function nameTravellers(on) {
    document.querySelectorAll(".note").forEach(function (n) {
      n.style.viewTransitionName = on ? "note-" + (n.dataset.n || n.id) : "";
    });
    document.querySelectorAll("figure.plate").forEach(function (f, i) {
      f.style.viewTransitionName = on ? "plate-" + i : "";
    });
    document.querySelectorAll("[data-vt]").forEach(function (el) {
      el.style.viewTransitionName = on ? el.dataset.vt : "";
    });
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
        if (el.classList.contains("note") || el.classList.contains("cover") || el.dataset.marked) return;
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
    root.classList.remove("summoning");
    summoned = null;
    pinned = false;
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

  function wireSummon() {
    var finePointer = window.matchMedia("(hover: hover)");
    document.addEventListener("mouseover", function (e) {
      if (!finePointer.matches || layout !== "wide") return;
      var t = triggerFor(e.target);
      if (t) { summon(t.trigger, t.item); return; }
      if (summoned && summoned.item.contains(e.target)) clearTimeout(leaveTimer);
    });
    document.addEventListener("mouseout", function (e) {
      if (!summoned || pinned) return;
      var to = e.relatedTarget;
      if (to && (summoned.trigger.contains(to) || summoned.item.contains(to))) return;
      var from = e.target;
      if (!(summoned.trigger.contains(from) || summoned.item.contains(from))) return;
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

  /* --- the switch --- */
  function apply(next) {
    layout = next;
    doc.setAttribute("data-layout", next);
    readHinge();
    place();
    document.dispatchEvent(new CustomEvent("wide:layout", { detail: next }));
  }

  function switchTo(next, animate) {
    if (next === layout) { place(); return; }
    if (!animate || reduce.matches) { apply(next); return; }
    doc.setAttribute("data-going", next);
    if (document.startViewTransition) {
      nameTravellers(true);
      var t = document.startViewTransition(function () { apply(next); });
      t.finished.finally(function () { doc.removeAttribute("data-going"); nameTravellers(false); });
    } else {
      apply(next);
      fallback();
      setTimeout(function () { doc.removeAttribute("data-going"); }, 700);
    }
  }

  /* browsers without View Transitions still get a soft arrival */
  function fallback() {
    if (!Element.prototype.animate) return;
    placed(document).forEach(function (el, i) {
      el.animate([{ opacity: 0, transform: "translateX(-18px)" }, { opacity: 1, transform: "none" }],
        { duration: 480, delay: 60 * i, easing: "cubic-bezier(.2,.8,.2,1)", fill: "backwards" });
    });
    document.querySelectorAll("[data-vt]").forEach(function (el, i) {
      el.animate([{ opacity: 0.35 }, { opacity: 1 }], { duration: 420, delay: 40 * i, fill: "backwards" });
    });
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
      switchTo(wanted(), true);
    });
  }

  function boot() {
    markFigures();
    wireNotes();
    wireSummon();
    apply(wanted());
    // show the margin once, all at once, after the fonts that decide where everything goes
    var shown = false;
    function show() {
      if (shown) return;
      shown = true;
      place();
      document.querySelectorAll("[data-wide-root]").forEach(function (r) {
        r.classList.add("ready", "revealing");
        setTimeout(function () { r.classList.remove("revealing"); }, 400);
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
