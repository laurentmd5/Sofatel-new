/**
 * Pagination côté CLIENT (JavaScript)
 * Gère la pagination de tableaux dynamiques
 * Affiche 10 éléments par page
 */

class ClientPagination {
    constructor(config = {}) {
        // Configuration
        this.itemsPerPage = config.itemsPerPage || 10;
        this.containerId = config.containerId || 'tableContainer';
        this.tbodyId = config.tbodyId || 'tableBody';
        this.paginationContainerId = config.paginationContainerId || 'paginationContainer';
        this.emptyStateId = config.emptyStateId || 'emptyState';
        this.statIdPrefix = config.statIdPrefix || 'stat'; // stat{Total,Valeur,Qty}
        
        // Données
        this.allItems = [];
        this.filteredItems = [];
        this.currentPage = 1;
        
        // Callbacks
        this.renderRowCallback = config.renderRowCallback;
        this.updateStatsCallback = config.updateStatsCallback;
    }

    /**
     * Initialiser les données
     */
    setData(items) {
        this.allItems = items;
        this.filteredItems = [...items];
        this.currentPage = 1;
    }

    /**
     * Appliquer un filtre aux données
     */
    applyFilter(filterFn) {
        this.filteredItems = this.allItems.filter(filterFn);
        this.currentPage = 1;
    }

    /**
     * Afficher la table avec pagination
     */
    displayTable() {
        const container = document.getElementById(this.containerId);
        const emptyState = document.getElementById(this.emptyStateId);
        const tbody = document.getElementById(this.tbodyId);

        tbody.innerHTML = '';

        // Afficher état vide si aucune donnée
        if (this.filteredItems.length === 0) {
            container.style.display = 'none';
            if (emptyState) emptyState.style.display = 'block';
            return;
        }

        container.style.display = 'block';
        if (emptyState) emptyState.style.display = 'none';

        // Calculer les éléments à afficher pour la page actuelle
        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageItems = this.filteredItems.slice(startIndex, endIndex);

        // Afficher les lignes
        pageItems.forEach(item => {
            const row = this.renderRowCallback(item);
            tbody.appendChild(row);
        });

        // Afficher la pagination
        this.renderPagination();

        // Mettre à jour les statistiques
        if (this.updateStatsCallback) {
            this.updateStatsCallback(this.filteredItems);
        }
    }

    /**
     * Rendre les contrôles de pagination
     */
    renderPagination() {
        const paginationContainer = document.getElementById(this.paginationContainerId);
        if (!paginationContainer) return;

        paginationContainer.innerHTML = '';

        const totalPages = Math.ceil(this.filteredItems.length / this.itemsPerPage);
        
        // Si seulement une page, ne pas afficher la pagination
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        // Conteneur nav
        const nav = document.createElement('nav');
        nav.setAttribute('aria-label', 'Pagination');

        // Conteneur ul
        const ul = document.createElement('ul');
        ul.className = 'pagination pagination-sm';

        // Bouton Précédent
        const prevLi = document.createElement('li');
        prevLi.className = 'page-item ' + (this.currentPage === 1 ? 'disabled' : '');
        const prevLink = document.createElement('a');
        prevLink.className = 'page-link';
        prevLink.href = '#';
        prevLink.textContent = 'Précédente';
        prevLink.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage > 1) {
                this.currentPage--;
                this.displayTable();
            }
        });
        prevLi.appendChild(prevLink);
        ul.appendChild(prevLi);

        // Numéros de page
        // Afficher max 5 numéros
        const pageNumbers = this.getPageNumbers(totalPages);

        pageNumbers.forEach(pageNum => {
            if (pageNum === '...') {
                const li = document.createElement('li');
                li.className = 'page-item disabled';
                li.innerHTML = '<span class="page-link">...</span>';
                ul.appendChild(li);
            } else {
                const li = document.createElement('li');
                li.className = 'page-item ' + (this.currentPage === pageNum ? 'active' : '');
                const link = document.createElement('a');
                link.className = 'page-link';
                link.href = '#';
                link.textContent = pageNum;
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.currentPage = pageNum;
                    this.displayTable();
                });
                li.appendChild(link);
                ul.appendChild(li);
            }
        });

        // Bouton Suivante
        const nextLi = document.createElement('li');
        nextLi.className = 'page-item ' + (this.currentPage === totalPages ? 'disabled' : '');
        const nextLink = document.createElement('a');
        nextLink.className = 'page-link';
        nextLink.href = '#';
        nextLink.textContent = 'Suivante';
        nextLink.addEventListener('click', (e) => {
            e.preventDefault();
            if (this.currentPage < totalPages) {
                this.currentPage++;
                this.displayTable();
            }
        });
        nextLi.appendChild(nextLink);
        ul.appendChild(nextLi);

        nav.appendChild(ul);
        paginationContainer.appendChild(nav);

        // Afficher info pagination
        const info = document.createElement('div');
        info.className = 'text-center mt-2 text-muted small';
        info.textContent = `Affichage de ${((this.currentPage - 1) * this.itemsPerPage) + 1} à ${Math.min(this.currentPage * this.itemsPerPage, this.filteredItems.length)} sur ${this.filteredItems.length} entrées`;
        paginationContainer.appendChild(info);
    }

    /**
     * Calculer les numéros de page à afficher
     */
    getPageNumbers(totalPages) {
        const pages = [];
        const maxVisible = 5;

        if (totalPages <= maxVisible) {
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            // Afficher toujours page 1
            pages.push(1);

            // Calculer la plage autour de la page actuelle
            let start = Math.max(2, this.currentPage - 1);
            let end = Math.min(totalPages - 1, this.currentPage + 1);

            if (start > 2) {
                pages.push('...');
            }

            for (let i = start; i <= end; i++) {
                pages.push(i);
            }

            if (end < totalPages - 1) {
                pages.push('...');
            }

            // Afficher toujours dernière page
            pages.push(totalPages);
        }

        return pages;
    }

    /**
     * Aller à une page spécifique
     */
    goToPage(pageNum) {
        const totalPages = Math.ceil(this.filteredItems.length / this.itemsPerPage);
        if (pageNum >= 1 && pageNum <= totalPages) {
            this.currentPage = pageNum;
            this.displayTable();
        }
    }

    /**
     * Réinitialiser la pagination
     */
    reset() {
        this.currentPage = 1;
        this.filteredItems = [...this.allItems];
    }
}
