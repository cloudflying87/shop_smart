/**
 * Theme Manager for ShopSmart
 * 
 * Handles theme switching between light and dark modes
 */

class ThemeManager {
    constructor() {
      this.themeToggle = document.getElementById('theme-toggle');
      this.currentTheme = localStorage.getItem('theme') || 'light';
      
      this.init();
    }
    
    /**
     * Initialize the theme manager
     */
    init() {
      // Set initial theme
      this.setTheme(this.currentTheme);
      
      // Add event listener to theme toggle button
      if (this.themeToggle) {
        this.themeToggle.addEventListener('click', () => {
          this.toggleTheme();
        });
      }
      
      // Check if user has system preference for dark mode
      this.checkSystemPreference();
    }
    
    /**
     * Set the current theme
     * @param {string} theme - Theme name ('light' or 'dark')
     */
    setTheme(theme) {
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('theme', theme);
      this.currentTheme = theme;
      
      // Update meta theme-color for browser UI
      const metaThemeColor = document.querySelector('meta[name="theme-color"]');
      if (metaThemeColor) {
        metaThemeColor.setAttribute(
          'content',
          theme === 'dark' ? '#121212' : '#4CAF50'
        );
      }
    }
    
    /**
     * Toggle between light and dark themes
     */
    toggleTheme() {
      const newTheme = this.currentTheme === 'light' ? 'dark' : 'light';
      this.setTheme(newTheme);
      
      // Announce theme change for screen readers
      this.announceThemeChange(newTheme);
    }
    
    /**
     * Check if user has system preference for dark mode
     */
    checkSystemPreference() {
      // Only apply system preference if user hasn't manually set a theme
      if (!localStorage.getItem('theme')) {
        const prefersDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        if (prefersDarkMode) {
          this.setTheme('dark');
        }
        
        // Listen for changes in system preference
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (event) => {
          if (!localStorage.getItem('theme')) {
            this.setTheme(event.matches ? 'dark' : 'light');
          }
        });
      }
    }
    
    /**
     * Announce theme change for screen readers
     * @param {string} theme - New theme
     */
    announceThemeChange(theme) {
      const announcement = document.createElement('div');
      announcement.setAttribute('aria-live', 'polite');
      announcement.setAttribute('class', 'sr-only');
      announcement.textContent = `Theme changed to ${theme} mode`;
      
      document.body.appendChild(announcement);
      
      // Remove the announcement after it's been read
      setTimeout(() => {
        document.body.removeChild(announcement);
      }, 3000);
    }
  }
  
  // Initialize the theme manager
  document.addEventListener('DOMContentLoaded', () => {
    window.themeManager = new ThemeManager();
  });