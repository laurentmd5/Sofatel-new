/**
 * =============================================================================
 * DASHBOARD CHEF PUR - Main Module
 * =============================================================================
 * WebView-safe, production-ready dashboard functionality
 * All event binding via addEventListener, no inline onclick attributes
 * Loads with defer attribute for non-blocking execution
 */

// ============================================================================
// 1. MODAL FUNCTIONS - Statistics & Details
// ============================================================================

/**
 * Show details modal for statistics counters
 * @param {string} type - Counter type (e.g., 'total_demandes')
 * @param {number|string} count - Count value
 * @param {string} title - Modal title
 */
function showDetailsModal(type, count, title) {
    const modalLabel = document.getElementById('statsModalLabel');
    const statsDetailsEl = document.getElementById('statsDetails');
    
    if (!modalLabel || !statsDetailsEl) return;
    
    modalLabel.textContent = title;
    const modal = new bootstrap.Modal(document.getElementById('statsModal'));
    modal.show();
    
    fetch(`/api/stats/details/${type}`)
        .then(response => response.json())
        .then(data => {
            displayStatsDetails(data, type);
        })
        .catch(error => {
            console.error('Error loading stats:', error);
            statsDetailsEl.innerHTML =
                '<div class="alert alert-danger">Erreur lors du chargement des détails</div>';
        });
}

/**
 * Show demande preview modal
 * @param {string} ids - Comma-separated demande IDs
 * @param {string} label - Preview label
 * @param {string} type - Preview type
 */
function showDemandePreview(ids, label, type) {
    if (!ids) return;
    
    const container = document.getElementById('statsDetails');
    if (!container) return;
    
    container.innerHTML = `
        <div class="text-center my-4">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Chargement...</span>
            </div>
        </div>
    `;
    
    fetch(`/api/demandes/preview?ids=${ids}`)
        .then(response => response.json())
        .then(data => {
            let html = `<h5 class="mb-3 text-center">Aperçu des demandes <span class="badge bg-primary">${type} : ${label}</span></h5>`;
            
            if (data.items && data.items.length > 0) {
                html += `<div class="table-responsive"><table class="table table-bordered table-sm">
                    <thead>
                        <tr>
                            <th>N° Demande</th>
                            <th>Client</th>
                            <th>Offre</th>
                            <th>Priorité</th>
                            <th>Âge</th>
                            <th>Zone</th>
                            <th>Date création</th>
                            <th>Statut</th>
                            <th>Orienter</th>
                        </tr>
                    </thead>
                    <tbody>`;
                    
                data.items.forEach(item => {
                    html += `<tr>
                        <td>${item.numero_demande}</td>
                        <td>${item.nom_client} ${item.prenom_client}</td>
                        <td>${item.offre || '-'}</td>
                        <td>${item.priorite || '-'}</td>
                        <td>${item.age || '-'}</td>
                        <td>${item.zone || '-'}</td>
                        <td>${item.date_creation ? new Date(item.date_creation).toLocaleDateString('fr-FR') : '-'}</td>
                        <td><span class="badge bg-secondary">${item.statut}</span></td>
                        <td>
                            <button type="button" class="btn btn-sm btn-primary dispatch-btn"
                                data-demande-id="${item.id}">
                                <i data-feather="user-plus" class="me-1"></i>
                                Orienter
                            </button>
                        </td>
                    </tr>`;
                });
                
                html += `</tbody></table></div>`;
            } else {
                html += `<div class="alert alert-info text-center">Aucune demande à afficher</div>`;
            }
            
            container.innerHTML = html;
            attachDispatchBtnListeners();
            if (typeof feather !== 'undefined' && typeof feather.replace === 'function') {
                try {
                    feather.replace();
                } catch (e) {
                    console.warn('Feather replace error:', e);
                }
            }
        })
        .catch(error => {
            console.error('Error loading demandes:', error);
            container.innerHTML = `<div class="alert alert-danger">Erreur lors du chargement des demandes</div>`;
        });
}

/**
 * Show dispatch modal for demande assignment
 * @param {number} demandeId - Demande ID
 */
function showDispatchModal(demandeId) {
    fetch(`/api/demande/${demandeId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (!document.getElementById('dispatchModal')) {
                    document.body.insertAdjacentHTML('beforeend', `
                        <div class="modal fade" id="dispatchModal" tabindex="-1" aria-labelledby="dispatchModalLabel" aria-hidden="true">
                            <div class="modal-dialog">
                                <div class="modal-content">
                                    <div class="modal-header">
                                        <h5 class="modal-title" id="dispatchModalLabel">Affectation de la demande</h5>
                                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                    </div>
                                    <div class="modal-body" id="modalContent"></div>
                                </div>
                            </div>
                        </div>
                    `);
                }
                document.getElementById('modalContent').innerHTML = generateModalContent(data.demande);
                new bootstrap.Modal(document.getElementById('dispatchModal')).show();
                if (typeof feather !== 'undefined' && typeof feather.replace === 'function') {
                    try {
                        feather.replace();
                    } catch (e) {
                        console.warn('Feather replace error:', e);
                    }
                }
            }
        })
        .catch(error => console.error('Error:', error));
}

// ============================================================================
// 2. STATS DETAILS DISPLAY
// ============================================================================

/**
 * Display detailed statistics
 * @param {object} data - Stats data from API
 * @param {string} type - Stats type
 */
function displayStatsDetails(data, type) {
    let html = '';

    // Age breakdown for daily requests
    if ((type === 'demandes_jour' || type === 'demandes_jour_sav' || type === 'demandes_jour_production') && data.details) {
        html += generateAgeBreakdownHtml(data.details);
    }

    // Service & technology breakdown
    if (type === 'total_demandes' && data.details && data.details.service_tech) {
        html += generateServiceTechHtml(data.details.service_tech);
    }

    // Items table
    if (data.items && data.items.length > 0) {
        html += generateItemsTableHtml(data.items, type);

        if (data.total > data.items.length) {
            html += `<p class="text-muted text-center mt-3">Affichage de ${data.items.length} sur ${data.total} éléments</p>`;
        }
    } else {
        html += '<div class="alert alert-info text-center">Aucune donnée disponible</div>';
    }

    const statsDetails = document.getElementById('statsDetails');
    if (statsDetails) {
        statsDetails.innerHTML = html;
        attachPreviewBtnListeners();
        if (typeof feather !== 'undefined' && typeof feather.replace === 'function') {
            try {
                feather.replace();
            } catch (e) {
                console.warn('Feather replace error:', e);
            }
        }
    }
}

/**
 * Generate age breakdown HTML
 */
function generateAgeBreakdownHtml(details) {
    return `
    <div class="row mb-3">
        <div class="col-md-4">
            <div class="card shadow-sm border-primary mb-3">
                <div class="card-header bg-primary text-white py-2">
                    <h6 class="mb-0">Répartition par âge</h6>
                </div>
                <div class="card-body p-2">
                    <ul class="list-unstyled mb-0">
                        ${Object.entries(details.age).map(([age, count]) => {
                            const ids = (details.age_ids && details.age_ids[age]) ? details.age_ids[age].join(',') : '';
                            return `<li>
                                <button type="button" class="btn btn-link p-0 text-decoration-none preview-btn"
                                    data-ids="${ids}" data-label="${age}" data-type="Âge">
                                    <span class="badge bg-info me-2" style="cursor:pointer">${count}</span>
                                    <strong>${age || 'Non renseigné'}</strong>
                                </button>
                            </li>`;
                        }).join('')}
                    </ul>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card shadow-sm border-warning mb-3">
                <div class="card-header bg-warning text-white py-2">
                    <h6 class="mb-0">Priorité de traitement</h6>
                </div>
                <div class="card-body p-2">
                    <ul class="list-unstyled mb-0">
                        ${Object.entries(details.priorite_traitement).map(([priorite, count]) => {
                            const ids = (details.priorite_ids && details.priorite_ids[priorite]) ? details.priorite_ids[priorite].join(',') : '';
                            return `<li>
                                <button type="button" class="btn btn-link p-0 text-decoration-none preview-btn"
                                    data-ids="${ids}" data-label="${priorite}" data-type="Priorité">
                                    <span class="badge bg-secondary me-2" style="cursor:pointer">${count}</span>
                                    <strong>${priorite || 'Non renseigné'}</strong>
                                </button>
                            </li>`;
                        }).join('')}
                    </ul>
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card shadow-sm border-success mb-3">
                <div class="card-header bg-success text-white py-2">
                    <h6 class="mb-0">Offre</h6>
                </div>
                <div class="card-body p-2">
                    <ul class="list-unstyled mb-0">
                        ${Object.entries(details.offre).map(([offre, count]) => {
                            const ids = (details.offre_ids && details.offre_ids[offre]) ? details.offre_ids[offre].join(',') : '';
                            return `<li>
                                <button type="button" class="btn btn-link p-0 text-decoration-none preview-btn"
                                    data-ids="${ids}" data-label="${offre}" data-type="Offre">
                                    <span class="badge bg-primary me-2" style="cursor:pointer">${count}</span>
                                    <strong>${offre || 'Non renseigné'}</strong>
                                </button>
                            </li>`;
                        }).join('')}
                    </ul>
                </div>
            </div>
        </div>
    </div>
    `;
}

/**
 * Generate service & technology breakdown HTML
 */
function generateServiceTechHtml(serviceTech) {
    return `
    <div class="row mb-3">
        <div class="col-12">
            <div class="card shadow-sm border-primary mb-3">
                <div class="card-header bg-primary text-white py-2">
                    <h6 class="mb-0">Répartition des Instances totales par Service et Technologie</h6>
                </div>
                <div class="card-body p-2">
                    <div class="table-responsive">
                        <table class="table table-bordered table-sm text-center align-middle">
                            <thead>
                                <tr>
                                    <th class="bg-info text-white">Service</th>
                                    <th class="bg-success text-white">Fibre</th>
                                    <th class="bg-warning text-white">Cuivre</th>
                                    <th class="bg-purple text-white" style="background-color:#6f42c1;">5G</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${['SAV', 'Production'].map(service => `
                                    <tr>
                                        <td class="fw-bold bg-light">${service}</td>
                                        <td><span class="badge bg-success fs-6">${serviceTech[service]['Fibre'] || 0}</span></td>
                                        <td><span class="badge bg-warning text-dark fs-6">${serviceTech[service]['Cuivre'] || 0}</span></td>
                                        <td><span class="badge" style="background-color:#6f42c1;">${serviceTech[service]['5G'] || 0}</span></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    `;
}

/**
 * Generate items table HTML
 */
function generateItemsTableHtml(items, type) {
    let html = '<div class="table-responsive"><table class="table table-striped">';

    if (type === 'total_demandes' || type === 'demandes_jour') {
        html += `
            <thead>
                <tr>
                    <th>N° Demande</th>
                    <th>Client</th>
                    <th>Service</th>
                    <th>Zone</th>
                    <th>Date création</th>
                    <th>Statut</th>
                </tr>
            </thead>
            <tbody>`;
        items.forEach(item => {
            html += `
                <tr>
                    <td>${item.numero_demande}</td>
                    <td>${item.nom_client}</td>
                    <td>${item.service_demande}</td>
                    <td>${item.zone || '-'}</td>
                    <td>${new Date(item.date_creation).toLocaleDateString('fr-FR')}</td>
                    <td><span class="badge bg-${getStatusColor(item.statut)}">${item.statut}</span></td>
                </tr>`;
        });
    } else if (isInterventionType(type)) {
        html += `
            <thead>
                <tr>
                    <th>N° Intervention</th>
                    <th>Client</th>
                    <th>Technicien</th>
                    <th>Zone</th>
                    <th>Date planifiée</th>
                    <th>Statut</th>
                </tr>
            </thead>
            <tbody>`;
        items.forEach(item => {
            html += `
                <tr>
                    <td>${item.numero_intervention}</td>
                    <td>${item.nom_client}</td>
                    <td>${item.technicien_nom || '-'}</td>
                    <td>${item.zone || '-'}</td>
                    <td>${item.date_planifiee ? new Date(item.date_planifiee).toLocaleDateString('fr-FR') : '-'}</td>
                    <td><span class="badge bg-${getStatusColor(item.statut)}">${item.statut}</span></td>
                </tr>`;
        });
    }

    html += '</tbody></table></div>';
    return html;
}

/**
 * Check if type is intervention type
 */
function isInterventionType(type) {
    return [
        'interventions_cours',
        'interventions_validees',
        'interventions_validees_sav',
        'interventions_validees_production',
        'attente_validation',
        'interventions_rejetees'
    ].includes(type);
}

/**
 * Get status color class
 */
function getStatusColor(status) {
    const colors = {
        'nouveau': 'primary',
        'affecte': 'info',
        'en_cours': 'warning',
        'termine': 'success',
        'valide': 'success',
        'rejete': 'danger'
    };
    return colors[status] || 'secondary';
}

// ============================================================================
// 3. DISPATCH & AFFECTATION FUNCTIONS
// ============================================================================

/**
 * Generate modal content for demande dispatch
 */
function generateModalContent(demande) {
    const techniciens = window.dashboardData?.techniciens || [];
    const equipes = window.dashboardData?.equipes || [];
    const demandeZoneNormalized = demande.zone ? demande.zone.toLowerCase() : '';
    
    let technicienOptions = '';
    techniciens.forEach(function(technicien) {
        if (technicien.zone && technicien.zone.toLowerCase() === demandeZoneNormalized) {
            technicienOptions += `<option value="${technicien.id}">${technicien.prenom} ${technicien.nom} (${technicien.zone}) (${technicien.technologies})</option>`;
        }
    });
    
    let equipeOptions = '';
    equipes.forEach(function(equipe) {
        if (equipe.zone && equipe.zone.toLowerCase() === demandeZoneNormalized) {
            equipeOptions += `<option value="${equipe.id}">${equipe.nom_equipe} (${equipe.technologies})</option>`;
        }
    });
    
    return `
        <div class="mb-3">
            <h6>Détails de la demande</h6>
            <p class="mb-1"><strong>Client:</strong> ${demande.nom_client} ${demande.prenom_client}</p>
            <p class="mb-1"><strong>ND:</strong> ${demande.nd}</p>
            <p class="mb-1"><strong>Technologie:</strong> ${demande.type_techno}</p>
            <p class="mb-3"><strong>Zone:</strong> ${demande.zone}</p>
        </div>
        <div class="mb-3">
            <label class="form-label">Technicien</label>
            <select class="form-select" id="modalTechnicien" required>
                <option value="">Sélectionner un technicien</option>
                ${technicienOptions}
            </select>
        </div>
        <div class="mb-3">
            <label class="form-label">Équipe (optionnel)</label>
            <select class="form-select" id="modalEquipe">
                <option value="">Aucune équipe</option>
                ${equipeOptions}
            </select>
        </div>
        <div class="mb-3">
            <label class="form-label">Commentaire</label>
            <textarea class="form-control" id="modalCommentaire" rows="3" placeholder="Commentaire d'affectation..."></textarea>
        </div>
        <div class="d-flex justify-content-end">
            <button type="button" class="btn btn-secondary me-2" data-bs-dismiss="modal">Annuler</button>
            <button type="button" class="btn btn-primary" id="affectBtn" data-demande-id="${demande.id}">
                <i data-feather="check" class="me-2"></i>
                Affecter
            </button>
        </div>
    `;
}

/**
 * Confirm and send demande affectation
 */
function confirmerAffectation(demandeId) {
    const technicienId = document.getElementById('modalTechnicien').value;
    const equipeId = document.getElementById('modalEquipe').value;
    const commentaire = document.getElementById('modalCommentaire').value;
    
    if (!technicienId) {
        alert('Veuillez sélectionner un technicien.');
        return;
    }
    
    affecterDemande(demandeId, technicienId, equipeId, commentaire);
}

/**
 * Send demande affectation request
 */
function affecterDemande(demandeId, technicienId, equipeId, commentaire) {
    const data = {
        demande_id: demandeId,
        technicien_id: technicienId,
        equipe_id: equipeId || null,
        commentaire: commentaire,
        mode: 'manuel'
    };
    
    fetch('/affecter-demande', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const modalEl = document.getElementById('dispatchModal');
                if (modalEl) {
                    bootstrap.Modal.getInstance(modalEl).hide();
                }
                alert(data.message);
            } else {
                alert('Erreur: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Erreur lors de l\'affectation');
        });
}

// ============================================================================
// 4. REFRESH & BASIC OPERATIONS
// ============================================================================

/**
 * Refresh dashboard statistics
 */
function refreshStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            location.reload();
        })
        .catch(error => {
            console.error('Error refreshing stats:', error);
        });
}

// ============================================================================
// 5. EVENT LISTENERS ATTACHMENT
// ============================================================================

/**
 * Attach listeners to statistics counter cards
 */
function attachStatCounterListeners() {
    const counterCards = document.querySelectorAll('[data-counter-type]');
    
    counterCards.forEach(card => {
        card.addEventListener('click', function() {
            const type = this.getAttribute('data-counter-type');
            const counterId = this.getAttribute('data-counter-id');
            const title = this.getAttribute('data-counter-title');
            
            if (type && counterId && title) {
                const countEl = document.getElementById(counterId);
                const count = countEl ? countEl.textContent : '0';
                showDetailsModal(type, count, title);
            }
        });
    });
}

/**
 * Attach listeners to preview buttons
 */
function attachPreviewBtnListeners() {
    const previewBtns = document.querySelectorAll('.preview-btn');
    
    previewBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const ids = this.getAttribute('data-ids');
            const label = this.getAttribute('data-label');
            const type = this.getAttribute('data-type');
            showDemandePreview(ids, label, type);
        });
    });
}

/**
 * Attach listeners to dispatch buttons
 */
function attachDispatchBtnListeners() {
    const dispatchBtns = document.querySelectorAll('.dispatch-btn');
    
    dispatchBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const demandeId = this.getAttribute('data-demande-id');
            showDispatchModal(parseInt(demandeId));
        });
    });
}

/**
 * Attach listener to affectation button
 */
function attachAffectBtnListener() {
    document.addEventListener('click', function(e) {
        if (e.target && e.target.id === 'affectBtn') {
            const demandeId = e.target.getAttribute('data-demande-id');
            confirmerAffectation(parseInt(demandeId));
        }
    });
}

/**
 * Attach listeners to refresh button
 */
function attachRefreshListener() {
    const refreshBtn = document.querySelector('[data-action="refresh-stats"]');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshStats);
    }
}

// ============================================================================
// 6. TEAMS MANAGEMENT
// ============================================================================

// Selection state
let selectedTeamIds = new Set();
let currentSelectionTeams = [];
let currentSelectionAction = '';

/**
 * Show team publication selection modal
 */
function showPublicationSelection() {
    selectedTeamIds.clear();
    fetch('/api/all-teams')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentSelectionTeams = data.teams;
                showTeamsSelectionModal(data.teams, 'publish');
            } else {
                alert('Erreur lors du chargement: ' + data.error);
            }
        })
        .catch(error => {
            alert('Erreur: ' + error.message);
        });
}

function showUnpublishSelection() {
    selectedTeamIds.clear();
    fetch('/api/all-teams')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentSelectionTeams = data.teams;
                showTeamsSelectionModal(data.teams, 'unpublish');
            } else {
                alert('Erreur lors du chargement: ' + data.error);
            }
        })
        .catch(error => {
            alert('Erreur: ' + error.message);
        });
}

/**
 * Show teams selection modal
 */
function showTeamsSelectionModal(teams, action = 'publish') {
    currentSelectionAction = action;
    
    let modalHtml = `
    <div class="modal fade" id="teamsSelectionModal" tabindex="-1">
        <div class="modal-dialog modal-xl">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">
                        <i data-feather="${action === 'publish' ? 'send' : 'eye-off'}" class="me-2"></i>
                        ${action === 'publish' ? 'Sélectionner les équipes à publier' : 'Sélectionner les équipes à dépublier'}
                    </h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row mb-3 align-items-end">
                        <div class="col-md-6">
                            <label class="form-label small fw-bold">Rechercher une équipe</label>
                            <div class="input-group">
                                <span class="input-group-text bg-white"><i data-feather="search" style="width: 16px;"></i></span>
                                <input type="text" id="teamSearchInput" class="form-control" placeholder="Nom, zone, technologie ou service..." >
                            </div>
                        </div>
                    </div>
    `;

    if (teams.length === 0) {
        modalHtml += '<p class="text-muted">Aucune équipe créée.</p>';
    } else {
        modalHtml += `
            <div id="selection-teams-container">
                ${renderSelectionTable(teams, action)}
            </div>
        `;
    }

    modalHtml += `
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Annuler</button>
    `;

    const hasActionableTeams = action === 'publish'
        ? teams.some(team => !team.publie)
        : teams.some(team => team.publie);

    if (hasActionableTeams) {
        const buttonClass = action === 'publish' ? 'btn-success' : 'btn-danger';
        const buttonText = action === 'publish' ? 'Publier les équipes sélectionnées' : 'Dépublier les équipes sélectionnées';
        const buttonIcon = action === 'publish' ? 'send' : 'eye-off';

        modalHtml += `
                    <button type="button" class="btn ${buttonClass}" id="publishActionBtn" data-action="${action}">
                        <i data-feather="${buttonIcon}" class="me-2"></i>
                        ${buttonText}
                    </button>
        `;
    }

    modalHtml += `
                </div>
            </div>
        </div>
    </div>`;

    const existingModal = document.getElementById('teamsSelectionModal');
    if (existingModal) {
        existingModal.remove();
    }

    document.body.insertAdjacentHTML('beforeend', modalHtml);

    const modal = new bootstrap.Modal(document.getElementById('teamsSelectionModal'));
    modal.show();

    attachTeamsSelectionListeners();
    if (typeof feather !== 'undefined' && typeof feather.replace === 'function') {
        try {
            feather.replace();
        } catch (e) {
            console.warn('Feather replace error:', e);
        }
    }
}

function renderSelectionTable(teams, action) {
    const filteredTeams = action === 'publish'
        ? teams.filter(team => !team.publie)
        : teams.filter(team => team.publie);

    if (filteredTeams.length === 0) {
        return `<p class="text-info">${action === 'publish' ? 'Aucune équipe à publier.' : 'Aucune équipe à dépublier.'}</p>`;
    }

    let html = `
    <div class="mb-3 d-flex justify-content-between align-items-center">
        <div>
            <button type="button" class="btn btn-sm btn-outline-primary select-all-btn" data-select="true">
                <i data-feather="check-square"></i> Tout sélectionner
            </button>
            <button type="button" class="btn btn-sm btn-outline-secondary ms-2 select-all-btn" data-select="false">
                <i data-feather="square"></i> Tout désélectionner
            </button>
        </div>
        <div class="text-muted small">
            ${selectedTeamIds.size} équipe(s) sélectionnée(s)
        </div>
    </div>
    <div class="table-responsive">
        <table class="table table-hover align-middle">
            <thead class="table-light">
                <tr>
                    <th width="40"><input type="checkbox" id="selectAllCheckbox" class="master-checkbox"></th>
                    <th>Équipe</th>
                    <th>Zone</th>
                    <th>Service</th>
                    <th>Technologies</th>
                    <th>Membres</th>
                    <th>Statut</th>
                </tr>
            </thead>
            <tbody>
    `;

    filteredTeams.forEach(team => {
        const statusBadge = team.publie ? '<span class="badge bg-success">Disponible</span>' : '<span class="badge bg-secondary">Brouillon</span>';
        const isChecked = selectedTeamIds.has(team.id);
        html += `
        <tr>
            <td><input type="checkbox" class="team-checkbox" value="${team.id}" ${isChecked ? 'checked' : ''}></td>
            <td><strong>${team.nom_equipe}</strong></td>
            <td><span class="badge bg-info">${team.zone}</span></td>
            <td><span class="badge bg-primary">${team.service}</span></td>
            <td><small class="badge bg-secondary">${team.technologies}</small></td>
            <td class="text-center">${team.nb_membres}</td>
            <td>${statusBadge}</td>
        </tr>`;
    });

    html += '</tbody></table></div>';
    return html;
}

function filterSelectionTeams() {
    const input = document.getElementById('teamSearchInput');
    if (!input) return;
    const query = input.value.toLowerCase();
    
    const filtered = currentSelectionTeams.filter(t => 
        t.nom_equipe.toLowerCase().includes(query) || 
        t.zone.toLowerCase().includes(query) ||
        t.technologies.toLowerCase().includes(query) ||
        t.service.toLowerCase().includes(query)
    );

    const container = document.getElementById('selection-teams-container');
    if (container) {
        container.innerHTML = renderSelectionTable(filtered, currentSelectionAction);
        attachTeamsSelectionListeners();
        if (typeof feather !== 'undefined') feather.replace();
    }
}

/**
 * Attach team selection event listeners
 */
function attachTeamsSelectionListeners() {
    const masterCheckbox = document.getElementById('selectAllCheckbox');
    const teamCheckboxes = document.querySelectorAll('.team-checkbox');
    const selectAllBtns = document.querySelectorAll('.select-all-btn');
    const publishActionBtn = document.getElementById('publishActionBtn');
    const searchInput = document.getElementById('teamSearchInput');

    if (searchInput && !searchInput.dataset.listenerAttached) {
        searchInput.addEventListener('keyup', filterSelectionTeams);
        searchInput.dataset.listenerAttached = 'true';
    }

    if (masterCheckbox) {
        masterCheckbox.addEventListener('change', function() {
            teamCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
                updateSelectedTeam(parseInt(checkbox.value), this.checked);
            });
        });
    }

    teamCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSelectedTeam(parseInt(this.value), this.checked);
        });
    });

    selectAllBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const shouldSelect = this.getAttribute('data-select') === 'true';
            teamCheckboxes.forEach(checkbox => {
                checkbox.checked = shouldSelect;
                updateSelectedTeam(parseInt(checkbox.value), shouldSelect);
            });
            if (masterCheckbox) {
                masterCheckbox.checked = shouldSelect;
            }
        });
    });

    if (publishActionBtn && !publishActionBtn.dataset.listenerAttached) {
        publishActionBtn.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            if (action === 'publish') {
                publishSelectedTeams();
            } else {
                unpublishSelectedTeams();
            }
        });
        publishActionBtn.dataset.listenerAttached = 'true';
    }
}

function updateSelectedTeam(id, isChecked) {
    if (isChecked) {
        selectedTeamIds.add(id);
    } else {
        selectedTeamIds.delete(id);
    }
    // Update counter display if exists
    const counterEl = document.querySelector('.text-muted.small');
    if (counterEl) {
        counterEl.textContent = `${selectedTeamIds.size} équipe(s) sélectionnée(s)`;
    }
}

function publishSelectedTeams() {
    const selectedTeams = Array.from(selectedTeamIds);
    if (selectedTeams.length === 0) {
        alert('Veuillez sélectionner au moins une équipe à publier.');
        return;
    }
    if (confirm(`Confirmer la publication de ${selectedTeams.length} équipe(s) ?`)) {
        performBulkTeamAction('publish', selectedTeams);
        const modal = bootstrap.Modal.getInstance(document.getElementById('teamsSelectionModal'));
        if (modal) modal.hide();
    }
}

function unpublishSelectedTeams() {
    const selectedTeams = Array.from(selectedTeamIds);
    if (selectedTeams.length === 0) {
        alert('Veuillez sélectionner au moins une équipe à dépublier.');
        return;
    }
    if (confirm(`Confirmer la dépublication de ${selectedTeams.length} équipe(s) ?`)) {
        performBulkTeamAction('unpublish', selectedTeams);
        const modal = bootstrap.Modal.getInstance(document.getElementById('teamsSelectionModal'));
        if (modal) modal.hide();
    }
}

/**
 * Perform team publication action
 */
function performTeamAction(action) {
    const selectedTeams = Array.from(document.querySelectorAll('.team-checkbox:checked'))
        .map(cb => parseInt(cb.value));

    if (selectedTeams.length === 0) {
        const actionText = action === 'publish' ? 'publier' : 'dépublier';
        alert(`Veuillez sélectionner au moins une équipe à ${actionText}.`);
        return;
    }

    const actionText = action === 'publish' ? 'publier' : 'dépublier';
    if (!confirm(`Confirmer ${actionText} ${selectedTeams.length} équipe(s) ?`)) {
        return;
    }

    const endpoint = action === 'publish' ? '/api/publish-selected-teams' : '/api/unpublish-selected-teams';

    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            team_ids: selectedTeams
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                const modal = bootstrap.Modal.getInstance(document.getElementById('teamsSelectionModal'));
                if (modal) modal.hide();
                refreshStats();
            } else {
                alert('Erreur: ' + data.error);
            }
        })
        .catch(error => {
            alert('Erreur lors de l\'action: ' + error.message);
        });
}

/**
 * Show all teams management interface
 */
function showAllTeamsManagement() {
    fetch('/api/all-teams')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayTeamsManagementTable(data.teams);
                const container = document.getElementById('teams-management-container');
                if (container) {
                    container.style.display = 'block';
                    container.scrollIntoView({ behavior: 'smooth' });
                }
            } else {
                alert('Erreur lors du chargement: ' + data.error);
            }
        })
        .catch(error => {
            alert('Erreur: ' + error.message);
        });
}

/**
 * Hide teams management interface
 */
function hideTeamsManagement() {
    const container = document.getElementById('teams-management-container');
    if (container) {
        container.style.display = 'none';
    }
}

/**
 * Display teams management table
 */
function displayTeamsManagementTable(teams) {
    let html = '';

    if (teams.length === 0) {
        html = `
            <div class="text-center py-5">
                <i data-feather="users" style="width: 64px; height: 64px;" class="text-muted mb-3"></i>
                <h5 class="text-muted">Aucune équipe créée</h5>
                <p class="text-muted">Commencez par créer votre première équipe</p>
                <a href="/create-team" class="btn btn-success">
                    <i data-feather="plus-circle" class="me-2"></i>
                    Créer une équipe
                </a>
            </div>`;
    } else {
        html = `
            <div class="mb-3 d-flex justify-content-between align-items-center">
                <div class="d-flex gap-2">
                    <button class="btn btn-sm btn-success bulk-action-btn" data-action="publish">
                        <i data-feather="send" class="me-1"></i>
                        Publier sélectionnées
                    </button>
                    <button class="btn btn-sm btn-warning bulk-action-btn" data-action="unpublish">
                        <i data-feather="eye-off" class="me-1"></i>
                        Dépublier sélectionnées
                    </button>
                </div>
                <span class="text-muted">Total: ${teams.length} équipe(s)</span>
            </div>
            <div class="table-responsive">
                <table class="table table-hover">
                    <thead class="table-light">
                        <tr>
                            <th width="40">
                                <input type="checkbox" id="selectAllTeamsCheckbox" class="master-teams-checkbox">
                            </th>
                            <th>Équipe</th>
                            <th>Zone</th>
                            <th>Service</th>
                            <th>Technologies</th>
                            <th>Membres</th>
                            <th>Statut</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>`;

        teams.forEach(team => {
            const statusBadge = team.publie
                ? '<span class="badge bg-success">Disponible</span>'
                : '<span class="badge bg-secondary">Non disponible</span>';

            const prestataireBadge = team.prestataire
                ? `<br><small class="badge bg-warning">${team.prestataire}</small>`
                : '';

            html += `
                <tr>
                    <td>
                        <input type="checkbox" class="team-management-checkbox" value="${team.id}">
                    </td>
                    <td>
                        <strong>${team.nom_equipe}</strong>
                        ${prestataireBadge}
                    </td>
                    <td><span class="badge bg-info">${team.zone}</span></td>
                    <td><span class="badge bg-primary">${team.service}</span></td>
                    <td><small class="badge bg-secondary">${team.technologies}</small></td>
                    <td class="text-center">${team.nb_membres}</td>
                    <td>${statusBadge}</td>
                    <td>
                        <div class="btn-group btn-group-sm">
                            <a href="/manage_team/${team.id}" class="btn btn-outline-primary" title="Gérer les membres">
                                <i data-feather="users"></i>
                            </a>
                            <a href="/edit-team/${team.id}" class="btn btn-outline-secondary" title="Modifier l'équipe">
                                <i data-feather="edit"></i>
                            </a>
                            <button class="btn btn-outline-${team.publie ? 'warning' : 'success'} toggle-team-pub-btn"
                                    data-team-id="${team.id}" data-is-published="${team.publie}"
                                    title="${team.publie ? 'Dépublier' : 'Publier'}">
                                <i data-feather="${team.publie ? 'eye-off' : 'send'}"></i>
                            </button>
                        </div>
                    </td>
                </tr>`;
        });

        html += `
                    </tbody>
                </table>
            </div>`;
    }

    const content = document.getElementById('teams-management-content');
    if (content) {
        content.innerHTML = html;
        attachTeamsManagementListeners();
        if (typeof feather !== 'undefined' && typeof feather.replace === 'function') {
            try {
                feather.replace();
            } catch (e) {
                console.warn('Feather replace error:', e);
            }
        }
    }
}

/**
 * Attach teams management event listeners
 */
function attachTeamsManagementListeners() {
    const masterCheckbox = document.getElementById('selectAllTeamsCheckbox');
    const teamCheckboxes = document.querySelectorAll('.team-management-checkbox');
    const bulkActionBtns = document.querySelectorAll('.bulk-action-btn');
    const togglePubBtns = document.querySelectorAll('.toggle-team-pub-btn');

    if (masterCheckbox) {
        masterCheckbox.addEventListener('change', function() {
            teamCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
        });
    }

    bulkActionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const action = this.getAttribute('data-action');
            const selectedTeams = Array.from(document.querySelectorAll('.team-management-checkbox:checked'))
                .map(cb => parseInt(cb.value));

            if (selectedTeams.length === 0) {
                alert('Veuillez sélectionner au moins une équipe.');
                return;
            }

            const actionText = action === 'publish' ? 'publier' : 'dépublier';
            if (confirm(`Confirmer ${actionText} ${selectedTeams.length} équipe(s) ?`)) {
                performBulkTeamAction(action, selectedTeams);
            }
        });
    });

    togglePubBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const teamId = parseInt(this.getAttribute('data-team-id'));
            const isPublished = this.getAttribute('data-is-published') === 'true';
            const action = isPublished ? 'unpublish' : 'publish';
            const actionText = isPublished ? 'dépublier' : 'publier';

            if (confirm(`Voulez-vous ${actionText} cette équipe ?`)) {
                performBulkTeamAction(action, [teamId]);
            }
        });
    });
}

/**
 * Perform bulk team action
 */
function performBulkTeamAction(action, teamIds) {
    const endpoint = action === 'publish' ? '/api/publish-selected-teams' : '/api/unpublish-selected-teams';

    fetch(endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            team_ids: teamIds
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                showAllTeamsManagement();
                refreshStats();
            } else {
                alert('Erreur: ' + data.error);
            }
        })
        .catch(error => {
            alert('Erreur lors de l\'action: ' + error.message);
        });
}

// ============================================================================
// 7. UTILITY FUNCTIONS
// ============================================================================

/**
 * Get CSRF token from meta tag
 */
function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute('content') : '';
}

// ============================================================================
// 8. INITIALIZATION - DOMContentLoaded
// ============================================================================

/**
 * Initialize dashboard on DOM ready
 */
document.addEventListener('DOMContentLoaded', function() {
    // Attach event listeners to interactive elements
    attachStatCounterListeners();
    attachRefreshListener();
    attachAffectBtnListener();
    attachTechButtonListeners();

    // Attach button listeners with delegation
    attachTeamManagementButtonListeners();
});

/**
 * Attach team management button listeners using event delegation
 */
function attachTeamManagementButtonListeners() {
    document.addEventListener('click', function(e) {
        // Show all teams management
        if (e.target?.getAttribute('data-action') === 'show-teams-mgmt' || 
            e.target?.closest('[data-action="show-teams-mgmt"]')) {
            showAllTeamsManagement();
        }
        
        // Hide teams management
        if (e.target?.getAttribute('data-action') === 'hide-teams-mgmt' ||
            e.target?.closest('[data-action="hide-teams-mgmt"]')) {
            hideTeamsManagement();
        }
        
        // Show publication selection
        if (e.target?.getAttribute('data-action') === 'show-publication-sel' ||
            e.target?.closest('[data-action="show-publication-sel"]')) {
            showPublicationSelection();
        }
    });
}

// ============================================================================
// EXPORTS
// ============================================================================

// Make functions globally available for templates that may need them
window.dashboardFunctions = {
    showDetailsModal,
    showDemandePreview,
    showDispatchModal,
    displayStatsDetails,
    refreshStats,
    showPublicationSelection,
    showAllTeamsManagement,
    hideTeamsManagement,
    confirmerAffectation
};

// ============================================================================
// 9. TECHNOLOGY HIGHLIGHTING - for tech button filters
// ============================================================================

/**
 * Highlight cells by technology
 */
function highlightTechnology(tech) {
    const allCells = document.querySelectorAll('td, th');
    allCells.forEach(cell => cell.classList.remove('highlight'));
    
    if (tech === 'all') return;
    
    let startIdx, endIdx;
    switch (tech) {
        case 'fibre': startIdx = 2; endIdx = 6; break;
        case 'cuivre': startIdx = 7; endIdx = 11; break;
        case '5g': startIdx = 12; endIdx = 16; break;
        default: return;
    }
    
    const headerRows = document.querySelectorAll('thead tr');
    headerRows.forEach(row => {
        const cells = row.querySelectorAll('th');
        for (let i = startIdx; i <= endIdx; i++) {
            if (cells[i]) cells[i].classList.add('highlight');
        }
    });
    
    const dataRows = document.querySelectorAll('tbody tr');
    dataRows.forEach(row => {
        const cells = row.querySelectorAll('td');
        for (let i = startIdx; i <= endIdx; i++) {
            if (cells[i]) cells[i].classList.add('highlight');
        }
    });
}

/**
 * Attach tech button listeners
 */
function attachTechButtonListeners() {
    const techButtons = document.querySelectorAll('.tech-btn');
    techButtons.forEach(button => {
        button.addEventListener('click', function() {
            techButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');
            const tech = this.getAttribute('data-tech');
            highlightTechnology(tech);
        });
    });
}
