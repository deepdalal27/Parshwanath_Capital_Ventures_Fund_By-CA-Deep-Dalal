/* ==========================================================================
   Parshwanath Capital Ventures Fund — site behaviour
   No dependencies. Progressive enhancement only: every page is fully
   readable with JavaScript disabled.
   ========================================================================== */
(function () {
  'use strict';

  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------------------------------------------------------------- nav */
  function initNav() {
    var nav = document.querySelector('[data-nav]');
    if (!nav) return;

    var toggle = nav.querySelector('[data-nav-toggle]');
    var drawer = document.querySelector('[data-nav-drawer]');

    var setSolid = function () {
      nav.setAttribute('data-solid', window.scrollY > 24 ? 'true' : 'false');
    };
    setSolid();
    window.addEventListener('scroll', setSolid, { passive: true });

    if (toggle && drawer) {
      var setDrawer = function (open) {
        toggle.setAttribute('aria-expanded', String(open));
        drawer.setAttribute('data-open', String(open));
        nav.setAttribute('data-drawer', String(open));
        document.body.style.overflow = open ? 'hidden' : '';
      };

      toggle.addEventListener('click', function () {
        setDrawer(toggle.getAttribute('aria-expanded') !== 'true');
      });

      drawer.addEventListener('click', function (e) {
        if (e.target.closest('a')) setDrawer(false);
      });

      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
          setDrawer(false);
          toggle.focus();
        }
      });

      window.addEventListener('resize', function () {
        if (window.innerWidth > 900) setDrawer(false);
      });
    }
  }

  /* ----------------------------------------------------------- progress */
  function initProgress() {
    var bar = document.querySelector('[data-progress]');
    if (!bar) return;
    var ticking = false;

    var update = function () {
      var doc = document.documentElement;
      var max = doc.scrollHeight - doc.clientHeight;
      var pct = max > 0 ? Math.min(window.scrollY / max, 1) : 0;
      bar.style.transform = 'scaleX(' + pct + ')';
      ticking = false;
    };

    window.addEventListener('scroll', function () {
      if (!ticking) {
        ticking = true;
        window.requestAnimationFrame(update);
      }
    }, { passive: true });
    update();
  }

  /* ------------------------------------------------------------ reveals */
  function initReveal() {
    var items = document.querySelectorAll('[data-reveal]');
    if (!items.length) return;

    if (!('IntersectionObserver' in window) || reduced) {
      items.forEach(function (el) { el.classList.add('is-visible'); });
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        io.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.12 });

    items.forEach(function (el, i) {
      // Stagger siblings within the same parent for a gentle cascade.
      if (!el.style.getPropertyValue('--d')) {
        var sibs = Array.prototype.filter.call(
          el.parentElement ? el.parentElement.children : [],
          function (n) { return n.hasAttribute && n.hasAttribute('data-reveal'); }
        );
        var idx = sibs.indexOf(el);
        el.style.setProperty('--d', (idx > 0 ? Math.min(idx, 5) * 90 : 0) + 'ms');
      }
      io.observe(el);
    });
  }

  /* ---------------------------------------------------------- accordion */
  function initAccordions() {
    document.querySelectorAll('[data-acc]').forEach(function (acc) {
      var buttons = acc.querySelectorAll('[data-acc-btn]');

      buttons.forEach(function (btn) {
        var panel = document.getElementById(btn.getAttribute('aria-controls'));
        if (!panel) return;

        btn.addEventListener('click', function () {
          var open = btn.getAttribute('aria-expanded') === 'true';

          if (acc.hasAttribute('data-acc-single') && !open) {
            buttons.forEach(function (other) {
              if (other === btn) return;
              other.setAttribute('aria-expanded', 'false');
              var op = document.getElementById(other.getAttribute('aria-controls'));
              if (op) op.setAttribute('data-open', 'false');
            });
          }

          btn.setAttribute('aria-expanded', String(!open));
          panel.setAttribute('data-open', String(!open));
        });
      });
    });
  }

  /* ----------------------------------------------------------- counters */
  function initCounters() {
    var els = document.querySelectorAll('[data-count]');
    if (!els.length) return;

    if (!('IntersectionObserver' in window) || reduced) {
      els.forEach(function (el) { el.textContent = el.getAttribute('data-count-display') || el.getAttribute('data-count'); });
      return;
    }

    var run = function (el) {
      var target = parseFloat(el.getAttribute('data-count'));
      var decimals = parseInt(el.getAttribute('data-count-decimals') || '0', 10);
      var prefix = el.getAttribute('data-count-prefix') || '';
      var suffix = el.getAttribute('data-count-suffix') || '';
      var start = performance.now();
      var dur = 1500;

      var step = function (now) {
        var p = Math.min((now - start) / dur, 1);
        var eased = 1 - Math.pow(1 - p, 3);
        el.textContent = prefix + (target * eased).toFixed(decimals) + suffix;
        if (p < 1) window.requestAnimationFrame(step);
      };
      window.requestAnimationFrame(step);
    };

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        run(entry.target);
        io.unobserve(entry.target);
      });
    }, { threshold: 0.5 });

    els.forEach(function (el) { io.observe(el); });
  }

  /* ------------------------------------------------- allocation bars */
  function initAlloc() {
    var groups = document.querySelectorAll('[data-alloc]');
    if (!groups.length) return;

    groups.forEach(function (group) {
      group.querySelectorAll('.alloc__fill').forEach(function (fill) {
        var pct = parseFloat(fill.getAttribute('data-pct') || '0');
        fill.style.setProperty('--w', Math.max(0, Math.min(pct, 100)) / 100);
      });
    });

    if (!('IntersectionObserver' in window) || reduced) {
      groups.forEach(function (g) { g.classList.add('is-visible'); });
      return;
    }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-visible');
        io.unobserve(entry.target);
      });
    }, { threshold: 0.3 });

    groups.forEach(function (g) { io.observe(g); });
  }

  /* --------------------------------------------------------------- year */
  function initYear() {
    var y = String(new Date().getFullYear());
    document.querySelectorAll('[data-year]').forEach(function (el) { el.textContent = y; });
  }

  /* --------------------------------------------------------------- form */
  /* The site ships without a backend. Set data-endpoint on the <form> to a
     form service (Formspree, Basin, a Lambda, …) and submissions POST there
     as JSON. With no endpoint configured the form falls back to composing a
     pre-filled email, so the enquiry never silently disappears.            */
  function initForm() {
    var form = document.querySelector('[data-enquiry-form]');
    if (!form) return;

    var status = form.querySelector('[data-form-status]');
    var submit = form.querySelector('[type="submit"]');

    var setStatus = function (state, message) {
      if (!status) return;
      status.setAttribute('data-state', state);
      status.textContent = message;
    };

    var markField = function (input, invalid) {
      var field = input.closest('.field, .check');
      if (field) field.setAttribute('data-invalid', String(invalid));
    };

    form.addEventListener('input', function (e) {
      if (e.target.matches('input, select, textarea')) markField(e.target, false);
    });

    form.addEventListener('submit', function (e) {
      e.preventDefault();

      var invalidCount = 0;
      form.querySelectorAll('input, select, textarea').forEach(function (input) {
        var bad = !input.checkValidity();
        markField(input, bad);
        if (bad && !invalidCount) input.focus();
        if (bad) invalidCount++;
      });

      if (invalidCount) {
        setStatus('err', 'Please complete the highlighted fields before submitting.');
        return;
      }

      var data = {};
      new FormData(form).forEach(function (value, key) { data[key] = value; });

      var endpoint = form.getAttribute('data-endpoint');

      if (!endpoint) {
        var to = form.getAttribute('data-mailto') || 'fundmanager@parshwanath.in';
        var body = Object.keys(data).map(function (k) { return k + ': ' + data[k]; }).join('\n');
        window.location.href = 'mailto:' + to +
          '?subject=' + encodeURIComponent('Investor enquiry — ' + (data.name || 'Website')) +
          '&body=' + encodeURIComponent(body);
        setStatus('ok', 'Opening your email client to send this enquiry. If nothing happens, write to ' + to + '.');
        return;
      }

      if (submit) { submit.disabled = true; }
      setStatus('ok', 'Submitting your enquiry…');

      fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify(data)
      }).then(function (res) {
        if (!res.ok) throw new Error('Request failed: ' + res.status);
        form.reset();
        setStatus('ok', 'Thank you. Your enquiry has been received — our investor relations team will respond within two business days.');
      }).catch(function () {
        setStatus('err', 'We could not submit the form. Please email fundmanager@parshwanath.in directly.');
      }).finally(function () {
        if (submit) { submit.disabled = false; }
      });
    });
  }

  /* --------------------------------------------------------------- init */
  function init() {
    initNav();
    initProgress();
    initReveal();
    initAccordions();
    initCounters();
    initAlloc();
    initYear();
    initForm();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
