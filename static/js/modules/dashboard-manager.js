/**
 * DashboardManager - Gestion du dashboard Chef PUR
 * @description Gère les mises à jour temps réel, compteurs, cartes et diagrammes
 * @version 2.0
 */

// ============================================================================
// CONFIGURATION ET ÉTAT GLOBAL
// ============================================================================

const REALTIME_CONFIG = {
    // NOTE: /api/stream/dashboard-summary retourne du JSON, pas du SSE
    // Utiliser directement le polling fallback sans tenter EventSource
    POLLING_INTERVAL: 10000,      // 10s
    RECONNECT_DELAY: 3000,         // 3s
    MAX_RETRIES: 5,
    DEBUG: true,
    USE_SSE: false  // Désactiver SSE - endpoint retourne JSON
};

const realTimeState = {
    eventSource: null,
    pollingInterval: null,
    isConnected: false,
    retryCount: 0,
    lastUpdate: null
};

const MAP_CONFIG = {
    center: [-9.5, 33.886917],  // Tunisia center
    defaultZoom: 7,
    colors: {
        'CREATED': '#3498db',      // Blue
        'ASSIGNED': '#9b59b6',     // Purple
        'IN_PROGRESS': '#f39c12',  // Orange
        'COMPLETED': '#27ae60',    // Green
        'VALIDATED': '#2ecc71',    // Bright Green
        'CLOSED': '#7f8c8d'        // Gray
    },
    statusLabels: {
        'CREATED': 'Nouveau',
        'ASSIGNED': 'Affecté',
        'IN_PROGRESS': 'En cours',
        'COMPLETED': 'Terminé',
        'VALIDATED': 'Validé',
        'CLOSED': 'Clôturé'
    }
};

const mapState = {
    map: null,
    markers: new Map(),
    lastUpdate: null,
    errorCount: 0,
    isInitialized: false,
    updateInterval: null
};

// ============================================================================
// UTILITAIRES
// ============================================================================

/**
 * Logger pour debug temps réel
 */
function rtLog(message, data = null) {
    if (REALTIME_CONFIG.DEBUG) {
        const timestamp = new Date().toLocaleTimeString();
        console.log(`[${timestamp}] REALTIME: ${message}`, data || '');
    }
}

// ============================================================================
// GESTION DES COMPTEURS
// ============================================================================

/**
 * Mettre à jour un compteur du dashboard
 */
function updateCounter(counterId, newValue, animated = true) {
    const element = document.getElementById(counterId);
    if (!element) {
        rtLog(`Élément ${counterId} non trouvé`);
        return;
    }

    const oldValue = parseInt(element.textContent) || 0;
    
    if (newValue === oldValue) {
        return;
    }

    if (animated && newValue !== oldValue) {
        element.classList.remove('pulse-update');
        void element.offsetWidth; // Force reflow
        element.classList.add('pulse-update');
        rtLog(`Counter ${counterId}: ${oldValue} → ${newValue}`);
    }

    element.textContent = newValue;
    realTimeState.lastUpdate = new Date();
}

/**
 * Mettre à jour tous les compteurs depuis les données SSE
 */
function updateCountersFromEvent(data) {
    if (!data.counters) {
        return;
    }

    const counters = data.counters;
    
    // Calculer le total
    let total = 0;
    Object.keys(counters).forEach(state => {
        if (state !== 'total') {
            total += counters[state] || 0;
        }
    });

    // Mettre à jour le total
    if (total > 0) {
        updateCounter('counter-total_demandes', total);
    }

    // Mettre à jour les compteurs spécifiques
    Object.keys(counters).forEach(state => {
        const value = counters[state] || 0;
        
        if (state === 'IN_PROGRESS' || state === 'ASSIGNED') {
            updateCounter('counter-interventions_cours', value);
        }
        if (state === 'COMPLETED') {
            updateCounter('counter-attente_validation', value);
        }
        if (state === 'VALIDATED') {
            updateCounter('counter-interventions_validees_sav', value);
        }
        if (state === 'CLOSED') {
            updateCounter('counter-interventions_validees_production', value);
        }
    });

    updateConnectionStatus(true);
}

// ============================================================================
// GESTION TEMPS RÉEL (POLLING)
// ============================================================================

/**
 * Initialiser le polling fallback
 * NOTE: /api/stream/dashboard-summary retourne du JSON, pas du SSE
 * Donc on utilise directement le polling sans tenter EventSource
 */
function initRealtimeUpdates() {
    rtLog('Initialisation du dashboard');
    rtLog('Utilisation du polling (endpoint retourne JSON, pas SSE)');
    
    initPollingFallback();
}

/**
 * Polling fallback
 */
function initPollingFallback() {
    rtLog('Activation du polling fallback (10s)');

    if (realTimeState.pollingInterval) {
        clearInterval(realTimeState.pollingInterval);
    }

    realTimeState.pollingInterval = setInterval(() => {
        fetchDashboardData();
    }, REALTIME_CONFIG.POLLING_INTERVAL);

    fetchDashboardData();
}

/**
 * Récupérer les données du dashboard
 */
function fetchDashboardData() {
    fetch('/api/stream/dashboard-summary')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.summary) {
                rtLog('Polling data reçu', data.summary);
                
                if (data.summary.counters) {
                    const counters = data.summary.counters;
                    Object.keys(counters).forEach(key => {
                        const counterId = `counter-${key}`;
                        updateCounter(counterId, counters[key]);
                    });
                }

                if (data.summary.total) {
                    updateCounter('counter-total_demandes', data.summary.total);
                }

                realTimeState.isConnected = true;
                updateConnectionStatus(true);
            }
        })
        .catch(error => {
            console.error('Erreur polling:', error);
            rtLog('Erreur lors du polling');
            updateConnectionStatus(false);
        });
}

/**
 * Mettre à jour le statut de connexion
 */
function updateConnectionStatus(isConnected) {
    let statusBadge = document.getElementById('realtime-status-badge');
    if (!statusBadge) {
        const container = document.querySelector('.h3.mb-4') || document.querySelector('h1');
        if (container) {
            statusBadge = document.createElement('span');
            statusBadge.id = 'realtime-status-badge';
            statusBadge.style.marginLeft = '10px';
            statusBadge.style.fontSize = '0.7em';
            container.appendChild(statusBadge);
        }
    }

    if (statusBadge) {
        if (isConnected) {
            statusBadge.className = 'badge bg-success';
            statusBadge.textContent = '🔴 Temps réel actif';
            statusBadge.title = `Dernière mise à jour: ${realTimeState.lastUpdate ? realTimeState.lastUpdate.toLocaleTimeString() : 'N/A'}`;
        } else {
            statusBadge.className = 'badge bg-warning';
            statusBadge.textContent = '🟡 Mise à jour (mode polling)';
        }
    }
}

/**
 * Arrêter les mises à jour temps réel
 */
function stopRealtimeUpdates() {
    rtLog('Arrêt des mises à jour temps réel');

    if (realTimeState.eventSource) {
        realTimeState.eventSource.close();
        realTimeState.eventSource = null;
    }

    if (realTimeState.pollingInterval) {
        clearInterval(realTimeState.pollingInterval);
        realTimeState.pollingInterval = null;
    }

    realTimeState.isConnected = false;
    updateConnectionStatus(false);
}

// ============================================================================
// GESTION CARTE (LEAFLET)
// ============================================================================

/**
 * Initialize Leaflet map
 */
function initMap() {
    try {
        const mapContainer = document.getElementById('map');
        if (!mapContainer || mapState.isInitialized) return;

        mapState.map = L.map('map').setView(MAP_CONFIG.center, MAP_CONFIG.defaultZoom);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18,
            minZoom: 5
        }).addTo(mapState.map);

        mapState.isInitialized = true;
        console.log('✅ Map initialized successfully');
        
        fetchInterventionsForMap();
        mapState.updateInterval = setInterval(fetchInterventionsForMap, 30000);
        
    } catch (error) {
        console.error('❌ Map initialization failed:', error);
        updateMapStatus('error', 'Erreur d\'initialisation');
    }
}

/**
 * Fetch interventions from API
 */
function fetchInterventionsForMap() {
    try {
        fetch('/interventions/api/interventions?limit=200')
            .then(response => {
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                return response.json();
            })
            .then(data => {
                mapState.errorCount = 0;
                updateMapStatus('connected', 'Connecté');
                updateMapMarkers(data.interventions || []);
                mapState.lastUpdate = new Date();
            })
            .catch(error => {
                mapState.errorCount++;
                console.warn('⚠️ Fetch failed:', error);
                
                if (mapState.errorCount > 3) {
                    updateMapStatus('error', 'Connexion perdue');
                } else {
                    updateMapStatus('polling', 'Tentative reconnexion');
                }
            });
    } catch (error) {
        console.error('❌ Fetch error:', error);
        updateMapStatus('error', 'Erreur réseau');
    }
}

/**
 * Update or create map markers
 */
function updateMapMarkers(interventions) {
    try {
        const currentIds = new Set(interventions.map(i => i.id));

        for (const [id, marker] of mapState.markers.entries()) {
            if (!currentIds.has(id)) {
                mapState.map.removeLayer(marker);
                mapState.markers.delete(id);
            }
        }

        interventions.forEach(intervention => {
            if (!intervention.gps_lat || !intervention.gps_long) return;

            const lat = parseFloat(intervention.gps_lat);
            const lon = parseFloat(intervention.gps_long);
            
            if (isNaN(lat) || isNaN(lon)) return;

            const status = intervention.state || intervention.statut || 'CREATED';
            const color = MAP_CONFIG.colors[status] || '#95a5a6';
            const statusLabel = MAP_CONFIG.statusLabels[status] || status;

            if (mapState.markers.has(intervention.id)) {
                const marker = mapState.markers.get(intervention.id);
                marker.setLatLng([lat, lon]);
            } else {
                const circleMarker = L.circleMarker([lat, lon], {
                    radius: 8,
                    fillColor: color,
                    color: 'white',
                    weight: 2,
                    opacity: 0.9,
                    fillOpacity: 0.8
                }).addTo(mapState.map);

                const popupContent = `
                    <div class="map-popup-content">
                        <strong>${statusLabel}</strong>
                        <hr style="margin: 8px 0;">
                        <div>
                            <strong>ID:</strong> ${intervention.id}<br>
                            <strong>Technicien:</strong> ${intervention.technicien_nom || 'N/A'}<br>
                            <strong>Client:</strong> ${intervention.client_nom || 'N/A'}<br>
                            <strong>Adresse:</strong> ${intervention.adresse || 'N/A'}<br>
                            <strong>Créée:</strong> ${intervention.date_creation ? new Date(intervention.date_creation).toLocaleString('fr-FR') : 'N/A'}<br>
                        </div>
                    </div>
                `;

                circleMarker.bindPopup(popupContent);
                circleMarker.on('click', function() {
                    console.log('Intervention details:', intervention);
                });

                mapState.markers.set(intervention.id, circleMarker);
            }
        });

    } catch (error) {
        console.error('❌ Error updating markers:', error);
    }
}

/**
 * Update map status badge
 */
function updateMapStatus(status, label) {
    try {
        const badge = document.getElementById('map-status-badge');
        if (!badge) return;

        badge.innerHTML = '';
        
        let statusColor = '#7f8c8d';
        let statusIcon = '⏳';

        if (status === 'connected') {
            statusColor = '#27ae60';
            statusIcon = '🟢';
        } else if (status === 'polling') {
            statusColor = '#f39c12';
            statusIcon = '🟡';
        } else if (status === 'error') {
            statusColor = '#e74c3c';
            statusIcon = '🔴';
        }

        badge.innerHTML = `
            <span style="color: ${statusColor}; font-weight: bold;">${statusIcon} ${label}</span>
        `;

    } catch (error) {
        console.error('❌ Error updating status badge:', error);
    }
}

// ============================================================================
// STYLES ET ANIMATIONS CSS
// ============================================================================

/**
 * Injecter les styles CSS dynamiquement
 */
function injectDashboardStyles() {
    const style = document.createElement('style');
    style.textContent = `
        #counter-total_demandes.pulse-update,
        #counter-demandes_jour_sav.pulse-update,
        #counter-demandes_jour_production.pulse-update,
        #counter-interventions_cours.pulse-update,
        #counter-attente_validation.pulse-update,
        #counter-interventions_rejetees.pulse-update,
        #counter-interventions_validees_sav.pulse-update,
        #counter-interventions_validees_production.pulse-update {
            animation: pulse-animation 0.6s ease-out;
            font-weight: bold;
        }

        @keyframes pulse-animation {
            0% {
                transform: scale(1);
                opacity: 1;
            }
            50% {
                transform: scale(1.15);
                opacity: 1;
            }
            100% {
                transform: scale(1);
                opacity: 1;
            }
        }

        #realtime-status-badge {
            animation: blink 1.5s infinite;
        }

        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        #map {
            background: #f0f0f0;
            border-radius: 4px;
        }

        .map-popup-content {
            font-size: 12px;
            min-width: 250px;
        }

        .map-popup-content strong {
            color: #2c3e50;
        }

        .map-status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 6px;
            vertical-align: middle;
        }
    `;
    document.head.appendChild(style);
}

// ============================================================================
// INITIALISATION
// ============================================================================

/**
 * Initialiser le dashboard
 */
function initDashboard() {
    rtLog('Initialisation du dashboard');
    
    // Injecter les styles
    injectDashboardStyles();
    
    // Initialiser le temps réel (polling only - endpoint retourne JSON)
    initRealtimeUpdates();

    // Initialiser la carte si Leaflet est disponible
    if (typeof L !== 'undefined') {
        const mapContainer = document.getElementById('map');
        if (mapContainer) {
            initMap();
        }
    }

    // Cleanup au départ
    window.addEventListener('beforeunload', stopRealtimeUpdates);
}

/**
 * Initialiser au chargement du DOM
 */
document.addEventListener('DOMContentLoaded', initDashboard);
