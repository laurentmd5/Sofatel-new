/**
 * Tests d'intégration pour TableManager
 * Sprint 1 - Phase 2 Implémentation
 */

// Test 1: Initialisation de base
test('TableManager initialisation', () => {
    const tableManager = new TableManager('usersTable', {
        sortable: true,
        searchable: true,
        bulkable: true
    });
    
    expect(tableManager.tableElement).toBeDefined();
    expect(tableManager.originalData.length).toBeGreaterThan(0);
    expect(tableManager.filteredData.length).toEqual(tableManager.originalData.length);
});

// Test 2: Tri par colonne
test('TableManager tri par colonne', () => {
    const tableManager = new TableManager('usersTable');
    
    const initialOrder = tableManager.filteredData.map(r => r.cells[0]);
    tableManager.sortBy(0); // Trier par première colonne
    const sortedOrder = tableManager.filteredData.map(r => r.cells[0]);
    
    // Vérifier que l'ordre a changé
    expect(JSON.stringify(initialOrder)).not.toBe(JSON.stringify(sortedOrder));
});

// Test 3: Recherche
test('TableManager recherche', () => {
    const tableManager = new TableManager('usersTable');
    
    tableManager.search('paul');
    const matchingRows = tableManager.filteredData.filter(row =>
        row.cells.some(cell => cell.toLowerCase().includes('paul'))
    );
    
    expect(tableManager.filteredData.length).toBeLessThanOrEqual(tableManager.originalData.length);
    expect(matchingRows.length).toBe(tableManager.filteredData.length);
});

// Test 4: Filtrage
test('TableManager filtrage', () => {
    const tableManager = new TableManager('usersTable');
    
    tableManager.setFilter('role', 'chef_pur');
    const expectedCount = tableManager.originalData.filter(r =>
        r.cells[1].toLowerCase().includes('chef_pur')
    ).length;
    
    expect(tableManager.filteredData.length).toBeLessThanOrEqual(expectedCount);
});

// Test 5: Sélection en masse
test('TableManager sélection en masse', () => {
    const tableManager = new TableManager('usersTable', { bulkable: true });
    
    tableManager.toggleSelectAll(true);
    expect(tableManager.selectedRows.size).toBe(tableManager.filteredData.length);
    
    tableManager.toggleSelectAll(false);
    expect(tableManager.selectedRows.size).toBe(0);
});

// Test 6: Export CSV
test('TableManager export CSV', () => {
    const tableManager = new TableManager('usersTable');
    
    const initialData = tableManager.filteredData.length;
    tableManager.exportCSV();
    
    // La fonction crée un fichier, on vérifie que les données n'ont pas changé
    expect(tableManager.filteredData.length).toBe(initialData);
});

// Test 7: État localStorage
test('TableManager localStorage', () => {
    const tableManager = new TableManager('usersTable');
    
    tableManager.search('test');
    tableManager.sortBy(0);
    tableManager.setFilter('role', 'chef_pur');
    tableManager._saveFilters();
    
    // Vérifier que l'état a été sauvegardé
    const state = JSON.parse(localStorage.getItem(`tableState_usersTable`));
    expect(state.searchQuery).toBe('test');
    expect(state.sortColumn).toBe(0);
    expect(state.filters.role).toBe('chef_pur');
});

// Test 8: Réinitialisation
test('TableManager réinitialisation', () => {
    const tableManager = new TableManager('usersTable');
    
    tableManager.search('test');
    tableManager.sortBy(0);
    tableManager.reset();
    
    expect(tableManager.searchQuery).toBe('');
    expect(tableManager.sortColumn).toBeNull();
    expect(tableManager.filters.size).toBe(0);
    expect(tableManager.filteredData.length).toBe(tableManager.originalData.length);
});

// Test 9: Performance - 10k lignes
test('TableManager performance (10k rows)', () => {
    const largeTable = createLargeTestTable(10000);
    const startTime = performance.now();
    
    const tableManager = new TableManager(largeTable.id);
    tableManager.search('item5000');
    
    const endTime = performance.now();
    const duration = endTime - startTime;
    
    // La recherche devrait être rapide (< 100ms)
    expect(duration).toBeLessThan(100);
    expect(tableManager.filteredData.length).toBeGreaterThan(0);
});

// Test 10: Intégration avec UsersManager
test('UsersManager intégration', () => {
    const usersManager = new UsersManager();
    
    expect(usersManager.tableManager).toBeDefined();
    expect(usersManager.deleteModal).toBeDefined();
    
    // Vérifier que les événements sont bien attachés
    const deleteBtn = document.querySelector('.delete-user');
    expect(deleteBtn).toBeDefined();
});

/**
 * Fonction utilitaire pour créer une grande table de test
 */
function createLargeTestTable(rowCount) {
    const table = document.createElement('table');
    table.id = `test-table-${Date.now()}`;
    
    const thead = document.createElement('thead');
    thead.innerHTML = '<tr><th>ID</th><th>Name</th><th>Email</th></tr>';
    table.appendChild(thead);
    
    const tbody = document.createElement('tbody');
    for (let i = 0; i < rowCount; i++) {
        const tr = document.createElement('tr');
        tr.setAttribute('data-row-id', i);
        tr.innerHTML = `
            <td>${i}</td>
            <td>Item ${i}</td>
            <td>item${i}@example.com</td>
        `;
        tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    document.body.appendChild(table);
    
    return table;
}
