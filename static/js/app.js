/**
 * Sofatelcom PUR - Application JavaScript principal
 * Gestion des fonctionnalités communes et utilitaires
 */

// Configuration globale
const SofatelcomApp = {
    config: {
        refreshInterval: 30000, // 30 secondes
        notificationDuration: 5000, // 5 secondes
        autoSaveInterval: 120000, // 2 minutes
        apiBaseUrl: window.location.origin
    },

    // État global de l'application
    state: {
        currentUser: null,
        notifications: [],
        intervalHandlers: []
    }
};

/**
 * Initialisation de l'application
 */
document.addEventListener('DOMContentLoaded', function () {
    initializeApp();
    setupGlobalEventListeners();
    initializeFeatherIcons();
    setupNotifications();
    setupAutoSave();
});

/**
 * Initialisation principale de l'application
 */
function initializeApp() {
    console.log('Initialisation de Sofatelcom PUR...');

    // Vérifier la connectivité
    checkConnectivity();

    // Initialiser les tooltips Bootstrap
    initializeTooltips();

    // Configurer les formulaires
    setupFormValidation();

    // Configurer les tableaux
    setupTables();

    // Démarrer les intervalles de rafraîchissement
    startRefreshIntervals();

    console.log('Sofatelcom PUR initialisé avec succès');
}

/**
 * Configuration des écouteurs d'événements globaux
 */
function setupGlobalEventListeners() {
    // Gestion de la déconnexion réseau
    window.addEventListener('offline', handleOffline);
    window.addEventListener('online', handleOnline);

    // Gestion des erreurs JavaScript globales
    window.addEventListener('error', handleGlobalError);

    // Gestion du redimensionnement de fenêtre
    window.addEventListener('resize', debounce(handleWindowResize, 250));

    // Prévention de la perte de données
    window.addEventListener('beforeunload', handleBeforeUnload);

    // Gestion des clics sur les éléments avec data-action
    document.addEventListener('click', handleDataActionClicks);
}

/**
 * Initialisation des icônes Feather avec gestion d'erreurs
 * Uses window.safeFeatherReplace from feather-fix.js
 */
function initializeFeatherIcons() {
    // Check if there are actually feather icons to initialize
    const hasFeatherIcons = document.querySelectorAll('[data-feather]').length > 0;

    if (!hasFeatherIcons) {
        return; // Skip if no feather icons
    }

    // Use the safe replace function from feather-fix.js
    if (typeof window.safeFeatherReplace === 'function') {
        window.safeFeatherReplace();
    } else if (typeof feather !== 'undefined' && typeof feather.replace === 'function') {
        try {
            feather.replace({
                'stroke-width': 2,
                width: 20,
                height: 20
            });
        } catch (e) {
            // Log non-critical errors only
            if (!(e && e.message && e.message.includes('toSvg'))) {
                console.warn('Feather icons error:', e.message);
            }
        }
    }
}

/**
 * Global safe feather replace function - can be called from anywhere
 * Prevents toSvg() errors by checking icons exist and using requestAnimationFrame
 */
window.safeFeatherReplace = function () {
    // Check if feather is available
    if (typeof feather === 'undefined' || typeof feather.replace !== 'function') {
        return;
    }

    // Only process if there are feather icons in DOM
    const featherIcons = document.querySelectorAll('[data-feather]');
    if (featherIcons.length === 0) {
        return;
    }

    // Use requestAnimationFrame to ensure DOM is stable
    requestAnimationFrame(() => {
        try {
            feather.replace();
        } catch (e) {
            // Silently ignore toSvg errors - they're not critical
            if (!(e && e.message && e.message.includes('toSvg'))) {
                console.warn('Feather replace warning (non-critical):', e);
            }
        }
    });
};

/**
 * Configuration des tooltips Bootstrap
 * ✅ FIX #4: Guard against double initialization and phantom listeners
 */
function initializeTooltips() {
    // Select only tooltips not yet initialized (avoid double creation)
    const tooltipTriggerList = [].slice.call(
        document.querySelectorAll('[data-bs-toggle="tooltip"]:not([data-tooltip-initialized])')
    );

    tooltipTriggerList.forEach(function (tooltipTriggerEl) {
        // Check if instance already exists
        const existing = bootstrap.Tooltip.getInstance(tooltipTriggerEl);
        if (!existing) {
            new bootstrap.Tooltip(tooltipTriggerEl);
            // Mark as initialized to prevent double creation
            tooltipTriggerEl.setAttribute('data-tooltip-initialized', 'true');
        }
    });
}

/**
 * Configuration de la validation des formulaires
 */
function setupFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');

    Array.from(forms).forEach(form => {
        form.addEventListener('submit', function (event) {
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
 * Configuration des tableaux
 */
function setupTables() {
    // Ajouter la classe table-hover aux tableaux
    const tables = document.querySelectorAll('table:not(.no-hover)');
    tables.forEach(table => {
        table.classList.add('table-hover');
    });

    // Gérer le tri des colonnes
    setupTableSorting();
}

/**
 * Configuration du tri des tableaux
 */
function setupTableSorting() {
    const sortableHeaders = document.querySelectorAll('th[data-sortable]');

    sortableHeaders.forEach(header => {
        header.style.cursor = 'pointer';
        header.classList.add('user-select-none');

        header.addEventListener('click', function () {
            const table = this.closest('table');
            const column = Array.from(this.parentNode.children).indexOf(this);
            const isAscending = this.classList.contains('sort-asc');

            // Réinitialiser tous les en-têtes
            sortableHeaders.forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
            });

            // Appliquer le nouveau tri
            this.classList.add(isAscending ? 'sort-desc' : 'sort-asc');

            sortTable(table, column, !isAscending);
        });
    });
}

/**
 * Tri d'un tableau
 */
function sortTable(table, column, ascending = true) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    rows.sort((a, b) => {
        const aValue = a.cells[column].textContent.trim();
        const bValue = b.cells[column].textContent.trim();

        // Détecter si c'est un nombre
        const aNum = parseFloat(aValue);
        const bNum = parseFloat(bValue);

        if (!isNaN(aNum) && !isNaN(bNum)) {
            return ascending ? aNum - bNum : bNum - aNum;
        }

        // Détecter si c'est une date
        const aDate = Date.parse(aValue);
        const bDate = Date.parse(bValue);

        if (!isNaN(aDate) && !isNaN(bDate)) {
            return ascending ? aDate - bDate : bDate - aDate;
        }

        // Tri alphabétique
        return ascending ?
            aValue.localeCompare(bValue, 'fr', { numeric: true, sensitivity: 'base' }) :
            bValue.localeCompare(aValue, 'fr', { numeric: true, sensitivity: 'base' });
    });

    // Réappliquer les lignes triées
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Démarrage des intervalles de rafraîchissement
 */
function startRefreshIntervals() {
    // Rafraîchissement des statistiques
    if (document.querySelector('.dashboard-stats')) {
        const statsInterval = setInterval(refreshDashboardStats, SofatelcomApp.config.refreshInterval);
        SofatelcomApp.state.intervalHandlers.push(statsInterval);
    }

    // Vérification des nouvelles notifications
    const notificationInterval = setInterval(checkNewNotifications, SofatelcomApp.config.refreshInterval);
    SofatelcomApp.state.intervalHandlers.push(notificationInterval);
}

/**
 * Rafraîchissement des statistiques du dashboard
 */
function refreshDashboardStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => updateDashboardStats(data))
        .catch(error => console.error('Erreur refresh stats:', error));
}

/**
 * Mise à jour des statistiques dans l'interface
 */
function updateDashboardStats(stats) {
    Object.keys(stats).forEach(key => {
        const element = document.querySelector(`[data-stat="${key}"]`);
        if (element) {
            const newValue = stats[key];
            const currentValue = parseInt(element.textContent);

            if (newValue !== currentValue) {
                animateCounterUpdate(element, currentValue, newValue);
            }
        }
    });
}

/**
 * Animation de mise à jour des compteurs
 */
function animateCounterUpdate(element, from, to) {
    const duration = 1000;
    const steps = 30;
    const stepValue = (to - from) / steps;
    let current = from;
    let step = 0;

    const interval = setInterval(() => {
        step++;
        current += stepValue;

        if (step >= steps) {
            element.textContent = to;
            clearInterval(interval);
        } else {
            element.textContent = Math.round(current);
        }
    }, duration / steps);

    // Ajouter un effet visuel
    element.classList.add('pulse');
    setTimeout(() => element.classList.remove('pulse'), duration);
}

/**
 * Vérification des nouvelles notifications
 */
function checkNewNotifications() {
    if (getCurrentUserRole() === 'technicien') {
        fetch('/interventions/api/check-new-interventions')
            .then(response => response.json())
            .then(data => {
                if (data.new_interventions > 0) {
                    showNotification(
                        `${data.new_interventions} nouvelle(s) intervention(s) assignée(s)`,
                        'info',
                        true
                    );

                    // Notification browser si autorisée
                    if (Notification.permission === 'granted') {
                        new Notification('Sofatelcom PUR', {
                            body: `${data.new_interventions} nouvelle(s) intervention(s) assignée(s)`,
                            icon: '/static/icon.png',
                            tag: 'new-interventions'
                        });
                    }
                }
            })
            .catch(error => console.error('Erreur check notifications:', error));
    }
}

/**
 * Configuration du système de notifications
 */
function setupNotifications() {
    // Demander permission pour les notifications browser
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }

    // Créer le conteneur de notifications si nécessaire
    if (!document.getElementById('notification-container')) {
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
}

/**
 * Affichage d'une notification
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

    // Safely replace feather icons if present
    if (document.querySelectorAll('[data-feather]').length > 0) {
        if (typeof window.safeFeatherReplace === 'function') {
            window.safeFeatherReplace();
        } else if (typeof feather !== 'undefined' && typeof feather.replace === 'function') {
            try {
                feather.replace();
            } catch (e) {
                // Silent fail for non-critical errors
                if (!(e && e.message && e.message.includes('toSvg'))) {
                    console.warn('Feather.replace() warning:', e.message);
                }
            }
        }
    }

    // Suppression automatique si non persistante
    if (!persistent) {
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 150);
            }
        }, SofatelcomApp.config.notificationDuration);
    }

    // Ajouter à l'état
    SofatelcomApp.state.notifications.push({
        message,
        type,
        timestamp: new Date(),
        element: notification
    });
}

/**
 * Obtenir l'icône pour une notification
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

/**
 * Configuration de la sauvegarde automatique
 */
function setupAutoSave() {
    const forms = document.querySelectorAll('[data-auto-save]');

    forms.forEach(form => {
        const interval = setInterval(() => {
            autoSaveForm(form);
        }, SofatelcomApp.config.autoSaveInterval);

        SofatelcomApp.state.intervalHandlers.push(interval);
    });
}

/**
 * Sauvegarde automatique d'un formulaire
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
        .catch(error => console.error('Erreur sauvegarde auto:', error));
}

/**
 * Indicateur de sauvegarde automatique
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
    // Sécuriser l'appel à feather.replace pour éviter l'erreur toSvg
    if (typeof feather !== 'undefined' && typeof feather.replace === 'function') {
        try {
            feather.replace();
        } catch (e) {
            console.warn('Feather.replace() error:', e);
        }
    }

    setTimeout(() => {
        indicator.classList.remove('show');
    }, 2000);
}

/**
 * Gestion des clics sur les éléments avec data-action
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
            console.warn('Action non reconnue:', action);
    }
}

/**
 * Export de données
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
 * Export d'un tableau en CSV
 */
/**
 * ✅ FIX #3: O(n) instead of O(n²) export complexity
 * Use row.children instead of querySelectorAll to avoid re-scanning table per row
 */
function exportTableToCSV(table, filename = 'export.csv') {
    const rows = table.querySelectorAll('tr:not(.no-export)');
    const csvContent = Array.from(rows).map(row => {
        // Direct child access: O(1) instead of DOM query O(n)
        const cells = Array.from(row.children);
        return cells.map(cell => {
            return `"${cell.textContent.trim().replace(/"/g, '""')}"`;
        }).join(',');
    }).join('\n');

    downloadCSV(csvContent, filename);
}

/**
 * Téléchargement d'un fichier CSV
 */
function downloadCSV(content, filename) {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');

    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }
}

/**
 * Copie dans le presse-papiers
 */
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showNotification('Copié dans le presse-papiers', 'success');
        });
    } else {
        // Fallback pour les navigateurs plus anciens
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            document.execCommand('copy');
            showNotification('Copié dans le presse-papiers', 'success');
        } catch (err) {
            showNotification('Erreur lors de la copie', 'error');
        }

        document.body.removeChild(textArea);
    }
}

/**
 * Vérification de la connectivité
 */
function checkConnectivity() {
    if (!navigator.onLine) {
        showNotification('Vous êtes hors ligne', 'warning', true);
    }
}

/**
 * Gestion de la déconnexion réseau
 */
function handleOffline() {
    showNotification('Connexion perdue. Certaines fonctionnalités peuvent être limitées.', 'warning', true);
    document.body.classList.add('offline');
}

/**
 * Gestion de la reconnexion réseau
 */
function handleOnline() {
    showNotification('Connexion rétablie', 'success');
    document.body.classList.remove('offline');
}

/**
 * Gestion des erreurs JavaScript globales
 */
function handleGlobalError(event) {
    // Affiche l'objet d'erreur complet pour le debug
    if (event && typeof event.error !== 'undefined') {
        console.error('Erreur JavaScript:', event.error);
    } else {
        console.error('Erreur JavaScript (event):', event);
    }

    // En mode développement, afficher l'erreur
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        let message = 'Erreur JavaScript inconnue';
        if (event && event.error) {
            if (typeof event.error === 'object' && event.error !== null) {
                message = event.error.message || event.error.toString();
            } else {
                message = event.error;
            }
        } else if (event && event.message) {
            message = event.message;
        } else {
            message = JSON.stringify(event);
        }
        showNotification(`Erreur: ${message}`, 'error');
    }
}
/**
 * Gestion du redimensionnement de fenêtre
 */
function handleWindowResize() {
    // Redimensionner les canvas de signature si présents
    const signaturePads = document.querySelectorAll('.signature-pad');
    signaturePads.forEach(canvas => {
        if (canvas.signaturePad) {
            canvas.signaturePad.resizeCanvas();
        }
    });

    // Réinitialiser les tooltips
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(el => {
        const tooltip = bootstrap.Tooltip.getInstance(el);
        if (tooltip) tooltip.dispose();
    });
    initializeTooltips();
}

/**
 * Gestion avant fermeture de page
 */
function handleBeforeUnload(event) {
    const forms = document.querySelectorAll('form[data-warn-unsaved]');
    const hasUnsavedChanges = Array.from(forms).some(form => formHasUnsavedChanges(form));

    if (hasUnsavedChanges) {
        event.preventDefault();
        event.returnValue = '';
    }
}

/**
 * Vérifier si un formulaire a des changements non sauvegardés
 */
function formHasUnsavedChanges(form) {
    const formData = new FormData(form);
    const originalData = form.dataset.originalData;

    if (!originalData) return false;

    const currentData = JSON.stringify(Array.from(formData.entries()));
    return currentData !== originalData;
}

/**
 * Obtenir le rôle de l'utilisateur actuel
 */
function getCurrentUserRole() {
    const userElement = document.querySelector('[data-user-role]');
    return userElement ? userElement.dataset.userRole : null;
}

/**
 * Utilitaire: Debounce
 */
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction() {
        const context = this;
        const args = arguments;

        const later = function () {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };

        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);

        if (callNow) func.apply(context, args);
    };
}

/**
 * Utilitaire: Throttle
 */
function throttle(func, limit) {
    let inThrottle;
    return function () {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Cleanup lors de la fermeture de page
 * ✅ FIX #6: Proper cleanup on navigation to prevent memory leaks
 * Dispose all component instances and disconnect observers
 */
window.addEventListener('beforeunload', function () {
    // Nettoyer les intervalles
    SofatelcomApp.state.intervalHandlers.forEach(handler => {
        clearInterval(handler);
    });

    // ✅ Dispose all Bootstrap tooltips (prevent phantom listeners)
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltips.forEach(el => {
        const tooltip = bootstrap.Tooltip.getInstance(el);
        if (tooltip) {
            tooltip.dispose();  // Cleanup instance and listeners
        }
    });

    // ✅ Disconnect MutationObserver if exists
    if (window.autoPagination && window.autoPagination.observer) {
        window.autoPagination.observer.disconnect();
        window.autoPagination.observer = null;
    }
});

// Export des fonctions utilitaires pour utilisation dans d'autres scripts
window.SofatelcomApp = SofatelcomApp;
window.showNotification = showNotification;
window.copyToClipboard = copyToClipboard;
window.exportTableToCSV = exportTableToCSV;
