// ═══════════════════════════════════════════════════════════
//  EFFECTS.JS — Aleix Jiménez Real Estate Operator
//  Interactive effects: cursor, tilt, parallax, map, counters
// ═══════════════════════════════════════════════════════════
(function () {
  'use strict';

  const isMobile = () => window.matchMedia('(hover: none)').matches;

  // ─── 1. CURSOR GLOW ────────────────────────────────────
  function initCursor() {
    const glow = document.getElementById('cursor-glow');
    if (!glow || isMobile()) return;
    let mx = window.innerWidth / 2, my = window.innerHeight / 2;
    let cx = mx, cy = my;
    document.addEventListener('mousemove', e => { mx = e.clientX; my = e.clientY; }, { passive: true });
    function lerp(a, b, t) { return a + (b - a) * t; }
    (function tick() {
      cx = lerp(cx, mx, 0.1);
      cy = lerp(cy, my, 0.1);
      glow.style.transform = `translate(${cx}px, ${cy}px) translate(-50%, -50%)`;
      requestAnimationFrame(tick);
    })();
  }

  // ─── 2. 3D CARD TILT ───────────────────────────────────
  function initTilt() {
    if (isMobile()) return;
    document.querySelectorAll('[data-tilt]').forEach(el => {
      let raf = null;
      el.addEventListener('mousemove', e => {
        if (raf) cancelAnimationFrame(raf);
        raf = requestAnimationFrame(() => {
          const r = el.getBoundingClientRect();
          const x = ((e.clientX - r.left)  / r.width  - 0.5) * 16;
          const y = ((e.clientY - r.top)   / r.height - 0.5) * -16;
          el.style.transform = `perspective(900px) rotateX(${y}deg) rotateY(${x}deg) translateZ(8px)`;
          el.style.transition = 'transform 0.08s ease';
        });
      });
      el.addEventListener('mouseleave', () => {
        if (raf) cancelAnimationFrame(raf);
        el.style.transform = 'perspective(900px) rotateX(0) rotateY(0) translateZ(0)';
        el.style.transition = 'transform 0.55s cubic-bezier(0.23, 1, 0.32, 1)';
      });
    });
  }

  // ─── 3. HERO PARALLAX + TILT ───────────────────────────
  function initHeroParallax() {
    const panel = document.getElementById('hero-panel');
    if (!panel || isMobile()) return;
    const layers = panel.querySelectorAll('[data-depth]');
    let rafId = null;
    let mx = 0, my = 0;
    document.addEventListener('mousemove', e => {
      mx = e.clientX; my = e.clientY;
      if (rafId) return;
      rafId = requestAnimationFrame(() => {
        rafId = null;
        const cx = (mx / window.innerWidth  - 0.5);
        const cy = (my / window.innerHeight - 0.5);
        // Per-layer parallax (depth cards)
        layers.forEach(layer => {
          const d = parseFloat(layer.dataset.depth) || 1;
          layer.style.transform = `translate(${cx * d * 16}px, ${cy * d * 14}px)`;
          layer.style.transition = 'transform 0.55s ease';
        });
        // Subtle 3D tilt on the whole panel
        const tx = cx * 6;
        const ty = cy * -4.5;
        panel.style.transform = `perspective(1100px) rotateY(${tx}deg) rotateX(${ty}deg)`;
        panel.style.transition = 'transform 0.9s ease';
      });
    }, { passive: true });
  }

  // ─── 4. MAP TILT ────────────────────────────────────────
  function initMapTilt() {
    const wrap = document.getElementById('map-wrap');
    if (!wrap || isMobile()) return;
    const svg = wrap.querySelector('svg');
    if (!svg) return;
    wrap.addEventListener('mousemove', e => {
      const r = wrap.getBoundingClientRect();
      const x = ((e.clientX - r.left) / r.width  - 0.5) * 10;
      const y = ((e.clientY - r.top)  / r.height - 0.5) * -10;
      svg.style.transform = `perspective(1200px) rotateX(${y}deg) rotateY(${x}deg)`;
      svg.style.transition = 'transform 0.12s ease';
    });
    wrap.addEventListener('mouseleave', () => {
      svg.style.transform = 'perspective(1200px) rotateX(0) rotateY(0)';
      svg.style.transition = 'transform 0.7s ease';
    });
  }

  // ─── 5. MAP NODE TOOLTIPS ───────────────────────────────
  function initMap() {
    const nodes   = document.querySelectorAll('.map-node');
    const tooltip = document.getElementById('map-tooltip');
    if (!nodes.length || !tooltip) return;

    nodes.forEach(node => {
      node.addEventListener('mouseenter', () => {
        const d = node.dataset;
        tooltip.innerHTML = `
          <div class="mtt-header">
            <span class="mtt-zone">${d.label}</span>
            <span class="mtt-market">${d.market}</span>
          </div>
          <div class="mtt-grid">
            <div class="mtt-cell"><div class="mtt-k">Demanda</div><div class="mtt-v">${d.demand}</div></div>
            <div class="mtt-cell"><div class="mtt-k">€/m²</div><div class="mtt-v">${d.ppm2}</div></div>
            <div class="mtt-cell"><div class="mtt-k">Comprador</div><div class="mtt-v">${d.buyer}</div></div>
            <div class="mtt-cell"><div class="mtt-k">Potencial</div><div class="mtt-v mtt-v-gold">${d.potential}</div></div>
          </div>
        `;
        tooltip.classList.add('visible');
      });

      node.addEventListener('mousemove', e => {
        const pad   = 16;
        const tw    = tooltip.offsetWidth  || 240;
        const th    = tooltip.offsetHeight || 140;
        let left = e.pageX + pad;
        let top  = e.pageY - th / 2;
        if (left + tw > window.innerWidth  - 20) left = e.pageX - tw - pad;
        if (top < 10)                             top  = 10;
        if (top + th > window.innerHeight + window.scrollY - 10)
          top = window.innerHeight + window.scrollY - th - 10;
        tooltip.style.left = left + 'px';
        tooltip.style.top  = top  + 'px';
      });

      node.addEventListener('mouseleave', () => {
        tooltip.classList.remove('visible');
      });
    });
  }

  // ─── 6. SCROLL REVEAL ──────────────────────────────────
  function initReveal() {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('in');
          obs.unobserve(e.target);
        }
      });
    }, { threshold: 0.07, rootMargin: '0px 0px -36px 0px' });
    document.querySelectorAll('.reveal').forEach(el => obs.observe(el));
  }

  // ─── 7. COUNTER ANIMATION ──────────────────────────────
  function initCounters() {
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) { animCounter(e.target); obs.unobserve(e.target); }
      });
    }, { threshold: 0.5 });
    document.querySelectorAll('.counter').forEach(el => obs.observe(el));
  }
  function animCounter(el) {
    const target = +el.dataset.target || 0;
    const dur = 1600;
    const t0 = performance.now();
    (function tick(now) {
      const p = Math.min((now - t0) / dur, 1);
      el.textContent = Math.round((1 - Math.pow(1 - p, 3)) * target);
      if (p < 1) requestAnimationFrame(tick);
    })(t0);
  }

  // ─── 8. HERO CHART BARS ────────────────────────────────
  function initHeroBars() {
    // Confidence bar
    const confBar = document.getElementById('hero-dash-bar');
    if (confBar) setTimeout(() => { confBar.style.width = '88%'; }, 900);

    // New hdb chart bars
    document.querySelectorAll('.hdb-bar').forEach((bar, i) => {
      const fill = bar.querySelector('.hdb-bar-fill');
      if (fill) {
        setTimeout(() => { fill.style.height = (bar.dataset.h || '50') + '%'; }, 700 + i * 130);
      }
    });

    // Legacy hero-cbar (kept for compatibility)
    document.querySelectorAll('.hero-cbar').forEach((b, i) => {
      setTimeout(() => { b.style.height = (b.dataset.h || '50') + '%'; }, 700 + i * 120);
    });
  }

  // ─── 9. TYPING EFFECT ──────────────────────────────────
  function initTyping() {
    const el = document.getElementById('typing-text');
    if (!el) return;
    const words = ['Vender', 'Alquilar', 'Reformar', 'Esperar'];
    let wi = 0, ci = 0, del = false;
    function tick() {
      const w = words[wi];
      if (!del) {
        el.textContent = w.slice(0, ++ci);
        if (ci === w.length) { del = true; setTimeout(tick, 2000); return; }
      } else {
        el.textContent = w.slice(0, --ci);
        if (!ci) { del = false; wi = (wi + 1) % words.length; }
      }
      setTimeout(tick, del ? 55 : 95);
    }
    tick();
  }

  // ─── 10. RADAR ANIMATION ───────────────────────────────
  function initRadar() {
    const items = document.querySelectorAll('.radar-item');
    if (!items.length) return;
    const obs = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        items.forEach((item, i) => {
          setTimeout(() => item.classList.add('active'), i * 80);
        });
        obs.disconnect();
      }
    }, { threshold: 0.3 });
    if (items[0]) obs.observe(items[0].closest('section') || items[0]);
  }

  // ─── 11. PROBLEM CARDS STAGGER ─────────────────────────
  function initProblemCards() {
    const cards = document.querySelectorAll('.prob-card');
    if (!cards.length) return;
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          cards.forEach((c, i) => {
            setTimeout(() => c.classList.add('in'), i * 90);
          });
          obs.disconnect();
        }
      });
    }, { threshold: 0.15 });
    if (cards[0]) obs.observe(cards[0].closest('section') || cards[0]);
  }

  // ─── 10. ANALYSIS MODULE BARS ──────────────────────────
  function initAnalysisBars() {
    const grid = document.getElementById('analysis-grid');
    if (!grid) return;
    const obs = new IntersectionObserver(entries => {
      if (entries[0].isIntersecting) {
        grid.querySelectorAll('.am-fill').forEach((fill, i) => {
          const w = fill.dataset.w || 70;
          setTimeout(() => { fill.style.width = w + '%'; }, i * 80);
        });
        obs.disconnect();
      }
    }, { threshold: 0.2 });
    obs.observe(grid);
  }

  // ─── 11. ZONE PANEL (map interaction) ──────────────────
  function initZonePanel() {
    const nodes   = document.querySelectorAll('.map-node-el');
    const defEl   = document.getElementById('zone-default');
    const dataEl  = document.getElementById('zone-data');
    const panel   = document.getElementById('zone-panel');
    if (!nodes.length || !dataEl) return;

    const POTENTIAL_COLORS = {
      venta:    '#c9a84c',
      alquiler: '#34d399',
      reforma:  '#a855f7',
      inversion:'#4f9ef8',
    };
    const DEMAND_COLORS   = { 1:'#f87171', 2:'#c9a84c', 3:'#34d399' };
    const DEMAND_PCT      = { 1:33,        2:66,        3:100       };

    function showZone(node) {
      // Mark active node
      nodes.forEach(n => n.classList.remove('active'));
      node.classList.add('active');

      const d = node.dataset;
      const level  = parseInt(d.demandLevel) || 2;
      const dColor = DEMAND_COLORS[level]  || '#c9a84c';
      const dPct   = DEMAND_PCT[level]     || 66;
      const pColor = POTENTIAL_COLORS[d.potentialType] || '#c9a84c';

      dataEl.innerHTML = `
        <div class="zp-zone-header">
          <div class="zp-zone-name">${d.name}</div>
          <span class="zp-zone-type">${d.type}</span>
        </div>
        <div class="zp-body">
          <div class="zp-demand-row">
            <span class="zp-demand-lbl">Demanda</span>
            <span class="zp-demand-val" style="color:${dColor}">${d.demand}</span>
          </div>
          <div class="zp-demand-track">
            <div class="zp-demand-fill" style="width:0%;background:${dColor}" id="zp-demand-bar"></div>
          </div>
          <div class="zp-rows">
            <div class="zp-row">
              <div class="zp-row-k">Perfil comprador</div>
              <div class="zp-row-v">${d.buyer}</div>
            </div>
            <div class="zp-row">
              <div class="zp-row-k">Potencial principal</div>
              <div class="zp-row-v potential" style="color:${pColor}">${d.potential}</div>
            </div>
            <div class="zp-row">
              <div class="zp-row-k">Riesgo principal</div>
              <div class="zp-row-v risk">${d.risk}</div>
            </div>
          </div>
        </div>
        <div class="zp-footer">
          <div>
            <div class="zp-ppm2-k">Precio medio orientativo</div>
            <div class="zp-ppm2-v">${d.ppm2}</div>
          </div>
          <a href="#calculadora" class="btn-gold text-xs py-2 px-4">Analizar esta zona</a>
        </div>
      `;

      if (defEl) defEl.classList.add('hidden');
      dataEl.classList.remove('hidden');
      if (panel) panel.classList.add('zp-active');

      // Animate demand bar after render
      requestAnimationFrame(() => {
        const bar = document.getElementById('zp-demand-bar');
        if (bar) setTimeout(() => { bar.style.width = dPct + '%'; }, 80);
      });
    }

    nodes.forEach(node => {
      // Desktop: hover
      node.addEventListener('mouseenter', () => showZone(node));
      // Mobile/touch: click
      node.addEventListener('click', () => showZone(node));
    });
  }

  // ─── INIT ───────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', () => {
    initCursor();
    initTilt();
    initHeroParallax();
    initMapTilt();
    initMap();
    initReveal();
    initCounters();
    initHeroBars();
    initTyping();
    initRadar();
    initProblemCards();
    initAnalysisBars();
    initZonePanel();
  });
})();
