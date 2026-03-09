/**
 * Gestion interactive des utilisateurs
 * Intégration de TableManager avec fonctionnalités métier
 */

class UsersManager {
    constructor() {
        this.tableManager = null;
        this.deleteModal = null;
        this.init();
    }

    init() {
        // Initialiser TableManager si le tableau existe
        if (document.getElementById('usersTable')) {
            this.tableManager = new TableManager('usersTable', {
                sortable: true,
                searchable: true,
                bulkable: true,
                onDelete: (rows) => this.onBulkDelete(rows)
            });
        }

        // Initialiser le modal de suppression
        const deleteModalEl = document.getElementById('deleteModal');
        if (deleteModalEl) {
            this.deleteModal = new bootstrap.Modal(deleteModalEl);
        }

        this._setupEventListeners();
    }

    _setupEventListeners() {
        // Boutons de suppression individuels
        document.addEventListener('click', (e) => {
            if (e.target.closest('.delete-user')) {
                const btn = e.target.closest('.delete-user');
                this.showDeleteModal(btn.dataset.userId, btn.dataset.username);
            }
        });

        // Bouton de confirmation de suppression
        const confirmDeleteBtn = document.getElementById('confirmDelete');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', () => this.confirmDelete());
        }

        // Toggle du statut utilisateur
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('status-toggle')) {
                this.toggleUserStatus(e.target);
            }
        });
    }

    /**
     * Affiche le modal de suppression
     */
    showDeleteModal(userId, username) {
        const userIdInput = document.getElementById('deleteUserId');
        if (userIdInput) {
            userIdInput.value = userId;
        }
        
        document.getElementById('deleteUsername').textContent = username;
        document.getElementById('deleteErrorDetail').classList.add('d-none');
        document.getElementById('deleteErrorDetail').innerHTML = '';
        
        if (this.deleteModal) {
            this.deleteModal.show();
        }
    }

    /**
     * Confirme la suppression de l'utilisateur
     */
    confirmDelete() {
        const userIdInput = document.getElementById('deleteUserId');
        const userId = userIdInput?.value;

        if (!userId) return;

        const confirmBtn = document.getElementById('confirmDelete');
        const errDiv = document.getElementById('deleteErrorDetail');

        confirmBtn.disabled = true;
        errDiv.classList.add('d-none');
        errDiv.innerHTML = '';

        fetch(`/delete-user/${userId}`, {
            method: 'POST'
        })
        .then(response => {
            return response.json().then(data => ({ 
                status: response.status, 
                ok: response.ok, 
                data 
            }));
        })
        .then(({ status, ok, data }) => {
            if (ok) {
                // Succès : supprimer la ligne du tableau
                const row = document.querySelector(`tr[data-user-id="${userId}"]`);
                if (row) {
                    row.classList.add('deleting');
                    setTimeout(() => {
                        row.remove();
                        // Réinitialiser TableManager
                        if (this.tableManager) {
                            this.tableManager._extractData();
                            this.tableManager._render();
                        }
                    }, 300);
                }

                if (this.deleteModal) {
                    this.deleteModal.hide();
                }

                this.showAlert(data.message, 'success');
                userIdInput.value = '';
            } else {
                // Erreur : afficher message detaillé
                let message = data?.error || 'Erreur lors de la suppression';
                
                if (status === 400) {
                    message += '<br><br><strong>Que faire :</strong><ul>' +
                        '<li>Réaffecter ou supprimer les interventions et demandes liées à cet utilisateur.</li>' +
                        '<li>Réassigner les équipes dont il est chef.</li>' +
                        '<li>Envisager d\'archiver plutôt que de supprimer.</li>' +
                        '</ul>';
                } else if (status === 409) {
                    message += '<br><br><strong>Que faire :</strong><ul>' +
                        '<li>Contacter l\'administrateur pour nettoyer les enregistrements d\'activité.</li>' +
                        '<li>Ces données empêchent la suppression.</li>' +
                        '</ul>';
                }

                errDiv.innerHTML = message;
                errDiv.classList.remove('d-none');
                this.showAlert('Impossible de supprimer l\'utilisateur', 'danger');
            }
        })
        .catch(error => {
            console.error('Erreur de suppression:', error);
            errDiv.innerHTML = 'Erreur de connexion. Veuillez réessayer.';
            errDiv.classList.remove('d-none');
            this.showAlert('Erreur de connexion', 'danger');
        })
        .finally(() => {
            confirmBtn.disabled = false;
        });
    }

    /**
     * Bascule le statut d'un utilisateur (actif/inactif)
     */
    toggleUserStatus(toggleElement) {
        const userId = toggleElement.dataset.userId;
        const isActive = toggleElement.checked;

        fetch(`/toggle-user-status/${userId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ actif: isActive })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.showAlert(data.message, 'success');
                
                // Mettre à jour le label visuel
                const label = toggleElement.nextElementSibling;
                if (label && label.classList.contains('form-check-label')) {
                    label.textContent = isActive ? 'Actif' : 'Inactif';
                }
            } else {
                toggleElement.checked = !isActive;
                this.showAlert(data.error || 'Erreur lors de la mise à jour', 'danger');
            }
        })
        .catch(error => {
            toggleElement.checked = !isActive;
            console.error('Erreur:', error);
            this.showAlert('Erreur de connexion', 'danger');
        });
    }

    /**
     * Gère la suppression en masse
     */
    onBulkDelete(rows) {
        console.log(`Suppression en masse de ${rows.length} utilisateurs`);
        // Logique de suppression en masse côté serveur
        // À implémenter selon les besoins
    }

    /**
     * Affiche une notification
     */
    showAlert(message, type = 'info') {
        if (typeof ToastManager !== 'undefined') {
            ToastManager.show(message, type);
        } else {
            console.log(`[${type}] ${message}`);
        }
    }
}

// Initialiser au chargement du DOM
document.addEventListener('DOMContentLoaded', () => {
    window.usersManager = new UsersManager();
});
