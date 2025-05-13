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
    
    // Category toggle removed - using flat view only
    
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
        
        // Category toggle button removed
        
        // Always use flat view
        showFlatListView();
        
        // Store the current mode in localStorage
        localStorage.setItem('shoppingListMode', 'edit');
        
        // Using flat view only
        
        // Reinitialize checkbox listeners after mode change
        if (typeof initializeCheckboxListeners === 'function') {
            setTimeout(initializeCheckboxListeners, 50);
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
        
        // Category toggle button removed
        
        // Always use flat list in store mode
        showFlatListView();
        
        // Store the current mode in localStorage
        localStorage.setItem('shoppingListMode', 'inStore');
        
        // Reinitialize checkbox listeners after mode change
        if (typeof initializeCheckboxListeners === 'function') {
            setTimeout(initializeCheckboxListeners, 50);
        }
    }
    
    // Categorized view removed - using flat view only
    
    // Function to show flat list view
    function showFlatListView() {
        // Show flat view container
        const flatView = document.querySelector('.flat-view');
        if (flatView) flatView.style.display = 'block';
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
    
    // Always use flat view
    localStorage.setItem('showCategories', 'false');
    showFlatListView();
});