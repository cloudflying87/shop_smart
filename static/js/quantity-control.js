/**
 * Handles quantity adjustments for shopping list items
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get all quantity increase and decrease buttons
    const increaseButtons = document.querySelectorAll('.quantity-increase');
    const decreaseButtons = document.querySelectorAll('.quantity-decrease');

    // Add event listeners for increase buttons
    increaseButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const itemId = this.dataset.itemId;
            const listId = this.dataset.listId;
            updateQuantity(itemId, listId, 'increase');
        });
    });

    // Add event listeners for decrease buttons
    decreaseButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            const itemId = this.dataset.itemId;
            const listId = this.dataset.listId;
            updateQuantity(itemId, listId, 'decrease');
        });
    });

    // Function to update quantity
    function updateQuantity(itemId, listId, action) {
        // Get current quantity
        const listItem = document.querySelector(`.list-item[data-item-id="${itemId}"]`);
        if (!listItem) return;

        const quantityElement = listItem.querySelector('.item-quantity');
        if (!quantityElement) return;
        
        // Parse current quantity - handle both "2" and "2 kg" formats
        let quantityText = quantityElement.textContent.trim();
        let unit = '';
        
        // Check if there's a unit
        if (quantityText.includes(' ')) {
            const parts = quantityText.split(' ');
            quantityText = parts[0];
            unit = parts.slice(1).join(' ');
        }
        
        let quantity = parseFloat(quantityText);
        
        // Calculate new quantity
        let newQuantity;
        if (action === 'increase') {
            if (quantity < 1) {
                // If less than 1, increment by 0.1 or 0.25 depending on value
                newQuantity = (quantity * 10 % 25 === 0) ? 
                    quantity + 0.25 : 
                    Math.round((quantity + 0.1) * 10) / 10;
            } else {
                // If 1 or greater, increment by 1
                newQuantity = quantity + 1;
            }
        } else { // decrease
            if (quantity <= 1) {
                // If 1 or less, decrement by 0.1 or 0.25 depending on value
                newQuantity = (quantity * 10 % 25 === 0) ? 
                    Math.max(0.25, quantity - 0.25) : 
                    Math.max(0.1, Math.round((quantity - 0.1) * 10) / 10);
            } else {
                // If greater than 1, decrement by 1
                newQuantity = quantity - 1;
            }
        }
        
        // Format the quantity with 1 decimal place if needed
        let formattedQuantity = newQuantity % 1 === 0 ? 
            newQuantity : 
            newQuantity.toFixed(1);
            
        // Update UI immediately for better responsiveness
        quantityElement.textContent = unit ? `${formattedQuantity} ${unit}` : formattedQuantity;
        
        // Create form data
        const formData = new FormData();
        formData.append('quantity', formattedQuantity);
        formData.append('csrfmiddlewaretoken', getCSRFToken());
        
        // Send request to server
        fetch(`/app/lists/${listId}/items/${itemId}/quantity/`, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error('Error updating quantity:', data.error);
                // Revert UI change on error
                quantityElement.textContent = unit ? `${quantity} ${unit}` : quantity;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            // Revert UI change on error
            quantityElement.textContent = unit ? `${quantity} ${unit}` : quantity;
        });
    }
    
    // Helper function to get CSRF token
    function getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue;
    }
});