/**
 * CHART MODAL - SIMPLE, DIRECT IMPLEMENTATION
 * No IIFE - functions exposed directly on window for immediate access
 * Includes chart instance registry to track charts created on the page
 */

console.log('🚀 [CHART-MODAL] Loading chart modal functions...');

// STATE - Chart registry to track all charts on the page
window.chartInstances = window.chartInstances || new Map();

let chartModalState = {
    isInitialized: false,
    modal: null,
    currentChart: null
};

// ========================================
// CHART REGISTRY FUNCTIONS
// ========================================

/**
 * Register a Chart.js instance for later retrieval
 */
window.registerChartInstance = function(canvasId, chartInstance) {
    if (!window.chartInstances) {
        window.chartInstances = new Map();
    }
    window.chartInstances.set(canvasId, chartInstance);
    console.log('✅ [CHART-MODAL] Chart registered:', canvasId);
};

/**
 * Get a registered Chart.js instance
 */
window.getChartInstance = function(canvasId) {
    if (!window.chartInstances) {
        window.chartInstances = new Map();
    }
    const instance = window.chartInstances.get(canvasId);
    if (instance) {
        console.log('✅ [CHART-MODAL] Chart found in registry:', canvasId);
    } else {
        console.log('⚠️ [CHART-MODAL] Chart not found in registry:', canvasId);
    }
    return instance;
};

// ========================================
// UTILITY FUNCTIONS
// ========================================

/**
 * Wait for Chart.js to load
 */
function waitForChart(callback, maxAttempts = 100) {
    if (typeof Chart !== 'undefined') {
        console.log('✅ [CHART-MODAL] Chart.js available');
        callback();
    } else if (maxAttempts > 0) {
        setTimeout(() => waitForChart(callback, maxAttempts - 1), 100);
    } else {
        console.error('❌ [CHART-MODAL] Chart.js timeout');
    }
}

/**
 * Setup modal event listeners
 */
function setupModalListeners() {
    if (chartModalState.isInitialized) {
        return;
    }

    const modal = document.getElementById('chartFullscreenModal');
    if (!modal) {
        // Modal not found yet - keep retrying indefinitely
        // This is because the modal is in {% block content %} which loads after scripts
        setTimeout(setupModalListeners, 200);
        return;
    }

    console.log('✅ [CHART-MODAL] Modal found in DOM, setting up listeners');
    chartModalState.modal = modal;

    // Click on background to close
    modal.addEventListener('click', function(e) {
        if (e.target === this) {
            closeChartModal();
        }
    });

    // Click on close button
    const closeBtn = modal.querySelector('.chart-modal-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            closeChartModal();
        });
    }

    // Escape key to close
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeChartModal();
        }
    });

    chartModalState.isInitialized = true;
    console.log('✅ [CHART-MODAL] Listeners attached to modal');
}

/**
 * Internal function to open modal with chart
 */
function openChartModalInternal(chartCanvasId, chartTitle) {
    console.log('📌 [CHART-MODAL] Opening modal for chart:', chartCanvasId);

    const modal = document.getElementById('chartFullscreenModal');
    if (!modal) {
        console.error('❌ [CHART-MODAL] Modal not found');
        return;
    }

    // Update title
    const titleEl = document.getElementById('chartModalTitle');
    if (titleEl) {
        titleEl.textContent = chartTitle;
    }

    // Get original canvas
    const originalCanvas = document.getElementById(chartCanvasId);
    if (!originalCanvas) {
        console.error('❌ [CHART-MODAL] Canvas not found:', chartCanvasId);
        return;
    }
    console.log('✅ [CHART-MODAL] Canvas found');

    // Try to get Chart instance from registry first
    let chartInstance = window.getChartInstance(chartCanvasId);
    
    // If not in registry, try canvas property
    if (!chartInstance) {
        if (originalCanvas.__chartjs__) {
            chartInstance = originalCanvas.__chartjs__;
            console.log('✅ [CHART-MODAL] Found chart via canvas.__chartjs__');
        } else if (typeof Chart !== 'undefined' && Chart.helpers && Chart.helpers.getChart) {
            chartInstance = Chart.helpers.getChart(originalCanvas);
            if (chartInstance) {
                console.log('✅ [CHART-MODAL] Found chart via Chart.helpers.getChart');
            }
        }
    }

    if (!chartInstance) {
        console.error('❌ [CHART-MODAL] Chart instance not found');
        return;
    }
    console.log('✅ [CHART-MODAL] Chart instance found, type:', chartInstance.config.type);

    // Get modal canvas
    const modalCanvas = document.getElementById('chartFullscreenCanvas');
    if (!modalCanvas) {
        console.error('❌ [CHART-MODAL] Modal canvas not found');
        return;
    }

    try {
        const config = {
            type: chartInstance.config.type,
            data: JSON.parse(JSON.stringify(chartInstance.config.data)),
            options: JSON.parse(JSON.stringify(chartInstance.config.options || {}))
        };

        config.options.responsive = true;
        config.options.maintainAspectRatio = false;

        // Destroy previous chart if exists
        if (window.currentFullscreenChart) {
            window.currentFullscreenChart.destroy();
        }

        // Create new chart
        window.currentFullscreenChart = new Chart(modalCanvas, config);
        console.log('✅ [CHART-MODAL] New chart created');

        // Show modal
        modal.classList.add('active');
        console.log('✅ [CHART-MODAL] Modal displayed');

        // Resize after a moment
        setTimeout(() => {
            if (window.currentFullscreenChart) {
                window.currentFullscreenChart.resize();
            }
        }, 100);

    } catch (error) {
        console.error('❌ [CHART-MODAL] Error creating chart:', error);
    }
}

// ========================================
// PUBLIC FUNCTIONS - EXPOSED ON WINDOW
// ========================================

/**
 * Open chart in fullscreen modal
 * @param {string} chartCanvasId - ID of the canvas element containing the chart
 * @param {string} chartTitle - Title to display in the modal
 */
window.openChartModal = function(chartCanvasId, chartTitle) {
    console.log('🔍 [CHART-MODAL] openChartModal called:', chartCanvasId);

    // Ensure modal listeners are initialized
    if (!chartModalState.isInitialized) {
        console.log('📌 [CHART-MODAL] Modal not initialized yet, initializing now...');
        setupModalListeners();
    }

    // Check if modal exists in DOM now
    const modal = document.getElementById('chartFullscreenModal');
    if (!modal) {
        console.error('❌ [CHART-MODAL] Modal still not found in DOM after initialization');
        console.log('📌 [CHART-MODAL] Will retry initialization in 100ms...');
        setTimeout(() => window.openChartModal(chartCanvasId, chartTitle), 100);
        return;
    }

    // Wait for Chart.js if needed
    if (typeof Chart === 'undefined') {
        console.warn('⏳ [CHART-MODAL] Waiting for Chart.js...');
        waitForChart(() => openChartModalInternal(chartCanvasId, chartTitle));
        return;
    }

    openChartModalInternal(chartCanvasId, chartTitle);
};

/**
 * Close the modal
 */
window.closeChartModal = function() {
    console.log('🔴 [CHART-MODAL] closeChartModal called');

    const modal = document.getElementById('chartFullscreenModal');
    if (modal) {
        modal.classList.remove('active');
    }

    if (window.currentFullscreenChart) {
        window.currentFullscreenChart.destroy();
        window.currentFullscreenChart = null;
    }

    console.log('✅ [CHART-MODAL] Modal closed');
};

// ========================================
// INITIALIZATION
// ========================================

console.log('📌 [CHART-MODAL] Document ready state:', document.readyState);

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        console.log('📌 [CHART-MODAL] DOMContentLoaded fired, initializing...');
        setupModalListeners();
    });
} else {
    console.log('📌 [CHART-MODAL] DOM already loaded, initializing now...');
    setupModalListeners();
}

console.log('✅ [CHART-MODAL] Script loaded! Available functions:');
console.log('   window.openChartModal(canvasId, title)');
console.log('   window.closeChartModal()');
console.log('   window.registerChartInstance(canvasId, chartInstance)');
console.log('   window.getChartInstance(canvasId)');
