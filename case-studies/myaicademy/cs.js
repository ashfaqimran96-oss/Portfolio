// myAIcademy case study: smooth scroll, reveals, and the few scenes that move with the scroll
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const hasGsap = typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined';

  // reveals: anything marked data-reveal fades up once as it enters
  const io = new IntersectionObserver(entries => entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
  }), { rootMargin: '0px 0px -12% 0px' });
  document.querySelectorAll('[data-reveal]').forEach((el, i) => { el.style.transitionDelay = (i % 4) * 0.08 + 's'; io.observe(el); });

  // the lit squares in the problem grid switch on one after another
  const lit = [...document.querySelectorAll('.pb-grid span.on')];
  new IntersectionObserver((entries, o) => entries.forEach(e => {
    if (!e.isIntersecting) return;
    lit.forEach((s, i) => setTimeout(() => s.classList.add('lit'), reduce ? 0 : 250 + i * 260));
    o.disconnect();
  }), { threshold: 0.4 }).observe(document.querySelector('.pb-grid'));

  // counters run up to their figure the first time they're seen
  const fmt = n => n.toLocaleString('en-US');
  document.querySelectorAll('[data-count]').forEach(el => {
    const to = +el.dataset.count;
    new IntersectionObserver((entries, o) => entries.forEach(e => {
      if (!e.isIntersecting) return;
      o.disconnect();
      if (reduce) return;
      const t0 = performance.now(), dur = 1400;
      const step = t => { const k = Math.min(1, (t - t0) / dur), v = Math.round(to * (1 - Math.pow(1 - k, 3))); el.textContent = fmt(v); if (k < 1) requestAnimationFrame(step); };
      requestAnimationFrame(step);
    }), { threshold: 0.6 }).observe(el);
  });

  if (!hasGsap || reduce) return;
  gsap.registerPlugin(ScrollTrigger);
  if (typeof Lenis !== 'undefined') {
    const lenis = new Lenis({ lerp: 0.1 });
    lenis.on('scroll', ScrollTrigger.update);
    gsap.ticker.add(t => lenis.raf(t * 1000));
    gsap.ticker.lagSmoothing(0);
  }

  // hero: the phones rise out of the horizon, the wordmark sinks behind them
  gsap.from('.hero-phones .phone', { yPercent: 40, opacity: 0, duration: 1.4, stagger: 0.12, ease: 'power3.out', delay: 0.2 });
  gsap.from('.hero-word', { yPercent: 20, opacity: 0, duration: 1.6, ease: 'power3.out' });
  gsap.to('.hero-word', { yPercent: 30, opacity: 0.25, ease: 'none', scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true } });
  gsap.to('.hero-phones', { yPercent: -10, ease: 'none', scrollTrigger: { trigger: '.hero', start: 'top top', end: 'bottom top', scrub: true } });

  // the rings tilt up into place as their sections arrive
  gsap.from('.ring', { rotateX: 88, scale: 0.6, opacity: 0, ease: 'power2.out', scrollTrigger: { trigger: '.ring-stage', start: 'top 85%', end: 'center 55%', scrub: true } });
  gsap.from('.platform i', { scale: 0.4, opacity: 0, stagger: 0.1, ease: 'power2.out', scrollTrigger: { trigger: '.platform-stage', start: 'top 85%', end: 'center 60%', scrub: true } });
  gsap.from('.beam-rings li', { scale: 0.7, opacity: 0, stagger: 0.18, ease: 'power2.out', scrollTrigger: { trigger: '.beam', start: 'top 80%', end: 'bottom 70%', scrub: true } });
  gsap.from('.beam-light', { opacity: 0, ease: 'none', scrollTrigger: { trigger: '.beam', start: 'top 80%', end: 'center 60%', scrub: true } });

  // pedestals grow from the floor in priority order
  gsap.from('.ped', { scaleY: 0, stagger: 0.15, ease: 'power3.out', duration: 1.1, scrollTrigger: { trigger: '.pedestals', start: 'top 70%' } });

  // the Aimy browser leans back onto the horizon
  gsap.from('.browser', { rotateX: 18, yPercent: 12, transformPerspective: 1400, transformOrigin: '50% 100%', ease: 'none', scrollTrigger: { trigger: '.pd-aimy', start: 'top 80%', end: 'center 50%', scrub: true } });

  // the type curve draws itself
  const curve = document.querySelector('.type-curve path');
  const len = curve.getTotalLength();
  gsap.fromTo(curve, { strokeDasharray: len, strokeDashoffset: len }, { strokeDashoffset: 0, ease: 'none', scrollTrigger: { trigger: '.type-spec', start: 'top 80%', end: 'bottom 50%', scrub: true } });
  gsap.from('.orb', { scale: 0.5, opacity: 0, stagger: 0.1, duration: 0.9, ease: 'back.out(1.6)', scrollTrigger: { trigger: '.orbs', start: 'top 80%' } });
})();
