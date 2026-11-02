/* MTH Labs interactive ambient effects: progressive enhancement, no dependencies. */
(() => {
  'use strict';
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  if (reduced.matches || !window.requestAnimationFrame) return;
  const canvas = document.createElement('canvas');
  canvas.className = 'mth-particle-layer';
  canvas.setAttribute('aria-hidden', 'true');
  document.body.appendChild(canvas);
  const ctx = canvas.getContext('2d', { alpha: true });
  if (!ctx) { canvas.remove(); return; }
  let width = 0, height = 0, dpr = 1, lastFrame = 0, lastTrail = 0, previousY = window.scrollY;
  const particles = [];
  const maxParticles = 155;
  const pointer = { x: -1000, y: -1000 };
  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  function emit(x, y, count, burst = false) {
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = (burst ? 1.3 : 0.35) + Math.random() * (burst ? 3.5 : 1.4);
      particles.push({
        x, y, vx: Math.cos(angle) * speed, vy: Math.sin(angle) * speed,
        life: 1, decay: (burst ? 0.014 : 0.022) + Math.random() * 0.013,
        radius: 0.7 + Math.random() * (burst ? 2.2 : 1.4),
        hue: Math.random() > 0.16 ? 201 : 266
      });
    }
    if (particles.length > maxParticles) particles.splice(0, particles.length - maxParticles);
  }
  function animate(timestamp) {
    if (document.hidden || reduced.matches) return;
    if (timestamp - lastFrame < 16) { requestAnimationFrame(animate); return; }
    const step = Math.min((timestamp - (lastFrame || timestamp)) / 16.7, 2);
    lastFrame = timestamp;
    ctx.clearRect(0, 0, width, height);
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.x += p.vx * step;
      p.y += p.vy * step;
      p.vx *= 0.985; p.vy *= 0.985;
      p.life -= p.decay * step;
      if (p.life <= 0) { particles.splice(i, 1); continue; }
      ctx.beginPath();
      ctx.fillStyle = 'hsla(' + p.hue + ',100%,72%,' + (p.life * 0.86) + ')';
      ctx.shadowBlur = 11;
      ctx.shadowColor = '#258dff';
      ctx.arc(p.x, p.y, Math.max(0.2, p.radius * p.life), 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.shadowBlur = 0;
    requestAnimationFrame(animate);
  }
  function pointerMove(event) {
    if (event.pointerType === 'touch') return;
    pointer.x = event.clientX; pointer.y = event.clientY;
    if (performance.now() - lastTrail > 28) {
      emit(pointer.x, pointer.y, 2);
      lastTrail = performance.now();
    }
  }
  function clickBurst(event) {
    if (event.target.closest('input,textarea,select')) return;
    emit(event.clientX, event.clientY, 24, true);
  }
  function scrollSpark() {
    const delta = Math.abs(window.scrollY - previousY);
    previousY = window.scrollY;
    if (delta > 5 && Math.random() > 0.7) {
      emit(Math.random() > 0.5 ? 24 : width - 24, height * (0.25 + Math.random() * 0.5), 2);
    }
  }
  window.addEventListener('resize', resize, { passive: true });
  window.addEventListener('pointermove', pointerMove, { passive: true });
  window.addEventListener('pointerdown', clickBurst, { passive: true });
  window.addEventListener('scroll', scrollSpark, { passive: true });
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden && !reduced.matches) { lastFrame = 0; requestAnimationFrame(animate); }
  });
  reduced.addEventListener('change', () => { if (reduced.matches) { particles.length = 0; ctx.clearRect(0,0,width,height); } else { lastFrame=0; requestAnimationFrame(animate); } });
  resize();
  requestAnimationFrame(animate);
  if ('IntersectionObserver' in window) {
    const targets = document.querySelectorAll('.service-card, .project-card, .section-heading, .process-card, .game-project, .studio-copy, .faq-section');
    targets.forEach(el => el.classList.add('mth-reveal'));
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) { entry.target.classList.add('mth-visible'); observer.unobserve(entry.target); }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px 45px 0px' });
    targets.forEach(el => observer.observe(el));
  }
})();