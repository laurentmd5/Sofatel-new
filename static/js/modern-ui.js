// Modern UI toggle script (opt-in via localStorage)
(function () {
    const KEY = 'sofatelcom_modern_ui_v1';

    // Modern UI is enabled by default unless the user explicitly opts-out
    // Set localStorage 'sofatelcom_modern_ui_v1' = '0' to disable.
    function applyModernIfEnabled() {
        try {
            const val = localStorage.getItem(KEY);
            const disabled = val === '0';
            if (!disabled && document.body) document.body.classList.add('modern');
        } catch (e) {
            // ignore localStorage errors
            if (document.body) document.body.classList.add('modern');
        }
    }

    function enableModernUI() {
        try { localStorage.setItem(KEY, '1'); } catch (e) {}
        if (document.body) document.body.classList.add('modern');
    }

    function disableModernUI() {
        try { localStorage.setItem(KEY, '0'); } catch (e) {}
        if (document.body) document.body.classList.remove('modern');
    }

    function toggleModernUI() {
        if (document.body && document.body.classList.contains('modern')) disableModernUI();
        else enableModernUI();
    }

    // Expose helpers for manual toggling (console/QA)
    window.enableModernUI = enableModernUI;
    window.disableModernUI = disableModernUI;
    window.toggleModernUI = toggleModernUI;

    // Apply on load (modern by default; set key to '0' to opt-out)
    applyModernIfEnabled();
})();
