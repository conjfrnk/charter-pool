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
  
  // Mobile menu toggle
  const menuToggle = document.querySelector('.mobile-menu-toggle');
  const nav = document.querySelector('.nav');
  
  if (menuToggle && nav) {
    menuToggle.addEventListener('click', () => {
      const isOpen = menuToggle.getAttribute('aria-expanded') === 'true';
      menuToggle.setAttribute('aria-expanded', !isOpen);
      nav.classList.toggle('mobile-menu-open');
    });
    
    // Close menu when clicking a link
    nav.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', () => {
        menuToggle.setAttribute('aria-expanded', 'false');
        nav.classList.remove('mobile-menu-open');
      });
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!e.target.closest('header')) {
        menuToggle.setAttribute('aria-expanded', 'false');
        nav.classList.remove('mobile-menu-open');
      }
    });
  }
  
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
  
  // Add touch-friendly tap effects on mobile with passive listeners
  if ('ontouchstart' in window) {
    document.addEventListener('touchstart', (e) => {
      if (e.target.closest('.btn, a, button')) {
        const element = e.target.closest('.btn, a, button');
        element.style.opacity = '0.7';
      }
    }, { passive: true });
    
    document.addEventListener('touchend', (e) => {
      if (e.target.closest('.btn, a, button')) {
        const element = e.target.closest('.btn, a, button');
        setTimeout(() => {
          element.style.opacity = '1';
        }, 150);
      }
    }, { passive: true });
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

  // Confirm before submitting report game form
  const reportForm = document.querySelector('.game-report-form');
  if (reportForm) {
    reportForm.addEventListener('submit', (e) => {
      const gameType = (new FormData(reportForm)).get('game_type') || 'singles';
      if (gameType === 'singles') {
        const opponent = (new FormData(reportForm)).get('opponent_netid');
        const winner = (new FormData(reportForm)).get('winner_netid');
        if (!opponent || !winner) return; // native required will handle
        const msg = `Submit singles result?\nOpponent: ${opponent}\nWinner: ${winner}`;
        if (!confirm(msg)) {
          e.preventDefault();
          return false;
        }
      } else {
        const partner = (new FormData(reportForm)).get('partner_netid');
        const opp1 = (new FormData(reportForm)).get('opponent1_netid');
        const opp2 = (new FormData(reportForm)).get('opponent2_netid');
        const winningTeam = (new FormData(reportForm)).get('winning_team');
        if (!partner || !opp1 || !opp2 || !winningTeam) return;
        const msg = `Submit doubles result?\nPartner: ${partner}\nOpponents: ${opp1}, ${opp2}\nWinning team: ${winningTeam}`;
        if (!confirm(msg)) {
          e.preventDefault();
          return false;
        }
      }
    });
  }
  
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
