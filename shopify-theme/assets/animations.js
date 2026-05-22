/**
 * BotBoutique — Animations & Scroll Effects
 * GSAP + IntersectionObserver (pas de dépendance externe obligatoire)
 */

(function () {
  'use strict';

  /* ── Utilitaires ───────────────────────────────────────────── */

  const raf = requestAnimationFrame;
  const select  = (s, ctx = document) => ctx.querySelector(s);
  const selectAll = (s, ctx = document) => [...ctx.querySelectorAll(s)];

  function lerp(a, b, t) { return a + (b - a) * t; }

  /* ── IntersectionObserver — Reveal au scroll ───────────────── */

  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  // Appliquer aux éléments data-reveal
  function initReveal() {
    selectAll('[data-reveal]').forEach((el, i) => {
      el.style.transitionDelay = `${(el.dataset.revealDelay || i * 80)}ms`;
      revealObserver.observe(el);
    });
  }

  /* ── Hero Typewriter ───────────────────────────────────────── */

  function initTypewriter() {
    const el = select('[data-typewriter]');
    if (!el) return;

    const words = (el.dataset.typewriter || el.textContent).split('|');
    let wordIdx = 0;
    let charIdx = 0;
    let isDeleting = false;
    const typingSpeed   = 65;
    const deletingSpeed = 35;
    const pauseAfterWord = 2200;

    el.textContent = '';

    function tick() {
      const word = words[wordIdx % words.length];

      if (isDeleting) {
        el.textContent = word.substring(0, charIdx - 1);
        charIdx--;
      } else {
        el.textContent = word.substring(0, charIdx + 1);
        charIdx++;
      }

      let delay = isDeleting ? deletingSpeed : typingSpeed;

      if (!isDeleting && charIdx === word.length) {
        delay = pauseAfterWord;
        isDeleting = true;
      } else if (isDeleting && charIdx === 0) {
        isDeleting = false;
        wordIdx++;
        delay = 400;
      }

      setTimeout(tick, delay);
    }

    tick();
  }

  /* ── Hero Split Text (CSS-only, no GSAP required) ─────────── */

  function initHeroSplitText() {
    const el = select('[data-split-animate]');
    if (!el) return;

    const text = el.textContent;
    el.innerHTML = '';

    text.split('').forEach((char, i) => {
      const span = document.createElement('span');
      span.textContent = char === ' ' ? ' ' : char;
      span.style.cssText = `
        display: inline-block;
        opacity: 0;
        transform: translateY(24px);
        animation: charReveal 0.6s cubic-bezier(0.16,1,0.3,1) forwards;
        animation-delay: ${i * 28}ms;
      `;
      el.appendChild(span);
    });
  }

  /* ── Product Card 3D Tilt ──────────────────────────────────── */

  function initCardTilt() {
    selectAll('.product-card[data-tilt]').forEach(card => {
      let rect, active = false;
      let cx = 0.5, cy = 0.5;
      let rx = 0, ry = 0;

      card.addEventListener('mouseenter', () => {
        rect = card.getBoundingClientRect();
        active = true;
      });

      card.addEventListener('mousemove', e => {
        if (!active) return;
        cx = (e.clientX - rect.left) / rect.width;
        cy = (e.clientY - rect.top)  / rect.height;
      });

      card.addEventListener('mouseleave', () => {
        active = false;
        cx = 0.5; cy = 0.5;
      });

      function loop() {
        const tx = active ? (cx - 0.5) * 16 : 0;
        const ty = active ? (cy - 0.5) * -16 : 0;
        rx = lerp(rx, tx, 0.1);
        ry = lerp(ry, ty, 0.1);

        card.style.transform = `perspective(800px) rotateY(${rx}deg) rotateX(${ry}deg)`;
        raf(loop);
      }

      loop();
    });
  }

  /* ── Sticky Header shrink on scroll ───────────────────────── */

  function initStickyHeader() {
    const header = select('.site-header');
    if (!header) return;

    let lastY = 0;

    window.addEventListener('scroll', () => {
      const y = window.scrollY;
      header.classList.toggle('is-scrolled', y > 60);
      header.classList.toggle('is-hidden', y > lastY && y > 200);
      lastY = y;
    }, { passive: true });
  }

  /* ── Gradient border hover animation ──────────────────────── */

  function initGradientBorders() {
    selectAll('.card-gradient-border').forEach(card => {
      card.addEventListener('mousemove', e => {
        const rect = card.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width)  * 100;
        const y = ((e.clientY - rect.top)  / rect.height) * 100;
        card.style.setProperty('--mouse-x', `${x}%`);
        card.style.setProperty('--mouse-y', `${y}%`);
      });
    });
  }

  /* ── Countdown Timer ───────────────────────────────────────── */

  function initCountdown() {
    selectAll('[data-countdown]').forEach(el => {
      const endTime = new Date(el.dataset.countdown).getTime();

      function update() {
        const diff = endTime - Date.now();
        if (diff <= 0) { el.textContent = 'Terminé'; return; }

        const h = Math.floor(diff / 3600000);
        const m = Math.floor((diff % 3600000) / 60000);
        const s = Math.floor((diff % 60000) / 1000);

        el.textContent = `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
      }

      update();
      setInterval(update, 1000);
    });
  }

  /* ── Product Image Gallery ─────────────────────────────────── */

  function initProductGallery() {
    const mainImg = select('.product-gallery__main img');
    if (!mainImg) return;

    selectAll('.product-gallery__thumb').forEach(thumb => {
      thumb.addEventListener('click', () => {
        const newSrc = thumb.querySelector('img').src;

        mainImg.style.opacity = '0';
        mainImg.style.transform = 'scale(0.97)';

        setTimeout(() => {
          mainImg.src = newSrc;
          mainImg.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
          mainImg.style.opacity = '1';
          mainImg.style.transform = 'scale(1)';
        }, 150);

        selectAll('.product-gallery__thumb').forEach(t => t.classList.remove('active'));
        thumb.classList.add('active');
      });
    });
  }

  /* ── FAQ Accordion ─────────────────────────────────────────── */

  function initFAQ() {
    selectAll('.faq-item').forEach(item => {
      const btn = item.querySelector('.faq-question');
      if (!btn) return;

      btn.addEventListener('click', () => {
        const isOpen = item.classList.contains('open');
        selectAll('.faq-item.open').forEach(openItem => {
          if (openItem !== item) openItem.classList.remove('open');
        });
        item.classList.toggle('open', !isOpen);
      });
    });
  }

  /* ── Quantity Selector ─────────────────────────────────────── */

  function initQuantitySelector() {
    selectAll('.quantity-selector').forEach(selector => {
      const input = selector.querySelector('.quantity-input');
      const btnMinus = selector.querySelector('[data-qty-minus]');
      const btnPlus  = selector.querySelector('[data-qty-plus]');
      if (!input) return;

      btnMinus?.addEventListener('click', () => {
        const val = parseInt(input.value) || 1;
        if (val > 1) input.value = val - 1;
      });

      btnPlus?.addEventListener('click', () => {
        input.value = (parseInt(input.value) || 1) + 1;
      });
    });
  }

  /* ── Variant Pills ─────────────────────────────────────────── */

  function initVariantPills() {
    selectAll('.variant-pills').forEach(group => {
      group.querySelectorAll('.variant-pill').forEach(pill => {
        pill.addEventListener('click', () => {
          group.querySelectorAll('.variant-pill').forEach(p => p.classList.remove('selected'));
          pill.classList.add('selected');
        });
      });
    });
  }

  /* ── Reviews Horizontal Scroll Carousel ───────────────────── */

  function initReviewsCarousel() {
    const track = select('.reviews-carousel__track');
    if (!track) return;

    let isDown = false, startX = 0, scrollLeft = 0;

    track.addEventListener('mousedown', e => {
      isDown = true;
      startX = e.pageX - track.offsetLeft;
      scrollLeft = track.scrollLeft;
      track.style.cursor = 'grabbing';
    });

    track.addEventListener('mouseleave', () => { isDown = false; track.style.cursor = 'grab'; });
    track.addEventListener('mouseup',    () => { isDown = false; track.style.cursor = 'grab'; });

    track.addEventListener('mousemove', e => {
      if (!isDown) return;
      e.preventDefault();
      const x = e.pageX - track.offsetLeft;
      track.scrollLeft = scrollLeft - (x - startX) * 1.5;
    });
  }

  /* ── Announcement Bar — ticker auto-scroll ─────────────────── */

  function initAnnouncementTicker() {
    const bar = select('.announcement-bar__ticker');
    if (!bar) return;

    const clone = bar.cloneNode(true);
    bar.parentElement.appendChild(clone);
    bar.parentElement.style.cssText = 'overflow:hidden; display:flex;';
    bar.style.animation = 'ticker 24s linear infinite';
    clone.style.animation = 'ticker 24s linear infinite';
    clone.style.animationDelay = '-12s';
  }

  /* ── Scroll Progress Bar ───────────────────────────────────── */

  function initScrollProgress() {
    const bar = select('#scroll-progress');
    if (!bar) return;

    window.addEventListener('scroll', () => {
      const pct = (window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100;
      bar.style.width = `${Math.min(pct, 100)}%`;
    }, { passive: true });
  }

  /* ── Add To Cart — micro-interaction ──────────────────────── */

  function initAddToCart() {
    selectAll('[data-add-to-cart]').forEach(btn => {
      btn.addEventListener('click', function(e) {
        if (btn.classList.contains('is-loading')) return;

        const originalText = btn.innerHTML;
        btn.classList.add('is-loading');
        btn.innerHTML = '<span class="spinner"></span> Ajout en cours…';

        setTimeout(() => {
          btn.classList.remove('is-loading');
          btn.classList.add('is-success');
          btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg> Ajouté !';

          setTimeout(() => {
            btn.classList.remove('is-success');
            btn.innerHTML = originalText;
          }, 2200);
        }, 800);
      });
    });
  }

  /* ── Init tout au chargement ───────────────────────────────── */

  document.addEventListener('DOMContentLoaded', () => {
    initReveal();
    initTypewriter();
    initHeroSplitText();
    initCardTilt();
    initStickyHeader();
    initGradientBorders();
    initCountdown();
    initProductGallery();
    initFAQ();
    initQuantitySelector();
    initVariantPills();
    initReviewsCarousel();
    initAnnouncementTicker();
    initScrollProgress();
    initAddToCart();
  });

  /* Injecter les keyframes manquants */
  const style = document.createElement('style');
  style.textContent = `
    @keyframes charReveal {
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes ticker {
      from { transform: translateX(0); }
      to   { transform: translateX(-50%); }
    }
    .site-header {
      transition: transform 0.3s ease, background 0.3s ease;
    }
    .site-header.is-hidden {
      transform: translateY(-100%);
    }
    .site-header.is-scrolled {
      background: rgba(10,10,15,0.97);
    }
    [data-reveal] {
      opacity: 0;
      transform: translateY(20px);
      transition: opacity 0.6s cubic-bezier(0.16,1,0.3,1), transform 0.6s cubic-bezier(0.16,1,0.3,1);
    }
    [data-reveal].is-visible {
      opacity: 1;
      transform: translateY(0);
    }
    .btn.is-loading, .btn.is-success {
      pointer-events: none;
    }
    .btn.is-success {
      background: var(--color-success) !important;
      color: #0A0A0F !important;
    }
    .spinner {
      display: inline-block;
      width: 14px; height: 14px;
      border: 2px solid rgba(0,0,0,0.3);
      border-top-color: #0A0A0F;
      border-radius: 50%;
      animation: spin 0.7s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    #scroll-progress {
      position: fixed;
      top: 0; left: 0;
      height: 2px;
      background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
      z-index: 9999;
      transition: width 0.1s linear;
    }
  `;
  document.head.appendChild(style);

})();
