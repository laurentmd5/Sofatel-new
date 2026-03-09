/**
 * 📍 SOFATELCOM MOBILE GEOLOCATION INTEGRATION
 * Bridges Flutter WebView GeolocationService with web dashboard
 * 
 * Usage:
 * - Call MobileGeo.startTracking() to begin GPS tracking
 * - Call MobileGeo.stopTracking() to stop tracking
 * - Automatically sends positions to /api/tracking endpoint
 */

const MobileGeo = (() => {
  const TAG = '[MOBILE-GEO]';
  let isTracking = false;
  let authToken = null;
  let currentIntervention = null;
  let trackingStatus = null;
  
  /**
   * Initialize mobile geolocation integration
   * Should be called after page load and user authentication
   */
  function init() {
    console.log(`${TAG} Initializing mobile geolocation integration...`);
    
    // Check if running in Flutter WebView
    if (!window.SofatelcomGeo) {
      console.warn(`${TAG} SofatelcomGeo interface not available (not in Flutter)`);
      return false;
    }
    
    // Get auth token from page (e.g., data attribute or global)
    authToken = document.body.dataset.authToken || 
                window.SOFATELCOM_AUTH_TOKEN || 
                localStorage.getItem('access_token');
    
    if (!authToken) {
      console.error(`${TAG} No auth token found. Cannot initialize GPS tracking.`);
      return false;
    }
    
    // Set token in native geolocation service
    window.SofatelcomGeo.setAuthToken(authToken);
    
    // Get current intervention from page
    currentIntervention = document.body.dataset.interventionId || 
                          window.CURRENT_INTERVENTION_ID || null;
    
    // Listen for location updates from native
    window.onGeoLocationUpdate = (latitude, longitude, accuracy) => {
      console.log(`${TAG} Position: ${latitude.toFixed(4)}, ${longitude.toFixed(4)} (±${accuracy.toFixed(1)}m)`);
      updateDashboardMap(latitude, longitude, accuracy);
    };
    
    // Listen for tracking status changes
    window.onTrackingStatusChanged = (status) => {
      isTracking = status === 'active';
      console.log(`${TAG} Tracking status: ${status}`);
      updateTrackingUI(isTracking);
    };
    
    console.log(`${TAG} Initialization complete`);
    return true;
  }
  
  /**
   * Start GPS tracking
   */
  function startTracking() {
    console.log(`${TAG} Starting GPS tracking...`);
    
    if (!window.SofatelcomGeo) {
      console.warn(`${TAG} SofatelcomGeo not available`);
      return false;
    }
    
    try {
      window.SofatelcomGeo.startTracking();
      isTracking = true;
      updateTrackingUI(true);
      return true;
    } catch (e) {
      console.error(`${TAG} Error starting tracking:`, e);
      return false;
    }
  }
  
  /**
   * Stop GPS tracking
   */
  function stopTracking() {
    console.log(`${TAG} Stopping GPS tracking...`);
    
    if (!window.SofatelcomGeo) {
      console.warn(`${TAG} SofatelcomGeo not available`);
      return false;
    }
    
    try {
      window.SofatelcomGeo.stopTracking();
      isTracking = false;
      updateTrackingUI(false);
      return true;
    } catch (e) {
      console.error(`${TAG} Error stopping tracking:`, e);
      return false;
    }
  }
  
  /**
   * Update dashboard map with new position
   */
  function updateDashboardMap(latitude, longitude, accuracy) {
    // Check if MapTracker is available (from map-realtime.js)
    if (window.MapTracker && window.MapTracker.state.map) {
      // Get current user/technician info
      const technicianId = document.body.dataset.technicianId || 
                          window.CURRENT_USER_ID;
      
      if (technicianId) {
        // Create position object
        const position = {
          technicien_id: technicianId,
          latitude: latitude,
          longitude: longitude,
          accuracy: accuracy,
          timestamp: new Date().toISOString(),
          status: document.body.dataset.trackingStatus || 'en_route'
        };
        
        // Update map marker
        MapTracker.updatePosition(position);
      }
    }
    
    // Update page indicator
    const indicator = document.querySelector('[data-tracking-status]');
    if (indicator) {
      indicator.textContent = `📍 ${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
      indicator.dataset.lastUpdate = new Date().toLocaleTimeString();
    }
  }
  
  /**
   * Update UI elements to reflect tracking status
   */
  function updateTrackingUI(active) {
    // Update button state
    const startBtn = document.querySelector('[data-action="start-tracking"]');
    const stopBtn = document.querySelector('[data-action="stop-tracking"]');
    
    if (startBtn) {
      startBtn.disabled = active;
      startBtn.style.opacity = active ? '0.5' : '1';
    }
    if (stopBtn) {
      stopBtn.disabled = !active;
      stopBtn.style.opacity = active ? '1' : '0.5';
    }
    
    // Update status badge
    const badge = document.querySelector('[data-tracking-badge]');
    if (badge) {
      badge.textContent = active ? '🔴 ACTIF' : '⏹️ INACTIF';
      badge.style.color = active ? '#dc3545' : '#6c757d';
    }
    
    // Update data attribute on body
    document.body.dataset.tracking = active ? 'true' : 'false';
  }
  
  /**
   * Get current tracking status
   */
  function getStatus() {
    return {
      isTracking: isTracking,
      hasAuth: !!authToken,
      currentIntervention: currentIntervention,
      isAvailable: !!window.SofatelcomGeo
    };
  }
  
  /**
   * Set current intervention (called when user selects/switches intervention)
   */
  function setCurrentIntervention(interventionId) {
    currentIntervention = interventionId;
    console.log(`${TAG} Current intervention set to: ${interventionId}`);
  }
  
  /**
   * Toggle tracking on/off
   */
  function toggle() {
    if (isTracking) {
      return stopTracking();
    } else {
      return startTracking();
    }
  }
  
  // Public API
  return {
    init,
    startTracking,
    stopTracking,
    toggle,
    getStatus,
    setCurrentIntervention,
    isAvailable: () => !!window.SofatelcomGeo,
  };
})();

/**
 * Auto-initialize when page loads and DOM is ready
 */
document.addEventListener('DOMContentLoaded', () => {
  // Wait for auth to be set (usually done by Flask template)
  setTimeout(() => {
    MobileGeo.init();
    
    // Set up button listeners
    const startBtn = document.querySelector('[data-action="start-tracking"]');
    const stopBtn = document.querySelector('[data-action="stop-tracking"]');
    const toggleBtn = document.querySelector('[data-action="toggle-tracking"]');
    
    if (startBtn) {
      startBtn.addEventListener('click', () => MobileGeo.startTracking());
    }
    if (stopBtn) {
      stopBtn.addEventListener('click', () => MobileGeo.stopTracking());
    }
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => MobileGeo.toggle());
    }
    
    console.log('[MOBILE-GEO] Initialization listeners set up');
  }, 500);
});

// Expose in console for debugging
window.MobileGeo = MobileGeo;
