/**
 * FEATHER ICONS FIX - Robust Global Handler
 * This file provides safe initialization and replacement of feather icons
 * Must be placed BEFORE feather script in HTML
 */

(function() {
    // Global feather state
    window.__featherState = {
        isLoaded: false,
        isInitialized: false,
        pendingReplacements: [],
        lastReplaceTime: 0,
        replaceDebounce: 50 // ms minimum between replace calls
    };

    // Wait for feather to be loaded and initialize it
    const checkFeatherInterval = setInterval(() => {
        if (window.feather && typeof window.feather.replace === 'function') {
            clearInterval(checkFeatherInterval);
            initializeFeatherSafely();
        }
    }, 100);

    // Timeout after 15 seconds
    setTimeout(() => {
        clearInterval(checkFeatherInterval);
        if (!window.__featherState.isLoaded) {
            console.warn('⚠️ Feather Icons did not load within 15 seconds');
        }
    }, 15000);

    /**
     * Safe initialization of feather with proper error handling
     */
    function initializeFeatherSafely() {
        if (window.__featherState.isLoaded) {
            return;
        }

        window.__featherState.isLoaded = true;
        const originalReplace = window.feather.replace;

        /**
         * Safe wrapper for feather.replace()
         */
        window.feather.replace = function(options) {
            const now = Date.now();
            const timeSinceLastReplace = now - window.__featherState.lastReplaceTime;

            // Debounce rapid successive calls
            if (timeSinceLastReplace < window.__featherState.replaceDebounce) {
                return;
            }

            // Check if there are actually feather icons to replace
            const featherIcons = document.querySelectorAll('[data-feather]');
            if (featherIcons.length === 0) {
                return; // No icons to replace
            }

            try {
                window.__featherState.lastReplaceTime = now;
                originalReplace.call(this, options);
            } catch (e) {
                // Only log non-toSvg errors (toSvg errors are known feather issues)
                if (e && e.message && !e.message.includes('toSvg')) {
                    console.warn('⚠️ Feather.replace() error:', e.message);
                }
            }
        };

        window.__featherState.isInitialized = true;
        console.log('✅ Feather Icons initialized safely');
    }

    /**
     * Global safe function to replace feather icons
     * Use this instead of feather.replace() directly
     */
    window.safeFeatherReplace = function() {
        if (!window.feather || typeof window.feather.replace !== 'function') {
            return; // Feather not loaded yet
        }

        const featherIcons = document.querySelectorAll('[data-feather]');
        if (featherIcons.length === 0) {
            return; // No icons to replace
        }

        try {
            window.feather.replace();
        } catch (e) {
            // Silently ignore toSvg errors - they're non-critical
            if (!(e && e.message && e.message.includes('toSvg'))) {
                console.warn('⚠️ Feather replace error:', e.message);
            }
        }
    };

    /**
     * Wait for feather to be loaded
     */
    window.waitForFeather = function(callback) {
        if (window.__featherState.isLoaded) {
            callback();
        } else {
            setTimeout(() => window.waitForFeather(callback), 100);
        }
    };
})();

