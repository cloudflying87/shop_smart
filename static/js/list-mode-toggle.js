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
        
        // Store the current mode in localStorage
        localStorage.setItem('shoppingListMode', 'edit');
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
        
        // Store the current mode in localStorage
        localStorage.setItem('shoppingListMode', 'inStore');
    }
    
    // Add event listeners to the buttons
    if (editModeBtn) {
        editModeBtn.addEventListener('click', activateEditMode);
    }
    
    if (inStoreModeBtn) {
        inStoreModeBtn.addEventListener('click', activateInStoreMode);
    }
    
    // Initialize the mode based on localStorage or default to edit mode
    const savedMode = localStorage.getItem('shoppingListMode');
    if (savedMode === 'inStore') {
        activateInStoreMode();
    } else {
        activateEditMode();
    }
});