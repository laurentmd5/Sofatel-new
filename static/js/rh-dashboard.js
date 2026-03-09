/**
 * RH Dashboard - Frontend JavaScript
 * Gestion des demandes de congés, calendrier, statistiques
 */

let currentMonth = new Date();
let currentTechnicianId = null;
let selectedForBulk = new Set();

/**
 * Initialiser le dashboard RH
 */
function initRHDashboard() {
    loadMyRequests();
    setupDateValidation();
    setupEventListeners();
}

/**
 * Charger les demandes personnelles
 */
function loadMyRequests() {
    const url = '/api/rh/conges?page=1&per_page=50';
    
    fetch(url, {
        headers: { 'Accept': 'application/json' }
    })
    .then(resp => handleResponseStatus(resp))
    .then(data => {
        if (!data.success) throw new Error(data.error);
        displayMyRequests(data.leaves);
        updateMyRequestsStats(data.leaves);
    })
    .catch(err => {
        console.error('Erreur chargement demandes:', err);
        document.getElementById('my-requests-list').innerHTML = 
            '<div class="alert alert-error">Erreur: ' + err.message + '</div>';
    });
}

/**
 * Afficher les demandes personnelles
 */
function displayMyRequests(leaves) {
    const container = document.getElementById('my-requests-list');
    
    if (leaves.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><p>Aucune demande trouvée</p></div>';
        container.classList.remove('loading');
        return;
    }

    container.innerHTML = leaves.map(leave => `
        <div class="leave-request ${leave.statut}">
            <div class="leave-request-info">
                <strong>${getLeaveTypeLabel(leave.type)}</strong>
                <div class="leave-request-dates">
                    ${formatDate(leave.date_debut)} → ${formatDate(leave.date_fin)}
                    <strong>(${Math.round(leave.business_days)} j.o.)</strong>
                </div>
                <span class="leave-request-type">${leave.type}</span>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">
                    ${leave.reason || 'Pas de motif'}
                </div>
                ${leave.statut === 'rejected' && leave.manager_comment ? 
                    `<div style="color: #721c24; margin-top: 5px; font-size: 12px;">
                        <strong>Raison du rejet:</strong> ${leave.manager_comment}
                    </div>` : ''}
            </div>
            <div style="text-align: right;">
                <div class="leave-request-status ${leave.statut}">
                    ${getStatusLabel(leave.statut)}
                </div>
                <div style="margin-top: 10px; font-size: 12px; color: #666;">
                    ${formatDate(leave.created_at)}
                </div>
                <button type="button" class="btn btn-primary btn-sm" style="margin-top: 10px;"
                        onclick="showRequestDetails(${leave.id})">
                    Détails
                </button>
            </div>
        </div>
    `).join('');
    container.classList.remove('loading');
}

/**
 * Mettre à jour les statistiques des demandes personnelles
 */
function updateMyRequestsStats(leaves) {
    const stats = {
        pending: leaves.filter(l => l.statut === 'pending').length,
        approved: leaves.filter(l => l.statut === 'approved').length,
        rejected: leaves.filter(l => l.statut === 'rejected').length
    };

    document.getElementById('count-pending').textContent = stats.pending;
    document.getElementById('count-approved').textContent = stats.approved;
    document.getElementById('count-rejected').textContent = stats.rejected;
}

/**
 * Configuration de la validation des dates du formulaire
 */
function setupDateValidation() {
    const dateStart = document.getElementById('date-start');
    const dateEnd = document.getElementById('date-end');

    if (dateStart && dateEnd) {
        // Définir la date minimale (aujourd'hui)
        const today = new Date().toISOString().split('T')[0];
        dateStart.min = today;
        dateEnd.min = today;

        // Événement: quand les dates changent
        dateStart.addEventListener('change', validateDateRange);
        dateEnd.addEventListener('change', validateDateRange);
    }
}

/**
 * Valider la plage de dates et calculer les jours ouvrables
 */
function validateDateRange() {
    const dateStart = document.getElementById('date-start');
    const dateEnd = document.getElementById('date-end');
    const businessDaysEl = document.getElementById('business-days');

    if (!dateStart.value || !dateEnd.value) return;

    const start = new Date(dateStart.value);
    const end = new Date(dateEnd.value);

    if (start > end) {
        dateEnd.setCustomValidity('La date de fin doit être après la date de début');
        return;
    }

    dateEnd.setCustomValidity('');

    // Calculer les jours ouvrables
    const businessDays = calculateBusinessDays(start, end);
    businessDaysEl.value = businessDays + ' jour(s) ouvrable(s)';

    // Vérifier les chevauchements et impact planning
    checkLeaveConflicts(start, end);
}

/**
 * Vérifier les chevauchements et l'impact sur le planning
 */
function checkLeaveConflicts(start, end) {
    // Pour l'instant, afficher une alerte visuelle simple
    const conflictDiv = document.getElementById('conflict-warning');
    const interventionDiv = document.getElementById('intervention-impact');

    // Réinitialiser
    conflictDiv.style.display = 'none';
    interventionDiv.style.display = 'none';

    // Appel API pour vérifier les conflits
    fetch('/api/rh/leave/check-conflicts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            date_debut: start.toISOString().split('T')[0],
            date_fin: end.toISOString().split('T')[0]
        })
    })
    .then(resp => handleResponseStatus(resp))
    .then(data => {
        if (data.conflicts && data.conflicts.length > 0) {
            const conflictDetails = document.getElementById('conflict-details');
            conflictDetails.innerHTML = data.conflicts.map(c => 
                `<div style="margin-top: 10px; font-size: 12px;">
                    Chevauchement: ${formatDate(c.date_debut)} - ${formatDate(c.date_fin)}
                </div>`
            ).join('');
            conflictDiv.style.display = 'block';
        }

        if (data.interventions && data.interventions.length > 0) {
            const interventionList = document.getElementById('intervention-list');
            interventionList.innerHTML = `
                <div style="font-size: 12px; margin-top: 10px;">
                    ${data.interventions.length} intervention(s) planifiée(s) pendant cette période
                </div>`;
            interventionDiv.style.display = 'block';
        }
    })
    .catch(err => console.log('Info: pas de vérification API', err));
}

/**
 * Soumettre une demande de congé
 */
function submitLeaveRequest(event) {
    event.preventDefault();

    const formMessage = document.getElementById('form-message');
    
    const data = {
        date_debut: document.getElementById('date-start').value,
        date_fin: document.getElementById('date-end').value,
        type: document.getElementById('leave-type').value,
        reason: document.getElementById('leave-reason').value
    };

    // Validation basique
    if (data.reason.length < 10) {
        showMessage('form-message', 'Le motif doit contenir au moins 10 caractères', 'error');
        return;
    }

    // Soumettre
    fetch('/api/rh/conges', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(resp => handleResponseStatus(resp))
    .then(data => {
        if (!data.success) throw new Error(data.error);
        
        showMessage('form-message', '✓ Demande soumise avec succès! Référence: ' + data.id, 'success');
        document.getElementById('leave-request-form').reset();
        document.getElementById('business-days').value = '';
        
        // Recharger la liste après 2 secondes
        setTimeout(() => {
            loadMyRequests();
            // Revenir au tab mes demandes
            document.getElementById('tab-my-requests').classList.add('active');
            document.getElementById('tab-new-request').classList.remove('active');
        }, 2000);
    })
    .catch(err => {
        console.error('Erreur soumission:', err);
        showMessage('form-message', '✗ Erreur: ' + err.message, 'error');
    });
}

/**
 * Charger le calendrier de l'équipe
 */
function loadTeamCalendar() {
    const year = currentMonth.getFullYear();
    const month = String(currentMonth.getMonth() + 1).padStart(2, '0');
    const container = document.getElementById('team-calendar-container');
    
    // Add loading state
    container.innerHTML = '<div class="loading"><div class="spinner"></div> Chargement du calendrier...</div>';
    container.classList.add('loading');

    fetch(`/api/rh/calendar/team?year=${year}&month=${month}`, {
        headers: { 'Accept': 'application/json' }
    })
    .then(resp => handleResponseStatus(resp))
    .then(data => {
        if (data.success) {
            container.innerHTML = '<div class="calendar-grid" id="calendar-grid"></div>';
            renderCalendar(data.calendar);
        } else {
            container.innerHTML = '<div class="alert alert-error">Erreur: ' + (data.error || 'Calendrier indisponible') + '</div>';
            container.classList.remove('loading');
        }
    })
    .catch(err => {
        console.error('Erreur chargement calendrier:', err);
        container.innerHTML = '<div class="alert alert-error">Erreur lors du chargement du calendrier: ' + err.message + '</div>';
        container.classList.remove('loading');
    });
}

/**
 * Rendre le calendrier mensuel
 */
function renderCalendar(calendarData) {
    const monthName = currentMonth.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });
    document.getElementById('calendar-month').textContent = monthName.charAt(0).toUpperCase() + monthName.slice(1);

    const grid = document.getElementById('calendar-grid');
    grid.innerHTML = '';

    // En-têtes jours
    const days = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'];
    days.forEach(day => {
        const header = document.createElement('div');
        header.className = 'calendar-day header';
        header.textContent = day;
        grid.appendChild(header);
    });

    // Jour 1 du mois
    const firstDay = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), 1);
    const lastDay = new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1, 0);
    const startDate = new Date(firstDay);
    startDate.setDate(startDate.getDate() - (firstDay.getDay() || 7) + 1);

    const today = new Date();
    today.setHours(0, 0, 0, 0);

    let current = new Date(startDate);
    while (current <= lastDay || current.getDay() !== 1) {
        const cell = document.createElement('div');
        cell.className = 'calendar-day';

        if (current.getMonth() !== currentMonth.getMonth()) {
            cell.classList.add('other-month');
        }

        const dateStr = current.toISOString().split('T')[0];
        if (current.toDateString() === today.toDateString()) {
            cell.classList.add('today');
        }

        const dayNum = current.getDate();
        cell.innerHTML = `<span class="number">${dayNum}</span>`;

        if (calendarData[dateStr]) {
            cell.classList.add('has-leave');
            const leaves = calendarData[dateStr];
            const count = leaves.length;
            
            // Build tooltip with technicien names and leave types
            let tooltip = leaves.map(l => `${l.technicien} (${getLeaveTypeLabel(l.type)})`).join(', ');
            
            cell.innerHTML += `<span class="leave-badge" title="${tooltip}">${count} absent${count > 1 ? 's' : ''}</span>`;
        }

        grid.appendChild(cell);
        current.setDate(current.getDate() + 1);
    }
    
    // Remove loading state
    const container = document.getElementById('team-calendar-container');
    if (container) {
        container.classList.remove('loading');
    }
}

/**
 * Mois précédent
 */
function previousMonth() {
    currentMonth.setMonth(currentMonth.getMonth() - 1);
    loadTeamCalendar();
}

/**
 * Mois suivant
 */
function nextMonth() {
    currentMonth.setMonth(currentMonth.getMonth() + 1);
    loadTeamCalendar();
}

/**
 * Charger les statistiques
 */
function loadStatistics() {
    const year = document.getElementById('stat-year').value;

    fetch(`/api/rh/leave/stats?year=${year}`, {
        headers: { 'Accept': 'application/json' }
    })
    .then(resp => handleResponseStatus(resp))
    .then(data => {
        if (data.success) {
            document.getElementById('stat-total').textContent = data.total;
            document.getElementById('stat-approved').textContent = data.approved;
            document.getElementById('stat-pending').textContent = data.pending;
            document.getElementById('stat-rejected').textContent = data.rejected;

            displayTechnicianStats(data.by_technician);
        } else {
            document.getElementById('technician-stats').innerHTML = '<div class="alert alert-error">Erreur: ' + (data.error || 'Statistiques indisponibles') + '</div>';
            document.getElementById('technician-stats').classList.remove('loading');
        }
    })
    .catch(err => {
        console.error('Erreur statistiques:', err);
        document.getElementById('technician-stats').innerHTML = '<div class="alert alert-error">Erreur: ' + err.message + '</div>';
        document.getElementById('technician-stats').classList.remove('loading');
    });
}

/**
 * Afficher les statistiques par technicien
 */
function displayTechnicianStats(stats) {
    const container = document.getElementById('technician-stats');

    if (!stats || Object.keys(stats).length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #999;">Aucune donnée disponible</p>';
        container.classList.remove('loading');
        return;
    }

    container.innerHTML = Object.entries(stats)
        .sort((a, b) => b[1].total_days - a[1].total_days)
        .map(([technicianName, stat]) => `
            <div class="leave-request">
                <div class="leave-request-info">
                    <strong>${technicianName}</strong>
                    <div style="font-size: 12px; color: #666; margin-top: 5px;">
                        Total: ${stat.total_days} j.o. | 
                        Approuvés: ${stat.approved_days} j.o. | 
                        En attente: ${stat.pending} demandes
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 24px; font-weight: bold; color: #007bff;">
                        ${stat.approved_days}j
                    </div>
                    <div style="font-size: 12px; color: #666;">jours approuvés</div>
                </div>
            </div>
        `).join('');
    container.classList.remove('loading');
}

/**
 * Charger les demandes en attente (pour validation RH)
 */
function loadPendingRequests() {
    const url = '/api/rh/conges?statut=pending&page=1&per_page=50';

    fetch(url, {
        headers: { 'Accept': 'application/json' }
    })
    .then(resp => handleResponseStatus(resp))
    .then(data => {
        if (data.success) {
            displayPendingRequests(data.leaves);
            document.getElementById('bulk-actions').style.display = 
                data.leaves.length > 0 ? 'block' : 'none';
        }
    })
    .catch(err => {
        console.error('Erreur chargement demandes:', err);
        document.getElementById('pending-requests-list').innerHTML = 
            '<div class="alert alert-error">Erreur: ' + err.message + '</div>';
    });
}

/**
 * Afficher les demandes en attente
 */
function displayPendingRequests(leaves) {
    const container = document.getElementById('pending-requests-list');

    if (leaves.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">✓</div><p>Aucune demande en attente</p></div>';
        container.classList.remove('loading');
        return;
    }

    container.innerHTML = leaves.map(leave => `
        <div class="leave-request pending" data-leave-id="${leave.id}">
            <div style="flex: 1;">
                <input type="checkbox" class="leave-checkbox" value="${leave.id}" style="margin-right: 10px; cursor: pointer;">
            </div>
            <div class="leave-request-info">
                <strong>${leave.technicien.nom} ${leave.technicien.prenom}</strong>
                <div class="leave-request-dates">
                    ${formatDate(leave.date_debut)} → ${formatDate(leave.date_fin)}
                    <strong>(${Math.round(leave.business_days)} j.o.)</strong>
                </div>
                <span class="leave-request-type">${getLeaveTypeLabel(leave.type)}</span>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">
                    <strong>Motif:</strong> ${leave.reason || 'Non spécifié'}
                </div>
            </div>
            <div style="text-align: right;">
                <div class="btn-group-sm">
                    <button type="button" class="btn btn-approve btn-sm" onclick="approveLeave(${leave.id})">
                        Approuver
                    </button>
                    <button type="button" class="btn btn-reject btn-sm" onclick="rejectLeave(${leave.id})">
                        Rejeter
                    </button>
                </div>
                <button type="button" class="btn btn-primary btn-sm" style="width: 100%; margin-top: 10px;"
                        onclick="showRequestDetails(${leave.id})">
                    Détails
                </button>
            </div>
        </div>
    `).join('');

    // Ajouter listeners aux checkboxes
    document.querySelectorAll('.leave-checkbox').forEach(cb => {
        cb.addEventListener('change', function() {
            if (this.checked) {
                selectedForBulk.add(parseInt(this.value));
            } else {
                selectedForBulk.delete(parseInt(this.value));
            }
        });
    });
}

/**
 * Afficher les détails d'une demande
 */
function showRequestDetails(leaveId) {
    const modal = document.getElementById('modal-details');
    const content = document.getElementById('modal-details-content');

    content.innerHTML = '<div class="loading"><div class="spinner"></div> Chargement...</div>';
    modal.classList.add('active');

    fetch(`/api/rh/conges/${leaveId}`, {
        headers: { 'Accept': 'application/json' }
    })
    .then(resp => handleResponseStatus(resp))
    .then(data => {
        if (data.success) {
            const leave = data.leave;
            content.innerHTML = `
                <div style="line-height: 1.8;">
                    <p><strong>Demandeur:</strong> ${leave.technicien.nom} ${leave.technicien.prenom}</p>
                    <p><strong>Type:</strong> ${getLeaveTypeLabel(leave.type)}</p>
                    <p><strong>Période:</strong> ${formatDate(leave.date_debut)} → ${formatDate(leave.date_fin)}</p>
                    <p><strong>Jours ouvrables:</strong> ${Math.round(leave.business_days)} j.o.</p>
                    <p><strong>Motif:</strong> ${leave.reason || 'Non spécifié'}</p>
                    <p><strong>Statut:</strong> <span class="leave-request-status ${leave.statut}">${getStatusLabel(leave.statut)}</span></p>
                    <p><strong>Date soumis:</strong> ${formatDate(leave.created_at)}</p>
                    ${leave.statut !== 'pending' ? `
                        <p><strong>Approuvé par:</strong> ${leave.manager.username}</p>
                        <p><strong>Commentaire:</strong> ${leave.manager_comment || '-'}</p>
                    ` : ''}
                </div>
            `;
        }
    })
    .catch(err => {
        content.innerHTML = '<div class="alert alert-error">Erreur: ' + err.message + '</div>';
    });
}

/**
 * Approuver une demande
 */
function approveLeave(leaveId) {
    openValidationModal(leaveId, 'approved');
}

/**
 * Rejeter une demande
 */
function rejectLeave(leaveId) {
    openValidationModal(leaveId, 'rejected');
}

/**
 * Ouvrir le modal de validation
 */
function openValidationModal(leaveId, decision) {
    const modal = document.getElementById('modal-validation');
    document.getElementById('validation-leave-id').value = leaveId;
    document.getElementById('validation-decision').value = decision;
    document.getElementById('validation-comment').value = '';
    modal.classList.add('active');
}

/**
 * Valider ou rejeter une demande
 */
function submitValidation(event) {
    event.preventDefault();

    const leaveId = document.getElementById('validation-leave-id').value;
    const decision = document.getElementById('validation-decision').value;
    const comment = document.getElementById('validation-comment').value;

    fetch(`/api/rh/conges/${leaveId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            statut: decision,
            comment: comment
        })
    })
    .then(resp => handleResponseStatus(resp))
    .then(data => {
        if (data.success) {
            closeModal('modal-validation');
            loadPendingRequests();
        } else {
            alert('Erreur: ' + data.error);
        }
    })
    .catch(err => {
        console.error('Erreur validation:', err);
        alert('Erreur: ' + err.message);
    });
}

/**
 * Approuver multiple
 */
function approvePendingBatch() {
    if (selectedForBulk.size === 0) {
        alert('Sélectionnez au moins une demande');
        return;
    }

    if (!confirm(`Approuver ${selectedForBulk.size} demande(s)?`)) return;

    fetch('/api/rh/leave/bulk-approve', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            leave_ids: Array.from(selectedForBulk),
            comment: 'Approuvé en batch'
        })
    })
    .then(resp => handleResponseStatus(resp))
    .then(data => {
        if (data.success) {
            alert(`✓ ${data.approved} demande(s) approuvée(s)`);
            selectedForBulk.clear();
            loadPendingRequests();
        }
    })
    .catch(err => alert('Erreur: ' + err.message));
}

/**
 * Rejeter multiple
 */
function rejectPendingBatch() {
    if (selectedForBulk.size === 0) {
        alert('Sélectionnez au moins une demande');
        return;
    }

    const reason = prompt('Motif du rejet:');
    if (reason === null) return; // Annulé

    fetch('/api/rh/leave/bulk-reject', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify({
            leave_ids: Array.from(selectedForBulk),
            comment: reason || 'Rejeté en batch'
        })
    })
    .then(resp => handleResponseStatus(resp))
    .then(data => {
        if (data.success) {
            alert(`✓ ${data.rejected} demande(s) rejetée(s)`);
            selectedForBulk.clear();
            loadPendingRequests();
        }
    })
    .catch(err => alert('Erreur: ' + err.message));
}

/**
 * Filtrer les demandes en attente
 */
function filterPendingRequests() {
    const searchTerm = document.getElementById('search-employee').value;
    if (searchTerm) {
        // Filtrer côté client
        document.querySelectorAll('.leave-request').forEach(el => {
            const text = el.textContent.toLowerCase();
            el.style.display = text.includes(searchTerm.toLowerCase()) ? 'flex' : 'none';
        });
    } else {
        document.querySelectorAll('.leave-request').forEach(el => {
            el.style.display = 'flex';
        });
    }
}

/**
 * Configurer les event listeners
 */
function setupEventListeners() {
    // Changer année statistiques
    const statYear = document.getElementById('stat-year');
    if (statYear) {
        statYear.addEventListener('change', loadStatistics);
    }
}

/**
 * Utilitaires
 */

function getLeaveTypeLabel(type) {
    const labels = {
        'conge_paye': 'Congés payés',
        'maladie': 'Maladie',
        'absence': 'Absence justifiée',
        'conge_sans_solde': 'Congé sans solde',
        'rtt': 'RTT'
    };
    return labels[type] || type;
}

function getStatusLabel(status) {
    const labels = {
        'pending': 'En attente',
        'approved': 'Approuvée',
        'rejected': 'Rejetée',
        'cancelled': 'Annulée'
    };
    return labels[status] || status;
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR');
}

function calculateBusinessDays(start, end) {
    let count = 0;
    let current = new Date(start);
    
    while (current <= end) {
        const day = current.getDay();
        if (day !== 0 && day !== 6) { // Pas dimanche ni samedi
            count++;
        }
        current.setDate(current.getDate() + 1);
    }
    return count;
}

function handleResponseStatus(response) {
    if (!response.ok) {
        if (response.status === 403) {
            throw new Error('Accès refusé - permissions insuffisantes');
        }
        if (response.status === 404) {
            throw new Error('Ressource non trouvée');
        }
        throw new Error(`HTTP ${response.status}`);
    }
    return response.json();
}

function updateDecisionMessage() {
    const decision = document.getElementById('validation-decision').value;
    const label = document.querySelector('label[for="validation-comment"]');
    
    if (decision === 'approved') {
        label.textContent = 'Commentaire (optionnel) - Approuvé';
    } else if (decision === 'rejected') {
        label.textContent = 'Raison du rejet *';
    }
}
