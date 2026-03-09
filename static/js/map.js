document.addEventListener('DOMContentLoaded', function() {
    // Localiser les champs GPS
    const gpsLatField = document.getElementById('gps_lat');
    const gpsLongField = document.getElementById('gps_long');
    const geolocateBtn = document.getElementById('geolocateBtn');
    const autoGeolocateBtn = document.getElementById('autoGeolocateBtn');
    
    // Debug: Log GPS fields found
    if (!gpsLatField && !gpsLongField) {
        console.log('ℹ️ No GPS fields found - geolocation features disabled for this page');
        return;
    }

    /**
     * Safely update feather icons after DOM modifications
     * Consolidated function to avoid excessive feather.replace() calls
     */
    function updateFeatherIcons() {
        if (typeof window.safeFeatherReplace === 'function') {
            window.safeFeatherReplace();
        }
    }

    // Fonction de géolocalisation
    function getCurrentLocation(button, isAutomatic = false) {
        if (!navigator.geolocation) {
            if (!isAutomatic) {
                alert("La géolocalisation n'est pas supportée par votre navigateur");
            }
            return;
        }

        if (button) {
            button.disabled = true;
            button.innerHTML = '<i data-feather="loader" class="me-1"></i> Localisation en cours...';
            // Update feather icons ONCE after changing button HTML
            setTimeout(updateFeatherIcons, 50);
        }

        navigator.geolocation.getCurrentPosition(
            function(position) {
                gpsLatField.value = position.coords.latitude.toFixed(6);
                gpsLongField.value = position.coords.longitude.toFixed(6);
                
                // Ajouter une notification discrète
                const notification = document.createElement('div');
                notification.className = 'alert alert-success alert-dismissible fade show position-fixed';
                notification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; width: 300px;';
                notification.innerHTML = `
                    <i data-feather="map-pin" class="me-2"></i>
                    Position obtenue: ${position.coords.latitude.toFixed(4)}, ${position.coords.longitude.toFixed(4)}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                `;
                document.body.appendChild(notification);
                // Update feather icons ONCE after adding notification
                setTimeout(updateFeatherIcons, 50);
                
                // Supprimer la notification après 5 secondes
                setTimeout(() => {
                    if (notification.parentNode) {
                        notification.remove();
                    }
                }, 5000);
                
                if (button) {
                    button.innerHTML = '<i data-feather="check" class="me-1"></i> Position obtenue';
                    button.className = button.className.replace('btn-outline-primary', 'btn-outline-success');
                    button.disabled = false;
                    // Update feather icons ONCE after changing button state
                    setTimeout(updateFeatherIcons, 50);
                }
            },
            function(error) {
                let errorMessage = "Erreur de localisation";
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        errorMessage = isAutomatic ? "Géolocalisation refusée" : "Vous avez refusé l'accès à la géolocalisation";
                        break;
                    case error.POSITION_UNAVAILABLE:
                        errorMessage = "Position indisponible";
                        break;
                    case error.TIMEOUT:
                        errorMessage = "Temps écoulé pour la localisation";
                        break;
                }
                
                if (button) {
                    button.innerHTML = '<i data-feather="alert-circle" class="me-1"></i> ' + errorMessage;
                    button.className = button.className.replace('btn-outline-primary', 'btn-outline-danger');
                    button.disabled = false;
                    // Update feather icons ONCE after error
                    setTimeout(updateFeatherIcons, 50);
                }
                
                if (!isAutomatic) {
                    // Afficher une notification d'erreur
                    const errorNotification = document.createElement('div');
                    errorNotification.className = 'alert alert-warning alert-dismissible fade show position-fixed';
                    errorNotification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; width: 300px;';
                    errorNotification.innerHTML = `
                        <i data-feather="alert-triangle" class="me-2"></i>
                        ${errorMessage}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    `;
                    document.body.appendChild(errorNotification);
                    // Update feather icons ONCE after adding error notification
                    setTimeout(updateFeatherIcons, 50);
                    
                    setTimeout(() => {
                        if (errorNotification.parentNode) {
                            errorNotification.remove();
                        }
                    }, 5000);
                }
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000 // Cache la position pendant 1 minute
            }
        );
    }

    // Event listeners pour les boutons
    if (geolocateBtn) {
        geolocateBtn.addEventListener('click', function() {
            getCurrentLocation(geolocateBtn, false);
        });
    }

    if (autoGeolocateBtn) {
        autoGeolocateBtn.addEventListener('click', function() {
            // Activer la géolocalisation automatique
            localStorage.setItem('autoGeolocate', 'true');
            getCurrentLocation(autoGeolocateBtn, true);
            
            // Changer le bouton pour indiquer que c'est activé
            autoGeolocateBtn.innerHTML = '<i data-feather="navigation" class="me-1"></i> Auto activée';
            autoGeolocateBtn.className = 'btn btn-success btn-sm ms-2';
            setTimeout(updateFeatherIcons, 50);
        });
    }

    // Géolocalisation automatique au chargement si activée et champs vides
    const isAutoGeolocateEnabled = localStorage.getItem('autoGeolocate') === 'true';
    const fieldsAreEmpty = !gpsLatField.value && !gpsLongField.value;
    
    if (isAutoGeolocateEnabled && fieldsAreEmpty) {
        // Attendre un peu pour que la page soit complètement chargée
        setTimeout(() => {
            getCurrentLocation(null, true);
            
            if (autoGeolocateBtn) {
                autoGeolocateBtn.innerHTML = '<i data-feather="navigation" class="me-1"></i> Auto activée';
                autoGeolocateBtn.className = 'btn btn-success btn-sm ms-2';
                setTimeout(updateFeatherIcons, 50);
            }
        }, 1000);
    }
});