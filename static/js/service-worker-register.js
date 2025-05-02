/**
 * Service Worker Registration Script for ShopSmart
 * 
 * Registers the service worker and manages installation prompts
 */

class ServiceWorkerManager {
  constructor() {
    this.swRegistration = null;
    this.installPrompt = null;
    this.installButton = document.getElementById('install-app');
    
    this.init();
  }
  
  /**
   * Initialize service worker registration
   */
  init() {
    // Check if service workers are supported
    if ('serviceWorker' in navigator) {
      // Register the service worker
      navigator.serviceWorker.register('/static/service-worker.js')
        .then(registration => {
          this.swRegistration = registration;
          console.log('Service Worker registered successfully with scope:', registration.scope);
          
          // Check for updates
          this.checkForUpdates();
        })
        .catch(error => {
          console.error('Service Worker registration failed:', error);
        });
      
      // Listen for controller changes (when SW activates)
      navigator.serviceWorker.addEventListener('controllerchange', () => {
        console.log('Service Worker controller changed');
      });
      
      // Set up installation banner
      this.setupInstallPrompt();
    } else {
      console.log('Service Workers are not supported in this browser');
    }
  }
  
  /**
   * Check for service worker updates
   */
  checkForUpdates() {
    // Check for updates every hour
    setInterval(() => {
      if (this.swRegistration) {
        this.swRegistration.update()
          .then(() => {
            console.log('Service Worker update check completed');
          })
          .catch(error => {
            console.error('Service Worker update check failed:', error);
          });
      }
    }, 60 * 60 * 1000); // 1 hour
  }
  
  /**
   * Set up the install prompt
   */
  setupInstallPrompt() {
    // Handle beforeinstallprompt event
    window.addEventListener('beforeinstallprompt', event => {
      // Prevent Chrome from showing the default prompt
      event.preventDefault();
      
      // Save the event for later use
      this.installPrompt = event;
      
      // Show install button
      this.showInstallButton();
    });
    
    // Handle appinstalled event
    window.addEventListener('appinstalled', () => {
      console.log('App installed successfully');
      
      // Hide install button
      this.hideInstallButton();
      
      // Clear saved event
      this.installPrompt = null;
      
      // Track installation in analytics
      if (typeof gtag === 'function') {
        gtag('event', 'app_installed');
      }
    });
  }
  
  /**
   * Show install button
   */
  showInstallButton() {
    if (this.installButton) {
      this.installButton.style.display = 'flex';
      
      // Add click handler to install button
      this.installButton.addEventListener('click', this.handleInstallClick.bind(this));
    }
  }
  
  /**
   * Hide install button
   */
  hideInstallButton() {
    if (this.installButton) {
      this.installButton.style.display = 'none';
    }
  }
  
  /**
   * Handle install button click
   */
  handleInstallClick() {
    if (!this.installPrompt) {
      return;
    }
    
    // Show prompt
    this.installPrompt.prompt();
    
    // Wait for user choice
    this.installPrompt.userChoice
      .then(choiceResult => {
        if (choiceResult.outcome === 'accepted') {
          console.log('User accepted the install prompt');
        } else {
          console.log('User dismissed the install prompt');
        }
        
        // Clear saved event
        this.installPrompt = null;
      });
  }
  
  /**
   * Request permission for push notifications
   */
  requestNotificationPermission() {
    if ('Notification' in window && 'serviceWorker' in navigator) {
      Notification.requestPermission()
        .then(permission => {
          if (permission === 'granted') {
            console.log('Notification permission granted');
            
            // Subscribe to push notifications
            this.subscribeToPushNotifications();
          }
        });
    }
  }
  
  /**
   * Subscribe to push notifications
   */
  subscribeToPushNotifications() {
    if (!this.swRegistration) {
      return;
    }
    
    // Check if push manager is supported
    if (!('PushManager' in window)) {
      return;
    }
    
    // Get server's public key
    const vapidPublicKey = document.querySelector('meta[name="vapid-public-key"]')?.content;
    
    if (!vapidPublicKey) {
      return;
    }
    
    // Convert base64 to array buffer
    const applicationServerKey = this.urlBase64ToUint8Array(vapidPublicKey);
    
    // Subscribe
    this.swRegistration.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: applicationServerKey
    })
      .then(subscription => {
        console.log('User subscribed to push notifications');
        
        // Send subscription to server
        this.saveSubscription(subscription);
      })
      .catch(error => {
        console.error('Failed to subscribe to push notifications:', error);
      });
  }
  
  /**
   * Convert base64 to Uint8Array
   * @param {string} base64String - Base64 string to convert
   * @returns {Uint8Array} - Converted array buffer
   */
  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');
    
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    
    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    
    return outputArray;
  }
  
  /**
   * Save subscription to server
   * @param {PushSubscription} subscription - Push subscription
   */
  saveSubscription(subscription) {
    const csrfToken = this.getCSRFToken();
    
    fetch('/api/notifications/subscribe/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
      },
      body: JSON.stringify(subscription)
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to save subscription');
        }
        
        return response.json();
      })
      .then(data => {
        console.log('Subscription saved:', data);
      })
      .catch(error => {
        console.error('Error saving subscription:', error);
      });
  }
  
  /**
   * Get CSRF token from cookies
   * @returns {string} CSRF token
   */
  getCSRFToken() {
    const name = 'csrftoken';
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    
    if (parts.length === 2) {
      return parts.pop().split(';').shift();
    }
    
    return '';
  }
  
  /**
   * Register for background sync
   * @param {string} tag - Sync tag
   * @returns {Promise<boolean>} - Success status
   */
  registerSync(tag) {
    return new Promise((resolve, reject) => {
      if (!('serviceWorker' in navigator) || !('SyncManager' in window)) {
        console.log('Background sync not supported');
        resolve(false);
        return;
      }
      
      navigator.serviceWorker.ready
        .then(registration => {
          return registration.sync.register(tag);
        })
        .then(() => {
          console.log(`Background sync registered for ${tag}`);
          resolve(true);
        })
        .catch(error => {
          console.error('Background sync registration failed:', error);
          resolve(false);
        });
    });
  }
}

// Initialize service worker manager
document.addEventListener('DOMContentLoaded', () => {
  window.swManager = new ServiceWorkerManager();
});