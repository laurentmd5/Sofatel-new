/**
 * Mobile Navigation Manager
 * Handles drawer navigation for mobile devices
 * Works with responsive CSS media queries
 * 
 * Features:
 * - Drawer toggle on hamburger click
 * - Backdrop overlay with close functionality
 * - Auto-close drawer on nav link click
 * - Body scroll lock when drawer open
 * - No dependencies (vanilla JS)
 */

class MobileNavManager {
    constructor() {
        this.navbarToggler = document.querySelector('.navbar-toggler');
        this.navbarCollapse = document.querySelector('.navbar-collapse');
        
        // Guard: exit if navbar elements are missing (e.g. on login page)
        if (!this.navbarCollapse) {
            console.log('ℹ️ Mobile navigation elements not found - manager disabled for this page');
            return;
        }

        this.navItems = document.querySelectorAll('.navbar-nav .nav-link');
        this.dropdownToggles = document.querySelectorAll('.navbar-nav .dropdown-toggle');
        
        this.isOpen = false;
        this.isMobile = window.innerWidth <= 768;
        
        this.init();
    }

    /**
     * Initialize event listeners
     */
    init() {
        // Hamburger menu toggle
        if (this.navbarToggler) {
            this.navbarToggler.addEventListener('click', (e) => {
                e.preventDefault();
                this.toggle();
            });
        }

        // CRITICAL: Disable Bootstrap dropdowns on mobile to prevent conflicts
        if (this.isMobile) {
            document.querySelectorAll('[data-mobile-dropdown]').forEach(dropdown => {
                dropdown.removeAttribute('data-bs-toggle');
                // Ensure Bootstrap hasn't already initialized a dropdown
                const dropdownInstance = bootstrap.Dropdown.getInstance(dropdown);
                if (dropdownInstance) {
                    dropdownInstance.dispose();
                }
            });
        }

        // Backdrop setup and click handling
        this.setupBackdrop();

        // Use event delegation for dropdown toggles (more robust than attaching to each one)
        document.addEventListener('click', (e) => {
            // Match any dropdown-toggle with data-mobile-dropdown attribute
            const toggle = e.target.closest('[data-mobile-dropdown]');
            
            if (toggle && toggle.classList.contains('dropdown-toggle') && this.isMobile) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation(); // CRITICAL: Prevent other listeners from interfering
                
                console.log('🔴 Dropdown toggle clicked:', toggle.textContent.trim());
                
                const parent = toggle.closest('.nav-item');
                if (!parent) {
                    console.warn('No nav-item parent found for dropdown toggle');
                    return;
                }
                
                const menu = parent.querySelector('.dropdown-menu');
                if (!menu) {
                    console.warn('No dropdown-menu found in parent');
                    return;
                }
                
                // Close all other dropdowns first
                document.querySelectorAll('.navbar-nav .dropdown-menu.show').forEach(otherMenu => {
                    if (otherMenu !== menu) {
                        otherMenu.classList.remove('show');
                        // Find toggle for this menu and update aria-expanded
                        const otherToggle = otherMenu.parentElement.querySelector('[data-mobile-dropdown]');
                        if (otherToggle) {
                            otherToggle.setAttribute('aria-expanded', 'false');
                        }
                    }
                });
                
                // Toggle current dropdown
                const wasOpen = menu.classList.contains('show');
                menu.classList.toggle('show');
                const isNowOpen = menu.classList.contains('show');
                toggle.setAttribute('aria-expanded', isNowOpen ? 'true' : 'false');
                console.log(`✅ Dropdown toggled: "${toggle.textContent.trim()}" | Was: ${wasOpen ? 'OPEN' : 'CLOSED'} → Now: ${isNowOpen ? 'OPEN' : 'CLOSED'}`);
                
                return false; // Block any further propagation
            }
        }, true); // Use CAPTURE phase to intercept before other listeners

        // Use event delegation for regular nav links (close drawer on click)
        document.addEventListener('click', (e) => {
            const link = e.target.closest('.navbar-nav .nav-link:not(.dropdown-toggle)');
            if (link && this.isMobile && this.isOpen) {
                // Close drawer after a small delay to allow navigation
                setTimeout(() => {
                    this.close();
                }, 100);
            }
        });

        // Use event delegation for dropdown items (close drawer after clicking, BUT don't interfere with dropdown toggle)
        document.addEventListener('click', (e) => {
            const item = e.target.closest('.navbar-nav .dropdown-item');
            // Make sure we didn't click the toggle itself
            const toggle = e.target.closest('[data-mobile-dropdown]');
            
            if (item && !toggle && this.isMobile) {
                e.stopPropagation();
                console.log('📌 Dropdown item clicked, closing drawer');
                setTimeout(() => {
                    this.close();
                }, 100);
            }
        });

        // Handle window resize
        window.addEventListener('resize', () => {
            this.handleResize();
        });

        // Initialize Feather icons in navbar
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }

    /**
     * Setup backdrop overlay for drawer
     */
    setupBackdrop() {
        let backdrop = document.querySelector('.navbar-backdrop');
        
        if (!backdrop) {
            backdrop = document.createElement('div');
            backdrop.className = 'navbar-backdrop';
            document.body.insertBefore(backdrop, document.querySelector('.navbar'));
        }

        backdrop.addEventListener('click', () => this.close());
    }

    /**
     * Toggle drawer open/close
     */
    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    /**
     * Open drawer
     */
    open() {
        if (!this.isMobile) return;
        
        this.isOpen = true;
        this.navbarCollapse.classList.add('show');
        
        const backdrop = document.querySelector('.navbar-backdrop');
        if (backdrop) {
            backdrop.classList.add('show');
        }
        
        // Lock body scroll
        document.body.classList.add('drawer-open');
        
        // Update aria-expanded on toggler
        if (this.navbarToggler) {
            this.navbarToggler.setAttribute('aria-expanded', 'true');
        }
    }

    /**
     * Close drawer
     */
    close() {
        this.isOpen = false;
        this.navbarCollapse.classList.remove('show');
        
        const backdrop = document.querySelector('.navbar-backdrop');
        if (backdrop) {
            backdrop.classList.remove('show');
        }
        
        // Unlock body scroll
        document.body.classList.remove('drawer-open');
        
        // Close all dropdowns
        document.querySelectorAll('.navbar-nav .dropdown-menu.show').forEach(menu => {
            menu.classList.remove('show');
        });
        
        // Reset aria-expanded on all toggles
        this.dropdownToggles.forEach(toggle => {
            toggle.setAttribute('aria-expanded', 'false');
        });
        
        // Update aria-expanded on hamburger
        if (this.navbarToggler) {
            this.navbarToggler.setAttribute('aria-expanded', 'false');
        }
    }

    /**
     * Handle window resize
     * Close drawer when transitioning to desktop
     */
    handleResize() {
        const wasMobile = this.isMobile;
        this.isMobile = window.innerWidth <= 768;
        
        // If resizing from mobile to desktop, close drawer
        if (wasMobile && !this.isMobile) {
            this.close();
            this.navbarCollapse.classList.remove('show');
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    new MobileNavManager();
});
