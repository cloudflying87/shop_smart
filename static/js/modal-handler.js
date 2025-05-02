/**
 * Modal Handler JS
 * Handles displaying and hiding modals
 */

document.addEventListener('DOMContentLoaded', function() {
    // Find all elements that should trigger a modal
    const modalTriggers = document.querySelectorAll('[data-toggle="modal"]');
    
    modalTriggers.forEach(trigger => {
        const targetSelector = trigger.getAttribute('data-target');
        const modal = document.querySelector(targetSelector);
        
        if (!modal) return;
        
        const closeButtons = modal.querySelectorAll('.modal-close, [data-dismiss="modal"]');
        const overlay = modal.querySelector('.modal-overlay');
        
        // Open modal when trigger is clicked
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            modal.classList.add('active');
            document.body.classList.add('modal-open');
        });
        
        // Close modal when close button is clicked
        closeButtons.forEach(button => {
            button.addEventListener('click', function() {
                modal.classList.remove('active');
                document.body.classList.remove('modal-open');
            });
        });
        
        // Close modal when overlay is clicked
        if (overlay) {
            overlay.addEventListener('click', function() {
                modal.classList.remove('active');
                document.body.classList.remove('modal-open');
            });
        }
        
        // Close modal when ESC key is pressed
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modal.classList.contains('active')) {
                modal.classList.remove('active');
                document.body.classList.remove('modal-open');
            }
        });
    });
    
    // Get CSRF token for AJAX requests
    window.getCSRFToken = function() {
        return document.cookie.split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1] || '';
    };
});