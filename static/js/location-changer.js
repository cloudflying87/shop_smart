/**
 * Handles changing the location of shopping list items
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get all location change buttons
    const locationButtons = document.querySelectorAll('.change-location-btn');
    const locationModal = document.getElementById('location-modal');
    const saveLocationBtn = document.getElementById('save-location-btn');
    
    // Add event listeners to location change buttons
    locationButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const itemId = this.dataset.itemId;
            const listId = this.dataset.listId;
            const itemName = this.closest('.list-item').querySelector('.item-name').textContent;
            
            // Set values in the modal
            document.getElementById('location-item-id').value = itemId;
            document.getElementById('location-list-id').value = listId;
            document.getElementById('location-modal-title').textContent = `Change Location: ${itemName}`;
            
            // Get current location if exists
            const listItem = this.closest('.list-item');
            const currentLocation = listItem.closest('.location-section')?.querySelector('.location-header')?.textContent;
            
            // Set current location in select if it exists
            if (currentLocation) {
                const locationSelect = document.getElementById('location-select');
                Array.from(locationSelect.options).forEach(option => {
                    if (option.textContent === currentLocation) {
                        locationSelect.value = option.value;
                    }
                });
            }
            
            // Show modal
            locationModal.classList.add('active');
        });
    });
    
    // Handle save button click
    saveLocationBtn.addEventListener('click', function() {
        const itemId = document.getElementById('location-item-id').value;
        const listId = document.getElementById('location-list-id').value;
        const locationId = document.getElementById('location-select').value;
        
        // Create form data
        const formData = new FormData();
        formData.append('location_id', locationId);
        formData.append('csrfmiddlewaretoken', getCSRFToken());
        
        // Send request to server
        fetch(`/app/lists/${listId}/items/${itemId}/location/`, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close modal
                locationModal.classList.remove('active');
                
                // Reload page to reflect new location
                window.location.reload();
            } else {
                console.error('Error changing location:', data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
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