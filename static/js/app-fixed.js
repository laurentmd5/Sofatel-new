/**
 * ============================================================================
 * APP.JS - PERFORMANCE FIXES
 * ============================================================================
 * CHANGES:
 * ✅ Use IntervalManager for all intervals (central control)
 * ✅ Debounced DOM updates
 * ✅ Safe feather icon updates
 * ✅ Proper cleanup on page unload
 * ✅ Removed animation jank (animateCounterUpdate)
 * 
 * LOAD ORDER:
 * 1. performance-utils.js (base utilities)
 * 2. app.js (this file - core lifecycle)
 * 3. Other dashboard modules
 * ============================================================================
 */

// ============================================================================
// CONFIGURATION & STATE
// ============================================================================

const SofatelcomApp = {
    config: {
        refreshInterval: 30000,      // 30 seconds
        notificationDuration: 5000,  // 5 seconds
        autoSaveInterval: 120000,    // 2 minutes
        apiBaseUrl: window.location.origin
    },
    
    state: {
        currentUser: null,
        notifications: [],
        initialized: false
    }
};

// ============================================================================
// INITIALIZATION
// ============================================================================

/**
 * Main initialization
 * ✅ FIX: Waits for PerformanceUtils to be loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    // ✅ FIX: Check dependencies loaded
    if (typeof window.PerformanceUtils === 'undefined') {
        console.warn('⚠️ PerformanceUtils not loaded, waiting...');
        setTimeout(() => initializeApp(), 100);
        return;
    }
    
    initializeApp();
    setupGlobalEventListeners();
    initializeFeatherIcons();
    setupNotifications();
    setupAutoSave();
    
    SofatelcomApp.state.initialized = true;
    console.log('✅ App initialized');
});

/**
 * Application initialization
 */
function initializeApp() {
    console.log('🚀 Initializing Sofatelcom PUR...');
    
    checkConnectivity();
    initializeTooltips();
    setupFormValidation();
    setupTables();
    startRefreshIntervals();
    
    console.log('✅ Sofatelcom PUR initialized');
}

// ============================================================================
// EVENT LISTENERS - Global Setup
// ============================================================================

/**
 * Configure global event listeners
 * ✅ FIX: Proper debounce/throttle on expensive handlers
 */
function setupGlobalEventListeners() {
    // Network connectivity
    window.addEventListener('offline', handleOffline);
    window.addEventListener('online', handleOnline);
    
    // Global errors
    window.addEventListener('error', handleGlobalError);
    
    // Window resize
    // ✅ FIX: Already debounced
    window.addEventListener('resize', window.PerformanceUtils.debounce(handleWindowResize, 250));
    
    // Prevent data loss
    window.addEventListener('beforeunload', handleBeforeUnload);
    
    // Data-action clicks (delegation)
    // ✅ FIX: Use event delegation, not individual listeners
    document.addEventListener('click', handleDataActionClicks);
}

/**
 * Initialize Feather icons
 * ✅ FIX: Use safe wrapper
 */
function initializeFeatherIcons() {
    if (typeof feather === 'undefined') return;
    
    try {
        feather.replace({
            'stroke-width': 2,
            width: 20,
            height: 20
        });
    } catch (e) {
        console.warn('⚠️ Feather initialization error:', e);
    }
}

// ============================================================================
// FORM & TABLE SETUP
// ============================================================================

/**
 * Setup form validation
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                showNotification('Veuillez corriger les erreurs dans le formulaire', 'warning');
            }
            
            form.classList.add('was-validated');
        });
    });
}

/**
 * Setup tables
 */
function setupTables() {
    const tables = document.querySelectorAll('table:not(.no-hover)');
    tables.forEach(table => {
        table.classList.add('table-hover');
    });
    
    setupTableSorting();
}

/**
 * Setup table sorting
 * ✅ FIX: Event delegation on headers
 */
function setupTableSorting() {
    // Use event delegation instead of individual listeners
    document.addEventListener('click', (e) => {
        const header = e.target.closest('th[data-sortable]');
        if (!header) return;
        
        const table = header.closest('table');
        if (!table) return;
        
        const column = Array.from(header.parentNode.children).indexOf(header);
        const isAscending = header.classList.contains('sort-asc');
        
        // Clear previous sort indicators
        const sortableHeaders = table.querySelectorAll('th[data-sortable]');
        sortableHeaders.forEach(h => {
            h.classList.remove('sort-asc', 'sort-desc');
        });
        
        // Apply new sort
        header.classList.add(isAscending ? 'sort-desc' : 'sort-asc');
        header.style.cursor = 'pointer';
        header.classList.add('user-select-none');
        
        // ✅ FIX: Sort in next frame to avoid blocking
        requestAnimationFrame(() => {
            sortTable(table, column, !isAscending);
        });
    });
}

/**
 * Sort table
 * ✅ FIX: Can be heavy, so wrapped in RAF above
 */
function sortTable(table, column, ascending = true) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        const aValue = a.cells[column].textContent.trim();
        const bValue = b.cells[column].textContent.trim();
        
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return ascending ? aNum - bNum : bNum - aNum;
        }
        
        const aDate = Date.parse(aValue);
        const bDate = Date.parse(bValue);
        
        if (!isNaN(aDate) && !isNaN(bDate)) {
            return ascending ? aDate - bDate : bDate - aDate;
        }
        
        return ascending ? 
            aValue.localeCompare(bValue, 'fr', { numeric: true, sensitivity: 'base' }) :
            bValue.localeCompare(aValue, 'fr', { numeric: true, sensitivity: 'base' });
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

// ============================================================================
// REFRESH & POLLING - Using IntervalManager
// ============================================================================

/**
 * Start refresh intervals
 * ✅ FIX: Use IntervalManager for centralized control
 */
function startRefreshIntervals() {
    const { IntervalManager } = window.PerformanceUtils;
    
    // Dashboard stats refresh
    if (document.querySelector('.dashboard-stats')) {
        IntervalManager.register(
            'refresh-dashboard-stats',
            refreshDashboardStats,
            SofatelcomApp.config.refreshInterval,
            false // Don't run immediately
        );
    }
    
    // Check new notifications
    IntervalManager.register(
        'check-new-notifications',
        checkNewNotifications,
        SofatelcomApp.config.refreshInterval,
        false
    );
}

/**
 * Refresh dashboard stats
 */
function refreshDashboardStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            if (data) {
                updateDashboardStats(data);
            }
        })
        .catch(error => console.error('❌ Stats refresh error:', error));
}

/**
 * Update dashboard stats
 * ✅ FIX: Batched updates, no animation jank
 */
function updateDashboardStats(stats) {
    const { batchDOMUpdates } = window.PerformanceUtils;
    
    // Read all values first
    const updates = [];
    Object.keys(stats).forEach(key => {
        const element = document.querySelector(`[data-stat="${key}"]`);
        if (element) {
            const newValue = stats[key];
            const currentValue = parseInt(element.textContent);
            
            if (newValue !== currentValue) {
                updates.push({ element, newValue });
            }
        }
    });
    
    // Update in batched writes
    if (updates.length > 0) {
        batchDOMUpdates(null, () => {
            updates.forEach(({ element, newValue }) => {
                element.textContent = newValue;
                // ✅ FIX: Simple pulse, no animation loop
                element.classList.add('pulse');
                setTimeout(() => element.classList.remove('pulse'), 300);
            });
        });
    }
}

/**
 * Check new notifications
 */
function checkNewNotifications() {
    if (getCurrentUserRole() !== 'technicien') return;
    
    fetch('/interventions/api/check-new-interventions')
        .then(response => response.json())
        .then(data => {
            if (data.new_interventions > 0) {
                showNotification(
                    `${data.new_interventions} nouvelle(s) intervention(s)`,
                    'info',
                    true
                );
                
                // Browser notification
                if (Notification?.permission === 'granted') {
                    try {
                        new Notification('Sofatelcom PUR', {
                            body: `${data.new_interventions} nouvelle(s) intervention(s)`,
                            icon: '/static/icon.png',
                            tag: 'new-interventions'
                        });
                    } catch (e) {
                        console.warn('⚠️ Notification error:', e);
                    }
                }
            }
        })
        .catch(error => console.error('❌ Notification check error:', error));
}

// ============================================================================
// NOTIFICATIONS
// ============================================================================

/**
 * Setup notifications
 */
function setupNotifications() {
    // Request browser notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
    
    // Create notification container if needed
    if (!document.getElementById('notification-container')) {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
}

/**
 * Show notification
 * ✅ FIX: Safe feather icon update
 */
function showNotification(message, type = 'info', persistent = false) {
    const container = document.getElementById('notification-container');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    notification.setAttribute('role', 'alert');
    
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <i data-feather="${getNotificationIcon(type)}" class="me-2"></i>
            <div class="flex-grow-1">${message}</div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    container.appendChild(notification);
    
    // ✅ FIX: Use safe feather replace
    window.PerformanceUtils.safeFeatherReplace(notification);
    
    if (!persistent) {
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 150);
            }
        }, SofatelcomApp.config.notificationDuration);
    }
    
    SofatelcomApp.state.notifications.push({
        message,
        type,
        timestamp: new Date(),
        element: notification
    });
}

/**
 * Get notification icon
 */
function getNotificationIcon(type) {
    const icons = {
        success: 'check-circle',
        info: 'info',
        warning: 'alert-triangle',
        error: 'alert-circle',
        danger: 'alert-circle'
    };
    return icons[type] || 'info';
}

// ============================================================================
// AUTO-SAVE - Using IntervalManager
// ============================================================================

/**
 * Setup auto-save
 * ✅ FIX: Use IntervalManager
 */
function setupAutoSave() {
    const { IntervalManager } = window.PerformanceUtils;
    const forms = document.querySelectorAll('[data-auto-save]');
    
    forms.forEach((form, idx) => {
        IntervalManager.register(
            `auto-save-form-${idx}`,
            () => autoSaveForm(form),
            SofatelcomApp.config.autoSaveInterval,
            false
        );
    });
}

/**
 * Auto-save form
 */
function autoSaveForm(form) {
    const formData = new FormData(form);
    const autoSaveUrl = form.dataset.autoSave;
    
    if (!autoSaveUrl) return;
    
    fetch(autoSaveUrl, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAutoSaveIndicator();
        }
    })
    .catch(error => console.error('❌ Auto-save error:', error));
}

/**
 * Show auto-save indicator
 */
function showAutoSaveIndicator() {
    let indicator = document.getElementById('auto-save-indicator');
    
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'auto-save-indicator';
        indicator.className = 'position-fixed bottom-0 end-0 m-3 alert alert-success alert-dismissible fade';
        indicator.innerHTML = `
            <small>
                <i data-feather="save" class="me-1"></i>
                Sauvegarde automatique
            </small>
        `;
        document.body.appendChild(indicator);
    }
    
    indicator.classList.add('show');
    window.PerformanceUtils.safeFeatherReplace(indicator);
    
    setTimeout(() => {
        indicator.classList.remove('show');
    }, 2000);
}

// ============================================================================
// DATA ACTION CLICKS
// ============================================================================

/**
 * Handle data-action clicks
 * ✅ FIX: Event delegation
 */
function handleDataActionClicks(event) {
    const element = event.target.closest('[data-action]');
    if (!element) return;
    
    const action = element.dataset.action;
    const params = element.dataset.params ? JSON.parse(element.dataset.params) : {};
    
    switch (action) {
        case 'refresh':
            location.reload();
            break;
        case 'print':
            window.print();
            break;
        case 'export':
            exportData(params);
            break;
        case 'copy':
            copyToClipboard(params.text || element.textContent);
            break;
        default:
            console.warn('⚠️ Unknown action:', action);
    }
}

// ============================================================================
// DATA EXPORT
// ============================================================================

/**
 * Export data
 */
function exportData(params) {
    const { type = 'csv', selector, filename } = params;
    
    if (type === 'csv' && selector) {
        const table = document.querySelector(selector);
        if (table) {
            exportTableToCSV(table, filename);
        }
    }
}

/**
 * Export table to CSV
 */
function exportTableToCSV(table, filename = 'export.csv') {
    const rows = table.querySelectorAll('tr:not(.no-export)');
    const csvContent = Array.from(rows).map(row => {
        const cells = row.querySelectorAll('th, td');
        return Array.from(cells).map(cell => {
            return `"${cell.textContent.trim().replace(/"/g, '""')}"`;
        }).join(',');
    }).join('\\n');
    
    const link = document.createElement('a');
    link.href = `data:text/csv;charset=utf-8,${encodeURIComponent(csvContent)}`;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * Copy to clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copié dans le presse-papiers', 'success');
    }).catch(err => {
        console.error('❌ Copy error:', err);
        showNotification('Erreur lors de la copie', 'error');
    });
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Check connectivity
 */
function checkConnectivity() {
    if (!navigator.onLine) {
        showNotification('Vous êtes hors ligne', 'warning', true);
    }
}

/**
 * Handle offline
 */
function handleOffline() {
    showNotification('Connexion internet perdue', 'danger', true);
}

/**
 * Handle online
 */
function handleOnline() {
    showNotification('Connexion rétablie', 'success');
}

/**
 * Handle global error
 */
function handleGlobalError(event) {
    console.error('❌ Global error:', event.error);
    showNotification('Une erreur est survenue. Veuillez rafraîchir la page.', 'error', true);
}

/**
 * Handle window resize
 * (Already debounced by caller)
 */
function handleWindowResize() {
    console.log('Window resized');
    // Responsive layout adjustments here
}

/**
 * Handle before unload
 */
function handleBeforeUnload(event) {
    // Cleanup via IntervalManager happens automatically
    const { IntervalManager } = window.PerformanceUtils;
    console.log('🛑 Page unloading, stopping intervals:', IntervalManager.getStatus());
}

/**
 * Get current user role
 */
function getCurrentUserRole() {
    return document.body.dataset.userRole || 'unknown';
}

/**
 * Initialize tooltips
 */
function initializeTooltips() {
    if (typeof bootstrap === 'undefined') return;
    
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.forEach(tooltipTriggerEl => {
        try {
            new bootstrap.Tooltip(tooltipTriggerEl);
        } catch (e) {
            console.warn('⚠️ Tooltip error:', e);
        }
    });
}

console.log('✅ App.js loaded (optimized)');
