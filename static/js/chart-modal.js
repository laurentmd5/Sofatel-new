/**
 * CHART MODAL MODULE
 * Gestion modulaire des modales fullscreen pour les graphiques Chart.js
 */

(function() {
    'use strict';

    // Stockage global des instances Chart
    const chartInstances = new Map();
    
    // État global pour les charts en fullscreen
    const chartModalState = {
        currentChart: null,
        currentCanvasId: null,
        modal: null,
        isOpen: false
    };

    /**
     * Enregistrer une instance Chart
     */
    function registerChartInstance(canvasId, chartInstance) {
        chartInstances.set(canvasId, chartInstance);
        console.log('✅ Chart registered:', canvasId, chartInstance);
    }

    /**
     * Récupérer une instance Chart
     */
    function getChartInstance(canvasId) {
        const instance = chartInstances.get(canvasId);
        console.log('🔍 Getting chart instance:', canvasId, instance);
        return instance;
    }

    /**
     * Initialiser le module du modal de chart
     * À appeler une fois au chargement de la page
     */
    function initChartModal() {
        chartModalState.modal = document.getElementById('chartFullscreenModal');
        
        console.log('📋 Initializing chart modal...');
        
        if (!chartModalState.modal) {
            console.error('❌ chartFullscreenModal not found in DOM');
            return;
        }

        console.log('✅ Chart modal initialized successfully');

        // Fermer le modal au clic sur le fond
        chartModalState.modal.addEventListener('click', function(event) {
            if (event.target === chartModalState.modal) {
                console.log('🔴 Closing modal via background click');
                closeChartModal();
            }
        });

        // Fermer au clavier (Échap)
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && chartModalState.isOpen) {
                console.log('🔴 Closing modal via Escape key');
                closeChartModal();
            }
        });
    }

    /**
     * Ouvrir le modal avec un graphique
     * @param {string} chartCanvasId - ID du canvas du graphique
     * @param {string} chartTitle - Titre du graphique
     */
    function openChartModal(chartCanvasId, chartTitle) {
        console.log('🔍 Opening chart modal:', chartCanvasId);
        
        const modal = document.getElementById('chartFullscreenModal');
        if (!modal) {
            console.error('❌ Chart modal not found');
            return;
        }

        // Mettre à jour le titre
        const titleElement = document.getElementById('chartModalTitle');
        if (titleElement) {
            titleElement.textContent = chartTitle;
        }

        // Récupérer l'instance Chart depuis notre registre
        const originalChartInstance = getChartInstance(chartCanvasId);
        
        if (!originalChartInstance) {
            console.error('❌ Chart instance not registered:', chartCanvasId);
            
            // Tentative de fallback : récupérer directement du canvas
            const originalCanvas = document.getElementById(chartCanvasId);
            if (!originalCanvas || !originalCanvas.__chartjs__) {
                console.error('❌ Chart canvas not found:', chartCanvasId);
                return;
            }
        }

        // Récupérer le canvas du modal
        const modalCanvas = document.getElementById('chartFullscreenCanvas');
        if (!modalCanvas) {
            console.error('❌ Modal canvas not found');
            return;
        }

        const ctx = modalCanvas.getContext('2d');

        // Copier la configuration du chart
        let chartConfig;
        
        if (originalChartInstance) {
            chartConfig = {
                type: originalChartInstance.config.type,
                data: JSON.parse(JSON.stringify(originalChartInstance.config.data)),
                options: JSON.parse(JSON.stringify(originalChartInstance.config.options))
            };
        } else {
            console.error('❌ Cannot get chart configuration');
            return;
        }

        // Détruire le chart précédent s'il existe
        if (chartModalState.currentChart) {
            try {
                chartModalState.currentChart.destroy();
            } catch (e) {
                console.warn('⚠️ Error destroying previous chart:', e);
            }
        }

        // Créer le nouveau chart dans le modal avec options adaptées
        chartConfig.options = chartConfig.options || {};
        chartConfig.options.responsive = true;
        chartConfig.options.maintainAspectRatio = false;
        chartConfig.options.plugins = chartConfig.options.plugins || {};
        chartConfig.options.plugins.legend = chartConfig.options.plugins.legend || {
            position: 'bottom'
        };

        try {
            chartModalState.currentChart = new Chart(ctx, chartConfig);
            chartModalState.currentCanvasId = chartCanvasId;
            chartModalState.isOpen = true;
            
            // Afficher le modal
            modal.classList.add('active');

            // Forcer le redimensionnement du chart
            setTimeout(() => {
                try {
                    window.dispatchEvent(new Event('resize'));
                    if (chartModalState.currentChart && typeof chartModalState.currentChart.resize === 'function') {
                        chartModalState.currentChart.resize();
                    }
                } catch (e) {
                    console.warn('⚠️ Error resizing chart:', e);
                }
            }, 100);

            console.log('✅ Chart modal opened:', chartTitle);
        } catch (error) {
            console.error('❌ Error creating fullscreen chart:', error);
        }
    }

    /**
     * Fermer le modal
     */
    function closeChartModal() {
        const modal = document.getElementById('chartFullscreenModal');
        if (modal) {
            modal.classList.remove('active');
            chartModalState.isOpen = false;
            
            // Détruire le chart pour libérer la mémoire
            if (chartModalState.currentChart) {
                try {
                    chartModalState.currentChart.destroy();
                    chartModalState.currentChart = null;
                } catch (e) {
                    console.warn('⚠️ Error destroying chart:', e);
                }
            }
            
            console.log('✅ Chart modal closed');
        }
    }

    /**
     * Exposer les fonctions et la méthode de registre globalement
     */
    window.openChartModal = openChartModal;
    window.closeChartModal = closeChartModal;
    window.registerChartInstance = registerChartInstance;

    /**
     * Initialiser au chargement du DOM
     */
    function initOnReady() {
        initChartModal();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initOnReady);
    } else {
        // DOM déjà chargé
        initOnReady();
    }

})();

