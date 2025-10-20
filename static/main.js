// Utility: Debounce function for performance
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Utility: Show loading state on form submission
function handleFormSubmit(form) {
  const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
  submitButtons.forEach(button => {
    button.disabled = true;
    const originalText = button.textContent || button.value;
    button.dataset.originalText = originalText;
    if (button.tagName === 'BUTTON') {
      button.textContent = 'Loading...';
    } else {
      button.value = 'Loading...';
    }
  });
}

// Utility: Wrap tables for mobile scrolling
function wrapTablesForMobile() {
  const tables = document.querySelectorAll('table:not(.wrapped)');
  tables.forEach(table => {
    if (!table.parentElement.classList.contains('table-container')) {
      const wrapper = document.createElement('div');
      wrapper.className = 'table-container';
      table.parentNode.insertBefore(wrapper, table);
      wrapper.appendChild(table);
      table.classList.add('wrapped');
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  console.log("Charter Pool initialized!");
  
  // Auto-hide flash messages after 5 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 500);
    }, 5000);
  });
  
  // Wrap tables for mobile scrolling
  wrapTablesForMobile();
  
  // Event delegation for form submissions
  document.addEventListener('submit', (e) => {
    if (e.target.tagName === 'FORM' && !e.target.classList.contains('no-loading')) {
      handleFormSubmit(e.target);
    }
  });
  
  // Event delegation for table row highlighting (desktop only)
  if (window.innerWidth > 768) {
    document.addEventListener('mouseenter', (e) => {
      if (e.target.closest('table tbody tr')) {
        const row = e.target.closest('table tbody tr');
        if (!row.classList.contains('highlight')) {
          row.style.backgroundColor = '#f8f9fa';
        }
      }
    }, true);
    
    document.addEventListener('mouseleave', (e) => {
      if (e.target.closest('table tbody tr')) {
        const row = e.target.closest('table tbody tr');
        if (!row.classList.contains('highlight')) {
          row.style.backgroundColor = '';
        }
      }
    }, true);
  }
  
  // Add touch-friendly tap effects on mobile
  if ('ontouchstart' in window) {
    document.addEventListener('touchstart', (e) => {
      if (e.target.closest('.btn, a, button')) {
        const element = e.target.closest('.btn, a, button');
        element.style.opacity = '0.7';
      }
    });
    
    document.addEventListener('touchend', (e) => {
      if (e.target.closest('.btn, a, button')) {
        const element = e.target.closest('.btn, a, button');
        setTimeout(() => {
          element.style.opacity = '1';
        }, 150);
      }
    });
  }
  
  // Debounced search handling (if search inputs exist)
  const searchInputs = document.querySelectorAll('input[type="search"], input[name*="search"]');
  searchInputs.forEach(input => {
    const debouncedHandler = debounce((e) => {
      console.log('Search query:', e.target.value);
      // Search logic would be triggered here
    }, 300);
    
    input.addEventListener('input', debouncedHandler);
  });
  
  // Lazy loading for heavy content (if needed in future)
  if ('IntersectionObserver' in window) {
    const lazyElements = document.querySelectorAll('[data-lazy]');
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const element = entry.target;
          // Trigger lazy loading here
          observer.unobserve(element);
        }
      });
    });
    
    lazyElements.forEach(el => observer.observe(el));
  }
});
