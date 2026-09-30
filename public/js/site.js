(function () {
  'use strict';

  var body = document.body;
  var raf = window.requestAnimationFrame
    ? window.requestAnimationFrame.bind(window)
    : function (fn) {
        return window.setTimeout(function () {
          fn(Date.now());
        }, 16);
      };

  /* ---------- Menú móvil ---------- */
  var navToggle = document.querySelector('.nav-toggle');
  var nav = document.getElementById('site-nav');

  if (navToggle && nav) {
    navToggle.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      navToggle.setAttribute('aria-expanded', String(open));
    });
    nav.addEventListener('click', function (event) {
      if (event.target.closest('a')) {
        nav.classList.remove('is-open');
        navToggle.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ---------- Animaciones de entrada ---------- */
  var reduceMotion = Boolean(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  var REVEAL_TARGETS = [
    '.section-head',
    '.block-head',
    '.module-grid a',
    '.phase-grid > *',
    '.block-grid > *',
    '.card',
    '.match',
    '.room-grid a',
    '.news-card',
    '.team-grid > *',
    '.member',
    '.link-grid a',
    '.award',
    '.rule-list > li',
    '.movement',
    '.ticks',
    '.config-list > li'
  ].join(', ');

  function countUp(el) {
    var text = el.textContent.trim();
    if (!/^\d{1,6}$/.test(text)) return;
    var target = Number(text);
    var length = text.length;
    var duration = 900;
    var start = null;
    function frame(time) {
      if (start === null) start = time;
      var progress = Math.min(1, (time - start) / duration);
      var eased = 1 - Math.pow(1 - progress, 3);
      var value = String(Math.round(target * eased));
      el.textContent = value.length < length ? value.padStart(length, '0') : value;
      if (progress < 1) raf(frame);
      else el.textContent = text;
    }
    raf(frame);
  }

  function createReveal() {
    var nodes = [];
    if (reduceMotion || !('IntersectionObserver' in window)) {
      return { scan: function () {} };
    }
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-in');
          if (!entry.target.hasAttribute('data-counted')) {
            entry.target.setAttribute('data-counted', '');
            Array.prototype.forEach.call(entry.target.querySelectorAll('.stat-strip strong'), countUp);
          }
          observer.unobserve(entry.target);
        });
      },
      { rootMargin: '0px 0px -8% 0px', threshold: 0.12 }
    );
    return {
      scan: function () {
        var candidates = document.querySelectorAll(REVEAL_TARGETS);
        for (var i = 0; i < candidates.length; i += 1) {
          var node = candidates[i];
          if (node.classList.contains('is-in') || nodes.indexOf(node) !== -1) continue;
          nodes.push(node);
          node.classList.add('reveal');
          observer.observe(node);
        }
      }
    };
  }

  var reveal = createReveal();
  reveal.scan();

  /* ---------- Grupos de pestañas ---------- */
  function wireTabs(root, buttonAttr, panelAttr) {
    var buttons = Array.prototype.slice.call(root.querySelectorAll('[' + buttonAttr + ']'));
    if (!buttons.length) return;
    buttons.forEach(function (button) {
      button.addEventListener('click', function () {
        var key = button.getAttribute(buttonAttr);
        buttons.forEach(function (item) {
          item.setAttribute('aria-selected', String(item === button));
        });
        root.querySelectorAll('[' + panelAttr + ']').forEach(function (panel) {
          panel.hidden = panel.getAttribute(panelAttr) !== key;
        });
        reveal.scan();
      });
    });
  }

  var divisionTabs = document.querySelector('[data-tabs="division"]');
  if (divisionTabs) wireTabs(divisionTabs, 'data-tab', 'data-tab-panel');

  document.querySelectorAll('[data-tabs="journey"]').forEach(function (root) {
    wireTabs(root, 'data-journey-tab', 'data-journey-panel');
  });

  var ruleTabs = document.querySelector('[data-tabs="rules"]');
  if (ruleTabs) wireTabs(ruleTabs, 'data-rule-tab', 'data-rule-panel');

  /* ---------- Filtros de la galería ---------- */
  var filterRow = document.querySelector('[data-filters]');
  if (filterRow) {
    var filterButtons = Array.prototype.slice.call(filterRow.querySelectorAll('[data-filter]'));
    var awards = Array.prototype.slice.call(document.querySelectorAll('.award[data-category]'));
    filterButtons.forEach(function (button) {
      button.addEventListener('click', function () {
        var filter = button.dataset.filter;
        filterButtons.forEach(function (item) {
          item.setAttribute('aria-pressed', String(item === button));
        });
        awards.forEach(function (award) {
          var match =
            filter === 'all' ||
            award.dataset.category === filter ||
            award.dataset.division === filter;
          award.hidden = !match;
        });
        reveal.scan();
      });
    });
  }

  /* ---------- Lightbox ---------- */
  var lightbox = document.querySelector('[data-lightbox-box]');
  if (lightbox) {
    var lightboxImg = lightbox.querySelector('[data-lightbox-img]');
    var lightboxCaption = lightbox.querySelector('[data-lightbox-caption]');
    var lastFocus = null;

    var closeLightbox = function () {
      lightbox.hidden = true;
      body.classList.remove('is-locked');
      if (lastFocus) lastFocus.focus();
    };

    document.addEventListener('click', function (event) {
      var trigger = event.target.closest('[data-lightbox]');
      if (trigger) {
        lastFocus = trigger;
        lightboxImg.src = trigger.dataset.lightbox;
        lightboxImg.alt = trigger.dataset.caption || '';
        lightboxCaption.textContent = trigger.dataset.caption || '';
        lightbox.hidden = false;
        body.classList.add('is-locked');
        lightbox.querySelector('[data-lightbox-close]').focus();
        return;
      }
      if (!lightbox.hidden && (event.target === lightbox || event.target.closest('[data-lightbox-close]'))) {
        closeLightbox();
      }
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && !lightbox.hidden) closeLightbox();
    });
  }

  /* ---------- Ver contraseña ---------- */
  var togglePassword = document.querySelector('[data-toggle-password]');
  if (togglePassword) {
    togglePassword.addEventListener('click', function () {
      var input = document.getElementById('password');
      var show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      togglePassword.textContent = show ? 'Ocultar' : 'Ver';
      input.focus();
    });
  }

  /* ---------- Resaltar la sección activa ---------- */
  var navLinks = Array.prototype.slice.call(document.querySelectorAll('[data-nav]'));
  var sections = navLinks
    .map(function (link) {
      return document.getElementById(link.dataset.nav);
    })
    .filter(Boolean);

  if (sections.length && 'IntersectionObserver' in window) {
    var spy = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          navLinks.forEach(function (link) {
            link.classList.toggle('is-active', link.dataset.nav === entry.target.id);
          });
        });
      },
      { rootMargin: '-45% 0px -50% 0px', threshold: 0 }
    );
    sections.forEach(function (section) {
      spy.observe(section);
    });
  }

  /* ---------- Progreso, cabecera y volver arriba ---------- */
  var header = document.querySelector('.site-header');
  var progressBar = document.querySelector('[data-scroll-bar]');
  var toTop = document.querySelector('[data-to-top]');
  var ticking = false;

  function onScroll() {
    if (ticking) return;
    ticking = true;
    raf(function () {
      var offset = window.pageYOffset || document.documentElement.scrollTop || 0;      var max = document.documentElement.scrollHeight - window.innerHeight;
      if (progressBar) {
        progressBar.style.transform = 'scaleX(' + (max > 0 ? Math.min(1, offset / max) : 0) + ')';
      }
      if (header) header.classList.toggle('is-stuck', offset > 12);
      if (toTop) toTop.hidden = offset < 600;
      ticking = false;
    });
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });
  onScroll();

  if (toTop) {
    toTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: reduceMotion ? 'auto' : 'smooth' });
    });
  }
})();
