/**
 * Auto-Pagination pour tableaux
 * Applique automatiquement la pagination à tous les tableaux dépassant 10 lignes
 * Compatible avec les tableaux dynamiques générés en JavaScript
 */

class AutoTablePagination {
    constructor(config = {}) {
        this.itemsPerPage = config.itemsPerPage || 10;
        this.tableSelector = config.tableSelector || 'table';
        this.autoInit = config.autoInit !== false;
        
        if (this.autoInit) {
            this.initializeOnReady();
        }
    }

    /**
     * Initialiser quando le DOM est pronto
     */
    initializeOnReady() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.findAndPaginateTables());
        } else {
            this.findAndPaginateTables();
        }
    }

    /**
     * Trouver tous les tableaux et appliquer la pagination
     */
    findAndPaginateTables() {
        // Traiter les tableaux existants
        document.querySelectorAll(this.tableSelector).forEach(table => {
            this.paginateTable(table);
        });

        // ✅ FIX #2: Debounced, scoped, and filtered MutationObserver
        // Avoid runaway loops by:
        // - Only watching main-content (not entire body)
        // - Debouncing with 500ms timer
        // - Filtering to meaningful mutations only
        
        if (!this.observer) {
            let debounceTimeout = null;
            
            this.observer = new MutationObserver((mutations) => {
                // Filter: only care about new table elements
                let hasNewTable = false;
                for (let mutation of mutations) {
                    if (mutation.type === 'childList') {
                        // Check if any added nodes contain tables
                        for (let node of mutation.addedNodes) {
                            if (node.tagName === 'TABLE' || (node.querySelector && node.querySelector('table'))) {
                                hasNewTable = true;
                                break;
                            }
                        }
                    }
                }
                
                if (hasNewTable) {
                    // Debounce: batch mutations within 500ms window
                    if (debounceTimeout) clearTimeout(debounceTimeout);
                    debounceTimeout = setTimeout(() => {
                        this.findAndPaginateTables();
                    }, 500);
                }
            });
            
            // Scope: watch only main content area (not entire document.body)
            const mainContent = document.getElementById('main-content') || document.body;
            this.observer.observe(mainContent, {
                childList: true,
                subtree: true
            });
        }
    }

    /**
     * Vérifier si une table a déjà une pagination serveur
     */
    hasServerPagination(table) {
        // Chercher les éléments avec la classe 'pagination' dans les parents
        let parent = table.parentElement;
        let depth = 0;
        const maxDepth = 5; // Limite de recherche
        
        while (parent && depth < maxDepth) {
            // Chercher une .pagination dans ce parent
            const pagination = parent.querySelector('.pagination');
            if (pagination) {
                // Vérifier que cette pagination n'est pas déjà créée par auto-pagination
                // (auto-pagination utilise la classe 'pagination-controls')
                if (!pagination.classList.contains('pagination-controls')) {
                    return true; // Pagination serveur trouvée
                }
            }
            
            parent = parent.parentElement;
            depth++;
        }
        
        return false;
    }

    /**
     * Paginer un tableau spécifique
     */
    paginateTable(table) {
        // Vérifier si déjà paginé
        if (table.dataset.paginated === 'true') return;

        // ✅ FIX: Vérifier si le tableau a déjà une pagination serveur
        if (this.hasServerPagination(table)) {
            // Cette table a une pagination serveur, ignorer la pagination côté client
            table.dataset.paginated = 'true'; // Marquer pour éviter les tentatives futures
            return;
        }

        const tbody = table.querySelector('tbody');
        if (!tbody) return;

        const rows = Array.from(tbody.querySelectorAll('tr'));
        if (rows.length <= this.itemsPerPage) return; // Pas besoin de paginer

        // Marquer comme paginé
        table.dataset.paginated = 'true';

        // Créer les éléments de pagination
        const paginationContainer = document.createElement('div');
        paginationContainer.className = 'pagination-controls mt-4 mb-4 d-flex justify-content-center';
        paginationContainer.style.display = 'none';

        // Insérer après la table
        table.parentNode.insertBefore(paginationContainer, table.nextSibling);

        // Données de pagination
        const paginationData = {
            currentPage: 1,
            totalPages: Math.ceil(rows.length / this.itemsPerPage),
            rows: rows,
            tbody: tbody,
            container: paginationContainer,
            table: table
        };

        // Afficher la première page
        this.showPage(paginationData, 1);
    }

    /**
     * Afficher une page spécifique
     */
    showPage(paginationData, pageNum) {
        const { rows, tbody, container, totalPages } = paginationData;
        paginationData.currentPage = pageNum;

        // Calculer l'index
        const startIdx = (pageNum - 1) * this.itemsPerPage;
        const endIdx = startIdx + this.itemsPerPage;

        // Masquer toutes les lignes
        rows.forEach(row => row.style.display = 'none');

        // Afficher les lignes de cette page
        rows.slice(startIdx, endIdx).forEach(row => row.style.display = '');

        // Rendre la pagination
        this.renderPagination(paginationData);
    }

    /**
     * Rendre les contrôles de pagination
     */
    renderPagination(paginationData) {
        const { currentPage, totalPages, container } = paginationData;

        if (totalPages <= 1) {
            container.style.display = 'none';
            return;
        }

        container.innerHTML = '';
        container.style.display = 'block';

        // Créer la nav
        const nav = document.createElement('nav');
        nav.setAttribute('aria-label', 'Pagination');

        const ul = document.createElement('ul');
        ul.className = 'pagination pagination-sm';

        // Bouton Précédent
        const prevLi = document.createElement('li');
        prevLi.className = 'page-item' + (currentPage === 1 ? ' disabled' : '');
        const prevLink = document.createElement('a');
        prevLink.className = 'page-link';
        prevLink.href = '#';
        prevLink.textContent = 'Précédente';
        prevLink.addEventListener('click', (e) => {
            e.preventDefault();
            if (currentPage > 1) {
                this.showPage(paginationData, currentPage - 1);
            }
        });
        prevLi.appendChild(prevLink);
        ul.appendChild(prevLi);

        // Numéros de page
        const pageNumbers = this.getPageNumbers(currentPage, totalPages);
        pageNumbers.forEach(pageNum => {
            if (pageNum === '...') {
                const li = document.createElement('li');
                li.className = 'page-item disabled';
                li.innerHTML = '<span class="page-link">...</span>';
                ul.appendChild(li);
            } else {
                const li = document.createElement('li');
                li.className = 'page-item' + (currentPage === pageNum ? ' active' : '');
                const link = document.createElement('a');
                link.className = 'page-link';
                link.href = '#';
                link.textContent = pageNum;
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.showPage(paginationData, pageNum);
                });
                li.appendChild(link);
                ul.appendChild(li);
            }
        });

        // Bouton Suivante
        const nextLi = document.createElement('li');
        nextLi.className = 'page-item' + (currentPage === totalPages ? ' disabled' : '');
        const nextLink = document.createElement('a');
        nextLink.className = 'page-link';
        nextLink.href = '#';
        nextLink.textContent = 'Suivante';
        nextLink.addEventListener('click', (e) => {
            e.preventDefault();
            if (currentPage < totalPages) {
                this.showPage(paginationData, currentPage + 1);
            }
        });
        nextLi.appendChild(nextLink);
        ul.appendChild(nextLi);

        nav.appendChild(ul);
        container.appendChild(nav);

        // Afficher info
        const info = document.createElement('div');
        info.className = 'text-center mt-2 text-muted small';
        info.textContent = `Page ${currentPage} sur ${totalPages} (${paginationData.rows.length} entrées)`;
        container.appendChild(info);
    }

    /**
     * Calculer les numéros de page à afficher
     */
    getPageNumbers(currentPage, totalPages) {
        const pages = [];
        const maxVisible = 5;

        if (totalPages <= maxVisible) {
            for (let i = 1; i <= totalPages; i++) {
                pages.push(i);
            }
        } else {
            pages.push(1);
            
            let start = Math.max(2, currentPage - 1);
            let end = Math.min(totalPages - 1, currentPage + 1);
            
            if (start > 2) pages.push('...');
            
            for (let i = start; i <= end; i++) {
                pages.push(i);
            }
            
            if (end < totalPages - 1) pages.push('...');
            
            pages.push(totalPages);
        }

        return pages;
    }
}

// ✅ FIX #5: Lazy initialization instead of eager
// Create only when first table is detected, not on script load
// This eliminates observer overhead during page startup

let autoPaginationInstance = null;

window.getAutoPagination = function() {
    if (!autoPaginationInstance) {
        autoPaginationInstance = new AutoTablePagination({
            itemsPerPage: 10,
            autoInit: false  // Don't auto-init in constructor
        });
        // Initialize on-demand
        autoPaginationInstance.findAndPaginateTables();
    }
    return autoPaginationInstance;
};

// Initialize only if tables exist on the page
if (document.querySelector('table')) {
    window.getAutoPagination();
}

// For backward compatibility
Object.defineProperty(window, 'autoPagination', {
    get: function() {
        return window.getAutoPagination();
    }
});
