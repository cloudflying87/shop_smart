/**
 * Toggles between categorized and flat list views in Edit mode
 */
document.addEventListener('DOMContentLoaded', function() {
    const categoryToggleBtn = document.getElementById('category-toggle-btn');
    
    if (!categoryToggleBtn) return;
    
    // View containers
    const categorizedView = document.querySelector('.categorized-view');
    const flatView = document.querySelector('.flat-view');
    
    // Get initial preference from Django template
    // If button text contains "Flat List", that means categories are currently shown
    const initialShowCategories = categoryToggleBtn.textContent.trim().includes('Flat List');
    
    // Save to localStorage on initial load
    if (typeof localStorage !== 'undefined') {
        localStorage.setItem('showCategories', initialShowCategories.toString());
    }
    
    // Update button text based on current view
    function updateToggleButtonText(showCategories) {
        if (showCategories) {
            categoryToggleBtn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" class="mr-1">
                    <path fill="none" d="M0 0h24v24H0z"/>
                    <path d="M3 4h18v2H3V4zm0 7h12v2H3v-2zm0 7h18v2H3v-2z" fill="currentColor"/>
                </svg>
                Flat List
            `;
        } else {
            categoryToggleBtn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" class="mr-1">
                    <path fill="none" d="M0 0h24v24H0z"/>
                    <path d="M3 4h18v2H3V4zm0 7h12v2H3v-2zm0 7h18v2H3v-2z" fill="currentColor"/>
                </svg>
                Categories
            `;
        }
    }
    
    // Function to set the active view
    function setActiveView() {
        const showCategories = localStorage.getItem('showCategories') === 'true';
        const inStoreMode = localStorage.getItem('shoppingListMode') === 'inStore';
        
        // In store mode, always use flat list
        if (inStoreMode) {
            if (categorizedView) categorizedView.style.display = 'none';
            if (flatView) flatView.style.display = 'block';
            return;
        }
        
        // In edit mode, respect user preference
        if (showCategories) {
            if (categorizedView) categorizedView.style.display = 'block';
            if (flatView) flatView.style.display = 'none';
            updateToggleButtonText(true);
        } else {
            if (categorizedView) categorizedView.style.display = 'none';
            if (flatView) flatView.style.display = 'block';
            updateToggleButtonText(false);
        }
    }
    
    // Toggle view function
    function toggleView() {
        const currentShowCategories = localStorage.getItem('showCategories') === 'true';
        localStorage.setItem('showCategories', (!currentShowCategories).toString());
        setActiveView();
    }
    
    // Add click handler
    categoryToggleBtn.addEventListener('click', function() {
        // Only allow toggling in edit mode
        if (localStorage.getItem('shoppingListMode') !== 'edit') return;
        
        // Show loading state on button
        const originalText = categoryToggleBtn.innerHTML;
        categoryToggleBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
        categoryToggleBtn.disabled = true;
        
        // Get CSRF token
        const csrfToken = getCSRFToken();
        
        // Current state from localStorage
        const currentShowCategories = localStorage.getItem('showCategories') === 'true';
        
        // Send request to server to update user preference
        fetch('/app/profile/toggle-categories/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                show_categories: !currentShowCategories
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            // Toggle view
            toggleView();
            // Re-enable button
            categoryToggleBtn.disabled = false;
        })
        .catch(error => {
            console.error('Error:', error);
            // Restore button state
            categoryToggleBtn.innerHTML = originalText;
            categoryToggleBtn.disabled = false;
            // Show error toast
            if (typeof toastNotification === 'function') {
                toastNotification('Error toggling view mode', 'error');
            }
        });
    });
    
    // Set initial view on page load
    setActiveView();
    
    // Debug log for data validation
    console.log("Categorized view has items:", categorizedView && categorizedView.querySelectorAll('.list-item').length > 0);
    console.log("Flat view has items:", flatView && flatView.querySelectorAll('.list-item').length > 0);
    
    // Helper function to get CSRF token
    function getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue;
    }
});