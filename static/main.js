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
  
  // Lazy loading for heavy content
  if ('IntersectionObserver' in window) {
    const lazyElements = document.querySelectorAll('[data-lazy]');
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const element = entry.target;
          
          // Lazy load images
          if (element.dataset.src) {
            element.src = element.dataset.src;
            element.removeAttribute('data-src');
          }
          
          // Lazy load content
          if (element.dataset.lazyContent) {
            const url = element.dataset.lazyContent;
            fetch(url)
              .then(response => response.text())
              .then(html => {
                element.innerHTML = html;
              })
              .catch(err => console.error('Failed to load content:', err));
          }
          
          observer.unobserve(element);
        }
      });
    }, {
      rootMargin: '50px' // Load slightly before entering viewport
    });
    
    lazyElements.forEach(el => observer.observe(el));
  }
  
  // Prefetch links on hover for faster navigation
  if ('requestIdleCallback' in window) {
    const prefetchLink = (url) => {
      const link = document.createElement('link');
      link.rel = 'prefetch';
      link.href = url;
      document.head.appendChild(link);
    };
    
    const prefetchedUrls = new Set();
    
    document.addEventListener('mouseover', (e) => {
      const link = e.target.closest('a[href^="/"]');
      if (link && !prefetchedUrls.has(link.href)) {
        requestIdleCallback(() => {
          prefetchLink(link.href);
          prefetchedUrls.add(link.href);
        });
      }
    }, { passive: true });
  }
  
  // Performance: Use requestAnimationFrame for smooth animations
  let rafId = null;
  const smoothScroll = (target) => {
    if (rafId) cancelAnimationFrame(rafId);
    
    const start = window.pageYOffset;
    const end = target.offsetTop;
    const distance = end - start;
    const duration = 500;
    const startTime = performance.now();
    
    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const ease = progress < 0.5 ? 2 * progress * progress : -1 + (4 - 2 * progress) * progress;
      
      window.scrollTo(0, start + distance * ease);
      
      if (progress < 1) {
        rafId = requestAnimationFrame(animate);
      }
    };
    
    rafId = requestAnimationFrame(animate);
  };
  
  // Use smooth scroll for anchor links
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a[href^="#"]');
    if (link) {
      e.preventDefault();
      const target = document.querySelector(link.getAttribute('href'));
      if (target) {
        smoothScroll(target);
      }
    }
  });
  
  // Client-side caching for AJAX requests
  const requestCache = new Map();
  const cachedFetch = (url, options = {}) => {
    const cacheKey = `${url}:${JSON.stringify(options)}`;
    const cached = requestCache.get(cacheKey);
    
    if (cached && Date.now() - cached.timestamp < 60000) { // 1 minute cache
      return Promise.resolve(cached.data);
    }
    
    return fetch(url, options)
      .then(response => response.clone().json().then(data => {
        requestCache.set(cacheKey, { data, timestamp: Date.now() });
        return data;
      }));
  };
  
  // Expose cached fetch globally for other scripts
  window.cachedFetch = cachedFetch;
  
  // Performance: Batch DOM updates
  let updateQueue = [];
  let updateScheduled = false;
  
  const batchDOMUpdate = (updateFn) => {
    updateQueue.push(updateFn);
    
    if (!updateScheduled) {
      updateScheduled = true;
      requestAnimationFrame(() => {
        updateQueue.forEach(fn => fn());
        updateQueue = [];
        updateScheduled = false;
      });
    }
  };
  
  window.batchDOMUpdate = batchDOMUpdate;
  
  // Virtual scrolling for large tables (if needed)
  const initVirtualScroll = (container, rowHeight = 50) => {
    if (!container) return;
    
    const rows = Array.from(container.querySelectorAll('tbody tr'));
    if (rows.length < 100) return; // Only virtualize large lists
    
    const totalHeight = rows.length * rowHeight;
    const viewportHeight = container.clientHeight;
    const visibleRows = Math.ceil(viewportHeight / rowHeight) + 2; // Buffer rows
    
    let scrollTop = 0;
    
    container.addEventListener('scroll', () => {
      scrollTop = container.scrollTop;
      const startIdx = Math.floor(scrollTop / rowHeight);
      const endIdx = Math.min(startIdx + visibleRows, rows.length);
      
      batchDOMUpdate(() => {
        rows.forEach((row, idx) => {
          if (idx >= startIdx && idx < endIdx) {
            row.style.display = '';
            row.style.transform = `translateY(${idx * rowHeight}px)`;
          } else {
            row.style.display = 'none';
          }
        });
      });
    }, { passive: true });
  };
  
  // Initialize virtual scroll for large tables
  const largeTables = document.querySelectorAll('.table-container table');
  largeTables.forEach(table => {
    if (table.querySelectorAll('tbody tr').length > 100) {
      initVirtualScroll(table.closest('.table-container'));
    }
  });
});
