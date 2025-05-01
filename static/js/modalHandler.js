/**
 * Modal Handler for ShopSmart
 * 
 * This script manages the global modal component that can be reused 
 * throughout the application for various purposes.
 */

class ModalHandler {
    constructor() {
      this.modal = document.getElementById('global-modal');
      this.modalOverlay = this.modal.querySelector('.modal-overlay');
      this.modalTitle = document.getElementById('modal-title');
      this.modalBody = document.getElementById('modal-body');
      this.modalFooter = document.getElementById('modal-footer');
      this.modalCloseBtn = this.modal.querySelector('.modal-close');
      
      this.init();
    }
    
    /**
     * Initialize modal event listeners
     */
    init() {
      // Close modal when clicking the close button
      this.modalCloseBtn.addEventListener('click', () => {
        this.close();
      });
      
      // Close modal when clicking the overlay
      this.modalOverlay.addEventListener('click', () => {
        this.close();
      });
      
      // Close modal when pressing Escape key
      document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && this.isOpen()) {
          this.close();
        }
      });
    }
    
    /**
     * Check if modal is currently open
     * @returns {boolean} True if modal is open
     */
    isOpen() {
      return this.modal.classList.contains('is-active');
    }
    
    /**
     * Open the modal with custom content
     * @param {string} title - Modal title
     * @param {string|HTMLElement} content - Modal body content (string or DOM element)
     * @param {Array} buttons - Array of button objects with text and onClick properties
     * @param {Object} options - Additional options (width, height, etc.)
     */
    open(title, content, buttons = [], options = {}) {
      // Set modal title
      this.modalTitle.textContent = title;
      
      // Set modal content
      if (typeof content === 'string') {
        this.modalBody.innerHTML = content;
      } else if (content instanceof HTMLElement) {
        this.modalBody.innerHTML = '';
        this.modalBody.appendChild(content);
      }
      
      // Add buttons to footer
      this.modalFooter.innerHTML = '';
      
      if (buttons.length === 0) {
        // Add default close button if no buttons are provided
        const closeButton = document.createElement('button');
        closeButton.className = 'btn btn-primary';
        closeButton.textContent = 'Close';
        closeButton.addEventListener('click', () => this.close());
        this.modalFooter.appendChild(closeButton);
      } else {
        // Add custom buttons
        buttons.forEach(button => {
          const btnElement = document.createElement('button');
          btnElement.className = button.class || 'btn btn-outline';
          btnElement.textContent = button.text;
          btnElement.addEventListener('click', (event) => {
            if (button.onClick) {
              button.onClick(event);
            }
            
            if (button.closeOnClick !== false) {
              this.close();
            }
          });
          this.modalFooter.appendChild(btnElement);
        });
      }
      
      // Apply custom options
      if (options.width) {
        this.modal.querySelector('.modal-container').style.maxWidth = options.width;
      }
      
      // Show the modal
      this.modal.classList.add('is-active');
      document.body.style.overflow = 'hidden'; // Prevent body scrolling
      
      // Focus the first focusable element for accessibility
      setTimeout(() => {
        const focusable = this.modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (focusable.length > 0) {
          focusable[0].focus();
        }
      }, 100);
      
      // Return the modal instance for chaining
      return this;
    }
    
    /**
     * Close the modal
     */
    close() {
      this.modal.classList.remove('is-active');
      document.body.style.overflow = ''; // Restore body scrolling
      
      // Clear content after animation
      setTimeout(() => {
        this.modalBody.innerHTML = '';
        this.modalFooter.innerHTML = '';
      }, 300);
    }
    
    /**
     * Create and open a price input modal
     * @param {string} itemName - Name of the item
     * @param {number} currentPrice - Current price of the item (if any)
     * @param {Function} onSave - Function to call when price is saved
     */
    openPriceModal(itemName, currentPrice = null, onSave) {
      const content = document.createElement('div');
      content.className = 'price-modal-content';
      
      const label = document.createElement('label');
      label.for = 'price-input';
      label.textContent = `Enter price for ${itemName}:`;
      
      const inputGroup = document.createElement('div');
      inputGroup.className = 'input-group';
      
      const currencySymbol = document.createElement('span');
      currencySymbol.className = 'input-group-text';
      currencySymbol.textContent = '$';
      
      const input = document.createElement('input');
      input.type = 'number';
      input.id = 'price-input';
      input.className = 'form-control';
      input.placeholder = '0.00';
      input.step = '0.01';
      input.min = '0';
      
      if (currentPrice !== null) {
        input.value = currentPrice;
      }
      
      inputGroup.appendChild(currencySymbol);
      inputGroup.appendChild(input);
      
      content.appendChild(label);
      content.appendChild(inputGroup);
      
      const buttons = [
        {
          text: 'Cancel',
          class: 'btn btn-outline'
        },
        {
          text: 'Save',
          class: 'btn btn-primary',
          onClick: () => {
            const price = parseFloat(input.value);
            if (!isNaN(price) && price >= 0) {
              onSave(price);
            }
          }
        }
      ];
      
      this.open(`Item Price`, content, buttons);
      
      // Focus the input field
      setTimeout(() => {
        input.focus();
      }, 100);
    }
    
    /**
     * Create and open a confirmation modal
     * @param {string} message - Confirmation message
     * @param {Function} onConfirm - Function to call when confirmed
     * @param {string} confirmText - Text for confirmation button
     * @param {string} cancelText - Text for cancel button
     */
    confirm(message, onConfirm, confirmText = 'Confirm', cancelText = 'Cancel') {
      const content = `<p>${message}</p>`;
      
      const buttons = [
        {
          text: cancelText,
          class: 'btn btn-outline'
        },
        {
          text: confirmText,
          class: 'btn btn-primary',
          onClick: onConfirm
        }
      ];
      
      this.open('Confirmation', content, buttons);
    }
    
    /**
     * Create and open an alert modal
     * @param {string} message - Alert message
     * @param {string} buttonText - Text for the button
     */
    alert(message, buttonText = 'OK') {
      const content = `<p>${message}</p>`;
      
      const buttons = [
        {
          text: buttonText,
          class: 'btn btn-primary'
        }
      ];
      
      this.open('Alert', content, buttons);
    }
  }
  
  // Initialize the global modal handler
  const modalHandler = new ModalHandler();
  
  // Make it available globally
  window.modalHandler = modalHandler;