(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const phone = matchMedia('(max-width: 860px)').matches;
  const hasGsap = typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined';
  const lerp = (a, b, t) => a + (b - a) * t;
  const clamp01 = v => Math.min(1, Math.max(0, v));
  const smooth = t => { t = clamp01(t); return t * t * (3 - 2 * t); };
  const span = (t, a, b) => clamp01((t - a) / (b - a));   // 0..1 progress of t through [a, b]

  if (!hasGsap || reduce) {
    document.querySelector('.loader')?.remove();
    document.documentElement.classList.remove('js');
    return;
  }
  gsap.registerPlugin(ScrollTrigger);

  // Smooth scroll
  let lenis;
  if (typeof Lenis !== 'undefined') {
    lenis = new Lenis({ lerp: 0.09 });
    lenis.on('scroll', ScrollTrigger.update);
    gsap.ticker.add(t => lenis.raf(t * 1000));
    gsap.ticker.lagSmoothing(0);
    document.querySelectorAll('a[href^="#"]').forEach(a => a.addEventListener('click', e => {
      const id = a.getAttribute('href');
      if (id.length > 1 && document.querySelector(id)) { e.preventDefault(); lenis.scrollTo(id, { offset: -10 }); }
    }));
  }

  const stage = document.querySelector('.film-stage');
  const bust = document.querySelector('.f-bust');
  const clip = document.querySelector('.f-clip');
  const cardBg = document.querySelector('.f-cardbg');
  const boxWrap = document.querySelector('.box-wrap');
  const box = document.querySelector('.box');
  const faces = [...document.querySelectorAll('.face')];
  const face0Bust = faces[0].querySelector('.face-bust');
  const hcards = [...document.querySelectorAll('.hcard')];
  const crowd = document.querySelector('.f-crowd');
  const crowdImg = document.querySelector('.crowd-img');
  const black = document.querySelector('.f-black');
  const logo = document.querySelector('.f-logo');

  // words that light up one at a time as the scroll passes them
  const splitWords = el => {
    el.innerHTML = el.textContent.trim().split(/\s+/).map(w => '<span class="w">' + w + '</span>').join(' ');
    return [...el.querySelectorAll('.w')];
  };
  const lineWords = [...document.querySelectorAll('.f-line')].flatMap(splitWords);
  const crowdWords = splitWords(document.querySelector('.crowd-words'));
  const introWords = splitWords(document.querySelector('.f-intro'));
  const light = (words, p) => { const n = Math.round(p * words.length); words.forEach((w, i) => w.classList.toggle('on', i < n)); };

  // ---------- Loader: mark and name rise in, tape coils in from two corners and the count runs to
  // 100; then it all clears, and the dark sheet lifts on a curve as the bust rises into place ----------
  const nameEl = document.querySelector('.loader-name');
  nameEl.innerHTML = [...nameEl.textContent].map(c => '<span>' + c + '</span>').join('');
  const countEl = document.querySelector('.loader-count'), count = { v: 0 };
  const rise = { y: 0.4 };   // the bust's lift during the intro, as a share of the screen
  lenis?.stop();
  const intro = gsap.timeline({ onComplete: () => { document.querySelector('.loader')?.remove(); lenis?.start(); } });
  intro
    .from('.loader-name span', { yPercent: 110, duration: 0.5, stagger: 0.025, ease: 'power3.out' }, 0.05)
    .from('.loader-tape--a', { xPercent: -55, yPercent: -55, rotate: '-=60', scale: 0.6, duration: 0.85, ease: 'power3.out' }, 0.1)
    .from('.loader-tape--b', { xPercent: 55, yPercent: 55, rotate: '+=60', scale: 0.6, duration: 0.85, ease: 'power3.out' }, 0.12)
    .to(count, { v: 100, duration: 1.1, ease: 'power1.inOut', onUpdate: () => { countEl.textContent = Math.round(count.v) + '%'; } }, 0)
    .to('.loader-name span', { yPercent: -110, duration: 0.35, stagger: 0.025, ease: 'power2.in' }, 1.25)
    .to('.loader-tape--a', { xPercent: -65, yPercent: -65, rotate: '-=45', duration: 0.5, ease: 'power3.in' }, 1.2)
    .to('.loader-tape--b', { xPercent: 65, yPercent: 65, rotate: '+=45', duration: 0.5, ease: 'power3.in' }, 1.2)
    .to('.loader-count', { opacity: 0, duration: 0.2 }, 1.3)
    .to('.loader-panel', { yPercent: -105, duration: 0.85, ease: 'power3.inOut' }, 1.8)
    .to(rise, { y: 0, duration: 1.1, ease: 'power3.out', onUpdate: () => render() }, 1.9)
    .from('.f-hero h1 > *', { yPercent: 60, opacity: 0, duration: 0.7, stagger: 0.07, ease: 'power3.out' }, 2.15)
    .from('.hero-cta, .hero-badge', { y: 24, opacity: 0, duration: 0.6, stagger: 0.08, ease: 'power3.out' }, 2.3)
    .from('.hcard', { scale: 0.4, opacity: 0, duration: 0.8, stagger: 0.06, ease: 'back.out(1.6)' }, 2.35)
    .from('.bar, .wordmark', { opacity: 0, duration: 0.5 }, 2.45);

  // ---------- The film. One scroll position t (0..12) drives every scene in the pinned stage ----------
  // 0–1.2   hero words leave, the card ribbon sweeps up and away, the bust settles lower
  // 0.6–3.4 the introduction sits large at the top and lights up word by word
  // (from here every time is measured from D = 2.5)
  // 0.6–2.2 the bust shrinks into the first face of the box
  // 2.4–7   the other cards open out into a ring of five, which turns card by card while the lines light up
  // 7.5–8.6 the black card zooms until the screen is black; the logo stays put
  // 8.6–12  the crowd fades up, the logo settles over the blue figure, the story lights up in white
  // the introduction scene is inserted after the hero; every later scene runs D later
  const D = 2.5, T = 12 + D;
  let t = 0;

  // the bust: [x, y, width] at rest in the hero, and where it sits inside the first face
  const BUST = { w: 2600, h: 3228, top: 0.089, neck: 0.5, cx: 0.5 };
  function bustRest() {
    const vh = stage.clientHeight, vw = stage.clientWidth;
    let [headTop, neckAt] = phone ? [0.4, 0.74] : [0.07, 0.62];
    // keep the crown clear of the floating nav (68px with its offset) with breathing room; same size, just lower
    const drop = phone ? 0 : Math.max(0, 108 / vh - headTop);
    headTop += drop; neckAt += drop;
    const h = vh * (neckAt - headTop) / (BUST.neck - BUST.top);
    const w = h * BUST.w / BUST.h;
    return [vw / 2 - BUST.cx * w, vh * headTop - BUST.top * h + rise.y * vh, w];
  }
  function bustMid() {
    // smaller and lower, leaving the top of the screen to the introduction
    const vh = stage.clientHeight, vw = stage.clientWidth;
    let [headTop, neckAt] = phone ? [0.4, 0.74] : [0.42, 0.84];
    // the crown always lands below the last line of the introduction, whatever the screen and line count
    const intro = document.querySelector('.f-intro');
    const clear = (intro.offsetTop + intro.offsetHeight + (phone ? 20 : 32)) / vh;
    const drop = Math.max(0, clear - headTop);
    headTop += drop; neckAt += drop;
    const h = vh * (neckAt - headTop) / (BUST.neck - BUST.top);
    const w = h * BUST.w / BUST.h;
    return [vw / 2 - BUST.cx * w, vh * headTop - BUST.top * h, w];
  }
  // the ring: five cards round a pentagon. Before it opens every card hides directly behind the
  // first; then each swings out to its place, and the ring turns one card per step
  const ANG = [0, 72, 144, -144, -72];
  function placeFaces(e) {
    // the pentagon's apothem, pushed out a little so neighbouring cards stand apart with a clear gap
    const r = boxWrap.offsetWidth / (2 * Math.tan(Math.PI / 5)) + boxWrap.offsetWidth * 0.075;
    faces.forEach((f, i) => {
      // only the two neighbours swing out from behind the first card; the two at the back of the
      // ring wait there, out of sight, until the turning brings them round
      const side = i === 1 || i === 4;
      const k = side ? e : 1;
      // they start well behind it and come forward as they swing, so their near edge never crosses its face
      const back = side ? Math.pow(1 - e, 0.7) * 0.8 * boxWrap.offsetWidth : 0;
      f.style.transform = 'rotateY(' + ANG[i] * k + 'deg) translateZ(' + (r - back) + 'px)';
      // '' inherits the ring's own visibility, so nothing shows before the hand-over
      f.style.visibility = side && e === 0 ? 'hidden' : '';
    });
  }
  let faceRect = null, cardRect = null;
  function measureFace() {
    // the ring at rest, closed, first card square to the screen: its bust's box and its edges are the targets
    placeFaces(0);
    gsap.set(box, { rotateY: 0, y: 0, rotateZ: 0 });
    gsap.set(boxWrap, { scale: 1 });
    const s = stage.getBoundingClientRect(), r = face0Bust.getBoundingClientRect(), c = faces[0].getBoundingClientRect();
    faceRect = [r.left - s.left, r.top - s.top, r.width];
    cardRect = [c.left - s.left, c.top - s.top, c.width, c.height];
    // the lifted logo starts exactly over the one printed on the card: same centre, same width
    // measured with the black card standing where it will be when it faces the screen
    const front = faces[0].style.transform, keep = faces[4].style.transform;
    faces[4].style.transform = front;
    const lg = faces[4].querySelector('.face-mark').getBoundingClientRect();
    faces[4].style.transform = keep;
    logoX0 = lg.left - s.left + lg.width / 2;
    logoY0 = lg.top - s.top + lg.height / 2;
    logoS0 = lg.width / logo.querySelector('img').offsetWidth;
    Object.assign(cardBg.style, { left: cardRect[0] + 'px', top: cardRect[1] + 'px', width: cardRect[2] + 'px', height: cardRect[3] + 'px' });
  }

  // the hero ribbon: cards ride a wave from lower left to upper right, behind the head
  let flow = 0;
  function ribbon(exit) {
    const vw = stage.clientWidth, vh = stage.clientHeight, n = hcards.length;
    const P = u => [lerp(-0.32, 1.32, u) * vw, vh * ((phone ? 0.84 : 0.8) - 0.4 * u + 0.09 * Math.sin(u * Math.PI * 2.4))];
    hcards.forEach((c, i) => {
      const u = ((i / n + flow) % 1 + 1) % 1;
      const [x, y] = P(u), [x2, y2] = P(u + 0.01);
      const a = Math.atan2(y2 - y, x2 - x) * 180 / Math.PI;
      // on the way out the whole ribbon lifts and spreads off the top of the screen
      const lift = exit * vh * (0.9 + (1 - u) * 0.5);
      c.style.transform = `translate(${x - c.offsetWidth / 2}px, ${y - c.offsetHeight / 2 - lift}px) rotate(${a + Math.sin(u * 9 + i) * 6}deg)`;
    });
  }

  let logoX0 = 0, logoY0 = 0, logoS0 = 1;   // where and how big the logo sits on the black card
  function placeLogo(k) {
    // from the centre of the black face to just over the blue figure's head in the crowd shot
    const vw = stage.clientWidth, vh = stage.clientHeight;
    // the crowd image is cover-fitted and centred, then scaled about 62% 60% of the stage
    const iw = 2400, ih = 1350, s0 = Math.max(vw / iw, vh / ih), sc = gsap.getProperty(crowdImg, 'scale');
    const ox = (vw - iw * s0) / 2, oy = (vh - ih * s0) / 2;
    const hx = ox + 0.535 * iw * s0, hy = oy + 0.215 * ih * s0;   // just above the blue figure's head
    const tx = 0.62 * vw + (hx - 0.62 * vw) * sc, ty = 0.6 * vh + (hy - 0.6 * vh) * sc;
    const x = lerp(logoX0, tx, k), y = lerp(logoY0, ty, k);
    logo.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%) scale(${lerp(logoS0, 0.85, k)})`;
    logo.style.left = '0'; logo.style.top = '0';
  }

  function render() {
    if (!faceRect) measureFace();
    // scene 1
    const heroOut = smooth(span(t, 0.15, 1));
    gsap.set('.f-hero', { opacity: 1 - heroOut, y: -60 * heroOut });
    ribbon(smooth(span(t, 0, 1.3)));
    gsap.set('.f-cards', { opacity: 1 - span(t, 0.9, 1.4) });

    // scene 1b: the introduction across the top, lit word by word, then away before the bust shrinks
    gsap.set('.f-intro', { opacity: span(t, 0.95, 1.45) * (1 - span(t, 3.1, 3.5)), y: (1 - span(t, 0.95, 1.45)) * 30 - span(t, 3.1, 3.5) * 40 });
    light(introWords, span(t, 1.35, 3));

    const u = t - D;
    // scene 1 → 2: the bust glides and shrinks into the first face, then the face takes over
    const k = gsap.parseEase('sine.inOut')(span(u, 0.5, 2.1));
    const r0 = bustRest(), r1 = bustMid(), m = gsap.parseEase('power2.inOut')(span(t, 0.4, 1.5));
    const a = [0, 1, 2].map(i => lerp(r0[i], r1[i], m)), b = faceRect;
    const bx = lerp(a[0], b[0], k), by = lerp(a[1], b[1], k), bw = lerp(a[2], b[2], k);
    bust.style.transform = `translate(${bx}px, ${by}px) scale(${bw / BUST.w})`;
    // the frame closes in on the card's edges a little behind the bust, and the yellow fills in under it
    const c = smooth(span(k, 0.3, 1)), vw = stage.clientWidth, vh = stage.clientHeight;
    const [cl, ct, cw, ch] = cardRect;
    clip.style.clipPath = 'inset(' + lerp(0, ct, c) + 'px ' + lerp(0, vw - cl - cw, c) + 'px ' + lerp(0, vh - ct - ch, c) + 'px ' + lerp(0, cl, c) + 'px)';
    cardBg.style.opacity = smooth(span(k, 0.45, 1));
    // once it has landed the box takes over: the same picture, the same edges, the same colour
    const inFace = k >= 1;
    clip.style.visibility = inFace ? 'hidden' : 'visible';
    boxWrap.style.visibility = inFace ? 'visible' : 'hidden';
    gsap.set(faces[0].querySelector('.face-text'), { opacity: span(u, 2.15, 2.5), y: (1 - span(u, 2.15, 2.5)) * 10 });

    // scene 2: the other cards slide out from behind the first and swing round into the ring,
    // then the ring turns a card at a time, with a hold on each
    placeFaces(gsap.parseEase('power3.inOut')(span(u, 2.4, 3.1)));
    const turns = [[3.4, 4], [4.4, 5], [5.4, 6], [6.4, 7]];
    const turn = turns.reduce((s, [p, q]) => s + gsap.parseEase('power2.inOut')(span(u, p, q)), 0);
    // a slight lift while each turn is under way
    const mid = turns.reduce((s, [p, q]) => s + Math.sin(Math.PI * span(u, p, q)), 0);
    gsap.set(box, { rotateY: -72 * turn, y: -12 * mid, rotateX: mid * 3 });
    const lines = span(u, 2.1, 2.6) * (1 - span(u, 7.3, 7.6));
    gsap.set('.f-line', { opacity: lines, y: (1 - span(u, 2.1, 2.6)) * 20 });
    light(lineWords, span(u, 2.6, 7.1));

    // scene 2 → 3: the black card grows past the edges of the screen; the logo is lifted off it first
    const z = gsap.parseEase('power3.in')(span(u, 7.5, 8.6));
    const cover = Math.max(stage.clientWidth / boxWrap.offsetWidth, stage.clientHeight / boxWrap.offsetHeight) * 1.4;
    gsap.set(boxWrap, { scale: lerp(1, cover, z) });
    gsap.set(faces[4].querySelector('.face-text'), { opacity: 1 - span(u, 7.4, 7.6) });
    // the blue figure fades into the black as the card grows, ready to reappear in the crowd
    gsap.set(faces[4].querySelector('.face-bust'), { opacity: 1 - span(u, 7.6, 8.15) });
    black.style.opacity = span(u, 8.2, 8.6);
    logo.style.opacity = span(u, 7.4, 7.6);

    // scene 3: the crowd, the logo over the blue figure, the story in white
    crowd.style.opacity = span(u, 8.6, 9.3);
    gsap.set(crowdImg, { scale: lerp(1.1, 1, smooth(span(u, 8.6, 10.2))) });
    placeLogo(smooth(span(u, 8.8, 9.8)));
    gsap.set('.crowd-copy', { opacity: span(u, 9.2, 9.7), y: (1 - span(u, 9.2, 9.7)) * 30 });
    light(crowdWords, span(u, 9.7, 11.7));

  }

  const filmST = ScrollTrigger.create({
    trigger: '.film', start: 'top top', end: 'bottom bottom', scrub: true,
    onUpdate: self => { t = self.progress * T; render(); },
    onRefresh: self => { faceRect = null; t = self.progress * T; render(); },
  });
  gsap.ticker.add(() => { flow += phone ? 0.0006 : 0.00045; if (t < 1.4) ribbon(smooth(span(t, 0, 1.3))); });
  addEventListener('resize', () => { faceRect = null; render(); });
  render();

  // ---------- Bar: hides while scrolling down, dark over the dark scenes ----------
  let last = 0;
  ScrollTrigger.create({
    start: 0, end: 'max',
    onUpdate: self => {
      const y = self.scroll(), bar = document.querySelector('.bar');
      bar.classList.toggle('is-hidden', y > last && y > innerHeight * 0.8);
      last = y;
    }
  });
  // the bar looks at what is really behind it: the topmost visible thing with a solid colour, or a
  // picture marked with data-tone, sampled at both ends and the middle of the oval
  const bar = document.querySelector('.bar');
  const lum = ([r, g, b]) => (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
  function seen(el) {
    let o = 1;
    for (let n = el; n && n !== document.documentElement; n = n.parentElement) {
      const cs = getComputedStyle(n);
      if (cs.visibility === 'hidden' || cs.display === 'none') return 0;
      o *= +cs.opacity;
    }
    return o;
  }
  function toneAt(x, y) {
    for (const el of document.elementsFromPoint(x, y)) {
      if (bar.contains(el) || el.classList.contains('wordmark') || seen(el) < 0.5) continue;
      if (el.dataset.tone) return el.dataset.tone === 'dark' ? 0 : 1;
      if (el.tagName === 'IMG') continue;
      const m = getComputedStyle(el).backgroundColor.match(/[\d.]+/g);
      if (m && (m[3] === undefined || +m[3] > 0.5)) return lum(m);
    }
    return lum(getComputedStyle(document.body).backgroundColor.match(/[\d.]+/g));
  }
  const chipsGlass = [bar, document.querySelector('.wordmark')];
  let tick = 0;
  gsap.ticker.add(() => {
    if (++tick % 4) return;
    // layers that ignore the pointer still count as backdrop, so open them to the probe for a moment
    document.documentElement.classList.add('probe');
    chipsGlass.forEach(g => {
      const r = g.getBoundingClientRect(), y = r.top + r.height / 2;
      const l = [r.left + 12, r.left + r.width / 2, r.right - 12].map(x => toneAt(x, y)).sort()[1];
      g.classList.toggle('is-dark', l < 0.5);
    });
    document.documentElement.classList.remove('probe');
  });
  // the section under the middle of the screen gets its chip
  const chips = [...bar.querySelectorAll('nav a')].map(a => {
    const id = a.getAttribute('href').slice(1);
    return [a, id === 'story' ? document.querySelector('.film') : document.getElementById(id)];
  });
  gsap.ticker.add(() => {
    if (tick % 4 !== 2) return;
    chips.forEach(([a, sec]) => { const r = sec.getBoundingClientRect(); a.classList.toggle('is-on', r.top < innerHeight / 2 && r.bottom > innerHeight / 2); });
  });

  // ---------- Work: one pinned stage. The track runs sideways through the project panels, the
  // drifting graphic pieces and onto the trophy; then the trophy's words come and go and the camera
  // pushes into its glow until it burns out to the path ----------
  const track = document.querySelector('.work-track');
  const workStage = document.querySelector('.work-stage');
  const panels = gsap.utils.toArray('.panel');
  const field = document.querySelector('.gfx-field');
  const tiles = gsap.utils.toArray('.gt');
  const workCount = document.querySelector('.work-count b');
  const dist = () => track.scrollWidth - innerWidth;
  // panels start below the heading
  const setHead = () => { const hd = document.querySelector('.work-head'); track.style.setProperty('--head', (hd.offsetTop + hd.offsetHeight) + 'px'); };
  setHead();
  addEventListener('resize', setHead);

  // each project's stack pops up card by card, back first, as its panel slides into view
  const pops = panels.map(p => {
    const deck = [...p.querySelectorAll('.dk')].reverse();
    gsap.set(deck, { transformPerspective: 1400, transformOrigin: '50% 100%', rotateY: -10, rotateZ: -2 });
    return gsap.fromTo(deck, { yPercent: 120, rotateZ: (k) => (k % 2 ? 7 : -5) }, { yPercent: 0, rotateZ: -2, duration: 0.85, ease: 'back.out(1.5)', stagger: 0.09, paused: true });
  });
  const shown = panels.map(() => false);
  function popPanels() {
    panels.forEach((p, i) => {
      const on = p.getBoundingClientRect().left < innerWidth * 0.78 && workStage.getBoundingClientRect().top < innerHeight * 0.45;
      if (on !== shown[i]) { shown[i] = on; on ? pops[i].play() : pops[i].reverse(); }
    });
    // the counter follows whichever panel is nearest the left edge
    const lead = panels.findIndex(p => p.getBoundingClientRect().right > innerWidth * 0.35);
    workCount.textContent = String(lead < 0 ? panels.length : lead + 1).padStart(2, '0');
  }

  const H = 10;   // the sideways run; the trophy scenes follow it
  const workTl = gsap.timeline({
    scrollTrigger: {
      trigger: '.work', start: 'top top', end: () => '+=' + (dist() + innerHeight * 4), pin: workStage, scrub: 0.6, invalidateOnRefresh: true,
      onUpdate: popPanels, onRefresh: popPanels,
    }
  });
  workTl.eventCallback('onUpdate', popPanels);
  workTl.to(track, { x: () => -dist(), ease: 'none', duration: H }, 0);
  // the graphic pieces drift at their own speeds against the track
  tiles.forEach(t => workTl.to(t, { x: () => -(+t.dataset.speed - 1) * innerWidth * 0.35, ease: 'none', duration: H }, 0));
  // the heading and the counter step away once the projects are done
  const fieldAt = () => H * clamp01((field.offsetLeft - innerWidth * 0.95) / dist());
  workTl.to('.work-head, .work-count', { opacity: 0, y: -30, ease: 'none', duration: 0.5 }, fieldAt());
  // the trophy comes in a little large and settles as it reaches the centre
  workTl.fromTo('.trophy .award-img', { scale: 1.18, xPercent: 8 }, { scale: 1, xPercent: 0, ease: 'none', duration: H * innerWidth / Math.max(dist(), 1) }, H - H * innerWidth / Math.max(dist(), 1));
  workTl
    // explicit both ends: the timeline re-measures on refresh, and a plain from() would lose its end state
    .fromTo('.award-copy h2, .award-copy p, .award-steps li', { y: 40, opacity: 0 }, { y: 0, opacity: 1, stagger: 0.08, duration: 0.5 }, H + 0.1)
    .to('.award-copy', { opacity: 0, y: -60, duration: 0.5, ease: 'power1.in' }, H + 1.5)
    .to('.trophy .award-img', { scale: 4.2, ease: 'power3.in', duration: 1.6 }, H + 1.6)
    .to('.award-flash', { opacity: 1, ease: 'power2.in', duration: 0.6 }, H + 2.6)
    .to({}, { duration: 0.6 });

  // ---------- Road: the line paints itself down the page; each role arrives as it is reached ----------
  const road = document.querySelector('.road-line');
  if (road && !phone) {
    const len = road.getTotalLength();
    gsap.set(road, { strokeDasharray: len, strokeDashoffset: len });
    gsap.to(road, { strokeDashoffset: 0, ease: 'none', scrollTrigger: { trigger: '.road-stage', start: 'top 60%', end: 'bottom 70%', scrub: 0.5 } });
  }
  gsap.utils.toArray('.stop').forEach(s => {
    gsap.from(s.querySelectorAll('.stop-when, h3, p:last-child'), { y: 30, opacity: 0, duration: 0.8, stagger: 0.08, ease: 'power3.out', scrollTrigger: { trigger: s, start: 'top 72%' } });
    gsap.from(s.querySelector('.stop-dot'), { scale: 0, duration: 0.6, ease: 'back.out(2.4)', scrollTrigger: { trigger: s, start: 'top 72%' } });
  });

  // ---------- Entrances: heading, then text, then the rest ----------
  document.querySelectorAll('.road-head, .kit-head, .close-top').forEach(group => {
    const parts = group.querySelectorAll('h2, p, .btn, .close-links > div');
    gsap.from(parts, { y: 28, opacity: 0, duration: 0.9, stagger: 0.08, ease: 'power3.out', scrollTrigger: { trigger: group, start: 'top 82%' } });
  });
  gsap.from('.folder', { y: 60, opacity: 0, duration: 0.8, stagger: 0.06, ease: 'power3.out', scrollTrigger: { trigger: '.folders', start: 'top 80%' } });

  // ---------- Close: tapes drift against each other, the name rises ----------
  [['.tape--1', -12], ['.tape--2', 10], ['.tape--3', -8]].forEach(([sel, x]) => {
    gsap.fromTo(sel, { xPercent: -x }, { xPercent: x, ease: 'none', scrollTrigger: { trigger: '.close', start: 'top bottom', end: 'bottom bottom', scrub: true } });
  });
  gsap.from('.close-name', { yPercent: 60, opacity: 0, ease: 'none', scrollTrigger: { trigger: '.tapes', start: 'top 90%', end: 'bottom 70%', scrub: true } });

  addEventListener('load', () => ScrollTrigger.refresh());
})();
