// Responsive menu script for LOCOTO
document.addEventListener('DOMContentLoaded', function() {
  console.log('💯 LOCOTO Enhanced Responsive Menu v2.0 loaded');
  
  // Get menu elements - target all possible structures across different pages
  const menuTrigger = document.querySelector('.menu-trigger');
  
  // Try different selectors for the nav element (order matters - most specific first)
  const navSelectors = [
    '.main-nav .nav',
    '.header-area .main-nav .nav',
    'nav .nav',
    'nav ul.nav'
  ];
  
  let navElement = null;
  
  // Try each selector until we find a matching element
  for (const selector of navSelectors) {
    const element = document.querySelector(selector);
    if (element) {
      navElement = element;
      console.log(`Nav element found with selector: ${selector}`);
      break;
    }
  }
  
  console.log('Menu elements found:', {
    menuTrigger: menuTrigger ? 'Yes' : 'No',
    navElement: navElement ? 'Yes' : 'No',
    page: window.location.pathname
  });
  
  if (!menuTrigger) {
    console.error('Menu trigger not found on page:', window.location.pathname);
    return;
  }
  
  if (!navElement) {
    console.error('Navigation element not found on page:', window.location.pathname);
    // Fallback - try to find any nav element to attach to
    navElement = document.querySelector('nav') || document.querySelector('header');
    if (!navElement) {
      console.error('No fallback navigation element found');
      return;
    }
    console.warn('Using fallback navigation element');
  }
  
  // Apply z-index to ensure menu appears on top
  if (navElement.style) {
    navElement.style.zIndex = '1000';
  }
  
  // Find the main content element to adjust padding when menu opens
  const mainBanner = document.querySelector('.main-banner');
  
  // Toggle menu on click
  menuTrigger.addEventListener('click', function(e) {
    e.preventDefault();
    e.stopPropagation();
    
    console.log('Menu trigger clicked on page:', window.location.pathname);
    menuTrigger.classList.toggle('active');
    navElement.classList.toggle('active');
    
    // Force display: block to ensure visibility
    if (navElement.classList.contains('active')) {
      navElement.style.display = 'block';
      
      // Adjust main content to prevent overlap on small screens
      if (window.innerWidth <= 991 && mainBanner) {
        // Calculate the expanded menu height
        const menuHeight = navElement.offsetHeight;
        // Add extra padding to main content to accommodate the open menu
        if (menuHeight > 0) {
          mainBanner.style.marginTop = (120 + menuHeight) + 'px';
          mainBanner.style.transition = 'margin-top 0.3s ease';
        }
      }
    } else {
      // Let CSS handle this when inactive
      navElement.style.removeProperty('display');
      
      // Reset main content positioning
      if (mainBanner) {
        mainBanner.style.marginTop = '';
        // Keep the transition for smooth animation
        setTimeout(() => {
          mainBanner.style.transition = '';
        }, 300);
      }
    }
    
    console.log('Nav toggled:', navElement.classList.contains('active'));
  });
  
  // Close menu when clicking outside
  document.addEventListener('click', function(e) {
    // If clicked outside nav and menu is active
    if (!e.target.closest('.main-nav') && 
        !e.target.closest('.menu-trigger') && 
        navElement.classList.contains('active')) {
      navElement.classList.remove('active');
      menuTrigger.classList.remove('active');
      // Let CSS handle display when inactive
      navElement.style.removeProperty('display');
      
      // Reset main content positioning
      if (mainBanner) {
        mainBanner.style.marginTop = '';
        // Keep the transition for smooth animation
        setTimeout(() => {
          mainBanner.style.transition = '';
        }, 300);
      }
      
      console.log('Closing menu from document click');
    }
  });
  
  // Close menu if window resized beyond breakpoint
  window.addEventListener('resize', function() {
    if (window.innerWidth > 991) {
      navElement.classList.remove('active');
      menuTrigger.classList.remove('active');
      // Let CSS handle display
      navElement.style.removeProperty('display');
      
      // Reset main content positioning
      if (mainBanner) {
        mainBanner.style.marginTop = '';
        mainBanner.style.transition = '';
      }
      
      console.log('Closing menu from resize');
    }
  });

  // Disable any jQuery handlers to prevent conflicts
  if (typeof jQuery !== 'undefined') {
    try {
      jQuery(document).off('click', '.menu-trigger');
      jQuery('.menu-trigger').off('click');
      jQuery(document).off('click', '.main-nav .nav');
      jQuery('.main-nav .nav').off('click');
      console.log('Disabled jQuery menu handlers');
    } catch (e) {
      console.error('Error disabling jQuery handlers:', e);
    }
  }

  // Let's make sure the menu trigger is visible
  try {
    const computedStyle = window.getComputedStyle(menuTrigger);
    console.log('Menu trigger display:', computedStyle.display);
    if (computedStyle.display === 'none') {
      console.warn('Menu trigger is hidden by CSS on page:', window.location.pathname);
    }
    
    // Make sure the menu trigger has pointer cursor
    menuTrigger.style.cursor = 'pointer';
  } catch (e) {
    console.error('Error checking menu trigger visibility:', e);
  }
  
  // Add swipe support for touch devices
  let touchStartX = 0;
  let touchEndX = 0;
  
  document.addEventListener('touchstart', function(e) {
    touchStartX = e.changedTouches[0].screenX;
  }, false);
  
  document.addEventListener('touchend', function(e) {
    touchEndX = e.changedTouches[0].screenX;
    handleSwipe();
  }, false);
  
  function handleSwipe() {
    // Left swipe (open menu)
    if (touchEndX < touchStartX - 75) {
      if (!navElement.classList.contains('active')) {
        menuTrigger.classList.add('active');
        navElement.classList.add('active');
        navElement.style.display = 'block';
        console.log('Opening menu from left swipe');
        
        // Adjust main content
        if (window.innerWidth <= 991 && mainBanner) {
          const menuHeight = navElement.offsetHeight;
          if (menuHeight > 0) {
            mainBanner.style.marginTop = (120 + menuHeight) + 'px';
            mainBanner.style.transition = 'margin-top 0.3s ease';
          }
        }
      }
    }
    
    // Right swipe (close menu)
    if (touchEndX > touchStartX + 75) {
      if (navElement.classList.contains('active')) {
        navElement.classList.remove('active');
        menuTrigger.classList.remove('active');
        navElement.style.removeProperty('display');
        console.log('Closing menu from right swipe');
        
        // Reset main content
        if (mainBanner) {
          mainBanner.style.marginTop = '';
          setTimeout(() => {
            mainBanner.style.transition = '';
          }, 300);
        }
      }
    }
  }
}); 