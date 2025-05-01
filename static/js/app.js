/**
 * Main Application JavaScript for ShopSmart
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize components
    initializeNavbar();
    initializeMessages();
    
    // Check if app is already installed
    if (window.matchMedia('(display-mode: standalone)').matches) {
      document.getElementById('install-app').style.display = 'none';
    }
  });
  
  /**
   * Initialize mobile navbar functionality
   */
  function initializeNavbar() {
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.nav-links');
    
    if (menuToggle && navLinks) {
      menuToggle.addEventListener('click', () => {
        navLinks.classList.toggle('is-active');
        
        // Toggle aria-expanded attribute for accessibility
        const isExpanded = navLinks.classList.contains('is-active');
        menuToggle.setAttribute('aria-expanded', isExpanded);
      });
      
      // Close menu when clicking outside
      document.addEventListener('click', (event) => {
        if (!event.target.closest('.navbar-menu') && navLinks.classList.contains('is-active')) {
          navLinks.classList.remove('is-active');
          menuToggle.setAttribute('aria-expanded', false);
        }
      });
    }
  }
  
  /**
   * Initialize the message closing functionality
   */
  function initializeMessages() {
    const messageCloseButtons = document.querySelectorAll('.message-close');
    
    messageCloseButtons.forEach(button => {
      button.addEventListener('click', () => {
        const message = button.closest('.message');
        
        // Add fade-out animation
        message.style.opacity = '0';
        message.style.transform = 'translateY(-10px)';
        message.style.transition = 'opacity 0.3s, transform 0.3s';
        
        // Remove after animation completes
        setTimeout(() => {
          message.remove();
        }, 300);
      });
    });
  }
  
  /**
   * Get CSRF token from cookie for AJAX requests
   * @returns {string} CSRF token
   */
  function getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    
    return cookieValue;
  }
  
  /**
   * Handle offline/online status changes
   */
  window.addEventListener('online', updateOnlineStatus);
  window.addEventListener('offline', updateOnlineStatus);
  
  function updateOnlineStatus() {
    const status = navigator.onLine ? 'online' : 'offline';
    
    if (status === 'offline') {
      // Create an offline indicator if it doesn't exist
      if (!document.querySelector('.offline-indicator')) {
        const indicator = document.createElement('div');
        indicator.className = 'offline-indicator';
        indicator.textContent = '🔄 You are offline. Changes will sync when you reconnect.';
        document.body.appendChild(indicator);
      }
    } else {
      // Remove the indicator if it exists
      const indicator = document.querySelector('.offline-indicator');
      if (indicator) {
        indicator.remove();
        
        // Trigger sync when coming back online
        syncOfflineChanges();
      }
    }
  }
  
  /**
   * Utility function for synchronizing offline changes
   * Note: This is a placeholder. Implementation will depend on the specific sync mechanism.
   */
  function syncOfflineChanges() {
    // Check for offline changes in localStorage or IndexedDB
    // Sync with server if there are any
    console.log('Syncing offline changes...');
    
    // Will be implemented with the offline functionality
  }
  
  /**
   * Utility function for data storage in IndexedDB
   * Used for offline support
   * @param {string} action - The action to perform (get, set, delete)
   * @param {string} storeName - The object store name
   * @param {string} key - The data key
   * @param {*} data - The data to store (for 'set' action)
   * @returns {Promise} Promise resolving to the data or success indicator
   */
  function dbOperation(action, storeName, key, data = null) {
    return new Promise((resolve, reject) => {
      const dbName = 'groceryBuddyDB';
      const dbVersion = 1;
      
      const request = indexedDB.open(dbName, dbVersion);
      
      request.onerror = (event) => {
        reject('IndexedDB error: ' + event.target.errorCode);
      };
      
      request.onupgradeneeded = (event) => {
        const db = event.target.result;
        
        // Create object stores if they don't exist
        if (!db.objectStoreNames.contains('lists')) {
          db.createObjectStore('lists', { keyPath: 'id' });
        }
        
        if (!db.objectStoreNames.contains('items')) {
          db.createObjectStore('items', { keyPath: 'id' });
        }
        
        if (!db.objectStoreNames.contains('syncLog')) {
          db.createObjectStore('syncLog', { keyPath: 'timestamp' });
        }
      };
      
      request.onsuccess = (event) => {
        const db = event.target.result;
        const transaction = db.transaction([storeName], action === 'get' ? 'readonly' : 'readwrite');
        const store = transaction.objectStore(storeName);
        let operation;
        
        switch (action) {
          case 'get':
            operation = store.get(key);
            operation.onsuccess = () => resolve(operation.result);
            break;
          case 'set':
            operation = store.put(data);
            operation.onsuccess = () => resolve(true);
            break;
          case 'delete':
            operation = store.delete(key);
            operation.onsuccess = () => resolve(true);
            break;
          default:
            reject('Invalid action: ' + action);
        }
        
        operation.onerror = (event) => {
          reject('Operation failed: ' + event.target.errorCode);
        };
        
        transaction.oncomplete = () => {
          db.close();
        };
      };
    });
  }