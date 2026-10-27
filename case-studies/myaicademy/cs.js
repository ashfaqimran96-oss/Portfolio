// myAIcademy case study: three scroll scenes on the shared stage (the seats, the loop, every screen),
// the role picker, figures that count up once, and the parts of every quiet section rising in turn
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  window.Scenes = window.Scenes || {};

  // ---------- scene: every seat lights up, then four in five go grey while the figure climbs ----------
  Scenes.seats = (root, o) => Stage.scene(root, {
    hold: o.hold ?? 2,
    build(tl, { q }) {
      const num = q('[data-seats-num]')[0], n = { v: 0 };
      tl.fromTo(q('.seat'), { scale: 0.86, autoAlpha: 0.14 }, { scale: 1, autoAlpha: 1, duration: 0.24, stagger: { each: 0.008, from: 'random' } }, 0)
        .fromTo(q('.seat:not(.keep) b'), { opacity: 0 }, { opacity: 1, duration: 0.3, stagger: { each: 0.012, from: 'random' } }, 0.42)
        .fromTo(q('.seats-beat, .seats .giant, .seats-src'), { autoAlpha: 0, y: 30 }, { autoAlpha: 1, y: 0, duration: 0.12, stagger: 0.05 }, 0.42)
        .fromTo(n, { v: 0 }, { v: 80, duration: 0.3, onUpdate: () => { num.textContent = Math.round(n.v); } }, 0.45)
        .fromTo(q('.seat.keep'), { scale: 1 }, { scale: 1.08, duration: 0.12 }, 0.8);
    },
  });

  // ---------- scene: one device moves from the job to the lesson, then opens into the browser ----------
  Scenes.loop = (root, o) => Stage.scene(root, {
    hold: o.hold ?? 3,
    build(tl, { q }) {
      const li = q('.loop-steps li'), shots = q('.device-phone img');
      const phone = q('.device-phone')[0], browser = q('.device-browser')[0];
      tl.fromTo([li[1], li[2]], { autoAlpha: 0 }, { autoAlpha: 0, duration: 0.001 }, 0)
        .fromTo(shots[1], { autoAlpha: 0 }, { autoAlpha: 0, duration: 0.001 }, 0)
        .fromTo(browser, { autoAlpha: 0, scale: 0.55 }, { autoAlpha: 0, scale: 0.55, duration: 0.001 }, 0)
        .fromTo(phone, { yPercent: 14 }, { yPercent: 0, duration: 0.25 }, 0)
        // the job becomes the lesson
        .to(li[0], { autoAlpha: 0, y: -30, duration: 0.06 }, 0.27)
        .fromTo(li[1], { autoAlpha: 0, y: 30 }, { autoAlpha: 1, y: 0, duration: 0.06 }, 0.36)
        .to(shots[1], { autoAlpha: 1, duration: 0.1 }, 0.32)
        // the phone gives way to the browser, where Aimy works beside the tool
        .to(li[1], { autoAlpha: 0, y: -30, duration: 0.06 }, 0.58)
        .fromTo(li[2], { autoAlpha: 0, y: 30 }, { autoAlpha: 1, y: 0, duration: 0.06 }, 0.68)
        .to(phone, { yPercent: 30, autoAlpha: 0, duration: 0.12 }, 0.6)
        .to(browser, { autoAlpha: 1, scale: 1, duration: 0.16, ease: 'power2.out' }, 0.64);
    },
  });

  // ---------- scene: the run of screens crosses the stage, odd ones drifting against the even ----------
  Scenes.pan = (root, o) => Stage.scene(root, {
    hold: o.hold ?? 2.5,
    build(tl, { q }) {
      const track = q('.pan-track')[0], panel = q('.pan-panel')[0];
      const run = () => -(track.scrollWidth - panel.clientWidth + parseFloat(getComputedStyle(panel).paddingLeft) * 2);
      tl.fromTo(track, { x: 0 }, { x: run, duration: 1 }, 0)
        .fromTo(q('.mock:nth-child(odd)'), { y: 24 }, { y: -24, duration: 1 }, 0);
    },
  });

  // ---------- the live thing: pick a job, get its first path ----------
  const paths = {
    consultant: ['AI for consultants', [['Turn interview notes into a findings deck', 'Claude'], ['Build a client-ready one-pager', 'Lovable'], ['Draft the steering-committee update', 'Copilot']]],
    teacher: ['AI for teachers', [['Plan a week of lessons around your syllabus', 'ChatGPT'], ['Make a quiz from your own slides', 'Claude'], ['Give fair feedback on thirty essays', 'Copilot']]],
    lawyer: ['AI for lawyers', [['Summarise a contract into its risks', 'Claude'], ['Compare two drafts clause by clause', 'Copilot'], ['Draft a client letter in your firm\'s voice', 'ChatGPT']]],
    marketing: ['AI for marketers', [['Write a campaign brief in an hour', 'Claude'], ['Make the launch visuals', 'Midjourney'], ['Voice the product video', 'ElevenLabs']]],
    hr: ['AI for HR and recruiting', [['Write a job description that attracts the right people', 'ChatGPT'], ['Screen applications against the brief', 'Copilot'], ['Build a first-week onboarding plan', 'Claude']]],
    sales: ['AI for sales', [['Research an account before the call', 'ChatGPT'], ['Write a follow-up that gets a reply', 'Claude'], ['Turn call notes into a proposal', 'Copilot']]],
  };
  const chips = [...document.querySelectorAll('.chips button')];
  const card = document.querySelector('.path');
  const title = document.querySelector('[data-path-title]');
  const list = document.querySelector('[data-path-list]');
  const esc = s => s.replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const pick = btn => {
    chips.forEach(c => c.setAttribute('aria-checked', String(c === btn)));
    const [t, rows] = paths[btn.dataset.role];
    const swap = () => {
      title.textContent = t;
      list.innerHTML = rows.map(([l, tool]) => `<li><span>${esc(l)}</span><b>${esc(tool)}</b></li>`).join('');
      card.classList.remove('is-swapping');
    };
    if (reduce) return swap();
    card.classList.add('is-swapping');
    setTimeout(swap, 260);
  };
  chips.forEach((c, i) => {
    c.addEventListener('click', () => pick(c));
    c.addEventListener('keydown', e => {
      const d = e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1 : 0;
      if (!d) return;
      e.preventDefault();
      const n = chips[(i + d + chips.length) % chips.length];
      n.focus(); pick(n);
    });
  });

  // ---------- figures count up the first time they're seen ----------
  document.querySelectorAll('[data-count]').forEach(el => {
    const to = +el.dataset.count;
    new IntersectionObserver((entries, ob) => entries.forEach(e => {
      if (!e.isIntersecting) return;
      ob.disconnect();
      if (reduce) return;
      const t0 = performance.now(), dur = 1300;
      const step = t => {
        const k = Math.min(1, (t - t0) / dur);
        el.textContent = Math.round(to * (1 - Math.pow(1 - k, 3))).toLocaleString('en-US');
        if (k < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    }), { threshold: 0.6 }).observe(el);
  });

  // ---------- entrances for the quiet sections: heading, text, picture, 70ms apart ----------
  if (!reduce) {
    const groups = document.querySelectorAll('.hero-copy, .research-words, .research-pic, .io-in, .io-out, .figures, .brand-panel, .swatches, .letter, .foot');
    groups.forEach(g => [...g.children].forEach((k, i) => { k.classList.add('rise'); k.style.setProperty('--d', (i * 0.07).toFixed(2) + 's'); }));
    const io = new IntersectionObserver(entries => entries.forEach(e => {
      if (!e.isIntersecting) return;
      e.target.querySelectorAll(':scope > .rise').forEach(k => k.classList.add('is-in'));
      io.unobserve(e.target);
    }), { rootMargin: '0px 0px -8% 0px' });
    groups.forEach(g => io.observe(g));
  }

  // ---------- the stage: smooth wheel, the scenes, and the hero phones drifting up as you leave ----------
  if (!window.Stage) return;
  Stage.smooth();
  Stage.init();
  if (Stage.live && !reduce) {
    gsap.to('.hero-phones', { yPercent: -12, ease: 'none', scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true } });
  }
})();
