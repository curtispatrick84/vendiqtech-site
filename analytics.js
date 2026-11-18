/* VendiQ visitor tracking for Google Analytics 4.
 * Loaded on every page after the gtag snippet. Adds:
 *  - campaign attribution (UTM tags, Facebook click IDs, in-app browser)
 *  - scroll depth, time on page, section views
 *  - click tracking for any element with data-track="event_name" data-track-label="..."
 * Never send names, emails, or other personal details to GA.
 * After editing, bump ?v= on every <script src="/analytics.js?v=..."> tag (nginx caches .js for 7 days).
 */
(function () {
  'use strict';
  var w = window, d = document, path = location.pathname;

  function track(name, params) {
    try { if (typeof w.gtag === 'function') w.gtag('event', name, params || {}); } catch (e) {}
  }
  w.vqTrack = track;

  // Storage can throw in private windows and some in-app browsers.
  function load(k) { try { return JSON.parse(w.localStorage.getItem(k) || 'null'); } catch (e) { return null; } }
  function save(k, v) { try { w.localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} }

  // ── Where did this visitor come from? ──
  var ua = navigator.userAgent || '';
  var inApp = /Instagram/i.test(ua) ? 'instagram' : /FBAN|FBAV|FB_IAB/i.test(ua) ? 'facebook' : 'none';
  if (typeof w.gtag === 'function') w.gtag('set', 'user_properties', { in_app_browser: inApp });

  var q = new URLSearchParams(location.search);
  var touch = {};
  ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'].forEach(function (k) {
    var v = q.get(k); if (v) touch[k] = v.slice(0, 100);
  });
  if (q.get('fbclid')) { touch.fbclid = true; if (!touch.utm_source) touch.utm_source = 'facebook'; }
  var refHost = '';
  try { refHost = d.referrer ? new URL(d.referrer).hostname : ''; } catch (e) {}
  if (refHost && refHost !== location.hostname && !touch.utm_source) touch.referrer = refHost;

  if (Object.keys(touch).length) {
    touch.landing_page = path;
    touch.date = new Date().toISOString().slice(0, 10);
    if (!load('vq_first_touch')) save('vq_first_touch', touch);
    save('vq_last_touch', touch);
    if (touch.utm_source || touch.fbclid) {
      track('campaign_landing', {
        campaign_source: touch.utm_source || '',
        campaign_name: touch.utm_campaign || '',
        campaign_content: touch.utm_content || '',
        in_app_browser: inApp,
        landing_page: path
      });
    }
  }

  // Plain-text summary for lead records (Zoho). Campaign info only, nothing personal.
  w.vqAttributionText = function () {
    function line(label, t) {
      if (!t) return label + ': direct / unknown';
      var src = t.utm_source || t.referrer || 'unknown';
      var bits = [src, t.utm_medium, t.utm_campaign, t.utm_content && ('ad: ' + t.utm_content)].filter(Boolean);
      return label + ': ' + bits.join(' / ') + ' (landed on ' + (t.landing_page || '/') + ', ' + (t.date || '') + ')';
    }
    return [line('First visit from', load('vq_first_touch')), line('Latest visit from', load('vq_last_touch')),
      'Browser: ' + (inApp === 'none' ? 'regular' : inApp + ' in-app')].join('\n');
  };

  // ── Form start (once per form per page load) ──
  var started = {};
  w.vqFormStart = function (form) {
    if (started[form]) return; started[form] = true;
    track('lead_form_start', { form_name: form });
  };

  // ── Scroll depth ──
  var marks = [25, 50, 75, 90], hitMarks = {}, ticking = false;
  function checkScroll() {
    ticking = false;
    var h = d.documentElement.scrollHeight - w.innerHeight;
    if (h <= 0) return;
    var pct = (w.scrollY / h) * 100;
    marks.forEach(function (m) {
      if (pct >= m && !hitMarks[m]) { hitMarks[m] = true; track('scroll_depth', { percent: m, page_path: path }); }
    });
  }
  w.addEventListener('scroll', function () { if (!ticking) { ticking = true; w.requestAnimationFrame(checkScroll); } }, { passive: true });

  // ── Time on page (only counts while the tab is visible) ──
  var seconds = 0, timeMarks = { 30: 'time_on_page_30s', 120: 'time_on_page_2m' };
  var timer = setInterval(function () {
    if (d.hidden) return;
    seconds++;
    if (timeMarks[seconds]) track(timeMarks[seconds], { page_path: path });
    if (seconds >= 120) clearInterval(timer);
  }, 1000);

  // ── Section views: add data-track-view="name" to a section ──
  function watchSections() {
    if (!('IntersectionObserver' in w)) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        track('section_view', { section: e.target.getAttribute('data-track-view'), page_path: path });
      });
    }, { threshold: 0.4 });
    d.querySelectorAll('[data-track-view]').forEach(function (el) { io.observe(el); });
  }
  if (d.readyState === 'loading') d.addEventListener('DOMContentLoaded', watchSections); else watchSections();

  // ── Clicks ──
  d.addEventListener('click', function (e) {
    var el = e.target.closest && e.target.closest('[data-track], a[href^="mailto:"], a[href^="tel:"]');
    if (!el) return;
    if (el.hasAttribute('data-track')) {
      track(el.getAttribute('data-track'), {
        cta: el.getAttribute('data-track-label') || (el.textContent || '').trim().slice(0, 60),
        page_path: path
      });
    } else {
      track('contact_click', { method: /^tel:/.test(el.getAttribute('href')) ? 'phone' : 'email', page_path: path });
    }
  }, true);
})();
