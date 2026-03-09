/**
 * TableManager - Gestion interactive des tables
 * Tri, filtrage, multi-sélection, bulk actions
 */

class TableManager {
  constructor(tableId, options = {}) {
    this.tableId = tableId;
    this.table = document.getElementById(tableId);
    if (!this.table) {
      console.error(`Table ${tableId} not found`);
      return;
    }

    this.originalData = [];
    this.filteredData = [];
    this.selectedRows = new Set();
    
    this.sortColumn = options.sortColumn || null;
    this.sortOrder = options.sortOrder || 'asc';
    this.filters = {};
    this.searchQuery = '';
    
    this.localStorageKey = options.localStorageKey || `table-${tableId}`;
    this.enableLocalStorage = options.enableLocalStorage !== false;
    this.enableExport = options.enableExport !== false;
    
    this.init();
  }

  /**
   * Initialisation
   */
  init() {
    this.extractTableData();
    this.setupEventListeners();
    this.restoreFilters();
  }

  /**
   * Extraire données du DOM
   */
  extractTableData() {
    const tbody = this.table.querySelector('tbody');
    if (!tbody) return;

    this.originalData = Array.from(tbody.querySelectorAll('tr')).map((row, idx) => ({
      id: row.dataset.rowId || idx,
      element: row,
      cells: Array.from(row.querySelectorAll('td')).map(td => td.textContent.trim())
    }));

    this.filteredData = [...this.originalData];
  }

  /**
   * Setup event listeners pour tri
   */
  setupEventListeners() {
    // Tri sur en-têtes cliquables
    this.table.querySelectorAll('th[data-column]').forEach(th => {
      th.style.cursor = 'pointer';
      th.addEventListener('click', () => this.sortBy(th.dataset.column));
    });

    // Checkboxes multi-sélection
    const masterCheckbox = this.table.querySelector('th input[type="checkbox"]');
    if (masterCheckbox) {
      masterCheckbox.addEventListener('change', (e) => this.toggleSelectAll(e.target.checked));
    }

    this.table.querySelectorAll('tbody input[type="checkbox"][data-row-id]').forEach(checkbox => {
      checkbox.addEventListener('change', (e) => {
        const rowId = e.target.dataset.rowId;
        e.target.checked ? this.selectedRows.add(rowId) : this.selectedRows.delete(rowId);
        this.updateBulkActions();
      });
    });

    // Recherche en temps réel
    const searchInput = document.querySelector(`[data-search-for="${this.tableId}"]`);
    if (searchInput) {
      searchInput.addEventListener('input', (e) => this.search(e.target.value));
    }

    // Filtres
    this.table.querySelectorAll('[data-filter]').forEach(filter => {
      filter.addEventListener('change', (e) => {
        const column = e.target.dataset.filterColumn;
        const value = e.target.value;
        this.setFilter(column, value);
      });
    });
  }

  /**
   * Tri par colonne
   */
  sortBy(column) {
    if (this.sortColumn === column) {
      this.sortOrder = this.sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
      this.sortColumn = column;
      this.sortOrder = 'asc';
    }

    this.filteredData.sort((a, b) => {
      const aVal = a.cells[column] || '';
      const bVal = b.cells[column] || '';

      // Tri numérique si valeurs sont des nombres
      const aNum = parseFloat(aVal);
      const bNum = parseFloat(bVal);

      if (!isNaN(aNum) && !isNaN(bNum)) {
        return this.sortOrder === 'asc' ? aNum - bNum : bNum - aNum;
      }

      // Tri alphabétique
      return this.sortOrder === 'asc'
        ? aVal.localeCompare(bVal, 'fr')
        : bVal.localeCompare(aVal, 'fr');
    });

    this.render();
    this.saveFilters();
    this.updateSortIndicators();
  }

  /**
   * Recherche
   */
  search(query) {
    this.searchQuery = query.toLowerCase();
    this.applyFilters();
  }

  /**
   * Filtrer par colonne
   */
  setFilter(column, value) {
    if (value) {
      this.filters[column] = value;
    } else {
      delete this.filters[column];
    }
    this.applyFilters();
    this.saveFilters();
  }

  /**
   * Appliquer tous les filtres
   */
  applyFilters() {
    this.filteredData = this.originalData.filter(row => {
      // Filtres colonnes
      for (const [column, filterValue] of Object.entries(this.filters)) {
        if (row.cells[column]?.toLowerCase() !== filterValue.toLowerCase()) {
          return false;
        }
      }

      // Recherche full-text
      if (this.searchQuery) {
        const matchesSearch = row.cells.some(cell =>
          cell.toLowerCase().includes(this.searchQuery)
        );
        if (!matchesSearch) return false;
      }

      return true;
    });

    this.render();
  }

  /**
   * Multi-sélection: tous/aucun
   */
  toggleSelectAll(checked) {
    this.filteredData.forEach(row => {
      const checkbox = this.table.querySelector(`input[data-row-id="${row.id}"]`);
      if (checkbox) {
        checkbox.checked = checked;
        checked ? this.selectedRows.add(row.id) : this.selectedRows.delete(row.id);
      }
    });
    this.updateBulkActions();
  }

  /**
   * Mettre à jour UI actions bulk
   */
  updateBulkActions() {
    const bulkActionsContainer = document.querySelector(`[data-bulk-actions-for="${this.tableId}"]`);
    if (!bulkActionsContainer) return;

    const count = this.selectedRows.size;
    bulkActionsContainer.style.display = count > 0 ? 'flex' : 'none';
    bulkActionsContainer.querySelector('[data-count]').textContent = count;
  }

  /**
   * Afficher/masquer colonnes
   */
  toggleColumn(columnIndex, visible) {
    this.table.querySelectorAll(`th:nth-child(${columnIndex + 1}), td:nth-child(${columnIndex + 1})`).forEach(el => {
      el.style.display = visible ? '' : 'none';
    });
  }

  /**
   * Export CSV
   */
  exportCSV() {
    const rows = this.filteredData.map(row => row.cells.join(','));
    const csv = rows.join('\n');
    this.downloadFile(csv, 'data.csv', 'text/csv');
  }

  /**
   * Export JSON
   */
  exportJSON() {
    const data = this.filteredData.map(row => ({
      id: row.id,
      data: row.cells
    }));
    const json = JSON.stringify(data, null, 2);
    this.downloadFile(json, 'data.json', 'application/json');
  }

  /**
   * Télécharger fichier
   */
  downloadFile(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  /**
   * Sauvegarder filtres en localStorage
   */
  saveFilters() {
    if (!this.enableLocalStorage) return;
    const state = {
      filters: this.filters,
      sortColumn: this.sortColumn,
      sortOrder: this.sortOrder,
      searchQuery: this.searchQuery
    };
    localStorage.setItem(this.localStorageKey, JSON.stringify(state));
  }

  /**
   * Restaurer filtres depuis localStorage
   */
  restoreFilters() {
    if (!this.enableLocalStorage) return;
    const saved = localStorage.getItem(this.localStorageKey);
    if (!saved) return;

    const state = JSON.parse(saved);
    this.filters = state.filters || {};
    this.sortColumn = state.sortColumn;
    this.sortOrder = state.sortOrder;
    this.searchQuery = state.searchQuery || '';

    // Restaurer valeurs dans UI
    Object.entries(this.filters).forEach(([column, value]) => {
      const filterEl = this.table.querySelector(`[data-filter-column="${column}"]`);
      if (filterEl) filterEl.value = value;
    });

    const searchEl = document.querySelector(`[data-search-for="${this.tableId}"]`);
    if (searchEl) searchEl.value = this.searchQuery;

    this.applyFilters();
  }

  /**
   * Mettre à jour les indicateurs visuels de tri
   */
  updateSortIndicators() {
    this.table.querySelectorAll('th[data-column]').forEach(th => {
      th.classList.remove('sorted-asc', 'sorted-desc');
      if (th.dataset.column === this.sortColumn) {
        th.classList.add(`sorted-${this.sortOrder}`);
      }
    });
  }

  /**
   * Rendre le tableau avec les données filtrées
   */
  render() {
    const tbody = this.table.querySelector('tbody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (this.filteredData.length === 0) {
      const emptyRow = `
        <tr class="table-empty-state">
          <td colspan="100%" class="text-center py-4">
            <i data-feather="inbox" class="text-muted mb-2"></i>
            <p class="text-muted">Aucun résultat</p>
          </td>
        </tr>
      `;
      tbody.innerHTML = emptyRow;
      feather.replace(); // Recharger les icônes
      return;
    }

    this.filteredData.forEach((row, idx) => {
      const tr = document.createElement('tr');
      tr.dataset.rowId = row.id;
      tr.className = 'table-row-item';

      // Checkbox pour sélection
      const checkboxCell = document.createElement('td');
      checkboxCell.innerHTML = `<input type="checkbox" data-row-id="${row.id}" class="form-check-input">`;

      tr.appendChild(checkboxCell);

      // Autres cellules
      row.cells.forEach(cell => {
        const td = document.createElement('td');
        td.textContent = cell;
        tr.appendChild(td);
      });

      tbody.appendChild(tr);
    });

    // Rebind checkboxes pour nouvelles lignes
    this.table.querySelectorAll('tbody input[type="checkbox"][data-row-id]').forEach(checkbox => {
      checkbox.removeEventListener('change', null);
      checkbox.addEventListener('change', (e) => {
        const rowId = e.target.dataset.rowId;
        e.target.checked ? this.selectedRows.add(rowId) : this.selectedRows.delete(rowId);
        this.updateBulkActions();
      });

      // Restaurer état de sélection
      if (this.selectedRows.has(checkbox.dataset.rowId)) {
        checkbox.checked = true;
      }
    });

    feather.replace(); // Recharger les icônes Feather
  }

  /**
   * Réinitialiser tous les filtres
   */
  reset() {
    this.filters = {};
    this.searchQuery = '';
    this.sortColumn = null;
    this.sortOrder = 'asc';
    this.selectedRows.clear();
    
    const searchEl = document.querySelector(`[data-search-for="${this.tableId}"]`);
    if (searchEl) searchEl.value = '';

    localStorage.removeItem(this.localStorageKey);
    this.filteredData = [...this.originalData];
    this.render();
  }

  /**
   * Obtenir les lignes sélectionnées
   */
  getSelectedRows() {
    return Array.from(this.selectedRows).map(id =>
      this.originalData.find(row => row.id === id)
    ).filter(Boolean);
  }

  /**
   * Supprimer lignes sélectionnées
   */
  deleteSelected() {
    if (!confirm(`Supprimer ${this.selectedRows.size} éléments?`)) return;
    
    this.selectedRows.forEach(id => {
      const row = this.originalData.find(r => r.id === id);
      if (row) {
        row.element.remove();
        const idx = this.originalData.indexOf(row);
        if (idx > -1) this.originalData.splice(idx, 1);
      }
    });

    this.selectedRows.clear();
    this.filteredData = this.filteredData.filter(row => !this.selectedRows.has(row.id));
    this.render();
    this.updateBulkActions();
    Toast.success(`${this.selectedRows.size} éléments supprimés`);
  }
}

// Export global
window.TableManager = TableManager;
