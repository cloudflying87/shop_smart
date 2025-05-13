/**
 * Handles the toggle between Edit mode and In-store mode for shopping lists
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get the mode toggle buttons
    const editModeBtn = document.getElementById('edit-mode-btn');
    const inStoreModeBtn = document.getElementById('in-store-mode-btn');
    
    // Get the content sections
    const editModeContent = document.getElementById('edit-mode-content');
    const inStoreModeContent = document.getElementById('in-store-mode-content');
    
    // Get the category toggle button
    const categoryToggleBtn = document.getElementById('category-toggle-btn');
    const categoryToggleContainer = document.querySelector('.category-toggle-container');
    
    // Find the location headers for category sections
    const locationHeaders = document.querySelectorAll('.location-header');
    
    // Category sections
    const categorySections = document.querySelectorAll('.location-section');
    const flatList = document.getElementById('flat-list');
    
    // Function to switch to Edit mode
    function activateEditMode() {
        // Update button states
        editModeBtn.classList.add('active');
        inStoreModeBtn.classList.remove('active');
        
        // Show/hide appropriate content
        if (editModeContent) editModeContent.style.display = 'block';
        if (inStoreModeContent) inStoreModeContent.style.display = 'none';
        
        // Show edit-mode-only elements
        document.querySelectorAll('.edit-mode-only').forEach(el => {
            el.style.display = 'block';
        });
        
        // Show category toggle button
        if (categoryToggleContainer) {
            categoryToggleContainer.style.display = 'flex';
        }
        
        // Apply category or flat view based on user preference
        const userPrefersCategorized = localStorage.getItem('showCategories') === 'true';
        
        if (userPrefersCategorized) {
            showCategorizedView();
        } else {
            showFlatListView();
        }
        
        // Store the current mode in localStorage
        localStorage.setItem('shoppingListMode', 'edit');
        
        // Make sure location headers are visible if in categorized view
        if (userPrefersCategorized) {
            locationHeaders.forEach(header => {
                header.style.display = 'block';
            });
        }
    }
    
    // Function to switch to In-store mode
    function activateInStoreMode() {
        // Update button states
        editModeBtn.classList.remove('active');
        inStoreModeBtn.classList.add('active');
        
        // Show/hide appropriate content
        if (editModeContent) editModeContent.style.display = 'none';
        if (inStoreModeContent) inStoreModeContent.style.display = 'block';
        
        // Hide edit-mode-only elements
        document.querySelectorAll('.edit-mode-only').forEach(el => {
            el.style.display = 'none';
        });
        
        // Hide category toggle button in in-store mode
        if (categoryToggleContainer) {
            categoryToggleContainer.style.display = 'none';
        }
        
        // Always use flat list in store mode
        showFlatListView();
        
        // Store the current mode in localStorage
        localStorage.setItem('shoppingListMode', 'inStore');
    }
    
    // Function to show categorized view (with headers)
    function showCategorizedView() {
        // Show categorized view container and hide flat view container
        const categorizedView = document.querySelector('.categorized-view');
        const flatView = document.querySelector('.flat-view');
        
        if (categorizedView) categorizedView.style.display = 'block';
        if (flatView) flatView.style.display = 'none';
        
        // Make sure headers are visible
        locationHeaders.forEach(header => {
            header.style.display = 'block';
        });
    }
    
    // Function to show flat list view (without headers)
    function showFlatListView() {
        // Show flat view container and hide categorized view container
        const categorizedView = document.querySelector('.categorized-view');
        const flatView = document.querySelector('.flat-view');
        
        if (categorizedView) categorizedView.style.display = 'none';
        if (flatView) flatView.style.display = 'block';
        
        // In store mode, ensure headers remain hidden
        if (localStorage.getItem('shoppingListMode') === 'inStore') {
            locationHeaders.forEach(header => {
                header.style.display = 'none';
            });
        }
    }
    
    // Add event listeners to the buttons
    if (editModeBtn) {
        editModeBtn.addEventListener('click', activateEditMode);
    }
    
    if (inStoreModeBtn) {
        inStoreModeBtn.addEventListener('click', activateInStoreMode);
    }
    
    // Make sure flat list view is visible immediately on script load 
    // to prevent flash of empty screen
    if (flatList) {
        const flatViewContainer = document.querySelector('.flat-view');
        if (flatViewContainer) {
            flatViewContainer.style.display = 'block';
        }
    }
    
    // Initialize the mode based on localStorage or default to edit mode
    const savedMode = localStorage.getItem('shoppingListMode');
    if (savedMode === 'inStore') {
        activateInStoreMode();
    } else {
        activateEditMode();
    }
    
    // Store the initial setting of show_categories
    if (categoryToggleBtn) {
        const initialShowCategories = categoryToggleBtn.textContent.trim().includes('Flat List');
        localStorage.setItem('showCategories', initialShowCategories.toString());
        
        // After localStorage is set, call the appropriate view function again
        if (initialShowCategories && localStorage.getItem('shoppingListMode') === 'edit') {
            showCategorizedView();
        } else {
            showFlatListView();
        }
    }
});