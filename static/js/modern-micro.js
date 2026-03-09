// Modern micro-interactions: lazy-load Alpine.js and provide small helpers
(function () {
    // Only run when modern mode is active
    if (!document.body || !document.body.classList.contains('modern')) return;

    // Load Alpine.js lazily (only when modern mode is enabled)
    function loadAlpine(cb) {
        if (window.Alpine) { cb && cb(); return; }
        const s = document.createElement('script');
        s.src = 'https://unpkg.com/alpinejs@3.12.0/dist/cdn.min.js';
        s.defer = true;
        s.onload = function () {
            if (window.Alpine) window.Alpine.start && window.Alpine.start();
            cb && cb();
        };
        s.onerror = function () { console.warn('Alpine failed to load'); cb && cb(); };
        document.head.appendChild(s);
    }

    // Expose a helper to ensure Alpine is available
    window.ensureAlpine = loadAlpine;

    // Skeleton helpers: show/hide by toggling data attribute
    window.showSkeleton = function (containerSelector) {
        try {
            const el = typeof containerSelector === 'string' ? document.querySelector(containerSelector) : containerSelector;
            if (!el) return;
            el.setAttribute('data-skeleton', '1');
        } catch (e) { console.error(e); }
    };

    window.hideSkeleton = function (containerSelector) {
        try {
            const el = typeof containerSelector === 'string' ? document.querySelector(containerSelector) : containerSelector;
            if (!el) return;
            el.removeAttribute('data-skeleton');
        } catch (e) { console.error(e); }
    };

    // Pressed state for buttons (small tactile feedback)
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn-sofatelcom-primary, .btn');
        if (!btn) return;
        btn.classList.add('pressed');
        setTimeout(() => btn.classList.remove('pressed'), 140);
    }, { passive: true });

    // Auto-initialize Alpine for components marked with data-alpine="1"
    document.addEventListener('DOMContentLoaded', function () {
        const needsAlpine = document.querySelector('[data-alpine="1"]');
        if (needsAlpine) loadAlpine();
    });

})();
