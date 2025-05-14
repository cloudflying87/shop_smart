/**
 * Offline Data Manager for ShopSmart
 * 
 * Provides robust offline data handling capabilities including:
 * - IndexedDB data storage and retrieval
 * - Conflict resolution for offline changes
 * - Change tracking and synchronization
 * - Smart caching strategies
 */

class OfflineDataManager {
  constructor() {
    this.dbName = 'shopsmart-db';
    this.dbVersion = 1;
    this.db = null;
    this.stores = [
      { name: 'lists', keyPath: 'id' },
      { name: 'items', keyPath: 'id' },
      { name: 'syncLog', keyPath: 'timestamp' },
      { name: 'products', keyPath: 'id' },
      { name: 'userPreferences', keyPath: 'key' }
    ];
    
    this.initialized = this.initDatabase();
    
    // Monitor online status
    window.addEventListener('online', this.handleOnlineStatusChange.bind(this));
    window.addEventListener('offline', this.handleOnlineStatusChange.bind(this));
  }
  
  /**
   * Initialize the database
   * @returns {Promise} Resolves when database is ready
   */
  async initDatabase() {
    try {
      this.db = await this.openDatabase();
      console.log('Offline database initialized');
      return true;
    } catch (error) {
      console.error('Failed to initialize offline database:', error);
      return false;
    }
  }
  
  /**
   * Open the IndexedDB database
   * @returns {Promise<IDBDatabase>} Database instance
   */
  openDatabase() {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.dbVersion);
      
      request.onerror = event => {
        console.error('Database error:', event.target.error);
        reject(event.target.error);
      };
      
      request.onsuccess = event => {
        const db = event.target.result;
        resolve(db);
      };
      
      request.onupgradeneeded = event => {
        const db = event.target.result;
        
        // Create object stores
        this.stores.forEach(store => {
          if (!db.objectStoreNames.contains(store.name)) {
            db.createObjectStore(store.name, { keyPath: store.keyPath });
            console.log(`Created store: ${store.name}`);
          }
        });
      };
    });
  }
  
  /**
   * Handle online/offline status changes
   */
  async handleOnlineStatusChange() {
    const isOnline = navigator.onLine;
    
    if (isOnline) {
      console.log('Device is online, attempting to sync changes');
      await this.syncChanges();
    } else {
      console.log('Device is offline, activating offline mode');
      this.showOfflineIndicator();
    }
  }
  
  /**
   * Show the offline status indicator
   */
  showOfflineIndicator() {
    // Create or show the offline indicator
    if (!document.querySelector('.offline-indicator')) {
      const indicator = document.createElement('div');
      indicator.className = 'offline-indicator';
      indicator.innerHTML = `
        <div class="offline-indicator-content">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" class="offline-icon">
            <path fill="none" d="M0 0h24v24H0z"/>
            <path d="M12 8.5a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7zm0 2a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zM5.439 4.11a10.945 10.945 0 0 1 5.023-1.11C16.373 3 21 7.6 21 13.5c0 1.47-.302 2.872-.84 4.144a.5.5 0 0 1-.27.25.5.5 0
            0 1-.38-.03l-1.88-1.03a.5.5 0 0 1-.25-.35.5.5 0 0 1 .07-.43 7.462 7.462 0 0 0 1.06-3.88c0-4.142-3.36-7.5-7.5-7.5a7.462 7.462 0 0 0-3.881 1.061.5.5 0 0 1-.43.07.5.5 0 0 1-.35-.25l-1
            0-1.84a.5.5 0 0 1-.03-.38.5.5 0 0 1 .25-.27zm13.12 15.74a.5.5 0 0 1 .03.38.5.5 0 0 1-.25.27c-1.565.866-3.84 1.5-6.339 1.5-5.783 0-10.39-4.574-10.5-10.254a.5.5 0 0 1 .11-.375l1.61-1.749a.5.5 0 0
             1 .365-.175c1.311 0 2.667.524 3.613 1.206.648.466 1.24 1.144 1.866 1.473a.5.5 0 0 1 .25.35.5.5 0 0 1-.08.43c-.173.253-.444.434-.78.434-.38 0-.867-.409-1.316-.715-.451-.306-1.002-.683-1.5-.683v2c.835
             0 1.675.533 2.309.989.636.455 1.071.847 1.525.882a.5.5 0 0 1 .47.345.5.5 0 0 1-.126.54c-.476.476-1.07.782-1.733.782-.8 0-1.308-.479-1.817-.887-.356-.285-.702-.519-1.101-.619
             a.5.5 0 0 1-.375-.575l.248-1.13a.5.5 0 0 1 .575-.375c.825.18 1.512.696 2.089 1.105.47.332.883.569 1.367.605a.5.5 0 0 1 .335.18.5.5 0 0 1 .098.5c-.143.354-.457.654-.906.654-.34
             0-.718-.272-1.085-.508-.387-.248-.776-.498-1.212-.654a.5.5 0 0 1-.32-.635l.152-.385a.5.5 0 0 1 .63-.325c.144.055.274.177.428.268.155.091.335.179.548.179v-1a2.1 2.1 0 0 0-.528-.079
             .5.5 0 0 1-.498-.5c0-.276.225-.5.499-.5.695 0 1.247.296 1.776.512.52.213 1.054.488 1.596.488a.5.5 0 0 1 .499.5c0 .276-.224.5-.499.5a2.533 2.533 0 0 1-1.015-.225l.053.245
             a.5.5 0 0 1-.485.595 3.814 3.814 0 0 1-.69-.06l1.088 1.94z" fill="currentColor"/>
          </svg>
          <span>You're offline. Changes will sync when you reconnect.</span>
        </div>
      `;
      
      document.body.appendChild(indicator);
      
      // Add fade-in animation
      setTimeout(() => {
        indicator.classList.add('active');
      }, 10);
    }
  }
  
  /**
   * Hide the offline status indicator
   */
  hideOfflineIndicator() {
    const indicator = document.querySelector('.offline-indicator');
    if (indicator) {
      // Add fade-out animation
      indicator.classList.remove('active');
      setTimeout(() => {
        indicator.remove();
      }, 300);
    }
  }
  
  /**
   * Synchronize pending changes with the server
   */
  async syncChanges() {
    try {
      // Ensure database is ready
      if (!this.db) {
        await this.initialized;
      }
      
      // Get pending sync items
      const pendingSyncs = await this.getAllFromStore('syncLog');
      
      if (pendingSyncs.length === 0) {
        console.log('No pending changes to sync');
        this.hideOfflineIndicator();
        return;
      }
      
      console.log(`Syncing ${pendingSyncs.length} pending changes`);
      
      // Group by model type
      const groupedSyncs = this.groupSyncsByModel(pendingSyncs);
      
      // Process each group
      for (const [modelName, items] of Object.entries(groupedSyncs)) {
        await this.syncModelChanges(modelName, items);
      }
      
      // Remove offline indicator after successful sync
      this.hideOfflineIndicator();
      
    } catch (error) {
      console.error('Error syncing changes:', error);
      
      // Keep offline indicator visible if sync failed
      this.showOfflineIndicator();
    }
  }
  
  /**
   * Group sync items by model name
   * @param {Array} syncItems - List of sync items
   * @returns {Object} - Grouped sync items
   */
  groupSyncsByModel(syncItems) {
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
   * Sync changes for a specific model
   * @param {string} modelName - Model name
   * @param {Array} items - List of items to sync
   */
  async syncModelChanges(modelName, items) {
    try {
      // Get endpoint URL
      const endpoint = this.getSyncEndpoint(modelName);
      if (!endpoint) {
        console.error(`No sync endpoint defined for model ${modelName}`);
        return;
      }
      
      // Prepare sync data
      const syncData = {
        model: modelName,
        items: items.map(item => ({
          operation: item.operation,
          data: item.data,
          timestamp: item.timestamp,
          record_id: item.record_id
        }))
      };
      
      // Get CSRF token
      const csrfToken = this.getCSRFToken();
      
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
      
      if (result.success) {
        // Remove synced items from local storage
        for (const item of items) {
          await this.deleteFromStore('syncLog', item.timestamp);
        }
        
        console.log(`Successfully synced ${items.length} ${modelName} items`);
        
        // Update local data with server responses if provided
        if (result.updated_records) {
          await this.updateLocalDataFromSync(modelName, result.updated_records);
        }
      } else {
        console.error(`Failed to sync ${modelName} items:`, result.error);
      }
    } catch (error) {
      console.error(`Error syncing ${modelName} items:`, error);
      throw error;
    }
  }
  
  /**
   * Update local data with server response after sync
   * @param {string} modelName - Model name
   * @param {Array} records - Updated records from server
   */
  async updateLocalDataFromSync(modelName, records) {
    try {
      const storeName = this.getStoreNameForModel(modelName);
      
      if (!storeName) {
        console.error(`No store defined for model ${modelName}`);
        return;
      }
      
      // Update each record in local database
      for (const record of records) {
        await this.saveToStore(storeName, record);
      }
      
      console.log(`Updated ${records.length} local ${modelName} records after sync`);
    } catch (error) {
      console.error(`Error updating local data after sync:`, error);
    }
  }
  
  /**
   * Get sync endpoint URL for a model
   * @param {string} modelName - Model name
   * @returns {string} - Endpoint URL
   */
  getSyncEndpoint(modelName) {
    const endpoints = {
      'shopping_list': '/api/lists/sync/',
      'shopping_list_item': '/api/lists/items/sync/',
      'user_profile': '/api/profile/sync/',
      'product': '/api/products/sync/'
    };
    
    return endpoints[modelName] || null;
  }
  
  /**
   * Get store name for a model
   * @param {string} modelName - Model name
   * @returns {string} - Store name
   */
  getStoreNameForModel(modelName) {
    const storeMapping = {
      'shopping_list': 'lists',
      'shopping_list_item': 'items',
      'product': 'products',
      'user_profile': 'userPreferences'
    };
    
    return storeMapping[modelName] || null;
  }
  
  /**
   * Get CSRF token from cookies
   * @returns {string} - CSRF token
   */
  getCSRFToken() {
    const name = 'csrftoken';
    let value = null;
    
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          value = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    
    return value;
  }
  
  /**
   * Add an item to the sync log
   * @param {string} modelName - Model name
   * @param {string} operation - Operation (create, update, delete)
   * @param {number|null} recordId - Record ID (null for create operations)
   * @param {Object} data - Data to sync
   * @returns {Promise<boolean>} - Success status
   */
  async addToSyncLog(modelName, operation, recordId, data) {
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
      syncEntry.data.csrf_token = this.getCSRFToken();
      
      // Store in IndexedDB
      await this.saveToStore('syncLog', syncEntry);
      
      // Try to sync immediately if online
      if (navigator.onLine) {
        this.syncChanges();
      }
      
      return true;
    } catch (error) {
      console.error('Error adding to sync log:', error);
      return false;
    }
  }
  
  /**
   * Save an item to a store
   * @param {string} storeName - Store name
   * @param {Object} item - Item to save
   * @returns {Promise<boolean>} - Success status
   */
  async saveToStore(storeName, item) {
    try {
      // Ensure database is ready
      if (!this.db) {
        await this.initialized;
      }
      
      return new Promise((resolve, reject) => {
        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        
        const request = store.put(item);
        
        request.onsuccess = () => {
          resolve(true);
        };
        
        request.onerror = (event) => {
          console.error(`Error saving to ${storeName}:`, event.target.error);
          reject(event.target.error);
        };
      });
    } catch (error) {
      console.error(`Error in saveToStore (${storeName}):`, error);
      return false;
    }
  }
  
  /**
   * Get an item from a store
   * @param {string} storeName - Store name
   * @param {*} key - Item key
   * @returns {Promise<Object>} - Retrieved item
   */
  async getFromStore(storeName, key) {
    try {
      // Ensure database is ready
      if (!this.db) {
        await this.initialized;
      }
      
      return new Promise((resolve, reject) => {
        const transaction = this.db.transaction([storeName], 'readonly');
        const store = transaction.objectStore(storeName);
        
        const request = store.get(key);
        
        request.onsuccess = () => {
          resolve(request.result);
        };
        
        request.onerror = (event) => {
          console.error(`Error getting from ${storeName}:`, event.target.error);
          reject(event.target.error);
        };
      });
    } catch (error) {
      console.error(`Error in getFromStore (${storeName}):`, error);
      return null;
    }
  }
  
  /**
   * Delete an item from a store
   * @param {string} storeName - Store name
   * @param {*} key - Item key
   * @returns {Promise<boolean>} - Success status
   */
  async deleteFromStore(storeName, key) {
    try {
      // Ensure database is ready
      if (!this.db) {
        await this.initialized;
      }
      
      return new Promise((resolve, reject) => {
        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        
        const request = store.delete(key);
        
        request.onsuccess = () => {
          resolve(true);
        };
        
        request.onerror = (event) => {
          console.error(`Error deleting from ${storeName}:`, event.target.error);
          reject(event.target.error);
        };
      });
    } catch (error) {
      console.error(`Error in deleteFromStore (${storeName}):`, error);
      return false;
    }
  }
  
  /**
   * Get all items from a store
   * @param {string} storeName - Store name
   * @returns {Promise<Array>} - All items in the store
   */
  async getAllFromStore(storeName) {
    try {
      // Ensure database is ready
      if (!this.db) {
        await this.initialized;
      }
      
      return new Promise((resolve, reject) => {
        const transaction = this.db.transaction([storeName], 'readonly');
        const store = transaction.objectStore(storeName);
        
        const request = store.getAll();
        
        request.onsuccess = () => {
          resolve(request.result || []);
        };
        
        request.onerror = (event) => {
          console.error(`Error getting all from ${storeName}:`, event.target.error);
          reject(event.target.error);
        };
      });
    } catch (error) {
      console.error(`Error in getAllFromStore (${storeName}):`, error);
      return [];
    }
  }
  
  /**
   * Clear all items from a store
   * @param {string} storeName - Store name
   * @returns {Promise<boolean>} - Success status
   */
  async clearStore(storeName) {
    try {
      // Ensure database is ready
      if (!this.db) {
        await this.initialized;
      }
      
      return new Promise((resolve, reject) => {
        const transaction = this.db.transaction([storeName], 'readwrite');
        const store = transaction.objectStore(storeName);
        
        const request = store.clear();
        
        request.onsuccess = () => {
          resolve(true);
        };
        
        request.onerror = (event) => {
          console.error(`Error clearing ${storeName}:`, event.target.error);
          reject(event.target.error);
        };
      });
    } catch (error) {
      console.error(`Error in clearStore (${storeName}):`, error);
      return false;
    }
  }
  
  /**
   * Save user preferences to IndexedDB
   * @param {Object} preferences - User preferences
   * @returns {Promise<boolean>} - Success status
   */
  async saveUserPreferences(preferences) {
    try {
      const prefObject = {
        key: 'userPreferences',
        data: preferences
      };
      
      await this.saveToStore('userPreferences', prefObject);
      
      // Add to sync log
      await this.addToSyncLog(
        'user_profile',
        'update',
        null,
        preferences
      );
      
      return true;
    } catch (error) {
      console.error('Error saving user preferences:', error);
      return false;
    }
  }
  
  /**
   * Get user preferences from IndexedDB
   * @returns {Promise<Object>} - User preferences
   */
  async getUserPreferences() {
    try {
      const prefObject = await this.getFromStore('userPreferences', 'userPreferences');
      return prefObject ? prefObject.data : null;
    } catch (error) {
      console.error('Error getting user preferences:', error);
      return null;
    }
  }
  
  /**
   * Cache a shopping list for offline use
   * @param {Object} list - Shopping list
   * @param {Array} items - List items
   * @returns {Promise<boolean>} - Success status
   */
  async cacheShoppingList(list, items) {
    try {
      // Save list to lists store
      await this.saveToStore('lists', list);
      
      // Save items to items store
      for (const item of items) {
        await this.saveToStore('items', item);
      }
      
      return true;
    } catch (error) {
      console.error('Error caching shopping list:', error);
      return false;
    }
  }
  
  /**
   * Get a cached shopping list
   * @param {number} listId - List ID
   * @returns {Promise<Object>} - Shopping list with items
   */
  async getCachedShoppingList(listId) {
    try {
      // Get list from lists store
      const list = await this.getFromStore('lists', listId);
      
      if (!list) {
        return null;
      }
      
      // Get all items
      const allItems = await this.getAllFromStore('items');
      
      // Filter items for this list
      const listItems = allItems.filter(item => item.shopping_list_id === listId);
      
      return {
        list,
        items: listItems
      };
    } catch (error) {
      console.error('Error getting cached shopping list:', error);
      return null;
    }
  }
  
  /**
   * Create a shopping list while offline
   * @param {Object} listData - List data
   * @returns {Promise<Object>} - Created list with temporary ID
   */
  async createOfflineList(listData) {
    try {
      // Generate temporary ID (negative to avoid conflicts with server IDs)
      const tempId = -Date.now();
      
      // Create list object
      const list = {
        ...listData,
        id: tempId,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        is_temp_id: true
      };
      
      // Save to IndexedDB
      await this.saveToStore('lists', list);
      
      // Add to sync log
      await this.addToSyncLog(
        'shopping_list',
        'create',
        null,
        {
          list_data: list,
          temp_id: tempId
        }
      );
      
      return list;
    } catch (error) {
      console.error('Error creating offline list:', error);
      throw error;
    }
  }
  
  /**
   * Add an item to a shopping list while offline
   * @param {number} listId - List ID
   * @param {Object} itemData - Item data
   * @returns {Promise<Object>} - Created item with temporary ID
   */
  async addOfflineListItem(listId, itemData) {
    try {
      // Generate temporary ID
      const tempId = -Date.now();
      
      // Create item object
      const item = {
        ...itemData,
        id: tempId,
        shopping_list_id: listId,
        is_temp_id: true
      };
      
      // Save to IndexedDB
      await this.saveToStore('items', item);
      
      // Add to sync log
      await this.addToSyncLog(
        'shopping_list_item',
        'create',
        null,
        {
          item_data: item,
          list_id: listId,
          temp_id: tempId
        }
      );
      
      return item;
    } catch (error) {
      console.error('Error adding offline list item:', error);
      throw error;
    }
  }
}

// Initialize offline data manager
document.addEventListener('DOMContentLoaded', () => {
  window.offlineManager = new OfflineDataManager();
  
  // Check initial online status
  if (!navigator.onLine) {
    window.offlineManager.showOfflineIndicator();
  }
});