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
  
  // Auto-hiding header on scroll
  let lastScrollTop = 0;
  let scrollTimeout;
  const header = document.querySelector('header');
  
  if (header && window.innerWidth <= 768) {
    window.addEventListener('scroll', () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > lastScrollTop && scrollTop > 100) {
          // Scrolling down
          header.classList.add('header-hidden');
        } else {
          // Scrolling up
          header.classList.remove('header-hidden');
        }
        
        lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
      }, 100);
    }, { passive: true });
  }
  
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
    
    // Close menu on escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && menuToggle.getAttribute('aria-expanded') === 'true') {
        menuToggle.setAttribute('aria-expanded', 'false');
        nav.classList.remove('mobile-menu-open');
        menuToggle.focus();
      }
    });
  }
  
  // Enhanced flash message handling
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    // Add dismiss button
    const dismissBtn = document.createElement('button');
    dismissBtn.className = 'alert-dismiss';
    dismissBtn.innerHTML = '×';
    dismissBtn.setAttribute('aria-label', 'Dismiss alert');
    dismissBtn.addEventListener('click', () => dismissAlert(alert));
    alert.appendChild(dismissBtn);
    
    // Auto-dismiss after 5 seconds
    const autoDismissTimeout = setTimeout(() => {
      dismissAlert(alert);
    }, 5000);
    
    // Swipe to dismiss on mobile
    if ('ontouchstart' in window) {
      let startX = 0;
      let currentX = 0;
      
      alert.addEventListener('touchstart', (e) => {
        startX = e.touches[0].clientX;
        alert.style.transition = 'none';
      }, { passive: true });
      
      alert.addEventListener('touchmove', (e) => {
        currentX = e.touches[0].clientX;
        const deltaX = currentX - startX;
        if (deltaX > 0) {
          alert.style.transform = `translateX(${deltaX}px)`;
          alert.style.opacity = 1 - (deltaX / 200);
        }
      }, { passive: true });
      
      alert.addEventListener('touchend', () => {
        const deltaX = currentX - startX;
        if (deltaX > 100) {
          clearTimeout(autoDismissTimeout);
          dismissAlert(alert);
        } else {
          alert.style.transition = 'transform 0.3s, opacity 0.3s';
          alert.style.transform = 'translateX(0)';
          alert.style.opacity = '1';
        }
      }, { passive: true });
    }
  });
  
  function dismissAlert(alert) {
    alert.classList.add('dismissing');
    setTimeout(() => alert.remove(), 300);
  }
  
  // Wrap tables for mobile scrolling
  wrapTablesForMobile();
  
  // Smooth scroll to focused inputs on mobile
  if (window.innerWidth <= 768) {
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
      input.addEventListener('focus', () => {
        setTimeout(() => {
          input.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 300);
      });
    });
  }
  
  // Enhanced form submission handling
  document.addEventListener('submit', (e) => {
    if (e.target.tagName === 'FORM' && !e.target.classList.contains('no-loading')) {
      const form = e.target;
      handleFormSubmit(form);
      
      // Add loading class to submit button
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.classList.add('loading');
        submitBtn.disabled = true;
      }
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
  
  // Enable card view for tables on mobile
  if (window.innerWidth <= 600) {
    const leaderboardTables = document.querySelectorAll('.leaderboard-table');
    leaderboardTables.forEach(table => {
      table.classList.add('card-view');
      
      // Add data-label attributes for mobile card view
      const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
      const rows = table.querySelectorAll('tbody tr');
      
      rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        cells.forEach((cell, index) => {
          if (headers[index]) {
            cell.setAttribute('data-label', headers[index]);
          }
        });
      });
    });
  }
  
  // Scroll animations with Intersection Observer
  if ('IntersectionObserver' in window) {
    const animatedElements = document.querySelectorAll('.card, .game-item, .tournament-card');
    
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry, index) => {
        if (entry.isIntersecting) {
          setTimeout(() => {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
          }, index * 50);
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);
    
    animatedElements.forEach(el => {
      el.style.opacity = '0';
      el.style.transform = 'translateY(20px)';
      el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      observer.observe(el);
    });
    
    // Lazy loading for heavy content
    const lazyElements = document.querySelectorAll('[data-lazy]');
    lazyElements.forEach(el => observer.observe(el));
  }
  
  // Performance: Add will-change to elements during scroll
  let scrolling = false;
  window.addEventListener('scroll', () => {
    if (!scrolling) {
      scrolling = true;
      document.body.style.willChange = 'scroll-position';
      
      setTimeout(() => {
        scrolling = false;
        document.body.style.willChange = 'auto';
      }, 300);
    }
  }, { passive: true });
});
