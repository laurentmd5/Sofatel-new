/**
 * SOFATELCOM Accessibility Manager
 * Improved ARIA labels, keyboard navigation, focus management
 */

class AccessibilityManager {
    constructor() {
        this.init();
    }

    init() {
        this.enhanceAriaLabels();
        this.setupKeyboardNavigation();
        this.setupFocusTrap();
        this.setupAriaLive();
        this.setupFormAccessibility();
        this.setupMotionPreferences();  // NEW: Motion preferences support
        this.announcePageLoad();
    }

    /**
     * Enhance ARIA labels for better screen reader experience
     */
    enhanceAriaLabels() {
        // Buttons without text
        document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])').forEach(btn => {
            const icon = btn.querySelector('i[data-feather]');
            const text = btn.textContent.trim();
            
            if (!text && icon) {
                const iconName = icon.getAttribute('data-feather');
                btn.setAttribute('aria-label', this.humanizeIconName(iconName));
            }
        });

        // Icon-only links
        document.querySelectorAll('a:not([aria-label]):not([aria-labelledby]):has(i[data-feather]):not(:has(span))').forEach(link => {
            const icon = link.querySelector('i[data-feather]');
            const iconName = icon.getAttribute('data-feather');
            link.setAttribute('aria-label', this.humanizeIconName(iconName));
        });

        // Tables
        document.querySelectorAll('table:not([role])').forEach(table => {
            table.setAttribute('role', 'table');
        });

        // Form sections
        document.querySelectorAll('fieldset').forEach(fieldset => {
            if (!fieldset.querySelector('legend')) {
                const title = fieldset.querySelector('h3, .form-section-title');
                if (title) {
                    fieldset.setAttribute('aria-labelledby', title.id || this.generateId('legend'));
                }
            }
        });
    }

    /**
     * Setup keyboard navigation
     */
    setupKeyboardNavigation() {
        // Close modals with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const openModals = document.querySelectorAll('.modal.show');
                openModals.forEach(modal => {
                    const bsModal = bootstrap.Modal.getInstance(modal);
                    if (bsModal) bsModal.hide();
                });
            }
        });

        // Navigate dropdowns with arrow keys
        document.querySelectorAll('[data-bs-toggle="dropdown"]').forEach(toggle => {
            toggle.addEventListener('keydown', (e) => {
                if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    const menu = toggle.nextElementSibling;
                    if (menu) {
                        const firstItem = menu.querySelector('.dropdown-item');
                        if (firstItem) firstItem.focus();
                    }
                }
            });
        });

        // Tabindex for interactive elements
        document.querySelectorAll('[role="button"]:not([tabindex])').forEach(btn => {
            btn.setAttribute('tabindex', '0');
        });
    }

    /**
     * Setup focus trap for modals (WCAG 2.1 A)
     */
    setupFocusTrap() {
        // Create focus trap for modals
        document.addEventListener('show.bs.modal', (e) => {
            const modal = e.target;
            const focusableElements = modal.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            
            if (focusableElements.length > 0) {
                const firstElement = focusableElements[0];
                const lastElement = focusableElements[focusableElements.length - 1];
                
                // Set initial focus to first focusable element
                setTimeout(() => firstElement.focus(), 100);
                
                modal.addEventListener('keydown', (e) => {
                    if (e.key === 'Tab') {
                        if (e.shiftKey) {
                            if (document.activeElement === firstElement) {
                                e.preventDefault();
                                lastElement.focus();
                            }
                        } else {
                            if (document.activeElement === lastElement) {
                                e.preventDefault();
                                firstElement.focus();
                            }
                        }
                    }
                });
            }
        });
    }

    /**
     * Check and respect prefers-reduced-motion (WCAG 2.3.3)
     */
    setupMotionPreferences() {
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (prefersReducedMotion) {
            // Apply reduced-motion class to document
            document.documentElement.classList.add('prefers-reduced-motion');
            
            // Set CSS variable for duration to 0
            document.documentElement.style.setProperty('--duration-75', '0ms');
            document.documentElement.style.setProperty('--duration-100', '0ms');
            document.documentElement.style.setProperty('--duration-150', '0ms');
            document.documentElement.style.setProperty('--duration-200', '0ms');
            document.documentElement.style.setProperty('--duration-300', '0ms');
            document.documentElement.style.setProperty('--duration-500', '0ms');
        }
        
        // Listen for changes in motion preference
        window.matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', (mql) => {
            if (mql.matches) {
                document.documentElement.classList.add('prefers-reduced-motion');
            } else {
                document.documentElement.classList.remove('prefers-reduced-motion');
            }
        });
    }

    /**
     * Setup ARIA live regions for dynamic content
     */
    setupAriaLive() {
        // Create main alert region
        if (!document.querySelector('[aria-live="polite"][role="status"]')) {
            const liveRegion = document.createElement('div');
            liveRegion.id = 'aria-live-region';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.setAttribute('role', 'status');
            liveRegion.style.cssText = 'position: absolute; left: -10000px; width: 1px; height: 1px; overflow: hidden;';
            document.body.appendChild(liveRegion);
        }

        // Announce toast messages to screen readers
        const originalShow = Toast.show;
        Toast.show = function(message, type, duration) {
            const liveRegion = document.getElementById('aria-live-region');
            if (liveRegion) {
                liveRegion.textContent = message;
            }
            return originalShow.call(this, message, type, duration);
        };
    }

    /**
     * Improve form accessibility
     */
    setupFormAccessibility() {
        // Associate labels with inputs
        document.querySelectorAll('label').forEach(label => {
            const input = label.querySelector('input, select, textarea');
            if (input && !label.htmlFor) {
                const id = input.id || this.generateId('input');
                input.id = id;
                label.htmlFor = id;
            }
        });

        // Add aria-required to required inputs
        document.querySelectorAll('input[required], select[required], textarea[required]').forEach(input => {
            input.setAttribute('aria-required', 'true');
        });

        // Add aria-invalid for invalid inputs
        document.querySelectorAll('.form-control.is-invalid').forEach(input => {
            input.setAttribute('aria-invalid', 'true');
            const error = input.parentElement.querySelector('.invalid-feedback');
            if (error) {
                const errorId = this.generateId('error');
                error.id = errorId;
                input.setAttribute('aria-describedby', errorId);
            }
        });
    }

    /**
     * Announce page load to screen readers
     */
    announcePageLoad() {
        const pageTitle = document.querySelector('h1, h2');
        if (pageTitle) {
            const liveRegion = document.getElementById('aria-live-region');
            if (liveRegion) {
                liveRegion.textContent = `Page chargée: ${pageTitle.textContent}`;
            }
        }
    }

    /**
     * Utility: Humanize icon names for accessibility
     */
    humanizeIconName(iconName) {
        return iconName
            .replace(/-/g, ' ')
            .split(' ')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    /**
     * Utility: Generate unique IDs
     */
    generateId(prefix) {
        return `${prefix}-${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Check if user prefers reduced motion
     */
    prefersReducedMotion() {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    }

    /**
     * Get dark mode preference
     */
    prefersDarkMode() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }

    /**
     * Setup skip link for keyboard navigation
     */
    setupSkipLink() {
        if (!document.querySelector('[href="#main-content"]')) {
            const skipLink = document.createElement('a');
            skipLink.href = '#main-content';
            skipLink.className = 'skip-link';
            skipLink.textContent = 'Aller au contenu principal';
            skipLink.style.cssText = `
                position: absolute;
                top: -40px;
                left: 0;
                background: #000;
                color: #fff;
                padding: 8px 12px;
                text-decoration: none;
                z-index: 100;
            `;
            skipLink.addEventListener('focus', () => {
                skipLink.style.top = '0';
            });
            skipLink.addEventListener('blur', () => {
                skipLink.style.top = '-40px';
            });
            document.body.insertBefore(skipLink, document.body.firstChild);
        }

        // Mark main content
        if (!document.getElementById('main-content')) {
            const main = document.querySelector('main');
            if (main) main.id = 'main-content';
        }
    }
}

// Initialize accessibility on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.a11y = new AccessibilityManager();
});

// Export for manual use
window.AccessibilityManager = AccessibilityManager;
