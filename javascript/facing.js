/* Theme switch for the Facing Pages layout: ○ light · ● dark · ◐ follow the device (the default).
   The choice is stored under the same "theme" key the rest of the site uses. */
(function () {
  "use strict";
  var root = document.documentElement;

  function current() {
    try { return localStorage.getItem("theme") || "system"; } catch (e) { return "system"; }
  }

  function apply(mode) {
    if (mode === "light" || mode === "dark") root.setAttribute("data-theme", mode);
    else root.removeAttribute("data-theme");
    document.querySelectorAll("[data-mode]").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.mode === mode));
    });
    if (window.FacingPages) window.FacingPages.place();
  }

  apply(current());

  document.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest("[data-mode]");
    if (!b) return;
    try { localStorage.setItem("theme", b.dataset.mode); } catch (err) {}
    apply(b.dataset.mode);
  });
})();

/* Links that leave the site open in a new tab, so the page you were reading stays where it was.
   Links between posts still turn the page in place. */
(function () {
  "use strict";
  document.querySelectorAll("a[href]").forEach(function (a) {
    if (!/^https?:$/.test(a.protocol) || a.origin === location.origin || a.target) return;
    a.target = "_blank";
    a.rel = (a.rel ? a.rel + " " : "") + "noopener";
  });
})();
