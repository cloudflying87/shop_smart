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
   * Reads from IndexedDB and synchronizes with the server
   */
  async function syncOfflineChanges() {
    console.log('Syncing offline changes...');
    
    // Check if we have background sync support
    if ('serviceWorker' in navigator && 'SyncManager' in window && window.swManager) {
      try {
        // Register sync tasks with the service worker
        await window.swManager.registerSync('sync-shopping-lists');
        await window.swManager.registerSync('sync-list-items');
        console.log('Background sync registered successfully');
        return true;
      } catch (error) {
        console.error('Background sync registration failed:', error);
        // Fall back to manual sync if background sync fails
      }
    }
    
    // Manual sync if background sync is not supported
    return manualSyncOfflineChanges();
  }

  /**
   * Manual synchronization of offline changes
   * Used as a fallback when background sync is not available
   */
  async function manualSyncOfflineChanges() {
    try {
      // Get all pending changes from IndexedDB
      const pendingSyncs = await getAllPendingSyncs();
      
      if (pendingSyncs.length === 0) {
        console.log('No pending changes to sync');
        return true;
      }
      
      console.log(`Found ${pendingSyncs.length} pending changes to sync`);
      
      // Group by model type
      const groupedSyncs = groupSyncsByModel(pendingSyncs);
      
      // Process each group
      const results = await Promise.all(
        Object.entries(groupedSyncs).map(([modelName, items]) => {
          return syncItemsByModel(modelName, items);
        })
      );
      
      // Check if all syncs were successful
      const allSuccessful = results.every(result => result);
      
      if (allSuccessful) {
        console.log('All offline changes synced successfully');
      } else {
        console.warn('Some offline changes failed to sync');
      }
      
      return allSuccessful;
    } catch (error) {
      console.error('Error syncing offline changes:', error);
      return false;
    }
  }

  /**
   * Get all pending sync items from IndexedDB
   * @returns {Promise<Array>} Array of pending sync items
   */
  async function getAllPendingSyncs() {
    return new Promise((resolve, reject) => {
      dbOperation('getAllFromStore', 'syncLog')
        .then(items => {
          resolve(items || []);
        })
        .catch(error => {
          console.error('Error getting pending syncs:', error);
          reject(error);
        });
    });
  }

  /**
   * Group sync items by model name for batch processing
   * @param {Array} syncItems - List of sync items
   * @returns {Object} Grouped sync items
   */
  function groupSyncsByModel(syncItems) {
    return syncItems.reduce((groups, item) => {
      const modelName = item.model_name;
      if (!groups[modelName]) {
        groups[modelName] = [];
      }
      groups[modelName].push(item);
      return groups;
    }, {});
  }

  /**
   * Sync items for a specific model
   * @param {string} modelName - Name of the model
   * @param {Array} items - List of items to sync
   * @returns {Promise<boolean>} Success status
   */
  async function syncItemsByModel(modelName, items) {
    try {
      const endpoint = getSyncEndpoint(modelName);
      
      if (!endpoint) {
        console.error(`No sync endpoint defined for model ${modelName}`);
        return false;
      }
      
      // Prepare data for sync
      const syncData = {
        model: modelName,
        items: items.map(item => ({
          operation: item.operation,
          data: item.data,
          timestamp: item.timestamp,
          id: item.record_id
        }))
      };
      
      // Get CSRF token
      const csrfToken = getCSRFToken();
      
      // Send data to server
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify(syncData)
      });
      
      if (!response.ok) {
        throw new Error(`Server returned ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      // Process server response
      if (result.success) {
        // Remove synced items from local storage
        await Promise.all(items.map(item => {
          return dbOperation('delete', 'syncLog', item.timestamp);
        }));
        
        console.log(`Successfully synced ${items.length} ${modelName} items`);
        return true;
      } else {
        console.error(`Failed to sync ${modelName} items:`, result.error);
        return false;
      }
    } catch (error) {
      console.error(`Error syncing ${modelName} items:`, error);
      return false;
    }
  }

  /**
   * Get sync endpoint URL for a given model
   * @param {string} modelName - Name of the model
   * @returns {string} Endpoint URL
   */
  function getSyncEndpoint(modelName) {
    const endpoints = {
      'shopping_list': '/api/lists/sync/',
      'shopping_list_item': '/api/lists/items/sync/',
      'user_profile': '/api/profile/sync/'
    };
    
    return endpoints[modelName] || null;
  }
  
  /**
   * Utility function for data storage in IndexedDB
   * Used for offline support
   * @param {string} action - The action to perform (get, set, delete, getAllFromStore)
   * @param {string} storeName - The object store name
   * @param {string} key - The data key (not used for getAllFromStore)
   * @param {*} data - The data to store (for 'set' action)
   * @returns {Promise} Promise resolving to the data or success indicator
   */
  function dbOperation(action, storeName, key = null, data = null) {
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
        const transaction = db.transaction([storeName], action === 'get' || action === 'getAllFromStore' ? 'readonly' : 'readwrite');
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
          case 'getAllFromStore':
            operation = store.getAll();
            operation.onsuccess = () => resolve(operation.result);
            break;
          default:
            reject('Invalid action: ' + action);
            return;
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
  
  /**
   * Add an item to the sync log for offline synchronization
   * @param {string} modelName - The model name
   * @param {string} operation - The operation (create, update, delete)
   * @param {number|null} recordId - The record ID (null for create operations)
   * @param {Object} data - The data to sync
   * @returns {Promise<boolean>} Success status
   */
  async function addToSyncLog(modelName, operation, recordId, data) {
    try {
      // Create sync log entry
      const syncEntry = {
        timestamp: Date.now(),
        model_name: modelName,
        operation: operation,
        record_id: recordId,
        data: data,
        synced: false
      };
      
      // Add CSRF token for server validation
      syncEntry.data.csrf_token = getCSRFToken();
      
      // Store in IndexedDB
      await dbOperation('set', 'syncLog', syncEntry.timestamp, syncEntry);
      
      // Try to sync immediately if online
      if (navigator.onLine) {
        // Use background sync if available
        if ('serviceWorker' in navigator && 'SyncManager' in window && window.swManager) {
          const tag = `sync-${modelName.replace('_', '-')}s`;
          await window.swManager.registerSync(tag);
        } else {
          // Otherwise try manual sync
          await syncOfflineChanges();
        }
      }
      
      return true;
    } catch (error) {
      console.error('Error adding to sync log:', error);
      return false;
    }
  }