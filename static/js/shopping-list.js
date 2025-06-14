/**
 * Main shopping list functionality
 */
// Define a global function to initialize all checkbox listeners
function initializeCheckboxListeners() {
    // Checkbox toggle functionality
    const checkboxes = document.querySelectorAll('.custom-checkbox');
    
    checkboxes.forEach(checkbox => {
        // Remove any existing listeners first to prevent duplicates
        checkbox.removeEventListener('click', handleCheckboxClick);
        // Add fresh listener
        checkbox.addEventListener('click', handleCheckboxClick);
    });
}

// Handler function for checkbox clicks
function handleCheckboxClick() {
    const itemId = this.dataset.itemId;
    const listId = this.dataset.listId;
    const listItem = this.closest('.list-item');
    
    // Toggle visual state immediately for better UX
    const wasChecked = this.classList.contains('checked');
    const isNowChecked = !wasChecked;
    
    // Get all instances of this checkbox and item
    const allCheckboxes = document.querySelectorAll(`.custom-checkbox[data-item-id="${itemId}"]`);
    const allListItems = document.querySelectorAll(`.list-item[data-item-id="${itemId}"]`);
    
    // Update all instances of this checkbox
    allCheckboxes.forEach(cb => {
        if (isNowChecked) {
            cb.classList.add('checked');
        } else {
            cb.classList.remove('checked');
        }
    });
    
    // Update all instances of the parent list item
    allListItems.forEach(li => {
        if (isNowChecked) {
            li.classList.add('checked');
        } else {
            li.classList.remove('checked');
        }
    });
    
    // Send toggle request to server first to ensure database gets updated
    fetch(`/app/lists/${listId}/items/${itemId}/toggle/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // After success, move checked items to bottom
            if (typeof moveCheckedItemToBottom === 'function') {
                moveCheckedItemToBottom(listItem, isNowChecked);
            }
            
            // Update progress immediately
            if (typeof updateProgress === 'function') {
                updateProgress();
            }
        } else {
            // Revert the visual state if there was an error
            allCheckboxes.forEach(cb => cb.classList.toggle('checked'));
            allListItems.forEach(li => li.classList.toggle('checked'));
            console.error('Error toggling item');
        }
    })
    .catch(error => {
        // Revert the visual state if there was an error
        allCheckboxes.forEach(cb => cb.classList.toggle('checked'));
        allListItems.forEach(li => li.classList.toggle('checked'));
        console.error('Error toggling item:', error);
    });
}

// Global flags to prevent duplicate initializations
let isInitialized = false;

$(document).ready(function() {
    // Prevent double initialization
    if (isInitialized) {
        return;
    }
    isInitialized = true;
    
    // Initialize checkbox listeners when the page loads
    initializeCheckboxListeners();
    
    // Initialize Select2 for item search
    $('#item-select').select2({
        placeholder: 'Search for items to add...',
        allowClear: true,
        minimumInputLength: 2,
        ajax: {
            url: `/api/items/search/`,
            dataType: 'json',
            delay: 250,
            data: function(params) {
                return {
                    query: params.term,
                    family: $('#item-select').data('family-id'),
                    store: $('#item-select').data('store-id')
                };
            },
            processResults: function(data) {
                return {
                    results: data.items.map(function(item) {
                        return {
                            id: item.id,
                            text: item.name,
                            brand: item.brand || ''
                        };
                    })
                };
            },
            cache: true
        },
        templateResult: formatItem,
        templateSelection: formatItemSelection
    });
    
    // Format the items in dropdown
    function formatItem(item) {
        if (!item.id) {
            return item.text;
        }
        
        var $container = $(
            '<div class="select2-result-item">' +
                '<div class="select2-result-item__name">' + item.text + '</div>' +
                (item.brand ? '<div class="select2-result-item__brand">' + item.brand + '</div>' : '') +
            '</div>'
        );
        
        return $container;
    }
    
    // Format the selected item
    function formatItemSelection(item) {
        return item.text;
    }
    
    // Remove any existing select2:select handlers to prevent duplicates
    $('#item-select').off('select2:select');
    
    // Handle item selection - direct add without modal
    $('#item-select').on('select2:select', function(e) {
        var data = e.params.data;
        var itemId = data.id;
        var itemName = data.text;
        
        // Disable the select2 immediately
        $(this).prop('disabled', true);
        
        // Add item directly to the list with default quantity
        addItemDirectly(itemId, itemName);
        
        // Clear selection but keep disabled until page reload
        setTimeout(function() {
            $('#item-select').val(null).trigger('change');
        }, 100);
    });
    
    // Map to track items being added - key is itemId
    const pendingItems = new Map();
    
    // Function to add an item directly to the list
    function addItemDirectly(itemId, itemName) {
        // Prevent duplicate submissions of the same item
        if (pendingItems.has(itemId)) {
            return;
        }
        
        // Mark this item as being processed
        pendingItems.set(itemId, Date.now());
        
        // Create form data with default values
        var formData = new FormData();
        formData.append('item_id', itemId);
        formData.append('quantity', 1);
        formData.append('unit', '');
        formData.append('note', '');
        formData.append('csrfmiddlewaretoken', getCSRFToken());
        
        // Show immediate feedback
        toastNotification(`Adding ${itemName}...`);
        
        // Get list ID from the container element
        const listIdFromJQuery = $('#shopping-list').data('list-id');
        const listIdFromVanilla = document.getElementById('shopping-list')?.dataset.listId;
        const listId = listIdFromJQuery || listIdFromVanilla;
        
        console.log('Debug - jQuery list ID:', listIdFromJQuery);
        console.log('Debug - Vanilla JS list ID:', listIdFromVanilla);
        console.log('Debug - Final list ID:', listId);
        
        if (!listId) {
            console.error('Unable to find list ID');
            toastNotification('Error: Unable to find list ID', 'error');
            pendingItems.delete(itemId);
            return;
        }
        
        // Add directly to the list
        fetch(`/app/lists/${listId}/items/add/`, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Response data:', data);
            // Remove from pending map
            pendingItems.delete(itemId);
            
            if (data.success) {
                // Show success toast
                toastNotification(`Added ${itemName} to your list`);
                
                // Add a delay before reload to ensure server transaction completes
                setTimeout(() => {
                    window.location.reload();
                }, 500);
            } else {
                // Error adding item
                console.error('Server error:', data.error || 'Unknown error');
                toastNotification(`Error adding item: ${data.error || 'Unknown error'}`, 'error');
            }
        })
        .catch(error => {
            console.error('Network or parse error:', error);
            // Remove from pending map on error
            pendingItems.delete(itemId);
            // Handle error
            toastNotification(`Error adding item: ${error.message}`, 'error');
        });
    }
    
    // Price update modal
    const priceModal = document.getElementById('price-modal');
    const editPriceBtns = document.querySelectorAll('.edit-price-btn');
    const saveButton = document.getElementById('save-price-btn');
    
    editPriceBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const itemId = this.dataset.itemId;
            const listId = this.dataset.listId;
            const itemName = this.closest('.list-item').querySelector('.item-name').textContent;
            
            document.getElementById('price-item-id').value = itemId;
            document.getElementById('price-list-id').value = listId;
            document.getElementById('price-modal-title').textContent = `Update Price: ${itemName}`;
            
            // Get current price if exists
            const priceElement = this.closest('.list-item').querySelector('.item-price');
            if (priceElement) {
                const currentPrice = priceElement.textContent.replace('$', '');
                document.getElementById('price-input').value = currentPrice;
            } else {
                document.getElementById('price-input').value = '';
            }
            
            // Show modal
            priceModal.classList.add('active');
        });
    });
    
    // Save price
    saveButton.addEventListener('click', function() {
        const itemId = document.getElementById('price-item-id').value;
        const listId = document.getElementById('price-list-id').value;
        const price = document.getElementById('price-input').value;
        
        if (!price) {
            return;
        }
        
        // Create form data
        const formData = new FormData();
        formData.append('price', price);
        formData.append('csrfmiddlewaretoken', getCSRFToken());
        
        // Send request to server
        fetch(`/app/lists/${listId}/items/${itemId}/price/`, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close modal
                priceModal.classList.remove('active');
                
                // Update UI
                const listItem = document.querySelector(`.list-item[data-item-id="${itemId}"]`);
                if (listItem) {
                    const itemDetails = listItem.querySelector('.item-details');
                    let priceElement = itemDetails.querySelector('.item-price');
                    
                    if (!priceElement) {
                        priceElement = document.createElement('span');
                        priceElement.className = 'item-price';
                        itemDetails.appendChild(priceElement);
                    }
                    
                    priceElement.textContent = `$${data.price}`;
                }
            } else {
                // Error updating price
            }
        })
        .catch(error => {
            // Handle error
        });
    });
    
    // Close modals
    document.querySelectorAll('.modal-close, .modal-overlay, [data-dismiss="modal"]').forEach(element => {
        element.addEventListener('click', function() {
            document.querySelectorAll('.modal').forEach(modal => {
                modal.classList.remove('active');
            });
        });
    });
    
    // Select2 handles the search functionality now
    // We'll add a "No results" template
    $('#item-select').on('select2:open', function() {
        // Create a link to add a new item if no results found
        if (!document.querySelector('.select2-no-results-action')) {
            $('.select2-dropdown').append(
                `<div class="select2-no-results-action" style="display:none; padding: 10px; text-align: center; border-top: 1px solid #ddd;">
                    <button type="button" class="btn btn-sm btn-primary" onclick="openAddProductModal()">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" style="margin-right: 5px; vertical-align: text-bottom;">
                            <path fill="none" d="M0 0h24v24H0z"/>
                            <path d="M11 11V5h2v6h6v2h-6v6h-2v-6H5v-2z" fill="currentColor"/>
                        </svg>
                        Create New Product
                    </button>
                </div>`
            );
            
            // Show the action link when no results found
            $(document).on('keyup', '.select2-search__field', function() {
                const searchTerm = $(this).val();
                setTimeout(function() {
                    if ($('.select2-results__message').length > 0) {
                        $('.select2-no-results-action').show();
                        // Store the search term for the modal
                        $('.select2-no-results-action').data('search-term', searchTerm);
                    } else {
                        $('.select2-no-results-action').hide();
                    }
                }, 300);
            });
        }
    });
    
    // Add recommended items directly
    document.querySelectorAll('.add-item-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const itemId = this.dataset.itemId;
            const itemName = this.dataset.itemName;
            
            // Show adding state immediately
            const originalText = this.innerHTML;
            this.innerHTML = '<span>Adding...</span>';
            this.disabled = true;
            
            // Add item directly without the modal
            addItemDirectly(itemId, itemName);
            
            // Button stays disabled until page reload
        });
    });
    
    // Remove item (no confirmation)
    const removeItemBtns = document.querySelectorAll('.remove-item-btn');
    
    removeItemBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const itemId = this.dataset.itemId;
            const listId = this.dataset.listId;
            
            // Send request to server immediately without confirmation
            fetch(`/app/lists/${listId}/items/${itemId}/remove/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCSRFToken()
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Remove item from UI
                    const listItem = this.closest('.list-item');
                    listItem.style.height = listItem.offsetHeight + 'px';
                    listItem.style.opacity = '0';
                    listItem.style.transform = 'translateX(20px)';
                    listItem.style.transition = 'opacity 0.3s, transform 0.3s';
                    
                    setTimeout(() => {
                        listItem.style.height = '0';
                        listItem.style.padding = '0';
                        listItem.style.margin = '0';
                        listItem.style.overflow = 'hidden';
                        listItem.style.transition = 'height 0.3s, padding 0.3s, margin 0.3s';
                        
                        setTimeout(() => {
                            listItem.remove();
                            
                            // Show toast notification
                            toastNotification('Item removed');
                            
                            // Update progress
                            updateProgress();
                            
                            // Check if section is empty
                            const section = this.closest('.location-section');
                            if (section && section.querySelectorAll('.list-item').length === 0) {
                                section.remove();
                            }
                            
                            // Check if list is empty
                            if (document.querySelectorAll('.list-item').length === 0) {
                                window.location.reload();
                            }
                        }, 300);
                    }, 300);
                } else {
                    // Error removing item
                    toastNotification('Error removing item', 'error');
                }
            })
            .catch(error => {
                // Handle error
                toastNotification('Error removing item', 'error');
            });
        });
    });
    
    // Dropdown menu toggle
    const dropdownToggle = document.getElementById('listActionsDropdown');
    const dropdownMenu = dropdownToggle.nextElementSibling;
    
    dropdownToggle.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropdownMenu.classList.toggle('d-none');
        
        // Close dropdown when clicking elsewhere
        const closeDropdown = function(event) {
            if (!dropdownToggle.contains(event.target) && !dropdownMenu.contains(event.target)) {
                dropdownMenu.classList.add('d-none');
                document.removeEventListener('click', closeDropdown);
            }
        };
        
        document.addEventListener('click', closeDropdown);
    });
    
    // List actions
    const listActions = document.querySelectorAll('[data-action]');
    const deleteModal = document.getElementById('delete-modal');
    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    
    listActions.forEach(action => {
        action.addEventListener('click', function(e) {
            e.preventDefault();
            
            const actionType = this.dataset.action;
            const listId = this.dataset.listId;
            
            switch (actionType) {
                case 'delete':
                    deleteModal.classList.add('active');
                    
                    // Set up confirm button
                    confirmDeleteBtn.onclick = function() {
                        window.location.href = `/app/lists/${listId}/delete/`;
                    };
                    break;
                    
                case 'duplicate':
                    // Send duplicate request
                    fetch(`/app/lists/${listId}/duplicate/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCSRFToken()
                        }
                    })
                    .then(response => {
                        // Redirect to the new list
                        window.location.href = response.url;
                    })
                    .catch(error => {
                        console.error('Error duplicating list:', error);
                    });
                    break;
                    
                case 'complete':
                    // Send complete request
                    fetch(`/app/lists/${listId}/complete/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCSRFToken()
                        }
                    })
                    .then(response => {
                        // Reload page
                        window.location.reload();
                    })
                    .catch(error => {
                        console.error('Error completing list:', error);
                    });
                    break;
                    
                case 'reopen':
                    // Send reopen request
                    fetch(`/app/lists/${listId}/reopen/`, {
                        method: 'POST',
                        headers: {
                            'X-CSRFToken': getCSRFToken()
                        }
                    })
                    .then(response => {
                        // Reload page
                        window.location.reload();
                    })
                    .catch(error => {
                        console.error('Error reopening list:', error);
                    });
                    break;
            }
        });
    });
    
    // Update progress calculation
    function updateProgress() {
        const totalItems = document.querySelectorAll('.list-item').length;
        const checkedItems = document.querySelectorAll('.list-item.checked').length;
        
        if (totalItems > 0) {
            const percentage = Math.round((checkedItems / totalItems) * 100);
            
            // Update progress bar
            const progressBar = document.querySelector('.progress-bar');
            progressBar.style.width = percentage + '%';
            progressBar.setAttribute('aria-valuenow', percentage);
            
            // Update progress text
            const progressCount = document.querySelector('.progress-count');
            progressCount.textContent = `${checkedItems}/${totalItems}`;
        }
    }
    
    // Checkbox handlers are now initialized at page load via initializeCheckboxListeners()
    
    // Function to handle item positioning based on checked state
    function moveCheckedItemToBottom(listItem, isChecked) {
        const itemId = listItem.dataset.itemId;
        
        // Get the flat list container
        const listContainer = document.getElementById('flat-list');
        if (!listContainer) return;
        
        // Apply visual effects to the current item being checked/unchecked
        listItem.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        listItem.style.opacity = '0.5';
        listItem.style.transform = 'translateX(10px)';
        
        // Delay slightly to allow the visual feedback to be seen
        setTimeout(() => {
            // Reorganize all items - unchecked at top, checked at bottom
            // Get all items in the list
            const allItems = Array.from(listContainer.querySelectorAll('.list-item'));
            
            // Separate checked and unchecked items
            const uncheckedItems = allItems.filter(item => !item.classList.contains('checked'));
            const checkedItems = allItems.filter(item => item.classList.contains('checked'));
            
            // Save references to the parent nodes
            const parentNodes = new Map();
            allItems.forEach(item => {
                if (item.parentNode) {
                    parentNodes.set(item, item.parentNode);
                }
            });
            
            // First, detach all items from the DOM (but keep references)
            allItems.forEach(item => {
                if (item.parentNode) {
                    item.parentNode.removeChild(item);
                }
            });
            
            // Then, add them back in the correct order (unchecked first, then checked)
            uncheckedItems.forEach(item => {
                listContainer.appendChild(item);
            });
            
            checkedItems.forEach(item => {
                listContainer.appendChild(item);
            });
            
            // Restore the visual appearance after the move with a smoother animation
            listItem.style.opacity = '1';
            listItem.style.transform = 'translateX(0)';
            
            // Highlight the moved item briefly
            if (isChecked) {
                setTimeout(() => {
                    listItem.style.transition = 'background-color 0.5s ease';
                    listItem.style.backgroundColor = 'rgba(0, 128, 0, 0.1)';
                    
                    setTimeout(() => {
                        listItem.style.backgroundColor = '';
                    }, 800);
                }, 150);
            }
        }, 150);
    }
    
    // Toast notification function
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
    
    // CSRF token helper function
    function getCSRFToken() {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        return cookieValue;
    }
    
    // Add Product Modal Functions
    window.openAddProductModal = function() {
        // Get the search term from the stored data or the search field
        let searchTerm = $('.select2-no-results-action').data('search-term') || $('.select2-search__field').val();
        
        // Close the Select2 dropdown first
        $('#item-select').select2('close');
        
        // Clear form and reset to defaults
        $('#add-product-form')[0].reset();
        
        // Pre-fill the product name with the search term if available
        if (searchTerm && searchTerm.trim()) {
            $('#product-name').val(searchTerm.trim());
        }
        
        $('#add-to-list').prop('checked', true);
        
        // Show the modal
        $('#add-product-modal').addClass('active');
        
        // Focus on the first empty required field
        setTimeout(() => {
            if (!searchTerm || !searchTerm.trim()) {
                $('#product-name').focus();
            } else {
                $('#product-category').focus();
            }
        }, 100);
    };
    
    // Close modal functionality
    $(document).on('click', '#add-product-modal .modal-close, #add-product-modal [data-dismiss="modal"]', function() {
        $('#add-product-modal').removeClass('active');
    });
    
    // Close modal when clicking outside
    $(document).on('click', '#add-product-modal .modal-overlay', function() {
        $('#add-product-modal').removeClass('active');
    });
    
    // Save product functionality
    $(document).on('click', '#save-product-btn', function() {
        const form = $('#add-product-form')[0];
        const saveBtn = $(this);
        
        // Validate required fields
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }
        
        // Show loading state
        saveBtn.find('.btn-text').hide();
        saveBtn.find('.btn-loading').show();
        saveBtn.prop('disabled', true);
        
        // Prepare form data
        const formData = {
            name: $('#product-name').val(),
            brand: $('#product-brand').val(),
            category: $('#product-category').val(),
            description: $('#product-description').val(),
            barcode: $('#product-barcode').val(),
            image_url: $('#product-image-url').val(),
            add_to_list: $('#add-to-list').is(':checked'),
            list_id: $('#shopping-list').data('list-id')
        };
        
        // Submit via AJAX
        $.ajax({
            url: '/api/items/create/',
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken(),
                'Content-Type': 'application/json'
            },
            data: JSON.stringify(formData),
            success: function(response) {
                // Close modal
                $('#add-product-modal').removeClass('active');
                
                // Show success message
                toastNotification(`Product "${formData.name}" created successfully!`, 'success');
                
                // If "add to list" was checked, add it to the current list
                if (formData.add_to_list && response.list_item) {
                    // Refresh the page to show the new item in the list
                    window.location.reload();
                } else {
                    // Just clear the search and show the new item is available
                    $('#item-select').val(null).trigger('change');
                    $('#item-select').select2('open');
                }
            },
            error: function(xhr, status, error) {
                console.error('Error creating product:', error);
                let errorMessage = 'Failed to create product. ';
                
                if (xhr.responseJSON && xhr.responseJSON.error) {
                    errorMessage += xhr.responseJSON.error;
                } else if (xhr.responseJSON && xhr.responseJSON.errors) {
                    const errors = Object.values(xhr.responseJSON.errors).flat();
                    errorMessage += errors.join(', ');
                } else {
                    errorMessage += 'Please try again.';
                }
                
                toastNotification(errorMessage, 'error');
            },
            complete: function() {
                // Reset loading state
                saveBtn.find('.btn-text').show();
                saveBtn.find('.btn-loading').hide();
                saveBtn.prop('disabled', false);
            }
        });
    });
});