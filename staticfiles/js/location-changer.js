/**
 * Handles changing the location of shopping list items
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("Location changer script loaded!");
    
    // Get all location change buttons
    const locationButtons = document.querySelectorAll('.change-location-btn');
    console.log(`Found ${locationButtons.length} location buttons`);
    
    const locationModal = document.getElementById('location-modal');
    const saveLocationBtn = document.getElementById('save-location-btn');
    
    // Add event listeners to location change buttons
    locationButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            console.log("Location button clicked");
            e.preventDefault();
            e.stopPropagation();
            
            const itemId = this.dataset.itemId;
            const listId = this.dataset.listId;
            const itemName = this.closest('.list-item').querySelector('.item-name').textContent;
            const locationId = this.dataset.locationId;
            
            console.log(`Opening location modal for item: ${itemName} (ID: ${itemId}, List: ${listId}, Location: ${locationId})`);
            
            // Set values in the modal
            document.getElementById('location-item-id').value = itemId;
            document.getElementById('location-list-id').value = listId;
            document.getElementById('location-modal-title').textContent = `Change Location: ${itemName}`;
            
            // Set the current location in the select dropdown
            const locationSelect = document.getElementById('location-select');
            if (locationId) {
                console.log(`Setting location dropdown to ID: ${locationId}`);
                locationSelect.value = locationId;
            } else {
                console.log("No location ID found, using default empty value");
                locationSelect.value = '';
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