/**
 * Handles editing notes for shopping list items
 */
document.addEventListener('DOMContentLoaded', function() {
    // Get all note edit buttons
    const noteButtons = document.querySelectorAll('.edit-note-btn');
    const noteModal = document.getElementById('note-modal');
    const saveNoteBtn = document.getElementById('save-note-btn');
    
    // Add event listeners to note edit buttons
    noteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const itemId = this.dataset.itemId;
            const listId = this.dataset.listId;
            const itemName = this.dataset.itemName;
            const currentNote = this.dataset.note || '';
            
            // Set values in the modal
            document.getElementById('note-item-id').value = itemId;
            document.getElementById('note-list-id').value = listId;
            document.getElementById('note-modal-title').textContent = `Note: ${itemName}`;
            document.getElementById('note-input').value = currentNote;
            
            // Show modal
            noteModal.classList.add('active');
            
            // Focus textarea
            setTimeout(() => {
                document.getElementById('note-input').focus();
            }, 100);
        });
    });
    
    // Handle save button click
    saveNoteBtn.addEventListener('click', function() {
        const itemId = document.getElementById('note-item-id').value;
        const listId = document.getElementById('note-list-id').value;
        const note = document.getElementById('note-input').value;
        
        // Create form data
        const formData = new FormData();
        formData.append('note', note);
        formData.append('csrfmiddlewaretoken', getCSRFToken());
        
        // Send request to server
        fetch(`/app/lists/${listId}/items/${itemId}/note/`, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close modal
                noteModal.classList.remove('active');
                
                // Update UI
                const listItem = document.querySelector(`.list-item[data-item-id="${itemId}"]`);
                if (listItem) {
                    const itemContent = listItem.querySelector('.item-content');
                    let noteElement = itemContent.querySelector('.item-note');
                    
                    if (note) {
                        if (!noteElement) {
                            noteElement = document.createElement('div');
                            noteElement.className = 'item-note';
                            itemContent.appendChild(noteElement);
                        }
                        noteElement.textContent = note;
                        
                        // Update button data attribute
                        const noteButton = listItem.querySelector('.edit-note-btn');
                        if (noteButton) {
                            noteButton.dataset.note = note;
                        }
                    } else if (noteElement) {
                        // Remove note element if note is empty
                        itemContent.removeChild(noteElement);
                        
                        // Update button data attribute
                        const noteButton = listItem.querySelector('.edit-note-btn');
                        if (noteButton) {
                            noteButton.dataset.note = '';
                        }
                    }
                }
                
                // Show toast notification
                toastNotification('Note updated');
            } else {
                console.error('Error updating note:', data.error);
                toastNotification('Error updating note', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            toastNotification('Error updating note', 'error');
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
    
    // Toast notification function if not already defined
    if (typeof toastNotification !== 'function') {
        window.toastNotification = function(message, type = 'success') {
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.textContent = message;
            document.body.appendChild(toast);
            
            // Animate in
            setTimeout(() => {
                toast.classList.add('active');
            }, 10);
            
            // Remove after 3 seconds
            setTimeout(() => {
                toast.classList.remove('active');
                setTimeout(() => {
                    document.body.removeChild(toast);
                }, 300);
            }, 3000);
        };
    }
});