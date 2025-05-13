/**
 * Toggles between categorized and flat list views
 */
document.addEventListener('DOMContentLoaded', function() {
    const categoryToggleBtn = document.getElementById('category-toggle-btn');
    
    if (!categoryToggleBtn) return;
    
    categoryToggleBtn.addEventListener('click', function() {
        // Show loading state on button
        const originalText = categoryToggleBtn.innerHTML;
        categoryToggleBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Loading...';
        categoryToggleBtn.disabled = true;
        
        // Get CSRF token
        const csrfToken = getCSRFToken();
        
        // Current state is embedded in the button text
        const currentShowCategories = categoryToggleBtn.textContent.includes('Flat List');
        
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
            // Reload the page to show the updated view
            window.location.reload();
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
    
    // Helper function to get CSRF token
    function getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue;
    }
});