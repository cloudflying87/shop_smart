/**
 * Mobile Navigation for ShopSmart
 * 
 * Handles mobile-specific navigation functionality:
 * - Side menu toggle
 * - Swipe gestures for list items
 * - Touch-friendly interactions
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize components
    initSideMenu();
    initSwipeActions();
    initBottomNav();
    setupPullToRefresh();
    setupListItemInteractions();
  });
  
  /**
   * Initialize side menu functionality
   */
  function initSideMenu() {
    const menuButton = document.querySelector('.menu-button');
    const closeMenuButton = document.querySelector('.close-menu');
    const sideMenu = document.querySelector('.side-menu');
    const menuOverlay = document.querySelector('.menu-overlay');
    
    if (!menuButton || !sideMenu) return;
    
    // Open menu
    menuButton.addEventListener('click', () => {
      sideMenu.classList.add('active');
      menuOverlay.classList.add('active');
      document.body.style.overflow = 'hidden'; // Prevent body scrolling
    });
    
    // Close menu
    const closeMenu = () => {
      sideMenu.classList.remove('active');
      menuOverlay.classList.remove('active');
      document.body.style.overflow = '';
    };
    
    closeMenuButton.addEventListener('click', closeMenu);
    menuOverlay.addEventListener('click', closeMenu);
    
    // Close menu on escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeMenu();
      }
    });
    
    // Handle swipe to close
    let touchStartX = 0;
    let touchEndX = 0;
    
    sideMenu.addEventListener('touchstart', (e) => {
      touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });
    
    sideMenu.addEventListener('touchend', (e) => {
      touchEndX = e.changedTouches[0].screenX;
      handleSwipeGesture();
    }, { passive: true });
    
    const handleSwipeGesture = () => {
      if (touchStartX - touchEndX > 50) {
        // Swiped left
        closeMenu();
      }
    };
  }
  
  /**
   * Initialize swipe actions for list items
   */
  function initSwipeActions() {
    // Find all swipe containers
    const swipeContainers = document.querySelectorAll('.swipe-container');
    
    swipeContainers.forEach(container => {
      let touchStartX = 0;
      let touchEndX = 0;
      const swipeContent = container.querySelector('.swipe-item-content');
      const swipeActions = container.querySelector('.swipe-actions');
      
      if (!swipeContent || !swipeActions) return;
      
      // Store the width of the actions for use during swiping
      const actionsWidth = swipeActions.offsetWidth;
      let isOpen = false;
      
      // Handle touch events
      container.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
      }, { passive: true });
      
      container.addEventListener('touchmove', (e) => {
        const currentX = e.changedTouches[0].screenX;
        const diff = touchStartX - currentX;
        
        // If swiping left (revealing actions)
        if (diff > 0) {
          const translateX = Math.min(diff, actionsWidth);
          swipeContent.style.transform = `translateX(-${translateX}px)`;
        } 
        // If swiping right (closing actions) and actions are open
        else if (isOpen) {
          const translateX = Math.max(actionsWidth + diff, 0);
          swipeContent.style.transform = `translateX(-${translateX}px)`;
        }
      }, { passive: true });
      
      container.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        const diff = touchStartX - touchEndX;
        
        // If swiped left far enough, fully open
        if (diff > actionsWidth / 2) {
          swipeContent.style.transform = `translateX(-${actionsWidth}px)`;
          isOpen = true;
        } 
        // Otherwise, close
        else {
          swipeContent.style.transform = 'translateX(0)';
          isOpen = false;
        }
      }, { passive: true });
      
      // Close when clicking anywhere else
      document.addEventListener('click', (e) => {
        if (isOpen && !container.contains(e.target)) {
          swipeContent.style.transform = 'translateX(0)';
          isOpen = false;
        }
      });
      
      // Add event listeners to action buttons
      const actionButtons = swipeActions.querySelectorAll('.swipe-action');
      actionButtons.forEach(button => {
        button.addEventListener('click', () => {
          // Reset position after action
          setTimeout(() => {
            swipeContent.style.transform = 'translateX(0)';
            isOpen = false;
          }, 300);
        });
      });
    });
  }
  
  /**
   * Initialize bottom navigation highlighting
   */
  function initBottomNav() {
    const bottomNav = document.querySelector('.bottom-nav');
    if (!bottomNav) return;
    
    // Get current URL path
    const currentPath = window.location.pathname;
    
    // Find all nav links
    const navLinks = bottomNav.querySelectorAll('.bottom-nav-link');
    
    // Highlight current section
    navLinks.forEach(link => {
      const linkPath = link.getAttribute('href');
      if (currentPath.includes(linkPath) && linkPath !== '/') {
        link.classList.add('active');
      }
    });
    
    // Special case for home page
    if (currentPath === '/' || currentPath === '/dashboard/') {
      const homeLink = bottomNav.querySelector('[href="/"]') || 
                       bottomNav.querySelector('[href="/dashboard/"]');
      if (homeLink) {
        homeLink.classList.add('active');
      }
    }
  }
  
  /**
   * Setup pull-to-refresh functionality for lists
   */
  function setupPullToRefresh() {
    // Only enable on pages that have a refresh-container
    const refreshContainer = document.querySelector('.refresh-container');
    if (!refreshContainer) return;
    
    let touchStartY = 0;
    let touchEndY = 0;
    let refreshing = false;
    let pullDistance = 0;
    const maxPullDistance = 80;
    
    // Create refresh indicator if it doesn't exist
    let refreshIndicator = document.querySelector('.refresh-indicator');
    if (!refreshIndicator) {
      refreshIndicator = document.createElement('div');
      refreshIndicator.className = 'refresh-indicator';
      refreshIndicator.innerHTML = `
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
          <path fill="none" d="M0 0h24v24H0z"/>
          <path d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10zm0-2a8 8 0 1 0 0-16 8 8 0 0 0 0 16zm1-8h4v2h-6V7h2v5z" fill="currentColor"/>
        </svg>
      `;
      refreshContainer.prepend(refreshIndicator);
    }
    
    // Add pull to refresh styles
    const style = document.createElement('style');
    style.textContent = `
      .refresh-container {
        position: relative;
        overflow-y: auto;
        -webkit-overflow-scrolling: touch;
      }
      
      .refresh-indicator {
        position: absolute;
        left: 50%;
        transform: translateX(-50%) translateY(-100%);
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background-color: var(--bg-primary);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        z-index: 5;
        transition: transform 0.3s;
      }
      
      .refresh-indicator svg {
        transition: transform 0.3s;
      }
      
      .refresh-indicator.pulled {
        transform: translateX(-50%) translateY(10px);
      }
      
      .refresh-indicator.refreshing svg {
        animation: spin 1s linear infinite;
      }
      
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
    `;
    document.head.appendChild(style);
    
    // Touch events
    refreshContainer.addEventListener('touchstart', (e) => {
      if (refreshContainer.scrollTop === 0) {
        touchStartY = e.touches[0].clientY;
      }
    }, { passive: true });
    
    refreshContainer.addEventListener('touchmove', (e) => {
      if (refreshing) return;
      
      // Only activate when at the top of the container
      if (refreshContainer.scrollTop === 0) {
        touchEndY = e.touches[0].clientY;
        pullDistance = touchEndY - touchStartY;
        
        if (pullDistance > 0) {
          // Prevent default only when we're pulling down
          e.preventDefault();
          
          // Apply resistance to make the pull feel natural
          const pullWithResistance = Math.min(pullDistance * 0.5, maxPullDistance);
          
          // Update indicator position
          refreshIndicator.style.transform = `translateX(-50%) translateY(${pullWithResistance - 40}px)`;
          
          // Rotate the icon based on pull distance
          const rotationDegree = (pullWithResistance / maxPullDistance) * 360;
          refreshIndicator.querySelector('svg').style.transform = `rotate(${rotationDegree}deg)`;
          
          if (pullWithResistance > 40) {
            refreshIndicator.classList.add('pulled');
          } else {
            refreshIndicator.classList.remove('pulled');
          }
        }
      }
    }, { passive: false });
    
    refreshContainer.addEventListener('touchend', (e) => {
      if (refreshing) return;
      
      if (pullDistance > 60) {
        // Trigger refresh
        refreshing = true;
        refreshIndicator.classList.add('refreshing');
        
        // Perform the refresh (reload the page for example)
        triggerRefresh();
      } else {
        // Reset the indicator
        refreshIndicator.style.transform = 'translateX(-50%) translateY(-100%)';
        refreshIndicator.classList.remove('pulled');
        refreshIndicator.querySelector('svg').style.transform = 'rotate(0deg)';
      }
      
      pullDistance = 0;
    }, { passive: true });
    
    function triggerRefresh() {
      // Simulate refresh for 1 second, then reload page
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    }
  }
  
  /**
   * Setup interactions for list items
   */
  function setupListItemInteractions() {
    // Setup custom checkboxes
    const checkboxes = document.querySelectorAll('.custom-checkbox');
    
    checkboxes.forEach(checkbox => {
      checkbox.addEventListener('click', () => {
        const listItem = checkbox.closest('.list-item');
        
        // Toggle checked state
        checkbox.classList.toggle('checked');
        
        if (listItem) {
          listItem.classList.toggle('checked');
          
          // Get the item data
          const itemId = listItem.dataset.itemId;
          const listId = document.querySelector('.shopping-list').dataset.listId;
          
          // Update on server
          updateItemStatus(listId, itemId, checkbox.classList.contains('checked'));
        }
      });
    });
    
    // Setup list item action buttons
    const priceButtons = document.querySelectorAll('.add-price-btn');
    
    priceButtons.forEach(button => {
      button.addEventListener('click', (e) => {
        e.stopPropagation(); // Prevent triggering the list item click
        const listItem = button.closest('.list-item');
        
        if (listItem) {
          const itemId = listItem.dataset.itemId;
          const listId = document.querySelector('.shopping-list').dataset.listId;
          
          // Open price modal
          openPriceModal(listId, itemId);
        }
      });
    });
  }