/* ═══════════════════════════════════════════════════════════
   ALEIX JIMÉNEZ — Promotoras Landing · Comportamiento
═══════════════════════════════════════════════════════════ */
(function () {
  'use strict';

  var C = window.PCONTENT;
  if (!C) { console.error('promotoras-content.js no cargado'); return; }

  /* ── Tiny HTML helpers ─────────────────────────────────── */
  function esc(v) {
    return String(v)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
  function attr(v) { return esc(v); }

  /* ══════════════════════════════════════════════════════════
     BUILD HTML
  ══════════════════════════════════════════════════════════ */
  function buildHeader() {
    var h = C.header;
    var navLinks = h.links.map(function(l) {
      return '<a href="' + attr(l.href) + '">' + esc(l.label) + '</a>';
    }).join('');
    var mobileLinks = h.links.map(function(l) {
      return '<a href="' + attr(l.href) + '" class="p-mobile-close">' + esc(l.label) + '</a>';
    }).join('');
    return (
      '<header class="p-header" id="p-header" role="banner">' +
        '<a href="#inicio" class="p-header-brand" aria-label="Inicio">' + esc(h.brand) + '</a>' +
        '<nav class="p-header-nav" aria-label="Navegación de la landing">' +
          navLinks +
          '<a href="' + attr(h.cta.href) + '" class="p-header-hablemos">' + esc(h.cta.label) + '</a>' +
        '</nav>' +
        '<button class="p-hamburger" id="p-hamburger" aria-label="Abrir menú" aria-expanded="false">' +
          '<span></span><span></span><span></span>' +
        '</button>' +
      '</header>' +
      '<div class="p-mobile-nav" id="p-mobile-nav" role="dialog" aria-modal="true" aria-label="Menú">' +
        mobileLinks +
        '<a href="' + attr(h.cta.href) + '" class="p-header-hablemos p-mobile-close">' + esc(h.cta.label) + '</a>' +
      '</div>'
    );
  }

  function buildHero() {
    var h = C.hero;
    var tags = h.tags.map(function(t) {
      return '<span class="p-hero-tag">' + esc(t) + '</span>';
    }).join('');
    var lastIdx = h.headlineLines.length - 1;
    var regularLines = h.headlineLines.slice(0, lastIdx).map(function(line, i) {
      return '<span class="p-hl-wrap"><span class="p-hl-line" style="--li:' + i + '">' + esc(line) + '</span></span>';
    }).join('');
    var lastLine = (
      '<span class="p-hl-wrap">' +
        '<span class="p-hl-line" style="--li:' + lastIdx + '">' +
          esc(h.headlineLines[lastIdx]) + ' <em class="p-serif">' + esc(h.headlineAccent) + '</em>' +
        '</span>' +
      '</span>'
    );
    return (
      '<section class="p-hero" id="inicio" aria-label="Presentación">' +
        '<div class="p-hero-inner">' +

          '<div class="p-hero-text">' +
            '<p class="p-hero-meta">' + esc(h.label) + '</p>' +
            '<h1 class="p-hero-headline">' + regularLines + lastLine + '</h1>' +
            '<p class="p-hero-body">' + esc(h.body) + '</p>' +
            '<div class="p-hero-ctas">' +
              '<a href="' + attr(h.cta1.href) + '" class="p-cta-outline">' + esc(h.cta1.label) + '</a>' +
              '<a href="' + attr(h.cta2.href) + '" class="p-cta-text">' + esc(h.cta2.label) + '</a>' +
            '</div>' +
            '<div class="p-hero-tags" aria-hidden="true">' + tags + '</div>' +
          '</div>' +

          '<div class="p-hero-divider" aria-hidden="true"></div>' +

          '<div class="p-hero-portrait">' +
            '<img src="' + attr(h.portrait) + '" alt="' + attr(h.portraitAlt) + '" loading="eager" fetchpriority="high">' +
            '<div class="p-hero-portrait-grad" aria-hidden="true"></div>' +
            '<div class="p-hero-portrait-label" aria-hidden="true">' + esc(h.portraitLabel) + '</div>' +
          '</div>' +

        '</div>' +
      '</section>'
    );
  }

  function buildManifesto() {
    var m = C.manifesto;
    var theses = m.theses.map(function(t, i) {
      return (
        '<div class="p-manifesto-thesis p-reveal" style="transition-delay:' + (i * 0.12) + 's">' +
          '<span class="p-manifesto-thesis-num" aria-hidden="true">' + esc(t.num) + '</span>' +
          '<p class="p-manifesto-thesis-text">' + esc(t.text) + '</p>' +
        '</div>'
      );
    }).join('');

    /* Inyecta serif italic en la palabra de acento */
    var climaxParts = m.climax.split(m.climaxAccent);
    var climaxHtml = esc(climaxParts[0]) +
      '<em class="p-serif">' + esc(m.climaxAccent) + '</em>' +
      (climaxParts[1] ? esc(climaxParts[1]) : '');

    return (
      '<section class="p-manifesto" aria-label="Manifiesto">' +
        '<div class="p-manifesto-inner">' +

          '<div class="p-manifesto-sidebar p-reveal">' +
            '<div class="p-manifesto-sidebar-line" aria-hidden="true"></div>' +
            '<div class="p-manifesto-sidebar-meta">' +
              '<span class="p-manifesto-sidebar-label">' + esc(m.label) + '</span>' +
              '<span class="p-manifesto-sidebar-index">' + esc(m.index) + '</span>' +
            '</div>' +
          '</div>' +

          '<div class="p-manifesto-content">' +
            theses +
            '<h2 class="p-manifesto-climax p-reveal" style="transition-delay:0.44s">' +
              climaxHtml +
            '</h2>' +
          '</div>' +

        '</div>' +
      '</section>'
    );
  }

  function buildPositioning() {
    var p = C.positioning;
    var theses = p.theses.map(function(t, i) {
      return (
        '<div class="p-manifesto-thesis p-reveal" style="transition-delay:' + (i * 0.12) + 's">' +
          '<span class="p-manifesto-thesis-num" aria-hidden="true">' + esc(t.num) + '</span>' +
          '<p class="p-manifesto-thesis-text">' + esc(t.text) + '</p>' +
        '</div>'
      );
    }).join('');

    var climaxParts = p.climax.split(p.climaxAccent);
    var climaxHtml = esc(climaxParts[0]) +
      '<em class="p-serif">' + esc(p.climaxAccent) + '</em>' +
      (climaxParts[1] ? esc(climaxParts[1]) : '');

    return (
      '<section class="p-positioning" id="enfoque" aria-label="El enfoque">' +
        '<div class="p-positioning-inner">' +

          '<div class="p-manifesto-sidebar p-reveal">' +
            '<div class="p-manifesto-sidebar-line" aria-hidden="true"></div>' +
            '<div class="p-manifesto-sidebar-meta">' +
              '<span class="p-manifesto-sidebar-label">' + esc(p.label) + '</span>' +
              '<span class="p-manifesto-sidebar-index">' + esc(p.index) + '</span>' +
            '</div>' +
          '</div>' +

          '<div>' +
            theses +
            '<h2 class="p-manifesto-climax p-reveal" style="transition-delay:0.44s">' +
              climaxHtml +
            '</h2>' +
          '</div>' +

        '</div>' +
      '</section>'
    );
  }

  function buildSystem() {
    var s = C.system;
    var items = s.items.map(function(item, i) {
      return (
        '<div class="p-system-item' + (i === 0 ? ' active' : '') + '" ' +
             'tabindex="0" role="button" ' +
             'aria-expanded="' + (i === 0 ? 'true' : 'false') + '" ' +
             'aria-label="' + attr(item.num + ' — ' + item.title) + '">' +
          '<div class="p-system-item-grid">' +
            '<div>' +
              '<h3 class="p-system-item-title">' +
                '<span class="p-system-item-num" aria-hidden="true">' + esc(item.num) + '</span>' +
                esc(item.title) +
              '</h3>' +
              '<div class="p-system-item-expand">' +
                '<p class="p-system-item-desc">' + esc(item.body) + '</p>' +
              '</div>' +
            '</div>' +
            '<div class="p-system-item-img-wrap" aria-hidden="true">' +
              '<img src="' + attr(item.image) + '" alt="" loading="lazy" ' +
                   'onerror="this.style.visibility=\'hidden\'">' +
            '</div>' +
          '</div>' +
        '</div>'
      );
    }).join('');

    return (
      '<section class="p-system" id="sistema" aria-label="Qué integra el sistema">' +
        '<div class="p-system-inner">' +
          '<div class="p-system-header p-reveal">' +
            '<div class="p-system-header-left">' +
              '<span class="p-system-header-line" aria-hidden="true"></span>' +
              '<span class="p-system-header-label">' + esc(s.sectionLabel) + '</span>' +
            '</div>' +
            '<span class="p-system-header-index">' + esc(s.index) + '</span>' +
          '</div>' +
          '<div class="p-system-list">' + items + '</div>' +
        '</div>' +
      '</section>'
    );
  }

  function buildImpact() {
    var im = C.impact;
    var lines = im.headlineLines.map(function(line, i) {
      return (
        '<span class="p-impact-line-wrap">' +
          '<span class="p-impact-line" style="--li:' + i + '">' + esc(line) + '</span>' +
        '</span>'
      );
    }).join('');
    var accentLine = (
      '<span class="p-impact-line-wrap">' +
        '<span class="p-impact-line" style="--li:' + im.headlineLines.length + '">' +
          '<em class="p-serif">' + esc(im.headlineAccent) + '</em>' +
        '</span>' +
      '</span>'
    );
    return (
      '<section class="p-impact" aria-label="Frase de impacto">' +
        '<div class="p-impact-inner">' +
          '<p class="p-impact-label">' + esc(im.label) + '</p>' +
          '<h2 class="p-impact-headline">' + lines + accentLine + '</h2>' +
          '<div class="p-impact-support">' +
            '<div class="p-impact-support-inner">' +
              '<span class="p-impact-support-rule" aria-hidden="true"></span>' +
              '<p class="p-impact-support-text">' + esc(im.support) + '</p>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</section>'
    );
  }

  function buildForWhom() {
    var fw = C.forWhom;
    var titleParts = fw.title.split(fw.titleAccent);
    var titleHtml = esc(titleParts[0]) + '<em class="p-serif">' + esc(fw.titleAccent) + '</em>' + (titleParts[1] ? esc(titleParts[1]) : '');
    var items = fw.items.map(function(item, i) {
      var cls = 'p-forwhom-item' + (item.featured ? ' p-forwhom-item--featured' : '') + ' p-reveal p-reveal-d' + (i + 1);
      return (
        '<div class="' + cls + '">' +
          '<div class="p-forwhom-item-role">' + esc(item.role) + '</div>' +
          '<div>' +
            '<div class="p-forwhom-item-name">' + esc(item.name) + '</div>' +
            '<div class="p-forwhom-item-desc">' + esc(item.body) + '</div>' +
          '</div>' +
        '</div>'
      );
    }).join('');
    return (
      '<section class="p-forwhom" aria-label="Para quién">' +
        '<div class="p-forwhom-inner">' +
          '<div class="p-forwhom-left p-reveal">' +
            '<div class="p-forwhom-left-meta">' +
              '<span class="p-forwhom-left-rule" aria-hidden="true"></span>' +
              '<span class="p-forwhom-left-label">' + esc(fw.label) + '</span>' +
            '</div>' +
            '<h2 class="p-forwhom-left-title">' + titleHtml + '</h2>' +
          '</div>' +
          '<div class="p-forwhom-right">' + items + '</div>' +
        '</div>' +
      '</section>'
    );
  }

  function buildProcess() {
    var pr = C.process;
    var steps = pr.steps.map(function(step, i) {
      return (
        '<div class="p-process-step p-reveal p-reveal-d' + (i + 1) + '">' +
          '<span class="p-process-step-num">' + esc(step.num) + '</span>' +
          '<h3 class="p-process-step-title">' + esc(step.title) + '</h3>' +
          '<p class="p-process-step-body">' + esc(step.body) + '</p>' +
        '</div>'
      );
    }).join('');
    return (
      '<section class="p-process" aria-label="Proceso">' +
        '<div class="p-process-inner">' +
          '<h2 class="p-process-title p-reveal">' + esc(pr.title) + '</h2>' +
          '<div class="p-process-grid">' + steps + '</div>' +
        '</div>' +
      '</section>'
    );
  }

  function buildAbout() {
    var a = C.about;
    return (
      '<section class="p-about" id="sobre-mi" aria-label="Sobre Aleix">' +
        '<div class="p-about-inner">' +
          '<div class="p-about-img-wrap p-reveal">' +
            '<img class="p-about-img" src="' + attr(a.image) + '" alt="' + attr(a.imageAlt) + '" loading="lazy" width="800" height="1000">' +
            '<span class="p-about-img-label" aria-hidden="true">' + esc(a.label) + '</span>' +
          '</div>' +
          '<div class="p-reveal p-reveal-d2">' +
            '<div class="p-label">' + esc(a.label) + '</div>' +
            '<h2 class="p-about-headline">' + esc(a.headline) + '</h2>' +
            '<p class="p-about-body">' + esc(a.body) + '</p>' +
            '<p class="p-about-closing">' + esc(a.closing) + '</p>' +
          '</div>' +
        '</div>' +
      '</section>'
    );
  }

  function buildCollaboration() {
    var co = C.collaboration;
    return (
      '<section class="p-collab" aria-label="Modelo de colaboración">' +
        '<div class="p-collab-inner">' +
          '<div class="p-label p-reveal">' + esc(co.label) + '</div>' +
          '<h2 class="p-collab-headline p-reveal p-reveal-d1">' + esc(co.headline) + '</h2>' +
          '<p class="p-collab-body p-reveal p-reveal-d2">' + esc(co.body) + '</p>' +
          '<div class="p-reveal p-reveal-d3">' +
            '<a href="' + attr(co.cta.href) + '" class="p-btn-primary">' + esc(co.cta.label) + '</a>' +
          '</div>' +
        '</div>' +
      '</section>'
    );
  }

  function buildFinalCta() {
    var fc = C.finalCta;
    return (
      '<section class="p-final-cta" aria-label="Llamada a la acción">' +
        '<div class="p-final-cta-inner">' +
          '<div class="p-label p-reveal">' + esc(fc.label) + '</div>' +
          '<h2 class="p-final-cta-headline p-reveal p-reveal-d1">' + esc(fc.headline) + '</h2>' +
          '<p class="p-final-cta-body p-reveal p-reveal-d2">' + esc(fc.body) + '</p>' +
          '<div class="p-reveal p-reveal-d3">' +
            '<a href="' + attr(fc.cta.href) + '" class="p-btn-primary">' + esc(fc.cta.label) + '</a>' +
            '<p class="p-final-cta-note">' + esc(fc.note) + '</p>' +
          '</div>' +
        '</div>' +
      '</section>'
    );
  }

  function buildContact() {
    var ct = C.contact;
    return (
      '<section class="p-contact" id="contacto" aria-label="Contacto">' +
        '<div class="p-contact-inner">' +
          '<h2 class="p-contact-headline p-reveal">' + esc(ct.headline) + '</h2>' +
          '<p class="p-contact-note p-reveal p-reveal-d1">' + esc(ct.note) + '</p>' +
          '<form id="p-form" class="p-reveal p-reveal-d2" novalidate>' +
            '<div class="p-form-grid">' +
              field('f-nombre',   'Nombre',     'input',    'text',   'Tu nombre',              true) +
              field('f-empresa',  'Empresa',    'input',    'text',   'Nombre de la empresa',   true) +
              field('f-email',    'Correo',     'input',    'email',  'correo@empresa.com',     true) +
              field('f-telefono', 'Teléfono',   'input',    'tel',    '+34 600 000 000',        false) +
              fieldSelect('f-tipo', 'Tipo de empresa', true, [
                { v: '', l: 'Seleccionar' },
                { v: 'promotora',        l: 'Promotora inmobiliaria' },
                { v: 'constructora',     l: 'Constructora con promociones propias' },
                { v: 'firma',            l: 'Firma inmobiliaria' },
                { v: 'otro',             l: 'Otro' },
              ]) +
              field('f-ubicacion', 'Ubicación de la promoción', 'input', 'text', 'Ciudad / provincia', false) +
              fieldSelect('f-fase', 'Fase actual del proyecto', false, [
                { v: '', l: 'Seleccionar' },
                { v: 'proyecto',     l: 'En proyecto / licencia' },
                { v: 'inicio-obra', l: 'Inicio de obra' },
                { v: 'en-curso',     l: 'Obra en curso' },
                { v: 'prox-entrega', l: 'Entrega próxima' },
                { v: 'post-entrega', l: 'Post entrega' },
              ]) +
              field('f-unidades', 'Unidades aproximadas', 'input', 'number', 'Ej. 24', false) +
              fieldFull('f-reto',    'Principal reto comercial', 'input',    'text',  'Describe brevemente tu principal reto', false) +
              fieldTextarea('f-mensaje', 'Mensaje', 'Cuéntame más sobre el proyecto y lo que necesitas') +
            '</div>' +
            '<div class="p-form-actions">' +
              '<button type="submit" id="p-submit" class="p-btn-primary">' + esc(ct.submitBtn) + '</button>' +
            '</div>' +
            '<p class="p-form-info">' + esc(ct.note) + '</p>' +
            '<div class="p-form-msg" id="p-msg-ok" role="alert">Solicitud recibida. Revisaré tu mensaje y me pondré en contacto si hay sintonía.</div>' +
            '<div class="p-form-msg" id="p-msg-err" role="alert">Ha ocurrido un error. Escríbeme directamente a <a href="mailto:' + attr(ct.links.email) + '" style="color:inherit;text-decoration:underline">' + esc(ct.links.email) + '</a>.</div>' +
          '</form>' +
          '<div class="p-contact-links p-reveal">' +
            '<a class="p-contact-link" href="mailto:' + attr(ct.links.email) + '">' + esc(ct.links.email) + '</a>' +
            '<a class="p-contact-link" href="' + attr(ct.links.instagram) + '" target="_blank" rel="noopener noreferrer">Instagram</a>' +
            '<a class="p-contact-link" href="' + attr(ct.links.linkedin) + '" target="_blank" rel="noopener noreferrer">LinkedIn</a>' +
          '</div>' +
        '</div>' +
      '</section>'
    );
  }

  function field(id, label, tag, type, placeholder, required) {
    var req = required ? ' required' : '';
    var input = '<input class="p-form-input" id="' + id + '" name="' + id + '" type="' + type + '" placeholder="' + attr(placeholder) + '"' + req + '>';
    return (
      '<div class="p-form-field">' +
        '<label class="p-form-label" for="' + id + '">' + esc(label) + (required ? ' *' : '') + '</label>' +
        input +
      '</div>'
    );
  }

  function fieldFull(id, label, tag, type, placeholder, required) {
    var req = required ? ' required' : '';
    var input = '<input class="p-form-input" id="' + id + '" name="' + id + '" type="' + type + '" placeholder="' + attr(placeholder) + '"' + req + '>';
    return (
      '<div class="p-form-field full">' +
        '<label class="p-form-label" for="' + id + '">' + esc(label) + '</label>' +
        input +
      '</div>'
    );
  }

  function fieldSelect(id, label, required, options) {
    var req = required ? ' required' : '';
    var opts = options.map(function(o) {
      return '<option value="' + attr(o.v) + '">' + esc(o.l) + '</option>';
    }).join('');
    return (
      '<div class="p-form-field">' +
        '<label class="p-form-label" for="' + id + '">' + esc(label) + (required ? ' *' : '') + '</label>' +
        '<select class="p-form-select" id="' + id + '" name="' + id + '"' + req + '>' + opts + '</select>' +
      '</div>'
    );
  }

  function fieldTextarea(id, label, placeholder) {
    return (
      '<div class="p-form-field full">' +
        '<label class="p-form-label" for="' + id + '">' + esc(label) + '</label>' +
        '<textarea class="p-form-textarea" id="' + id + '" name="' + id + '" placeholder="' + attr(placeholder) + '"></textarea>' +
      '</div>'
    );
  }

  function buildFooter() {
    var f = C.footer;
    var ct = C.contact;
    var legal = f.legal.map(function(l) {
      return '<a href="' + attr(l.href) + '">' + esc(l.label) + '</a>';
    }).join('');
    return (
      '<footer class="p-footer" aria-label="Pie de página">' +
        '<div class="p-footer-inner">' +
          '<div>' +
            '<div class="p-footer-brand">' + esc(f.brand) + '</div>' +
            '<div class="p-footer-tagline">' + esc(f.tagline) + '</div>' +
            '<div class="p-footer-socials">' +
              '<a href="' + attr(ct.links.instagram) + '" target="_blank" rel="noopener noreferrer">Instagram</a>' +
              '<a href="' + attr(ct.links.linkedin) + '" target="_blank" rel="noopener noreferrer">LinkedIn</a>' +
              '<a href="mailto:' + attr(ct.links.email) + '">Email</a>' +
            '</div>' +
            '<div class="p-footer-closing">' + esc(f.closing) + '</div>' +
          '</div>' +
          '<div class="p-footer-legal">' + legal + '</div>' +
        '</div>' +
      '</footer>'
    );
  }

  /* ══════════════════════════════════════════════════════════
     RENDER
  ══════════════════════════════════════════════════════════ */
  function render() {
    var app = document.getElementById('p-app');
    if (!app) return;
    app.innerHTML = [
      buildHeader(),
      buildHero(),
      buildManifesto(),
      buildPositioning(),
      buildSystem(),
      buildImpact(),
      buildForWhom(),
      buildProcess(),
      buildAbout(),
      buildCollaboration(),
      buildFinalCta(),
      buildContact(),
      buildFooter(),
    ].join('');

    initAll();
    document.body.classList.add('p-loaded');
  }

  /* ══════════════════════════════════════════════════════════
     BEHAVIORS
  ══════════════════════════════════════════════════════════ */
  function initAll() {
    initHeader();
    initReveal();
    initSmoothScroll();
    initMobileNav();
    initSystem();
    initImpact();
    initForm();
  }

  /* Sticky header */
  function initHeader() {
    var header = document.getElementById('p-header');
    if (!header) return;
    function tick() { header.classList.toggle('scrolled', window.scrollY > 40); }
    window.addEventListener('scroll', tick, { passive: true });
    tick();
  }

  /* Generic scroll reveal */
  function initReveal() {
    var els = document.querySelectorAll('.p-reveal');
    var obs = new IntersectionObserver(function(entries) {
      entries.forEach(function(e) {
        if (e.isIntersecting) { e.target.classList.add('visible'); obs.unobserve(e.target); }
      });
    }, { threshold: 0.1 });
    els.forEach(function(el) { obs.observe(el); });
  }

  /* Smooth scroll for internal anchors */
  function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(function(link) {
      link.addEventListener('click', function(e) {
        var id = link.getAttribute('href');
        var target = document.querySelector(id);
        if (!target) return;
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    });
  }

  /* Mobile nav */
  function initMobileNav() {
    var btn = document.getElementById('p-hamburger');
    var nav = document.getElementById('p-mobile-nav');
    if (!btn || !nav) return;

    function open() {
      nav.classList.add('open');
      btn.classList.add('open');
      btn.setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden';
    }
    function close() {
      nav.classList.remove('open');
      btn.classList.remove('open');
      btn.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
    }

    btn.addEventListener('click', function() {
      nav.classList.contains('open') ? close() : open();
    });
    nav.querySelectorAll('.p-mobile-close').forEach(function(l) {
      l.addEventListener('click', close);
    });
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && nav.classList.contains('open')) close();
    });
  }

  /* Sistema — lista interactiva hover/focus */
  function initSystem() {
    var items = document.querySelectorAll('.p-system-item');
    if (!items.length) return;

    var current = items[0];

    function activate(item) {
      if (item === current) return;
      current.classList.remove('active');
      current.setAttribute('aria-expanded', 'false');
      current = item;
      item.classList.add('active');
      item.setAttribute('aria-expanded', 'true');
    }

    items.forEach(function(item) {
      item.addEventListener('mouseenter', function() { activate(item); });
      item.addEventListener('click',      function() { activate(item); });
      item.addEventListener('focus',      function() { activate(item); });
      item.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          activate(item);
        }
        var idx = Array.prototype.indexOf.call(items, item);
        if (e.key === 'ArrowDown' && idx < items.length - 1) {
          e.preventDefault(); items[idx + 1].focus();
        }
        if (e.key === 'ArrowUp' && idx > 0) {
          e.preventDefault(); items[idx - 1].focus();
        }
      });
    });
  }

  /* Scroll-triggered animation for the impact section */
  function initImpact() {
    var section = document.querySelector('.p-impact');
    if (!section) return;
    var obs = new IntersectionObserver(function(entries) {
      if (entries[0].isIntersecting) {
        section.classList.add('p-impact-entered');
        obs.disconnect();
      }
    }, { threshold: 0.15 });
    obs.observe(section);
  }

  /* Form handling */
  function initForm() {
    var form = document.getElementById('p-form');
    var submitBtn = document.getElementById('p-submit');
    var msgOk  = document.getElementById('p-msg-ok');
    var msgErr = document.getElementById('p-msg-err');
    if (!form) return;

    form.addEventListener('submit', function(e) {
      e.preventDefault();
      if (!validate()) return;

      submitBtn.disabled = true;
      submitBtn.textContent = 'Enviando…';
      msgOk.classList.remove('success');
      msgErr.classList.remove('error');

      doSubmit(new FormData(form))
        .then(function() {
          form.reset();
          msgOk.classList.add('success');
          msgOk.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        })
        .catch(function() {
          msgErr.classList.add('error');
        })
        .finally(function() {
          submitBtn.disabled = false;
          submitBtn.textContent = C.contact.submitBtn;
        });
    });

    function validate() {
      var ok = true;
      form.querySelectorAll('[required]').forEach(function(f) {
        f.parentElement.classList.remove('p-has-error');
        if (!f.value.trim()) {
          f.parentElement.classList.add('p-has-error');
          if (ok) f.focus();
          ok = false;
        }
      });
      var emailEl = form.querySelector('#f-email');
      if (emailEl && emailEl.value && !emailEl.value.includes('@')) {
        emailEl.parentElement.classList.add('p-has-error');
        ok = false;
      }
      return ok;
    }
  }

  /* ── CONECTAR FORMULARIO ─────────────────────────────────
     Reemplaza el cuerpo de esta función con una de las opciones:

     OPCIÓN A — Formspree:
       var res = await fetch('https://formspree.io/f/TU_ID', {
         method: 'POST', headers: { Accept: 'application/json' }, body: data
       });
       if (!res.ok) throw new Error();

     OPCIÓN B — Función serverless propia (/api/contact):
       var res = await fetch('/api/contact', {
         method: 'POST',
         headers: { 'Content-Type': 'application/json' },
         body: JSON.stringify(Object.fromEntries(data)),
       });
       if (!res.ok) throw new Error();

     OPCIÓN C — EmailJS:
       await emailjs.sendForm('SERVICE_ID', 'TEMPLATE_ID', form);
  ─────────────────────────────────────────────────────────── */
  function doSubmit(data) {
    // STUB — simula envío exitoso para preview. Sustituir por fetch real.
    return new Promise(function(resolve) { setTimeout(resolve, 1000); });
  }

  /* ── Boot ──────────────────────────────────────────────── */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', render);
  } else {
    render();
  }

})();
