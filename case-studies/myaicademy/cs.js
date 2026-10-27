// myAIcademy case study: the stage follows the section in view, the role picker rebuilds the path,
// figures count up once, and the parts of every section rise in turn
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ---------- the stage: whichever section crosses the middle of the screen picks the picture ----------
  const captions = {
    welcome: ['The welcome screen', 'myAIcademy app'],
    layer: ['Pitch deck, the adoption layer', 'Brand and deck design'],
    problem: ['Pitch deck, the problem', 'Brand and deck design'],
    question: ['Pitch deck, the research', 'Brand and deck design'],
    position: ['Pitch deck, positioning', 'Brand and deck design'],
    role: ['Onboarding, step one', 'iOS, Android and web'],
    lesson: ['A follow-along lesson in Lovable', 'iOS, Android and web'],
    aimy: ['Aimy inside ChatGPT, prototype', 'Web, beside the approved tool'],
  };
  document.querySelectorAll('.split').forEach(split => {
    const stage = split.querySelector('.stage');
    const shots = [...stage.querySelectorAll('.shot')];
    const cap = stage.querySelectorAll('.stage-bar span');
    const parts = [...split.querySelectorAll('[data-shot]')];
    const show = id => {
      shots.forEach(s => s.classList.toggle('is-on', s.dataset.id === id));
      parts.forEach(p => p.classList.toggle('is-on', p.dataset.shot === id));
      if (captions[id]) { cap[0].textContent = captions[id][0]; cap[1].textContent = captions[id][1]; }
    };
    const io = new IntersectionObserver(entries => entries.forEach(e => { if (e.isIntersecting) show(e.target.dataset.shot); }),
      { rootMargin: '-48% 0px -48% 0px' });
    parts.forEach(p => io.observe(p));
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
    // arrow keys move through the group, as a radio group should
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
    new IntersectionObserver((entries, o) => entries.forEach(e => {
      if (!e.isIntersecting) return;
      o.disconnect();
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

  // ---------- entrances: heading, then text, then picture, 70ms apart, once per section ----------
  if (reduce) return;
  const groups = document.querySelectorAll('.sheet-main, .block, .io-in, .io-out, .steps, .tools, .mosaic, .brand-inner, .letter-col, .foot');
  groups.forEach(g => {
    const kids = [...g.children].filter(k => !k.classList.contains('io-word'));
    kids.forEach((k, i) => { k.classList.add('rise'); k.style.setProperty('--d', (i * 0.07).toFixed(2) + 's'); });
  });
  const rio = new IntersectionObserver(entries => entries.forEach(e => {
    if (!e.isIntersecting) return;
    e.target.querySelectorAll(':scope > .rise').forEach(k => k.classList.add('is-in'));
    rio.unobserve(e.target);
  }), { rootMargin: '0px 0px -10% 0px' });
  groups.forEach(g => rio.observe(g));
  // the first screen is in view at load
  requestAnimationFrame(() => document.querySelectorAll('.sheet-main > .rise').forEach(k => k.classList.add('is-in')));
})();
