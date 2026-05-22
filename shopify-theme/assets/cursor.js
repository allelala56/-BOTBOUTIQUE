/**
 * BotBoutique — Curseur custom avec traînée néon
 * Désactivé sur mobile/tablet (pointer: coarse)
 */

(function () {
  'use strict';

  if (window.matchMedia('(pointer: coarse)').matches) return;
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  /* ── DOM ──────────────────────────────────────────────────── */

  const cursor = document.createElement('div');
  cursor.id = 'bb-cursor';
  cursor.innerHTML = '<div class="bb-cursor__dot"></div>';

  const trail = document.createElement('div');
  trail.id = 'bb-cursor-trail';

  const styleEl = document.createElement('style');
  styleEl.textContent = `
    *, *::before, *::after { cursor: none !important; }

    #bb-cursor {
      position: fixed;
      top: 0; left: 0;
      pointer-events: none;
      z-index: 99999;
      mix-blend-mode: difference;
      transform: translate(-50%, -50%);
      transition: transform 80ms linear;
    }

    .bb-cursor__dot {
      width: 10px;
      height: 10px;
      background: #00F0FF;
      border-radius: 50%;
      transition: transform 0.15s cubic-bezier(0.16,1,0.3,1), background 0.2s;
      box-shadow: 0 0 12px #00F0FF, 0 0 24px rgba(0,240,255,0.5);
    }

    #bb-cursor.is-hovering .bb-cursor__dot {
      transform: scale(3);
      background: #B847FF;
      box-shadow: 0 0 20px #B847FF, 0 0 40px rgba(184,71,255,0.5);
    }

    #bb-cursor.is-clicking .bb-cursor__dot {
      transform: scale(0.6);
    }

    #bb-cursor-trail {
      position: fixed;
      top: 0; left: 0;
      pointer-events: none;
      z-index: 99998;
      transform: translate(-50%, -50%);
    }

    .bb-trail-particle {
      position: absolute;
      width: 4px;
      height: 4px;
      border-radius: 50%;
      background: var(--color, #00F0FF);
      pointer-events: none;
      transform: translate(-50%, -50%);
      animation: trailFade var(--dur, 0.6s) ease-out forwards;
    }

    @keyframes trailFade {
      0%   { opacity: 0.8; transform: translate(-50%, -50%) scale(1); }
      100% { opacity: 0;   transform: translate(-50%, -50%) scale(0.2); }
    }
  `;

  document.head.appendChild(styleEl);
  document.body.appendChild(cursor);
  document.body.appendChild(trail);

  /* ── State ────────────────────────────────────────────────── */

  let mx = -100, my = -100;
  let cx = -100, cy = -100;
  let isHovering = false;
  let lastTrailTime = 0;

  /* ── Mouse tracking ───────────────────────────────────────── */

  document.addEventListener('mousemove', e => {
    mx = e.clientX;
    my = e.clientY;

    // Traînée
    const now = Date.now();
    if (now - lastTrailTime > 35) {
      spawnParticle(mx, my);
      lastTrailTime = now;
    }
  });

  document.addEventListener('mousedown', () => cursor.classList.add('is-clicking'));
  document.addEventListener('mouseup',   () => cursor.classList.remove('is-clicking'));

  /* Hover sur éléments interactifs */
  const hoverTargets = 'a, button, [role="button"], input, select, textarea, label, .btn, .product-card, .variant-pill, .faq-question, .product-gallery__thumb';

  document.addEventListener('mouseover', e => {
    if (e.target.closest(hoverTargets)) {
      isHovering = true;
      cursor.classList.add('is-hovering');
    }
  });

  document.addEventListener('mouseout', e => {
    if (e.target.closest(hoverTargets)) {
      isHovering = false;
      cursor.classList.remove('is-hovering');
    }
  });

  /* Hide when leaving window */
  document.addEventListener('mouseleave', () => { cursor.style.opacity = '0'; });
  document.addEventListener('mouseenter', () => { cursor.style.opacity = '1'; });

  /* ── RAF loop — smooth following ──────────────────────────── */

  const lerpSpeed = 0.18;

  function loop() {
    cx = cx + (mx - cx) * lerpSpeed;
    cy = cy + (my - cy) * lerpSpeed;

    cursor.style.left = cx + 'px';
    cursor.style.top  = cy + 'px';

    requestAnimationFrame(loop);
  }

  loop();

  /* ── Trail particles ──────────────────────────────────────── */

  const colors = ['#00F0FF', '#B847FF', '#00FF94'];

  function spawnParticle(x, y) {
    const el = document.createElement('div');
    el.className = 'bb-trail-particle';

    const color = colors[Math.floor(Math.random() * colors.length)];
    const dur = (0.4 + Math.random() * 0.35).toFixed(2);
    const offsetX = (Math.random() - 0.5) * 14;
    const offsetY = (Math.random() - 0.5) * 14;
    const size = 2 + Math.random() * 3;

    el.style.cssText = `
      left: ${x + offsetX}px;
      top:  ${y + offsetY}px;
      width:  ${size}px;
      height: ${size}px;
      --color: ${color};
      --dur: ${dur}s;
    `;

    trail.appendChild(el);
    setTimeout(() => el.remove(), parseFloat(dur) * 1000 + 50);
  }

})();
