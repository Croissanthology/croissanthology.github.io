/* ============================================================
   LE MONDIAL, POUR MARGOT — interactions
   Vanilla JS. Consumes the global MONDIAL object from data.js.
   ============================================================ */

(function () {
"use strict";

const $ = (sel, root) => (root || document).querySelector(sel);
const $$ = (sel, root) => Array.from((root || document).querySelectorAll(sel));
const SVG_NS = "http://www.w3.org/2000/svg";
const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function svgEl(tag, attrs, parent) {
  const el = document.createElementNS(SVG_NS, tag);
  for (const k in attrs) el.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(el);
  return el;
}

function htmlEl(tag, cls, html, parent) {
  const el = document.createElement(tag);
  if (cls) el.className = cls;
  if (html != null) el.innerHTML = html;
  if (parent) parent.appendChild(el);
  return el;
}

const esc = (s) => String(s == null ? "" : s)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

/* ---------- theme toggle ---------- */

(function themeInit() {
  const btn = $("#theme-toggle");
  const stored = localStorage.getItem("mondial-theme");
  if (stored) document.documentElement.setAttribute("data-theme", stored);
  btn.addEventListener("click", () => {
    const cur = document.documentElement.getAttribute("data-theme") ||
      (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    const next = cur === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("mondial-theme", next);
  });
})();

/* ---------- reveal on scroll ---------- */

const revealObs = new IntersectionObserver((entries) => {
  entries.forEach((e) => { if (e.isIntersecting) { e.target.classList.add("in"); revealObs.unobserve(e.target); } });
}, { threshold: 0.12 });
function observeReveals(root) { $$(".reveal", root).forEach((el) => revealObs.observe(el)); }

/* ---------- bubble tooltip ---------- */

const bubble = $("#bubble");
let bubbleOwner = null;

function showBubble(anchorRect, title, text) {
  bubble.innerHTML = (title ? `<div class="b-title">${esc(title)}</div>` : "") + esc(text);
  bubble.classList.add("show");
  const pad = 10;
  const bw = Math.min(270, window.innerWidth - 2 * pad);
  bubble.style.maxWidth = bw + "px";
  // measure after content set
  const bh = bubble.offsetHeight || 80;
  let x = anchorRect.left + anchorRect.width / 2 - bubble.offsetWidth / 2;
  x = Math.max(pad, Math.min(x, window.innerWidth - bubble.offsetWidth - pad));
  let y = anchorRect.top - bh - 12;
  if (y < pad) y = anchorRect.bottom + 12;
  bubble.style.left = x + window.scrollX + "px";
  bubble.style.top = y + window.scrollY + "px";
}
function hideBubble() { bubble.classList.remove("show"); bubbleOwner = null; }
document.addEventListener("pointerdown", (e) => {
  if (!bubble.contains(e.target) && (!bubbleOwner || !bubbleOwner.contains(e.target))) hideBubble();
});
window.addEventListener("scroll", hideBubble, { passive: true });

function bindBubble(el, title, text) {
  const open = (ev) => {
    ev.stopPropagation();
    if (bubbleOwner === el && bubble.classList.contains("show")) { hideBubble(); return; }
    bubbleOwner = el;
    showBubble(el.getBoundingClientRect(), title, text);
  };
  el.addEventListener("pointerdown", open);
  el.addEventListener("keydown", (ev) => { if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); open(ev); } });
  if (!el.hasAttribute("tabindex")) el.setAttribute("tabindex", "0");
}

/* ---------- hero ball ---------- */

(function heroBall() {
  const ball = $("#hero-ball");
  let kicks = 0;
  const kick = () => {
    if (reducedMotion) return;
    ball.classList.remove("kicked");
    void ball.getBoundingClientRect(); // reflow to restart animation
    ball.classList.add("kicked");
    kicks++;
    if (kicks === 3) {
      const cue = $(".scroll-cue");
      if (cue) cue.textContent = "GOAL! ok, on descend maintenant ↓";
    }
  };
  ball.addEventListener("pointerdown", kick);
  ball.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); kick(); } });
})();

/* ============================================================
   PITCH DRAWING HELPERS
   ============================================================ */

/** Draw pitch furniture into an svg (vertical orientation, attacking up). */
function drawPitch(svg, W, H, opts) {
  opts = opts || {};
  const line = "var(--pitch-line)";
  const g = svgEl("g", { fill: "none", stroke: line, "stroke-width": 2 }, svg);
  // outer boundary
  svgEl("rect", { x: 8, y: 8, width: W - 16, height: H - 16, rx: 4 }, g);
  if (!opts.halfOnly) {
    // halfway line + center circle
    svgEl("line", { x1: 8, y1: H / 2, x2: W - 8, y2: H / 2 }, g);
    svgEl("circle", { cx: W / 2, cy: H / 2, r: 34 }, g);
    svgEl("circle", { cx: W / 2, cy: H / 2, r: 2.5, fill: line }, g);
  }
  // boxes top (opponent goal) and bottom (our goal)
  const boxW = W * 0.62, box6W = W * 0.34;
  const drawBox = (yEdge, dir) => {
    svgEl("rect", { x: (W - boxW) / 2, y: dir > 0 ? yEdge : yEdge - 58, width: boxW, height: 58 }, g);
    svgEl("rect", { x: (W - box6W) / 2, y: dir > 0 ? yEdge : yEdge - 22, width: box6W, height: 22 }, g);
    svgEl("circle", { cx: W / 2, cy: dir > 0 ? yEdge + 42 : yEdge - 42, r: 2.5, fill: line }, g);
    // goal mouth
    svgEl("rect", { x: (W - 44) / 2, y: dir > 0 ? yEdge - 7 : yEdge, width: 44, height: 7, fill: line, opacity: .85 }, g);
  };
  drawBox(8, 1);
  if (!opts.halfOnly) drawBox(H - 8, -1);
  return g;
}

/** A tappable player dot. cx/cy in svg coords. */
function playerDot(svg, cx, cy, label, fill, r) {
  const gp = svgEl("g", { class: "player-dot", transform: `translate(${cx},${cy})`, tabindex: 0, role: "button" }, svg);
  svgEl("circle", { class: "body", cx: 0, cy: 0, r: r || 13, fill: fill || "var(--copper)", stroke: "var(--pitch-line)", "stroke-width": 2 }, gp);
  if (label) svgEl("text", {
    x: 0, y: 1, "text-anchor": "middle", "dominant-baseline": "middle",
    "font-size": 10, "font-weight": 600, fill: "var(--ground)", "font-family": "var(--font-body)"
  }, gp).textContent = label;
  return gp;
}

/* ============================================================
   CHAPTER 0 — pitch anatomy
   ============================================================ */

(function anatomy() {
  const svg = $("#anatomy-pitch");
  const W = 340, H = 500;
  const zones = [
    { y: 8, h: 158, name: "The attacking third", text: "The danger zone — closest to the goal you're attacking. Chances are created and buried here. Defenders call it 'the place where mistakes cost you the World Cup'." },
    { y: 166, h: 168, name: "The midfield", text: "The engine room. Whoever controls the middle controls the match's tempo — like controlling the conversation at dinner." },
    { y: 334, h: 158, name: "The defensive third", text: "Home territory, in front of your own goal. The rule here: safety first, no fancy business, clear the ball if in doubt." },
  ];
  zones.forEach((z) => {
    const r = svgEl("rect", { x: 8, y: z.y, width: W - 16, height: z.h, fill: "transparent", stroke: "none" }, svg);
    r.style.cursor = "pointer";
    bindBubble(r, z.name, z.text);
  });
  drawPitch(svg, W, H);

  const feats = [
    { x: W / 2, y: 50, name: "The penalty box", text: "The 16-meter rectangle. Foul an attacker inside it and the referee awards a penalty: one shooter, one goalkeeper, eleven meters, pure theatre." },
    { x: W / 2, y: 250, name: "The center circle", text: "Where every match (and every half) begins with kick-off. Opponents must stay out of the circle until the first touch." },
    { x: 24, y: 480, name: "The corner", text: "If a defender knocks the ball over their own goal-line, the attackers get a corner kick — a free cross into the box, and mayhem." },
  ];
  feats.forEach((f) => {
    const c = svgEl("circle", { cx: f.x, cy: f.y, r: 11, fill: "color-mix(in srgb, var(--copper) 65%, transparent)", stroke: "var(--pitch-line)", "stroke-width": 2 }, svg);
    c.style.cursor = "pointer";
    if (!reducedMotion) {
      const a = svgEl("animate", { attributeName: "r", values: "10;13;10", dur: "2.6s", repeatCount: "indefinite" }, c);
    }
    bindBubble(c, f.name, f.text);
  });

  const posDots = [
    { x: W / 2, y: 455, label: "GK", name: "Goalkeeper — le gardien", text: "The only player allowed to use hands (inside their own box). Half acrobat, half psychologist: a keeper spends 89 minutes waiting and 1 minute deciding the match." },
    { x: W / 2 - 80, y: 380, label: "DF", name: "Defender — le défenseur", text: "Bodyguards of the goal. Center-backs are the tall towers who win headers; full-backs patrol the sides and sneak forward to attack when nobody's looking." },
    { x: W / 2 + 60, y: 250, label: "MF", name: "Midfielder — le milieu", text: "The connectors. They win the ball back, keep it moving, and set the rhythm. Every great team has a midfielder who seems to have a map of the pitch in their head." },
    { x: W / 2 + 40, y: 105, label: "FW", name: "Forward — l'attaquant", text: "The goalscorers, paid in glory. Wingers hug the sidelines and dribble; the striker (number 9, traditionally) lives in the box, waiting for one half-second of freedom." },
  ];
  posDots.forEach((p) => {
    const dot = playerDot(svg, p.x, p.y, p.label, "var(--copper)");
    bindBubble(dot, p.name, p.text);
  });
})();

/* ---------- rules flip cards ---------- */

const RULES = [
  { q: "90 minutes… or is it?", a: "Two halves of 45, plus 'stoppage time' the referee adds for interruptions. In knockout games, a draw means 30 more minutes of extra time — then the dreaded penalty shootout." },
  { q: "Yellow card, red card", a: "Yellow = official warning, for a cynical foul or theatrical time-wasting. Two yellows (or one horror foul) = red: you're off, no replacement, your team plays with 10. National tragedy." },
  { q: "Why can't they use their hands?", a: "That's the whole point — in 1863 the English wrote it down to split from rugby. Handle the ball deliberately and it's a free kick; do it in your own box and it's a penalty." },
  { q: "What's a 'cap'?", a: "One appearance for your national team = one cap (England once literally handed out embroidered caps). 100+ caps makes you national furniture." },
  { q: "Le penalty", a: "A one-on-one duel from 11 meters, awarded for a foul in the box. About 3 in 4 go in — which makes the misses unforgettable." },
  { q: "Substitutes", a: "Each team may replace up to 5 players during the match. Once you're off, you're off — no coming back, even if you sulk." },
];

(function rulesCards() {
  const host = $("#rules-facts");
  RULES.forEach((r) => host.appendChild(makeFlipCard(r.q, r.a)));
})();

function makeFlipCard(q, a) {
  const b = htmlEl("button", "fact", null);
  b.setAttribute("aria-expanded", "false");
  b.innerHTML = `<span class="f-inner">
    <span class="f-face f-front"><span class="f-hint">tap</span><span class="f-q">${esc(q)}</span></span>
    <span class="f-face f-back">${esc(a)}</span>
  </span>`;
  b.addEventListener("click", () => {
    b.classList.toggle("flipped");
    b.setAttribute("aria-expanded", b.classList.contains("flipped") ? "true" : "false");
  });
  return b;
}

/* ============================================================
   OFFSIDE INTERACTIVE
   ============================================================ */

(function offside() {
  const svg = $("#offside-pitch");
  const W = 340, H = 240;
  // horizontal half-pitch: goal on the right
  const g = svgEl("g", { fill: "none", stroke: "var(--pitch-line)", "stroke-width": 2 }, svg);
  svgEl("rect", { x: 8, y: 8, width: W - 16, height: H - 16, rx: 4 }, g);
  svgEl("rect", { x: W - 66, y: (H - 130) / 2, width: 58, height: 130 }, g); // box
  svgEl("rect", { x: W - 8, y: (H - 56) / 2, width: 6, height: 56, fill: "var(--pitch-line)" }, g); // goal
  // players
  const DEF_X = 232; // last defender
  const defLine = svgEl("line", { x1: DEF_X, y1: 12, x2: DEF_X, y2: H - 12, stroke: "var(--rouge)", "stroke-width": 1.5, "stroke-dasharray": "5 5", opacity: .8 }, svg);
  playerDot(svg, W - 26, H / 2, "GK", "var(--ink-2)", 11);
  playerDot(svg, DEF_X, 78, "DF", "var(--ink-2)", 11);
  playerDot(svg, DEF_X - 26, 168, "DF", "var(--ink-2)", 11);
  const passer = playerDot(svg, 60, 170, "", "var(--copper)", 11);
  svgEl("text", { x: 22, y: 202, "text-anchor": "start", "font-size": 11, fill: "var(--pitch-line)", "font-family": "var(--font-body)" }, svg).textContent = "your teammate (has the ball)";
  const attacker = playerDot(svg, 120, 70, "", "var(--copper-2)", 12);
  const flag = svgEl("text", { x: 0, y: 0, "font-size": 20, "text-anchor": "middle" }, svg);
  flag.textContent = "🚩";
  flag.setAttribute("opacity", 0);

  const slider = $("#offside-slider");
  const verdict = $("#offside-verdict");
  function update() {
    const t = Number(slider.value) / 100;
    const x = 90 + t * (W - 130); // from 90 to ~300
    attacker.setAttribute("transform", `translate(${x},70)`);
    const off = x > DEF_X;
    flag.setAttribute("x", x);
    flag.setAttribute("y", 38);
    flag.setAttribute("opacity", off ? 1 : 0);
    verdict.innerHTML = off
      ? `<span class="flag">🚩 OFFSIDE — you're past the last defender. The café groans.</span>`
      : `<span class="ok">✓ Onside — the pass is legal. <span class="fr">Allez !</span></span>`;
    defLine.setAttribute("opacity", off ? 1 : .5);
  }
  slider.addEventListener("input", update);
  update();
})();

/* ============================================================
   FORMATION MORPHER
   ============================================================ */

/** Returns [{x,y,role}] for a formation string like "4-3-3", on a W×H half-up pitch. */
function formationCoords(fstr, W, H) {
  const rows = fstr.split("-").map(Number);
  const out = [{ x: W / 2, y: H - 42, role: "GK" }];
  const bandTop = 46, bandBottom = H - 88;
  const n = rows.length;
  rows.forEach((count, i) => {
    // i=0 defenders (near bottom) … last row = forwards (top)
    const y = bandBottom - (i * (bandBottom - bandTop)) / Math.max(1, n - 1);
    for (let k = 0; k < count; k++) {
      const x = (W * (k + 1)) / (count + 1);
      out.push({ x, y, role: i === 0 ? "DF" : i === n - 1 ? "FW" : "MF" });
    }
  });
  return out;
}

const FORMATIONS = {
  "4-3-3": { caption: "The entertainer's shape — three forwards stretch the defense wide, and the wingers live for one-on-one duels. Spain and France both start from here. Personality: confident, likes the ball." },
  "4-2-3-1": { caption: "The pragmatist's shape — two midfield bodyguards protect the defense, one creative soul (the '10') floats behind a lone striker. Personality: organized, sensible shoes, dangerous anyway." },
  "3-5-2": { caption: "The gambler's shape — only three defenders, but the wide midfielders sprint up AND down all match (the hardest job in football). Personality: bold, cardio-obsessed." },
  "4-4-2": { caption: "The classic — two banks of four, two strikers hunting as a pair. How everyone's grandfather says football should be played. Personality: nostalgic, honest, loves a long ball." },
  "5-4-1": { caption: "The bus — 'parking the bus' means everyone defends. Five at the back, one forward left alone up front like a lighthouse keeper. Personality: survivor. Often seen when protecting a 1-0 lead." },
};

(function formationMorph() {
  const svg = $("#formation-pitch");
  const W = 340, H = 440;
  drawPitch(svg, W, H, { halfOnly: true });
  svgEl("line", { x1: 8, y1: H - 8, x2: W - 8, y2: H - 8, stroke: "var(--pitch-line)", "stroke-width": 2 }, svg);

  const dots = [];
  for (let i = 0; i < 11; i++) {
    const gp = svgEl("g", { class: "player-dot" }, svg);
    gp.style.transition = reducedMotion ? "none" : "transform .8s cubic-bezier(.3,.7,.2,1)";
    svgEl("circle", { class: "body", r: 13, fill: i === 0 ? "var(--ink-2)" : "var(--copper)", stroke: "var(--pitch-line)", "stroke-width": 2 }, gp);
    const t = svgEl("text", { y: 1, "text-anchor": "middle", "dominant-baseline": "middle", "font-size": 9, "font-weight": 600, fill: "var(--ground)", "font-family": "var(--font-body)" }, gp);
    dots.push({ gp, t });
  }

  const btnHost = $("#formation-buttons");
  const cap = $("#formation-caption");
  function apply(name) {
    const coords = formationCoords(name, W, H);
    coords.forEach((c, i) => {
      dots[i].gp.setAttribute("transform", `translate(${c.x},${c.y})`);
      dots[i].t.textContent = c.role;
    });
    cap.innerHTML = `<strong>${esc(name)}</strong> — ${esc(FORMATIONS[name].caption)}`;
    $$("button", btnHost).forEach((b) => b.setAttribute("aria-pressed", b.dataset.f === name ? "true" : "false"));
  }
  Object.keys(FORMATIONS).forEach((name) => {
    const b = htmlEl("button", "", esc(name), btnHost);
    b.dataset.f = name;
    b.addEventListener("click", () => apply(name));
  });
  apply("4-3-3");
})();

/* ============================================================
   TOURNAMENT SECTION (data-driven)
   ============================================================ */

(function tournament() {
  const T = MONDIAL.tournament;
  $("#tournament-sub").textContent = T.sub;
  const prose = $("#tournament-prose");
  T.prose.forEach((p, i) => htmlEl("p", i === 0 ? "lede dropcap" : "", p, prose));

  // funnel
  const funnel = $("#format-funnel");
  const stages = [
    [48, "teams arrive — 12 groups of 4, everyone plays 3 matches"],
    [32, "survive the groups → sudden-death knockouts begin"],
    [16, "round of 16 — one bad afternoon and you fly home"],
    [8, "quarterfinals — where we are NOW (your six teams are all here!)"],
    [4, "semifinals"],
    [2, "the final — MetLife Stadium, New York area, 19 July"],
    [1, "champion of the world, for four whole years"],
  ];
  stages.forEach(([n, capTxt]) => {
    const row = htmlEl("div", "f-row", null, funnel);
    const bar = htmlEl("div", "f-bar tnum", esc(String(n)), row);
    bar.style.width = "34px";
    bar.style.setProperty("--pct", Math.round((n / 48) * 100) + "%");
    if (n <= 8) bar.style.color = "var(--ink)";
    htmlEl("div", "f-cap", esc(capTxt), row);
    row.dataset.target = Math.max(10, Math.round((n / 48) * 100)) + "%";
    row._bar = bar;
  });
  const funnelObs = new IntersectionObserver((es) => {
    es.forEach((e) => {
      if (!e.isIntersecting) return;
      $$(".f-row", funnel).forEach((row, i) => {
        setTimeout(() => { row._bar.style.width = `max(34px, calc(${row.dataset.target} * .62))`; }, i * 120);
      });
      funnelObs.disconnect();
    });
  }, { threshold: 0.3 });
  funnelObs.observe(funnel);

  // bracket
  drawBracket($("#bracket-svg"), MONDIAL.bracket);
  $("#bracket-note").innerHTML = T.bracketNote;

  // storylines
  const host = $("#storyline-facts");
  T.storylines.forEach((s) => host.appendChild(makeFlipCard(s.q, s.a)));
})();

function drawBracket(svg, B) {
  const W = 760, rowH = 64, pad = 10;
  const qfs = B.qfs;
  const H = pad * 2 + qfs.length * rowH + 30;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);

  const teamSet = new Set(MONDIAL.teams.map((t) => t.name));
  const colQF = 10, colSF = 300, colF = 560;

  function matchBox(x, y, w, m) {
    const g = svgEl("g", {}, svg);
    svgEl("rect", { x, y, width: w, height: 46, rx: 9, fill: "var(--card)", stroke: "var(--hairline)" }, g);
    const line = (team, dy, score, isWinner) => {
      const known = team && teamSet.has(team);
      const t = svgEl("text", {
        x: x + 12, y: y + dy, "font-size": 13.5, "font-family": "var(--font-body)",
        "font-weight": known || isWinner ? 600 : 400,
        fill: known ? "var(--copper)" : "var(--ink)",
      }, g);
      t.textContent = team || "—";
      if (score != null) {
        const s = svgEl("text", { x: x + w - 12, y: y + dy, "font-size": 13.5, "text-anchor": "end", "font-family": "var(--font-body)", "font-weight": 600, fill: isWinner ? "var(--ink)" : "var(--ink-3)" }, g);
        s.textContent = score;
      }
    };
    line(m.a, 18, m.scoreA, m.winner === "a");
    line(m.b, 37, m.scoreB, m.winner === "b");
    if (m.tag) {
      svgEl("text", { x, y: y - 5, "font-size": 10.5, "font-family": "var(--font-body)", "letter-spacing": "1.5", fill: "var(--ink-3)" }, g)
        .textContent = m.tag.toUpperCase();
    }
    return { midY: y + 23, right: x + w };
  }

  const boxW = 240;
  const outs = qfs.map((m, i) => matchBox(colQF, pad + 16 + i * rowH, boxW, m));

  // connectors QF -> SF
  const sfY = [pad + 16 + rowH * 0.5, pad + 16 + rowH * 2.5];
  const conn = (x1, y1, x2, y2) =>
    svgEl("path", { d: `M ${x1} ${y1} H ${(x1 + x2) / 2} V ${y2} H ${x2}`, fill: "none", stroke: "var(--hairline)", "stroke-width": 2 }, svg);
  outs.forEach((o, i) => conn(o.right, o.midY, colSF, sfY[Math.floor(i / 2)] + 23));
  const sfOuts = B.sfs.map((m, i) => matchBox(colSF, sfY[i], boxW, m));
  sfOuts.forEach((o) => conn(o.right, o.midY, colF, pad + 16 + rowH * 1.5 + 23));
  matchBox(colF, pad + 16 + rowH * 1.5, 190, B.final);
}

/* ============================================================
   TEAM CHAPTERS
   ============================================================ */

const RATING_LABELS = [
  ["possession", "Keeps the ball"],
  ["pressing", "Hunts in packs"],
  ["counterAttack", "Lightning counters"],
  ["physicality", "Muscle"],
  ["flair", "Flair & magic"],
  ["defensiveSolidity", "Hard to score on"],
];

function renderMeters(host, ratings, accent, ratingsB, accentB) {
  host.innerHTML = "";
  RATING_LABELS.forEach(([key, label]) => {
    const m = htmlEl("div", "meter", null, host);
    htmlEl("div", "m-label", esc(label), m);
    const track = htmlEl("div", "m-track", null, m);
    const fill = htmlEl("div", "m-fill", null, track);
    fill.style.background = accent;
    fill.dataset.w = (ratings[key] || 0) * 10 + "%";
    let valTxt = String(ratings[key] || 0);
    if (ratingsB) {
      const fb = htmlEl("div", "m-fill b", null, track);
      fb.style.background = accentB;
      fb.dataset.w = (ratingsB[key] || 0) * 10 + "%";
      track.style.height = "20px";
      track.style.background = "transparent";
      fill.style.top = "0"; fill.style.height = "6px";
      valTxt = "";
    }
    htmlEl("div", "m-val tnum", esc(valTxt), m);
  });
  // animate when visible
  const obs = new IntersectionObserver((es) => {
    es.forEach((e) => {
      if (!e.isIntersecting) return;
      $$(".m-fill", host).forEach((f) => { f.style.width = f.dataset.w; });
      obs.disconnect();
    });
  }, { threshold: 0.25 });
  obs.observe(host);
}

/** Build a team's lineup pitch: formation dots, key players attached to slots. */
function renderLineup(frameEl, svg, team, cardHost) {
  const W = 340, H = 440;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  drawPitch(svg, W, H, { halfOnly: true });
  svgEl("line", { x1: 8, y1: H - 8, x2: W - 8, y2: H - 8, stroke: "var(--pitch-line)", "stroke-width": 2 }, svg);

  const coords = formationCoords(team.formationKey, W, H);
  // map positions to slot preference
  const rolesOf = { GK: "GK", CB: "DF", LB: "DF", RB: "DF", LWB: "DF", RWB: "DF", DF: "DF",
    CDM: "MF", CM: "MF", CAM: "MF", MF: "MF", LM: "MF", RM: "MF",
    LW: "FW", RW: "FW", ST: "FW", CF: "FW", FW: "FW" };
  const slots = coords.map((c) => ({ ...c, player: null }));

  // wing preference: LB/LW → left-most, RB/RW → right-most, CAM → highest MF
  function pickSlot(pos) {
    const role = rolesOf[pos] || "MF";
    const free = slots.filter((s) => !s.player && s.role === role);
    if (!free.length) return slots.find((s) => !s.player && s.role !== "GK") || null;
    if (/^L/.test(pos)) return free.reduce((a, b) => (a.x < b.x ? a : b));
    if (/^R/.test(pos)) return free.reduce((a, b) => (a.x > b.x ? a : b));
    if (pos === "ST" || pos === "CF") {
      const c = free.reduce((a, b) => (Math.abs(a.x - W / 2) < Math.abs(b.x - W / 2) ? a : b));
      return c;
    }
    if (pos === "CAM") return free.reduce((a, b) => (a.y < b.y ? a : b));
    if (pos === "CDM") return free.reduce((a, b) => (a.y > b.y ? a : b));
    return free.reduce((a, b) => (Math.abs(a.x - W / 2) < Math.abs(b.x - W / 2) ? a : b));
  }

  const starters = team.keyPlayers.filter((p) => !p.bench).slice(0, 11);
  const bench = team.keyPlayers.filter((p) => p.bench);
  starters.forEach((p) => {
    const slot = pickSlot(p.pos);
    if (slot) slot.player = p; else bench.push(p);
  });

  let activeDot = null;
  function showPlayer(p, dot) {
    if (activeDot) activeDot.classList.remove("is-active");
    activeDot = dot || null;
    if (dot) dot.classList.add("is-active");
    cardHost.className = "player-card card show";
    cardHost.style.setProperty("--accent", team.accent);
    cardHost.innerHTML = `
      <div class="pc-head">
        <span class="pc-name">${esc(p.name)}</span>
        <span class="pc-pos">${esc(p.posLabel || p.pos)}</span>
      </div>
      <div class="pc-meta tnum">${esc(p.club)}${p.age ? " · " + esc(p.age) + " yrs" : ""}${p.num ? " · #" + esc(p.num) : ""}</div>
      <p class="pc-why">${esc(p.why)}</p>`;
  }

  slots.forEach((s) => {
    const isNamed = !!s.player;
    const label = isNamed
      ? (s.player.num != null ? String(s.player.num) : s.player.name.split(" ").pop().slice(0, 3).toUpperCase())
      : s.role;
    const fill = isNamed ? team.accent : "color-mix(in srgb, var(--ink-2) 70%, transparent)";
    const dot = playerDot(svg, s.x, s.y, label, fill, isNamed ? 14 : 11);
    if (isNamed) {
      const nm = svgEl("text", { x: s.x, y: s.y + 26, "text-anchor": "middle", "font-size": 9.5, "font-weight": 600, fill: "var(--pitch-line)", "font-family": "var(--font-body)" }, svg);
      nm.textContent = s.player.name.split(" ").pop();
      dot.addEventListener("pointerdown", (e) => { e.stopPropagation(); showPlayer(s.player, dot); });
      dot.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); showPlayer(s.player, dot); } });
      dot.setAttribute("aria-label", s.player.name);
    } else {
      bindBubble(dot, positionName(s.role), genericRoleText(s.role));
    }
  });

  return { bench, showPlayer };
}

function positionName(role) {
  return { GK: "Goalkeeper", DF: "Defender", MF: "Midfielder", FW: "Forward" }[role] || role;
}
function genericRoleText(role) {
  return {
    GK: "The goalkeeper — the last line, and the only one allowed to use hands.",
    DF: "A defender — one of the bodyguards protecting the goal.",
    MF: "A midfielder — engine-room worker, keeping the machine running.",
    FW: "A forward — employed exclusively to cause chaos near the other goal.",
  }[role];
}

function renderChapters() {
  const host = $("#chapters");
  const navChips = $("#nav-chips");
  const compareAnchor = navChips.querySelector('a[href="#compare"]');

  MONDIAL.teams.forEach((team, idx) => {
    // nav chip
    const chip = htmlEl("a", "chip", `<span class="dot" style="--accent:${team.accent}"></span>${esc(team.name)}`);
    chip.href = `#team-${team.id}`;
    chip.style.setProperty("--accent", team.accent);
    navChips.insertBefore(chip, compareAnchor);

    const sec = htmlEl("section", "chapter", null, host);
    sec.id = `team-${team.id}`;
    sec.style.setProperty("--accent", team.accent);

    const wrap = htmlEl("div", "wrap", null, sec);

    // header
    const head = htmlEl("div", "ch-head reveal", null, wrap);
    htmlEl("p", "ch-index", `Équipe ${["une","deux","trois","quatre","cinq","six"][idx]} / six`, head);
    htmlEl("h2", "display", esc(team.name), head);
    htmlEl("p", "ch-nick", `${esc(team.nickname)}`, head);
    const ribbon = htmlEl("div", "flag-ribbon", null, head);
    team.flag.forEach((c) => { const i = htmlEl("i", "", null, ribbon); i.style.background = c; });

    // identity row: keywords + coach + formation
    const meta = htmlEl("div", "chip-row reveal", null, wrap);
    meta.style.marginBottom = "22px";
    htmlEl("span", "chip card", `<span class="dot"></span>Coach: ${esc(team.coach)}`, meta);
    htmlEl("span", "chip card", `<span class="dot"></span>Shape: ${esc(team.formation)}`, meta);
    team.styleKeywords.forEach((k) => htmlEl("span", "chip card", `<span class="dot"></span>${esc(k)}`, meta));

    // philosophy
    const prose = htmlEl("div", "prose reveal", null, wrap);
    team.philosophy.forEach((p, i) => htmlEl("p", i === 0 ? "dropcap" : "", p, prose));

    // grid: lineup | star + meters
    const grid = htmlEl("div", "ch-grid reveal", null, wrap);
    grid.style.marginTop = "34px";

    const colA = htmlEl("div", "", null, grid);
    htmlEl("p", "block-label", `How they line up — ${esc(team.formation)} · tap a player`, colA);
    const frame = htmlEl("div", "pitch-frame pinstripes", null, colA);
    const svg = svgEl("svg", { "aria-label": `${team.name} lineup` }, frame);
    const cardHost = htmlEl("div", "player-card card", null, colA);
    const { bench, showPlayer } = renderLineup(frame, svg, team, cardHost);
    if (bench.length) {
      const benchRow = htmlEl("div", "chip-row", null, colA);
      benchRow.style.marginTop = "12px";
      htmlEl("span", "block-label", "Also worth knowing:", benchRow).style.margin = "6px 6px 0 0";
      bench.forEach((p) => {
        const b = htmlEl("button", "chip", `<span class="dot" style="--accent:${team.accent}"></span>${esc(p.name)}`, benchRow);
        b.addEventListener("click", () => showPlayer(p, null));
      });
    }

    const colB = htmlEl("div", "", null, grid);
    const star = htmlEl("div", "star-block", null, colB);
    htmlEl("p", "block-label", "La star", star);
    htmlEl("div", "s-name display", esc(team.starPlayer.name), star);
    htmlEl("p", "s-story", team.starPlayer.story, star);

    htmlEl("p", "block-label", "How they play — the six dials", colB).style.marginTop = "26px";
    const metersCard = htmlEl("div", "card", null, colB);
    const meters = htmlEl("div", "meters", null, metersCard);
    renderMeters(meters, team.ratings, team.accent);

    // path
    const pathWrap = htmlEl("div", "reveal", null, wrap);
    pathWrap.style.marginTop = "40px";
    htmlEl("p", "block-label", `Their road so far — Group ${esc(team.path.group)}`, pathWrap);
    const tl = htmlEl("div", "timeline", null, pathWrap);
    team.path.matches.forEach((m) => {
      const item = htmlEl("div", "tl-item" + (m.upcoming ? " upcoming" : ""), null, tl);
      htmlEl("div", "tl-round", esc(m.round), item);
      htmlEl("div", "tl-score", esc(m.fixture), item);
      if (m.note) htmlEl("div", "tl-note", m.note, item);
    });
    htmlEl("p", "callout", team.path.status, pathWrap).style.marginTop = "14px";

    // history + facts
    const histWrap = htmlEl("div", "reveal", null, wrap);
    histWrap.style.marginTop = "36px";
    htmlEl("p", "block-label", "Pedigree — their World Cup story", histWrap);
    const histProse = htmlEl("div", "prose", null, histWrap);
    htmlEl("p", "", team.history, histProse);

    const factsWrap = htmlEl("div", "reveal", null, wrap);
    factsWrap.style.marginTop = "30px";
    htmlEl("p", "block-label", "Le saviez-vous ? — tap to flip", factsWrap);
    const facts = htmlEl("div", "facts", null, factsWrap);
    team.facts.forEach((f) => facts.appendChild(makeFlipCard(f.q, f.a)));
  });
}

/* ============================================================
   COMPARE
   ============================================================ */

function renderCompare() {
  const pickers = $("#compare-pickers");
  const legend = $("#compare-legend");
  const meters = $("#compare-meters");
  const note = $("#compare-note");
  let selA = 0, selB = 5;

  const rowA = htmlEl("div", "chip-row", null, pickers);
  const rowB = htmlEl("div", "chip-row", null, pickers);
  function buildRow(row, getSel, setSel) {
    row.innerHTML = "";
    MONDIAL.teams.forEach((t, i) => {
      const b = htmlEl("button", "chip", `<span class="dot" style="--accent:${t.accent}"></span>${esc(t.name)}`, row);
      b.setAttribute("aria-pressed", getSel() === i ? "true" : "false");
      b.addEventListener("click", () => { setSel(i); update(); });
    });
  }
  function update() {
    if (selA === selB) selB = (selB + 1) % MONDIAL.teams.length;
    buildRow(rowA, () => selA, (i) => (selA = i));
    buildRow(rowB, () => selB, (i) => (selB = i));
    const A = MONDIAL.teams[selA], B = MONDIAL.teams[selB];
    legend.innerHTML = `
      <span class="l-item"><span class="l-swatch" style="background:${A.accent}"></span>${esc(A.name)}</span>
      <span class="l-item"><span class="l-swatch" style="background:${B.accent}"></span>${esc(B.name)}</span>`;
    renderMeters(meters, A.ratings, A.accent, B.ratings, B.accent);
    $$(".m-fill", meters).forEach((f) => { f.style.width = f.dataset.w; });
    note.innerHTML = compareBlurb(A, B);
  }
  update();
}

function compareBlurb(A, B) {
  const dims = RATING_LABELS.map(([k, label]) => ({ k, label, d: (A.ratings[k] || 0) - (B.ratings[k] || 0) }));
  const maxA = dims.reduce((a, b) => (b.d > a.d ? b : a));
  const maxB = dims.reduce((a, b) => (b.d < a.d ? b : a));
  return `Biggest gap: <strong>${esc(A.name)}</strong> wins “${esc(maxA.label.toLowerCase())}” by ${Math.abs(maxA.d)} point${Math.abs(maxA.d) === 1 ? "" : "s"}, while <strong>${esc(B.name)}</strong> takes “${esc(maxB.label.toLowerCase())}” by ${Math.abs(maxB.d)}. Same sport, different religions.`;
}

/* ============================================================
   QUIZ
   ============================================================ */

function renderQuiz() {
  const card = $("#quiz-card");
  const Q = MONDIAL.quiz.questions;
  let step = 0;
  const scores = {};
  MONDIAL.teams.forEach((t) => (scores[t.id] = 0));

  function drawProgress() {
    return `<div class="quiz-progress">${Q.map((_, i) => `<i class="${i < step ? "done" : ""}"></i>`).join("")}</div>`;
  }

  function ask() {
    const q = Q[step];
    card.innerHTML = drawProgress() + `
      <p class="eyebrow">Question ${step + 1} / ${Q.length}</p>
      <p class="quiz-q">${esc(q.q)}</p>
      <div class="quiz-opts"></div>`;
    const opts = $(".quiz-opts", card);
    q.options.forEach((o) => {
      const b = htmlEl("button", "", esc(o.label), opts);
      b.addEventListener("click", () => {
        o.teams.forEach((id) => (scores[id] += o.pts || 1));
        step++;
        if (step < Q.length) ask();
        else result();
      });
    });
  }

  function result() {
    const best = MONDIAL.teams.reduce((a, b) => (scores[b.id] > scores[a.id] ? b : a));
    const blurb = MONDIAL.quiz.results[best.id];
    card.innerHTML = `
      <div class="quiz-result" style="--accent:${best.accent}">
        <p class="eyebrow">Verdict</p>
        <p style="margin: 4px 0 0;">Your team is…</p>
        <p class="qr-team display">${esc(best.name)}</p>
        <div class="flag-ribbon" style="display:inline-flex; height:5px; width:96px; border-radius:3px; overflow:hidden;">
          ${best.flag.map((c) => `<i style="flex:1; background:${c}"></i>`).join("")}
        </div>
        <p style="margin-top: 16px;">${blurb}</p>
        <p style="margin-top: 18px;"><button id="quiz-again">Recommencer</button>
        <a href="#team-${best.id}" style="margin-left: 10px;">Meet your team ↑</a></p>
      </div>`;
    $("#quiz-again").addEventListener("click", () => { step = 0; MONDIAL.teams.forEach((t) => (scores[t.id] = 0)); ask(); });
  }

  ask();
}

/* ============================================================
   PENALTY GAME
   ============================================================ */

function renderPenalty() {
  const svg = $("#pen-svg");
  const W = 340, H = 230;
  // stadium backdrop
  svgEl("rect", { x: 0, y: 0, width: W, height: H, fill: "var(--pitch)" }, svg);
  // goal frame
  const G = { x: 40, y: 40, w: 260, h: 110 };
  svgEl("rect", { x: G.x - 5, y: G.y - 5, width: G.w + 10, height: G.h + 5, fill: "none", stroke: "var(--pitch-line)", "stroke-width": 6, rx: 3 }, svg);
  // net
  const net = svgEl("g", { stroke: "color-mix(in srgb, var(--pitch-line) 40%, transparent)", "stroke-width": 1 }, svg);
  for (let i = 1; i < 13; i++) svgEl("line", { x1: G.x + (G.w / 13) * i, y1: G.y, x2: G.x + (G.w / 13) * i, y2: G.y + G.h }, net);
  for (let i = 1; i < 6; i++) svgEl("line", { x1: G.x, y1: G.y + (G.h / 6) * i, x2: G.x + G.w, y2: G.y + (G.h / 6) * i }, net);
  // ground
  svgEl("rect", { x: 0, y: G.y + G.h, width: W, height: H - G.y - G.h, fill: "color-mix(in srgb, var(--pitch-line) 12%, var(--pitch))" }, svg);

  // keeper (simple figure)
  const keeper = svgEl("g", {}, svg);
  const kBody = svgEl("g", {}, keeper);
  svgEl("circle", { cx: 0, cy: -26, r: 9, fill: "var(--copper-2)" }, kBody);
  svgEl("rect", { x: -8, y: -18, width: 16, height: 30, rx: 7, fill: "var(--copper)" }, kBody);
  svgEl("line", { x1: -8, y1: -12, x2: -24, y2: 2, stroke: "var(--copper)", "stroke-width": 6, "stroke-linecap": "round" }, kBody);
  svgEl("line", { x1: 8, y1: -12, x2: 24, y2: 2, stroke: "var(--copper)", "stroke-width": 6, "stroke-linecap": "round" }, kBody);
  keeper.style.transition = reducedMotion ? "none" : "transform .38s cubic-bezier(.3,.8,.4,1)";
  const keeperHome = `translate(${W / 2},${G.y + G.h - 14})`;
  keeper.setAttribute("transform", keeperHome);

  // ball
  const ball = svgEl("g", {}, svg);
  svgEl("circle", { r: 9, fill: "var(--card)", stroke: "var(--ink)", "stroke-width": 1.5 }, ball);
  svgEl("circle", { r: 3.2, fill: "var(--ink)" }, ball);
  const ballHome = `translate(${W / 2},${H - 16})`;
  ball.setAttribute("transform", ballHome);
  ball.style.transition = reducedMotion ? "none" : "transform .32s cubic-bezier(.2,.6,.3,1)";

  // zones: 3 cols × 2 rows
  const zones = [];
  const cols = 3, rows = 2;
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const zw = G.w / cols, zh = G.h / rows;
    const zx = G.x + c * zw, zy = G.y + r * zh;
    const zg = svgEl("g", { class: "pen-zone", tabindex: 0, role: "button", "aria-label": `Shoot ${r === 0 ? "high" : "low"} ${c === 0 ? "left" : c === 1 ? "center" : "right"}` }, svg);
    svgEl("rect", { x: zx + 3, y: zy + 3, width: zw - 6, height: zh - 6, rx: 8 }, zg);
    zones.push({ el: zg, cx: zx + zw / 2, cy: zy + zh / 2, col: c, row: r });
  }

  const scoreHost = $("#pen-score");
  const msg = $("#pen-msg");
  const resetBtn = $("#pen-reset");
  let shots, goals, busy;

  const CHEERS = ["BUUUUT ! 🎉", "Quel tir, Margot !", "Petit pont, grand moment.", "Elle est au fond ! ⚽", "La lucarne ! Magnifique !"];
  const SAVES = ["Arrêt du gardien… 🧤", "Il l'a lue comme un livre.", "Pas de chance — même les pros ratent.", "Le gardien s'envole… et la prend."];

  function reset() {
    shots = 0; goals = 0; busy = false;
    scoreHost.innerHTML = "";
    for (let i = 0; i < 5; i++) htmlEl("i", "", null, scoreHost);
    msg.textContent = "Cinq tirs. Choisis ton coin.";
    resetBtn.hidden = true;
    keeper.setAttribute("transform", keeperHome);
    ball.setAttribute("transform", ballHome);
  }

  function finish() {
    const lines = goals >= 5 ? "5/5 — parfait. On t'attend en équipe de France. 🇫🇷"
      : goals >= 4 ? `${goals}/5 — sang-froid de pro. Sérieusement.`
      : goals >= 3 ? `${goals}/5 — tu gagnes la plupart des shootouts avec ça.`
      : goals >= 2 ? `${goals}/5 — honorable ! Les tirs au but sont cruels.`
      : `${goals}/5 — c'est exactement pour ça que les joueurs pleurent. Réessaie !`;
    msg.textContent = lines;
    resetBtn.hidden = false;
  }

  zones.forEach((z) => {
    const shoot = () => {
      if (busy || shots >= 5) return;
      busy = true;
      // keeper picks a zone; slightly favors middle-height corners
      const guess = zones[Math.floor(Math.random() * zones.length)];
      const saved = guess.col === z.col && guess.row === z.row;
      // also: shooting center-low is easier to save
      const bonusSave = !saved && z.col === 1 && Math.random() < 0.35;
      const isGoal = !(saved || bonusSave);

      ball.setAttribute("transform", `translate(${z.cx},${z.cy})`);
      const kx = G.x + guess.col * (G.w / 3) + G.w / 6;
      const rot = guess.col === 0 ? -55 : guess.col === 2 ? 55 : 0;
      keeper.setAttribute("transform", `translate(${bonusSave ? z.cx : kx},${G.y + (guess.row === 0 ? 34 : G.h - 24)}) rotate(${bonusSave ? (z.col === 0 ? -55 : 55) : rot})`);

      setTimeout(() => {
        shots++;
        if (isGoal) goals++;
        scoreHost.children[shots - 1].className = isGoal ? "goal" : "miss";
        msg.textContent = isGoal
          ? CHEERS[Math.floor(Math.random() * CHEERS.length)]
          : SAVES[Math.floor(Math.random() * SAVES.length)];
        setTimeout(() => {
          keeper.setAttribute("transform", keeperHome);
          ball.setAttribute("transform", ballHome);
          busy = false;
          if (shots >= 5) finish();
        }, 700);
      }, reducedMotion ? 50 : 400);
    };
    z.el.addEventListener("pointerdown", shoot);
    z.el.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); shoot(); } });
  });

  resetBtn.addEventListener("click", reset);
  reset();
}

/* ============================================================
   BOOT
   ============================================================ */

renderChapters();
renderCompare();
renderQuiz();
renderPenalty();
observeReveals(document);

})();
