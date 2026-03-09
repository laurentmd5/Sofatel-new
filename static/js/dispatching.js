/**
 * Sofatelcom PUR - Module de Dispatching
 * Gestion de l'affectation des demandes d'intervention
 */

// Fonction de normalisation des zones (comme dans utils.py)
function normalizeZone(zone) {
    if (!zone) return 'DAKAR';
    const z = zone.toUpperCase();
    if (z.includes('MBOUR')) return 'MBOUR';
    if (z.includes('KAOLACK')) return 'KAOLACK';
    if (z.includes('FATICK')) return 'FATICK';
    return 'DAKAR';
}

// Fonction de normalisation des technologies
function normalizeTech(tech) {
    return tech ? tech.charAt(0).toUpperCase() + tech.slice(1).toLowerCase() : '';
}

// État du module dispatching
const DispatchingModule = {
    selectedDemandes: [],
    techniciens: [],
    equipes: [],
    currentModal: null,

    // Configuration
    config: {
        compatibilityMatrix: {
            'Fibre': ['Fibre', 'Fibre,Cuivre', 'Fibre,5G', 'Fibre,Cuivre,5G'],
            'Cuivre': ['Cuivre', 'Fibre,Cuivre', 'Cuivre,5G', 'Fibre,Cuivre,5G'],
            '5G': ['5G', 'Fibre,5G', 'Cuivre,5G', 'Fibre,Cuivre,5G']
        },
        zoneCompatibility: {
            'DAKAR': ['DAKAR', 'Toutes'],
            'MBOUR': ['MBOUR', 'Toutes'],
            'KAOLACK': ['KAOLACK', 'Toutes'],
            'Autres': ['Autres', 'Toutes']
        }
    }

};

/**
 * Initialisation du module dispatching
 */
document.addEventListener('DOMContentLoaded', function () {
    if (document.querySelector('#demandesTable')) {
        initializeDispatching();
    }

    // Initialiser les filtres au chargement
    if (document.getElementById('filterTechnologie') ||
        document.getElementById('filterZone') ||
        document.getElementById('filterPriorite')) {
        filterDemandes();
    }
});

/**
 * Filtre les demandes en fonction des critères sélectionnés
 */
function filterDemandes() {
    const technologie = document.getElementById('filterTechnologie')?.value || '';
    const zone = document.getElementById('filterZone')?.value || '';
    const priorite = document.getElementById('filterPriorite')?.value || '';
    const age = document.getElementById('filterAge')?.value || '';
    const offre = document.getElementById('filterOffre')?.value || '';

    // Construire l'URL avec les paramètres de filtre
    let url = new URL(window.location.href);
    const params = new URLSearchParams();

    if (technologie) params.append('technologie', technologie);
    if (zone) params.append('zone', zone);
    if (priorite) params.append('priorite_traitement', priorite);
    if (age) params.append('age', age);
    if (offre) params.append('offre', offre);

    // Mettre à jour l'URL sans recharger la page
    const queryString = params.toString();
    const newUrl = queryString ? `${url.pathname}?${queryString}` : url.pathname;

    // Recharger la page avec les nouveaux filtres
    window.location.href = newUrl;
}

/**
 * Initialisation principale
 */
function initializeDispatching() {
    console.log('Initialisation du module Dispatching...');

    loadTechniciensData();
    loadEquipesData();
    setupDispatchingEventListeners();
    initializeFilters();
    setupKeyboardShortcuts();

    console.log('Module Dispatching initialisé');
}

/**
 * Chargement des données des techniciens
 */
function loadTechniciensData() {
    const technicienSelects = document.querySelectorAll('select[id*="technicien"], select[id*="Technicien"]');

    technicienSelects.forEach(select => {
        Array.from(select.options).forEach(option => {
            if (option.value) {
                DispatchingModule.techniciens.push({
                    id: option.value,
                    nom: option.textContent,
                    technologies: option.dataset.technologies || '',
                    zone: option.dataset.zone || ''
                });
            }
        });
    });
}

/**
 * Chargement des données des équipes
 */
function loadEquipesData() {
    const equipeSelects = document.querySelectorAll('select[id*="equipe"], select[id*="Equipe"]');

    equipeSelects.forEach(select => {
        Array.from(select.options).forEach(option => {
            if (option.value) {
                DispatchingModule.equipes.push({
                    id: option.value,
                    nom: option.textContent,
                    technologies: option.dataset.technologies || '',
                    zone: option.dataset.zone || ''
                });
            }
        });
    });
}

/**
 * Configuration des écouteurs d'événements
 */
function setupDispatchingEventListeners() {
    // Sélection multiple des demandes
    document.addEventListener('change', function (e) {
        if (e.target.classList.contains('demande-checkbox')) {
            handleDemandeSelection(e.target);
        }
    });

    // Filtres
    ['filterTechnologie', 'filterZone', 'filterPriorite'].forEach(filterId => {
        const filter = document.getElementById(filterId);
        if (filter) {
            filter.addEventListener('change', applyFilters);
        }
    });

    // Recherche textuelle
    const searchInput = document.getElementById('searchText');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(applyFilters, 300));
    }

    // Sélection de technicien pour suggestions intelligentes
    document.addEventListener('change', function (e) {
        if (e.target.id === 'groupTechnicien') {
            updateTechnicienSuggestions(e.target.value);
        }
    });
}

/**
 * Gestion de la sélection des demandes
 */
function handleDemandeSelection(checkbox) {
    const demandeId = checkbox.value;
    const row = checkbox.closest('tr');

    if (checkbox.checked) {
        DispatchingModule.selectedDemandes.push(demandeId);
        row.classList.add('selected');
        highlightCompatibleTechniciens(row);
    } else {
        const index = DispatchingModule.selectedDemandes.indexOf(demandeId);
        if (index > -1) {
            DispatchingModule.selectedDemandes.splice(index, 1);
        }
        row.classList.remove('selected');
    }

    updateSelectionCount();
    updateGroupActionVisibility();
}

/**
 * Mise en surbrillance des techniciens compatibles
 */
function highlightCompatibleTechniciens(demandeRow) {
    const technologie = demandeRow.dataset.technologie;
    const zone = demandeRow.dataset.zone;

    const technicienSelect = document.getElementById('groupTechnicien');
    if (!technicienSelect) return;

    Array.from(technicienSelect.options).forEach(option => {
        if (option.value) {
            const isCompatible = checkTechnicienCompatibility(
                option.dataset.technologies,
                option.dataset.zone,
                technologie,
                zone
            );

            option.style.backgroundColor = isCompatible ? '#d4edda' : '#f8d7da';
            option.style.color = isCompatible ? '#155724' : '#721c24';
        }
    });
}

/**
 * Vérification de la compatibilité technicien/demande
 */
function checkTechnicienCompatibility(techTechnologies, techZone, demandeTechno, demandeZone) {
    if (!techTechnologies) return false;

    // Normaliser les valeurs
    const techNormalized = normalizeTech(demandeTechno);
    const zoneNormalized = normalizeZone(demandeZone);
    const techCompat = techTechnologies.split(',').map(t => normalizeTech(t.trim()));
    const zoneCompat = techZone ? [normalizeZone(techZone)] : [];

    console.log('Vérification compatibilité:', {
        demande: { tech: techNormalized, zone: zoneNormalized },
        technicien: { tech: techCompat, zone: zoneCompat }
    });

    // Vérifier la technologie
    const techCompatible = DispatchingModule.config.compatibilityMatrix[techNormalized]?.some(compat =>
        techCompat.includes(compat)
    ) || false;

    // Vérifier la zone
    const zoneCompatible = DispatchingModule.config.zoneCompatibility[zoneNormalized]?.some(compat =>
        zoneCompat.includes(compat)
    ) || false;

    console.log('Résultat compatibilité:', { techCompatible, zoneCompatible });

    return techCompatible && zoneCompatible;
}

/**
 * Mise à jour du compteur de sélection
 */
function updateSelectionCount() {
    const countElement = document.getElementById('selectCount');
    if (countElement) {
        countElement.textContent = DispatchingModule.selectedDemandes.length;

        // Animation du compteur
        countElement.classList.add('pulse');
        setTimeout(() => countElement.classList.remove('pulse'), 600);
    }
}

/**
 * Mise à jour de la visibilité des actions groupées
 */
function updateGroupActionVisibility() {
    const groupActions = document.querySelector('.card:has(#groupTechnicien)');
    if (groupActions) {
        groupActions.style.display = DispatchingModule.selectedDemandes.length > 0 ? 'block' : 'none';
    }
}

/**
 * Application des filtres côté client (filtrage sans rechargement de page)
 * @returns {boolean} Retourne false si aucun filtre n'est actif
 */
function applyFilters() {
    const filters = {
        technologie: document.getElementById('filterTechnologie')?.value || '',
        zone: document.getElementById('filterZone')?.value || '',
        priorite: document.getElementById('filterPriorite')?.value || '',
        age: document.getElementById('filterAge')?.value || '',
        offre: document.getElementById('filterOffre')?.value || '',
        search: document.getElementById('searchText')?.value.toLowerCase() || ''
    };

    // Vérifier si des filtres sont actifs
    const hasActiveFilters = Object.values(filters).some(filter => filter !== '');
    const rows = document.querySelectorAll('#demandesTable tbody tr');
    let visibleCount = 0;

    rows.forEach(row => {
        let visible = true;
        const rowData = row.dataset;

        // Si aucun filtre actif, on affiche tout
        if (!hasActiveFilters) {
            row.style.display = '';
            visibleCount++;
            return;
        }

        // Filtre par technologie
        if (filters.technologie && rowData.technologie !== filters.technologie) {
            visible = false;
        }

        // Filtre par zone
        if (visible && filters.zone) {
            const rowZone = normalizeZone(rowData.zone || '');
            const filterZone = normalizeZone(filters.zone);
            if (rowZone !== filterZone) {
                visible = false;
            }
        }

        // Filtre par priorité
        if (visible && filters.priorite && rowData.priorite !== filters.priorite) {
            visible = false;
        }

        // Filtre par âge
        if (visible && filters.age && rowData.age !== filters.age) {
            visible = false;
        }

        // Filtre par offre
        if (visible && filters.offre && rowData.offre !== filters.offre) {
            visible = false;
        }

        // Filtre de recherche textuelle
        if (visible && filters.search) {
            const rowText = row.textContent.toLowerCase();
            if (!rowText.includes(filters.search)) {
                visible = false;
            }
        }

        // Appliquer la visibilité
        row.style.display = visible ? '' : 'none';
        if (visible) visibleCount++;
    });

    // Mettre à jour le compteur de résultats
    updateFilterResults(visibleCount);

    // Décocher les demandes qui viennent d'être masquées
    const hiddenCheckboxes = document.querySelectorAll('#demandesTable tbody tr[style*="none"] .demande-checkbox:checked');
    hiddenCheckboxes.forEach(checkbox => {
        checkbox.checked = false;
        handleDemandeSelection(checkbox);
    });

    return hasActiveFilters;
}

/**
 * Mise à jour des résultats de filtrage
 */
function updateFilterResults(count) {
    let resultElement = document.getElementById('filter-results');

    if (!resultElement) {
        resultElement = document.createElement('div');
        resultElement.id = 'filter-results';
        resultElement.className = 'text-muted small mt-2';

        const tableCard = document.querySelector('#demandesTable').closest('.card');
        if (tableCard) {
            tableCard.querySelector('.card-header').appendChild(resultElement);
        }
    }

    resultElement.textContent = `${count} demande(s) affichée(s)`;
}

/**
 * Sélection de toutes les demandes visibles
 */
function selectAllVisible() {
    const visibleCheckboxes = document.querySelectorAll('#demandesTable tbody tr:not([style*="none"]) .demande-checkbox');

    visibleCheckboxes.forEach(checkbox => {
        if (!checkbox.checked) {
            checkbox.checked = true;
            handleDemandeSelection(checkbox);
        }
    });
}

/**
 * Désélection de toutes les demandes
 */
function clearAllSelection() {
    const checkboxes = document.querySelectorAll('.demande-checkbox:checked');

    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
        handleDemandeSelection(checkbox);
    });

    document.getElementById('selectAllCheckbox').checked = false;
}

/**
 * Affichage du modal d'affectation individuelle
 */
function showDispatchModal(demandeId) {
    fetch(`/api/demande/${demandeId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayDispatchModal(data.demande);
            } else {
                showNotification('Erreur lors du chargement de la demande', 'error');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showNotification('Erreur lors du chargement', 'error');
        });
}

/**
 * Affichage du contenu du modal
 */
function displayDispatchModal(demande) {
    const modalContent = generateDispatchModalContent(demande);
    document.getElementById('modalContent').innerHTML = modalContent;

    // Pré-sélectionner les techniciens compatibles
    populateCompatibleTechniciens(demande);

    DispatchingModule.currentModal = new bootstrap.Modal(document.getElementById('dispatchModal'));
    DispatchingModule.currentModal.show();

    feather.replace();
}


/**
 * Génération du contenu du modal
 */
function generateDispatchModalContent(demande) {

    return `
        <div class="mb-3">
            <h6 class="text-primary mb-3">
                <i data-feather="info" class="me-2"></i>
                Détails de la demande
            </h6>
            <div class="row">
                <div class="col-md-6">
                    <p class="mb-2"><strong>Client:</strong> ${demande.nom_client} ${demande.prenom_client}</p>
                    <p class="mb-2"><strong>ND:</strong> <code>${demande.nd}</code></p>
                    <p class="mb-2"><strong>Technologie:</strong> 
                        <span class="badge bg-primary">${demande.type_techno}</span>
                    </p>
                </div>
                <div class="col-md-6">
                    <p class="mb-2"><strong>Zone:</strong> ${demande.zone}</p>
                    <p class="mb-2"><strong>Service:</strong> 
                        <span class="badge bg-success">${demande.service}</span>
                    </p>
                    <p class="mb-2"><strong>Priorité:</strong> 
                        <span class="badge bg-warning">${demande.priorite_traitement || 'Normale'}</span>
                    </p>
                </div>
            </div>
            <div class="row">
                <div class="col-12">
                    <p class="mb-0"><strong>Adresse:</strong> ${demande.libelle_commune}${demande.libelle_quartier ? ', ' + demande.libelle_quartier : ''}</p>
                </div>
            </div>
        </div>
        
        <div class="mb-3">
            <label class="form-label">
                <i data-feather="user" class="me-1"></i>
                Technicien <span class="text-danger">*</span>
            </label>
            <select class="form-select" id="modalTechnicien" required>
                <option value="">Sélectionner un technicien</option>
            </select>
            <div class="form-text">Les techniciens compatibles sont en vert</div>
        </div>
        
        <div class="mb-3">
            <label class="form-label">
                <i data-feather="users" class="me-1"></i>
                Équipe (optionnel)
            </label>
            <select class="form-select" id="modalEquipe">
                <option value="">Aucune équipe</option>
            </select>
        </div>
        
        <div class="mb-3">
            <label class="form-label">
                <i data-feather="message-square" class="me-1"></i>
                Commentaire
            </label>
            <textarea class="form-control" id="modalCommentaire" rows="3" 
                      placeholder="Commentaire d'affectation (optionnel)..."></textarea>
        </div>
        
        <div class="d-flex justify-content-between">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                <i data-feather="x" class="me-2"></i>
                Annuler
            </button>
            <button type="button" class="btn btn-primary" onclick="confirmerAffectationIndividuelle(${demande.id})">
                <i data-feather="check" class="me-2"></i>
                Affecter
            </button>
        </div>
    `;
}


/**
 * Population des techniciens compatibles
 */
function populateCompatibleTechniciens(demande) {
    const technicienSelect = document.getElementById('modalTechnicien');
    const equipeSelect = document.getElementById('modalEquipe');

    if (!technicienSelect) return;

    // Vider les options existantes (sauf la première)
    technicienSelect.innerHTML = '<option value="">Sélectionner un technicien</option>';
    equipeSelect.innerHTML = '<option value="">Aucune équipe</option>';

    // Ajouter les techniciens avec indication de compatibilité
    DispatchingModule.techniciens.forEach(technicien => {
        const isCompatible = checkTechnicienCompatibility(
            technicien.technologies,
            technicien.zone,
            demande.type_techno,
            demande.zone
        );

        const option = document.createElement('option');
        option.value = technicien.id;
        option.textContent = technicien.nom;
        option.style.backgroundColor = isCompatible ? '#d4edda' : '#f8d7da';
        option.style.color = isCompatible ? '#155724' : '#721c24';
        option.dataset.compatible = isCompatible;

        technicienSelect.appendChild(option);
    });

    // Ajouter les équipes compatibles
    DispatchingModule.equipes.forEach(equipe => {
        const isCompatible = checkEquipeCompatibility(equipe, demande);

        if (isCompatible) {
            const option = document.createElement('option');
            option.value = equipe.id;
            option.textContent = equipe.nom;
            equipeSelect.appendChild(option);
        }
    });
}

/**
 * Vérification de la compatibilité équipe/demande
 */
function checkEquipeCompatibility(equipe, demande) {
    return equipe.technologies.includes(demande.type_techno) &&
        (equipe.zone === demande.zone || equipe.zone === 'Toutes');
}

/**
 * Confirmation d'affectation individuelle
 */
function confirmerAffectationIndividuelle(demandeId) {
    const technicienId = document.getElementById('modalTechnicien').value;
    const equipeId = document.getElementById('modalEquipe').value;
    const commentaire = document.getElementById('modalCommentaire').value;

    if (!technicienId) {
        showNotification('Veuillez sélectionner un technicien', 'warning');
        return;
    }

    // Vérifier la compatibilité
    const selectedOption = document.querySelector('#modalTechnicien option:checked');
    if (selectedOption.dataset.compatible === 'false') {
        if (!confirm('Le technicien sélectionné n\'est pas optimal pour cette demande. Continuer quand même ?')) {
            return;
        }
    }

    affecterDemande(demandeId, technicienId, equipeId, commentaire, 'manuel');
}


/**
 * Affectation d'une demande
 */
function affecterDemande(demandeId, technicienId, equipeId, commentaire, mode = 'manuel') {
    return new Promise((resolve, reject) => {
        const data = {
            demande_id: demandeId,
            technicien_id: technicienId,
            equipe_id: equipeId || null,
            commentaire: commentaire,
            mode: mode
        };

        const button = document.querySelector(`button[onclick*="${demandeId}"]`);
        if (button) {
            button.disabled = true;
            button.innerHTML = '<i data-feather="loader" class="me-2"></i>Affectation...';
        }

        fetch('/affecter-demande', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    showNotification(result.message, 'success');

                    // Fermer le modal seulement pour l'affectation individuelle
                    if (mode === 'manuel' && DispatchingModule.currentModal) {
                        DispatchingModule.currentModal.hide();
                    }

                    // Supprimer la ligne du tableau seulement pour l'affectation individuelle
                    if (mode === 'manuel') {
                        removeDemandFromTable(demandeId);
                    }

                    // Mettre à jour les statistiques
                    updateDispatchingStats();

                } else {
                    showNotification('Erreur: ' + result.error, 'error');
                }
                resolve(result);
            })
            .catch(error => {
                console.error('Erreur:', error);
                showNotification('Erreur lors de l\'affectation', 'error');
                reject(error);
            })
            .finally(() => {
                if (button) {
                    button.disabled = false;
                    button.innerHTML = '<i data-feather="user-plus" class="me-1"></i>Affecter';
                    feather.replace();
                }
            });
    });
}

/**
 * Suppression d'une demande du tableau
 */
function removeDemandFromTable(demandeId) {
    const row = document.querySelector(`tr[data-demande-id="${demandeId}"]`);
    if (row) {
        row.style.transition = 'all 0.3s ease';
        row.style.opacity = '0';
        row.style.transform = 'translateX(-100%)';

        setTimeout(() => {
            row.remove();
            updateTableEmptyState();
        }, 300);
    }
}

/**
 * Mise à jour de l'état vide du tableau
 */
function updateTableEmptyState() {
    const tbody = document.querySelector('#demandesTable tbody');
    const visibleRows = tbody.querySelectorAll('tr:not([style*="none"])');

    if (visibleRows.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center py-5">
                    <i data-feather="check-circle" style="width: 64px; height: 64px;" class="text-success mb-3"></i>
                    <h5 class="text-muted">Toutes les demandes ont été affectées</h5>
                    <p class="text-muted">Excellent travail ! Toutes les demandes sont maintenant prises en charge.</p>
                </td>
            </tr>
        `;
        feather.replace();
    }
}

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
 * Affectation groupée
 */
function affecterSelection() {
    const technicienId = document.getElementById('groupTechnicien').value;
    const equipeId = document.getElementById('groupEquipe').value;

    if (!technicienId) {
        showNotification('Veuillez sélectionner un technicien pour l\'affectation groupée', 'warning');
        return;
    }

    if (DispatchingModule.selectedDemandes.length === 0) {
        showNotification('Veuillez sélectionner au moins une demande', 'warning');
        return;
    }

    const confirmMessage = `Affecter ${DispatchingModule.selectedDemandes.length} demande(s) au technicien sélectionné ?`;

    if (!confirm(confirmMessage)) {
        return;
    }

    showGroupAffectationProgress();

    let completed = 0;
    let errors = 0;
    const total = DispatchingModule.selectedDemandes.length;

    const promises = DispatchingModule.selectedDemandes.map((demandeId, index) => {
        return new Promise((resolve) => {
            setTimeout(() => {
                affecterDemande(demandeId, technicienId, equipeId, 'Affectation groupée', 'manuel_groupe')
                    .then((result) => {
                        if (result.success) {
                            completed++;
                        } else {
                            errors++;
                        }
                        resolve();
                    })
                    .catch(() => {
                        errors++;
                        resolve();
                    });
            }, index * 200);
        });
    });

    Promise.all(promises).then(() => {
        hideGroupAffectationProgress();
        clearAllSelection();

        if (errors === 0) {
            showNotification(`${completed} demande(s) affectée(s) avec succès`, 'success');
        } else {
            showNotification(`${completed} demande(s) affectée(s), ${errors} erreur(s)`, 'warning');
        }

        // Recharger la page pour mettre à jour le tableau
        setTimeout(() => location.reload(), 1000);
    });
}


/**
 * Affichage du progrès d'affectation groupée
 */
function showGroupAffectationProgress() {
    let progressModal = document.getElementById('groupProgressModal');

    if (!progressModal) {
        progressModal = document.createElement('div');
        progressModal.id = 'groupProgressModal';
        progressModal.className = 'modal fade';
        progressModal.innerHTML = `
            <div class="modal-dialog modal-sm">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i data-feather="send" class="me-2"></i>
                            Affectation en cours
                        </h5>
                    </div>
                    <div class="modal-body text-center">
                        <div class="progress mb-3">
                            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                 id="groupProgress" role="progressbar" style="width: 0%"></div>
                        </div>
                        <p id="groupProgressText">Préparation...</p>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(progressModal);
        feather.replace();
    }

    new bootstrap.Modal(progressModal).show();
}

/**
 * Mise à jour du progrès d'affectation groupée
 */
function updateGroupAffectationProgress(completed, total) {
    const progressBar = document.getElementById('groupProgress');
    const progressText = document.getElementById('groupProgressText');

    if (progressBar && progressText) {
        const percentage = (completed / total) * 100;
        progressBar.style.width = percentage + '%';
        progressText.textContent = `${completed} / ${total} demandes affectées`;
    }
}

/**
 * Masquage du progrès d'affectation groupée
 */
function hideGroupAffectationProgress() {
    const progressModal = bootstrap.Modal.getInstance(document.getElementById('groupProgressModal'));
    if (progressModal) {
        setTimeout(() => {
            progressModal.hide();
        }, 1000);
    }
}

/**
 * Dispatching automatique
 */
function dispatchingAutomatique() {
    const visibleDemandes = document.querySelectorAll('#demandesTable tbody tr:not([style*="none"])');

    if (visibleDemandes.length === 0) {
        showNotification('Aucune demande à traiter', 'info');
        return;
    }

    const confirmMessage = `Lancer le dispatching automatique pour ${visibleDemandes.length} demande(s) ?`;

    if (!confirm(confirmMessage)) {
        return;
    }

    const button = document.querySelector('button[onclick="dispatchingAutomatique()"]');
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i data-feather="zap" class="me-2"></i>Traitement en cours...';
    }

    fetch('/dispatching-automatique', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(data.message, 'success');
                setTimeout(() => location.reload(), 2000);
            } else {
                showNotification('Erreur: ' + data.error, 'error');
            }
        })
        .catch(error => {
            console.error('Erreur:', error);
            showNotification('Erreur lors du dispatching automatique', 'error');
        })
        .finally(() => {
            if (button) {
                button.disabled = false;
                button.innerHTML = '<i data-feather="zap" class="me-2"></i>Dispatching automatique';
                feather.replace();
            }
        });
}

/**
 * Mise à jour des statistiques de dispatching
 */
function updateDispatchingStats() {
    const statsElements = document.querySelectorAll('[data-stat]');

    fetch('/api/dispatching-stats')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                Object.keys(data.stats).forEach(key => {
                    const element = document.querySelector(`[data-stat="${key}"]`);
                    if (element) {
                        element.textContent = data.stats[key];
                        element.classList.add('pulse');
                        setTimeout(() => element.classList.remove('pulse'), 600);
                    }
                });
            }
        })
        .catch(error => console.error('Erreur stats:', error));
}

/**
 * Configuration des raccourcis clavier
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function (e) {
        // Ctrl+A pour sélectionner toutes les demandes visibles
        if (e.ctrlKey && e.key === 'a' && document.activeElement.tagName !== 'INPUT') {
            e.preventDefault();
            selectAllVisible();
        }

        // Escape pour désélectionner
        if (e.key === 'Escape') {
            clearAllSelection();
        }

        // Ctrl+D pour dispatching automatique
        if (e.ctrlKey && e.key === 'd') {
            e.preventDefault();
            dispatchingAutomatique();
        }
    });
}

/**
 * Suggestions intelligentes de techniciens
 */
function updateTechnicienSuggestions(technicienId) {
    if (!technicienId) return;

    const technicien = DispatchingModule.techniciens.find(t => t.id == technicienId);
    if (!technicien) return;

    // Mettre en évidence les demandes compatibles
    const rows = document.querySelectorAll('#demandesTable tbody tr');

    rows.forEach(row => {
        const isCompatible = checkTechnicienCompatibility(
            technicien.technologies,
            technicien.zone,
            row.dataset.technologie,
            row.dataset.zone
        );

        if (isCompatible) {
            row.classList.add('table-success', 'border', 'border-success');
        } else {
            row.classList.add('table-warning', 'border', 'border-warning');
        }
    });

    // Afficher un message informatif
    showTechnicienSuggestionInfo(technicien);
}

/**
 * Affichage des informations de suggestion
 */
function showTechnicienSuggestionInfo(technicien) {
    let infoElement = document.getElementById('technicien-suggestion-info');

    if (!infoElement) {
        infoElement = document.createElement('div');
        infoElement.id = 'technicien-suggestion-info';
        infoElement.className = 'alert alert-info mt-3';

        const groupActions = document.querySelector('.card:has(#groupTechnicien) .card-body');
        if (groupActions) {
            groupActions.appendChild(infoElement);
        }
    }

    infoElement.innerHTML = `
        <i data-feather="info" class="me-2"></i>
        <strong>${technicien.nom}</strong> - ${technicien.technologies} (${technicien.zone})
        <br>
        <small>Les demandes compatibles sont en vert, les autres en orange.</small>
    `;

    feather.replace();
}

/**
 * Initialisation des filtres avec valeurs par défaut
 */
function initializeFilters() {
    // Appliquer les filtres sauvegardés dans le localStorage
    const savedFilters = localStorage.getItem('dispatching_filters');

    if (savedFilters) {
        const filters = JSON.parse(savedFilters);

        Object.keys(filters).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                element.value = filters[key];
            }
        });

        applyFilters();
    }

    // Sauvegarder les filtres lors des changements
    ['filterTechnologie', 'filterZone', 'filterPriorite'].forEach(filterId => {
        const filter = document.getElementById(filterId);
        if (filter) {
            filter.addEventListener('change', saveFilters);
        }
    });
}


/**
* Sauvegarde des filtres
*/
function saveFilters() {
    const filters = {
        filterTechnologie: document.getElementById('filterTechnologie')?.value || '',
        filterZone: document.getElementById('filterZone')?.value || '',
        filterPriorite: document.getElementById('filterPriorite')?.value || ''
    };

    localStorage.setItem('dispatching_filters', JSON.stringify(filters));
}

// Fonction debounce pour limiter les appels
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export du module pour utilisation globale
window.DispatchingModule = DispatchingModule;
window.selectAllVisible = selectAllVisible;
window.clearAllSelection = clearAllSelection;
window.showDispatchModal = showDispatchModal;
window.confirmerAffectationIndividuelle = confirmerAffectationIndividuelle;
window.affecterSelection = affecterSelection;
window.dispatchingAutomatique = dispatchingAutomatique;
