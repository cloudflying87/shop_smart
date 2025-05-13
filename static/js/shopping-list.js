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
    const isNowChecked = !this.classList.contains('checked');
    
    // Sync the checked state with the same item in both views
    const allCheckboxes = document.querySelectorAll(`.custom-checkbox[data-item-id="${itemId}"]`);
    const allListItems = document.querySelectorAll(`.list-item[data-item-id="${itemId}"]`);
    
    allCheckboxes.forEach(cb => {
        if (isNowChecked) {
            cb.classList.add('checked');
        } else {
            cb.classList.remove('checked');
        }
    });
    
    allListItems.forEach(li => {
        if (isNowChecked) {
            li.classList.add('checked');
        } else {
            li.classList.remove('checked');
        }
    });
    
    // Send toggle request to server
    fetch(`/app/lists/${listId}/items/${itemId}/toggle/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Move checked item to the bottom of its section
            if (isNowChecked) {
                moveCheckedItemToBottom(listItem);
            }
            
            // Update progress
            updateProgress();
        } else {
            // Revert the visual state if there was an error
            allCheckboxes.forEach(cb => cb.classList.toggle('checked'));
            allListItems.forEach(li => li.classList.toggle('checked'));
            console.error('Error toggling item:', data.error);
        }
    })
    .catch(error => {
        // Revert the visual state if there was an error
        allCheckboxes.forEach(cb => cb.classList.toggle('checked'));
        allListItems.forEach(li => li.classList.toggle('checked'));
        console.error('Error:', error);
    });
}

$(document).ready(function() {
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
    
    // Handle item selection - direct add without modal
    $('#item-select').on('select2:select', function(e) {
        var data = e.params.data;
        var itemId = data.id;
        var itemName = data.text;
        
        // Add item directly to the list with default quantity
        addItemDirectly(itemId, itemName);
        
        // Clear selection after adding
        setTimeout(function() {
            $('#item-select').val(null).trigger('change');
        }, 100);
    });
    
    // Function to add an item directly to the list
    function addItemDirectly(itemId, itemName) {
        // Create form data with default values
        var formData = new FormData();
        formData.append('item_id', itemId);
        formData.append('quantity', 1);
        formData.append('unit', '');
        formData.append('note', '');
        formData.append('csrfmiddlewaretoken', getCSRFToken());
        
        // Add directly to the list
        fetch(`/app/lists/${$('#shopping-list').data('list-id')}/items/add/`, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show success toast
                toastNotification(`Added ${itemName} to your list`);
                
                // Reload to show the new item
                window.location.reload();
            } else {
                console.error('Error adding item:', data.error);
                toastNotification('Error adding item', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            toastNotification('Error adding item', 'error');
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
                console.error('Error updating price:', data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
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
                    <a href="/app/items/create/?list=${$('#shopping-list').data('list-id')}&family=${$('#item-select').data('family-id')}" class="btn btn-sm btn-primary">
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" style="margin-right: 5px; vertical-align: text-bottom;">
                            <path fill="none" d="M0 0h24v24H0z"/>
                            <path d="M11 11V5h2v6h6v2h-6v6h-2v-6H5v-2z" fill="currentColor"/>
                        </svg>
                        Create New Item
                    </a>
                </div>`
            );
            
            // Show the action link when no results found
            $(document).on('keyup', '.select2-search__field', function() {
                setTimeout(function() {
                    if ($('.select2-results__message').length > 0) {
                        $('.select2-no-results-action').show();
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
            
            // Add item directly without the modal
            addItemDirectly(itemId, itemName);
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
                    console.error('Error removing item:', data.error);
                    toastNotification('Error removing item', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
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
    
    // Function to move checked items to the bottom
    function moveCheckedItemToBottom(listItem) {
        const itemId = listItem.dataset.itemId;
        
        // Find all instances of this item in both views
        const allListItems = document.querySelectorAll(`.list-item[data-item-id="${itemId}"]`);
        
        // Move each instance to the bottom of its respective container
        allListItems.forEach(item => {
            // Get the parent list container
            let listContainer = null;
            
            // If this item is in the flat list
            if (item.closest('#flat-list')) {
                listContainer = document.getElementById('flat-list');
            } else {
                // If this item is in a category section
                const locationSection = item.closest('.location-section');
                if (locationSection) {
                    listContainer = locationSection.querySelector('.list-items');
                }
            }
            
            if (listContainer) {
                // Apply transition effect
                item.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                item.style.opacity = '0.5';
                item.style.transform = 'translateX(10px)';
                
                setTimeout(() => {
                    // Move the item to the end of its list
                    listContainer.appendChild(item);
                    
                    // Restore visibility with animation
                    setTimeout(() => {
                        item.style.opacity = '1';
                        item.style.transform = 'translateX(0)';
                    }, 50);
                }, 300);
            }
        });
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
});