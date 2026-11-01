/* Case studies, the small things that help a reader scan. Everything is in the HTML without this script.
   1. The bar from the home page, tabs, and the thinking lens with its dock.
   2. The journey holds one frame; the step in the middle of the screen chooses its recording, which plays once
      and rests on its last frame, where the numbered pins appear.
   3. The opening screen settles as you scroll.
   4. The parts of each section rise in turn, once. Screens open full size. ?review marks wording to check. */
(function () {
  var html = document.documentElement;
  var reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (/review/.test(location.search)) html.classList.add("review");
  if (/still/.test(location.search)) reduce = true; // ?still: everything in place at once, for checking and screenshots
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  // 1. the bar, as on the home page: hides while you scroll down, and turns dark over anything dark
  var barEl = document.querySelector(".bar"), mark = document.querySelector(".wordmark"), lastY = scrollY;
  var lum = function (m) { return (0.2126 * m[0] + 0.7152 * m[1] + 0.0722 * m[2]) / 255; };
  function toneAt(x, y) {
    var els = document.elementsFromPoint(x, y);
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      if (barEl.contains(el) || el === mark || el.tagName === "IMG") continue;
      if (el.tagName === "VIDEO") return 0;
      var m = getComputedStyle(el).backgroundColor.match(/[\d.]+/g);
      if (m && (m[3] === undefined || +m[3] > 0.5)) return lum(m);
    }
    return lum(getComputedStyle(document.body).backgroundColor.match(/[\d.]+/g));
  }
  function glass() {
    if (!barEl) return;
    var y = scrollY, hide = y > lastY && y > innerHeight * 0.8;
    barEl.classList.toggle("is-hidden", hide); if (mark) mark.classList.toggle("is-hidden", hide);
    lastY = y;
    html.classList.add("probe");
    [barEl, mark].forEach(function (g) {
      if (!g) return;
      var r = g.getBoundingClientRect(), cy = r.top + r.height / 2;
      var l = [r.left + 12, r.left + r.width / 2, r.right - 12].map(function (x) { return toneAt(x, cy); }).sort()[1];
      g.classList.toggle("is-dark", l < 0.5);
    });
    html.classList.remove("probe");
  }
  glass();

  // tabs: the AI stages and the badge rounds, with arrow keys
  $$('[role="tablist"]').forEach(function (list) {
    var tabs = $$('[role="tab"]', list);
    function pick(t, focus) {
      tabs.forEach(function (x) {
        var on = x === t; x.setAttribute("aria-selected", String(on)); x.tabIndex = on ? 0 : -1;
        var p = document.getElementById(x.getAttribute("aria-controls")); if (p) p.hidden = !on;
      });
      if (focus) t.focus();
      if (lens) apply(lens, false);
    }
    tabs.forEach(function (t, i) {
      t.addEventListener("click", function () { pick(t); });
      t.addEventListener("keydown", function (e) {
        var k = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
        if (k) { e.preventDefault(); pick(tabs[(i + k + tabs.length) % tabs.length], true); }
      });
    });
  });

  // the lens: one kind of thinking, marked wherever it shaped the product; the dock steps through the moments
  var lens = null, hits = [], at = -1, names = {};
  var dock = document.querySelector(".dock"), cards = $$(".lens-card");
  cards.forEach(function (c) { names[c.dataset.lensSet] = c.querySelector(".lc-name").textContent; });
  function clear() {
    $$(".lens-hit").forEach(function (e) { e.classList.remove("lens-hit", "lens-current"); });
    $$(".lens-note.show").forEach(function (e) { e.classList.remove("show"); });
  }
  function visible(e) { return e.offsetParent !== null || e.closest("[hidden]"); }
  function apply(k, jump) {
    clear(); lens = k;
    cards.forEach(function (c) { c.setAttribute("aria-pressed", String(c.dataset.lensSet === k)); });
    if (!k) { if (dock) dock.hidden = true; return; }
    hits = $$('[data-lens~="' + k + '"]').filter(visible);
    hits.forEach(function (e) {
      e.classList.add("lens-hit");
      $$('.lens-note[data-for="' + k + '"]', e).forEach(function (n) { if (n.closest("[data-lens]") === e) n.classList.add("show"); });
    });
    if (dock) { dock.hidden = false; dock.querySelector(".dock-name").textContent = names[k] || k; }
    if (jump) go(0); else count();
  }
  function count() { if (dock) dock.querySelector(".dock-count").textContent = (at + 1) + " of " + hits.length; }
  function go(i) {
    if (!hits.length) return;
    at = (i + hits.length) % hits.length;
    var e = hits[at];
    var panel = e.closest('[role="tabpanel"][hidden]') || (e.getAttribute("role") === "tabpanel" && e.hidden ? e : null);
    if (panel) { var tab = document.getElementById(panel.getAttribute("aria-labelledby")); if (tab) tab.click(); }
    hits.forEach(function (h) { h.classList.toggle("lens-current", h === e); });
    e.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "center" });
    count();
  }
  cards.forEach(function (c) {
    c.addEventListener("click", function () { var k = c.dataset.lensSet; at = -1; apply(lens === k ? null : k, lens !== k); });
  });
  if (dock) {
    dock.querySelector(".dock-next").addEventListener("click", function () { go(at + 1); });
    dock.querySelector(".dock-prev").addEventListener("click", function () { go(at - 1); });
    dock.querySelector(".dock-off").addEventListener("click", function () { apply(null); });
    addEventListener("keydown", function (e) { if (e.key === "Escape" && lens) apply(null); });
  }

  // the opening screen: the product screen settles flat over the first screen of scrolling
  var stage = document.querySelector(".stage-in");
  function settle() {
    if (!stage) return;
    if (reduce) { stage.style.setProperty("--t", 1); return; }
    var r = stage.getBoundingClientRect(), t = Math.min(1, Math.max(0, (innerHeight - r.top) / (innerHeight * 0.75) - 0.25));
    stage.style.setProperty("--t", t.toFixed(3));
  }
  settle();

  // 2. the held frame
  var steps = $$(".step"), shots = $$(".steps .shot"), segs = $$(".segs i"), cur = -1;
  function play(i) {
    var s = shots[i]; if (!s) return;
    var v = s.querySelector("video");
    if (!v) return;
    if (v.preload !== "auto") v.preload = "auto";
    if (reduce) return; // the poster is the last frame, so the pins are already in place
    s.classList.add("playing");
    try { v.currentTime = 0; } catch (e) {}
    var p = v.play(); if (p && p.catch) p.catch(function () { s.classList.remove("playing"); });
  }
  function show(i) {
    if (i === cur) return; cur = i;
    if (narrow.matches) return;
    steps.forEach(function (s, k) { s.classList.toggle("is-active", k === i); });
    shots.forEach(function (s, k) {
      if (narrow.matches) return;
      s.classList.toggle("is-on", k === i);
      var v = s.querySelector("video"); if (v && k !== i) { v.pause(); s.classList.remove("playing"); }
    });
    segs.forEach(function (g, k) { g.classList.toggle("on", k <= i); });
    play(i);
  }
  shots.forEach(function (s) {
    var v = s.querySelector("video");
    if (v) v.addEventListener("ended", function () { s.classList.remove("playing"); });
  });
  var replay = document.querySelector(".replay");
  if (replay) replay.addEventListener("click", function () { if (cur >= 0) { var r = reduce; reduce = false; play(cur); reduce = r; } });
  if (steps.length && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) show(steps.indexOf(e.target)); });
    }, { rootMargin: "-48% 0px -48% 0px" });
    steps.forEach(function (s) { io.observe(s); });
    var jstart = new IntersectionObserver(function (es) {
      if (es[0].isIntersecting && cur < 1) { cur = -1; show(0); jstart.disconnect(); }
    }, { threshold: 0.3 });
    var f = document.querySelector(".steps-media"); if (f) jstart.observe(f);
  }
  // below 1080px there is no room to hold a frame: each step takes its own screen, placed after its words
  var frame = document.querySelector(".steps .frame"), narrow = matchMedia("(max-width: 1080px)");
  function place() {
    shots.forEach(function (s, i) {
      if (narrow.matches) { var st = steps[i], n = st && st.querySelector(".notes"); if (st) st.insertBefore(s, n); }
      else if (frame) frame.appendChild(s);
    });
    if (narrow.matches && "IntersectionObserver" in window) shots.forEach(function (s) { seenShot.observe(s); });
  }
  var seenShot = "IntersectionObserver" in window ? new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting && narrow.matches) { seenShot.unobserve(e.target); play(shots.indexOf(e.target)); } });
  }, { threshold: 0.6 }) : null;
  if (frame) { place(); narrow.addEventListener("change", place); }

  // notes and pins share a number
  steps.forEach(function (step, si) {
    var notes = $$(".notes li", step), pins = shots[si] ? $$(".pin", shots[si]) : [];
    function on(i, yes) { notes[i].classList.toggle("on", yes); if (pins[i]) pins[i].classList.toggle("on", yes); }
    notes.forEach(function (n, i) {
      n.tabIndex = 0;
      ["mouseenter", "focus"].forEach(function (ev) { n.addEventListener(ev, function () { on(i, true); }); });
      ["mouseleave", "blur"].forEach(function (ev) { n.addEventListener(ev, function () { on(i, false); }); });
    });
  });

  // 3. on scroll: the opening screen settles, the bar finds its tone
  var ticking = false;
  function update() { ticking = false; settle(); glass(); }
  addEventListener("scroll", function () { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
  addEventListener("resize", update); update();

  // 4. entrances: siblings rise in turn
  var risers = $$(".rise");
  var groups = new Map();
  risers.forEach(function (el) {
    var p = el.parentElement, n = groups.get(p) || 0;
    el.style.setProperty("--i", Math.min(n, 5)); groups.set(p, n + 1);
  });
  if ("IntersectionObserver" in window && !reduce) {
    var ro = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); ro.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    risers.forEach(function (el) { ro.observe(el); });
  } else risers.forEach(function (el) { el.classList.add("in"); });

  // screens open full size
  var box;
  $$("img.zoomable").forEach(function (im) {
    im.addEventListener("click", function () {
      if (!box) {
        box = document.createElement("div"); box.className = "lightbox"; box.setAttribute("role", "dialog"); box.setAttribute("aria-label", "Image, full size");
        box.appendChild(document.createElement("img")); document.body.appendChild(box);
        box.addEventListener("click", function () { box.classList.remove("open"); });
        addEventListener("keydown", function (e) { if (e.key === "Escape") box.classList.remove("open"); });
      }
      var b = box.querySelector("img"); b.src = im.currentSrc || im.src; b.alt = im.alt; box.classList.add("open");
    });
  });
})();
