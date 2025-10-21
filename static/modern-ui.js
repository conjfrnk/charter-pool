/* ========================================
   Modern UI JavaScript - Enhanced Interactions
   ======================================== */

class CharterPoolUI {
  constructor() {
    this.theme = localStorage.getItem('theme') || 'light';
    this.touchStartY = 0;
    this.touchEndY = 0;
    this.pullDistance = 0;
    this.isRefreshing = false;
    
    this.init();
  }
  
  init() {
    // Initialize theme
    this.initTheme();
    
    // Initialize mobile interactions
    this.initMobileInteractions();
    
    // Initialize toast system
    this.initToastSystem();
    
    // Initialize form enhancements
    this.initFormEnhancements();
    
    // Initialize pull to refresh
    this.initPullToRefresh();
    
    // Initialize swipe gestures
    this.initSwipeGestures();
    
    // Initialize skeleton loading
    this.initSkeletonLoading();
    
    // Convert flash messages to toasts
    this.convertFlashToToasts();
    
    // Initialize ripple effects
    this.initRippleEffects();
    
    // Initialize lazy loading
    this.initLazyLoading();
    
    // Initialize page transitions
    this.initPageTransitions();
    
    // Initialize scroll animations
    this.initScrollAnimations();
    
    // Add page load complete
    this.onPageLoad();
  }
  
  /* ========================================
     Page Load & Transitions
     ======================================== */
  
  onPageLoad() {
    // Fade in content
    document.body.classList.add('loaded');
    
    // Remove loading indicator
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
      loadingIndicator.classList.remove('active');
    }
  }
  
  initPageTransitions() {
    // Show loading indicator on link clicks
    document.querySelectorAll('a:not([target="_blank"])').forEach(link => {
      link.addEventListener('click', (e) => {
        // Only show for navigation links (not anchors)
        if (!link.href.includes('#') && link.href.includes(window.location.origin)) {
          const loadingIndicator = document.getElementById('loading-indicator');
          if (loadingIndicator) {
            loadingIndicator.classList.add('active');
          }
        }
      });
    });
    
    // Listen for beforeunload
    window.addEventListener('beforeunload', () => {
      const loadingIndicator = document.getElementById('loading-indicator');
      if (loadingIndicator) {
        loadingIndicator.classList.add('active');
      }
    });
  }
  
  /* ========================================
     Scroll Animations
     ======================================== */
  
  initScrollAnimations() {
    // Fade in elements on scroll
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('animate-in');
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);
    
    // Observe cards and major elements
    document.querySelectorAll('.card, .table-card, .game-history-card, .tournament-card-modern').forEach(el => {
      el.classList.add('animate-on-scroll');
      observer.observe(el);
    });
  }
  
  /* ========================================
     Theme Management
     ======================================== */
  
  initTheme() {
    // Apply saved theme
    document.body.setAttribute('data-theme', this.theme);
    
    // Update icon visibility
    this.updateThemeIcon();
    
    // Theme toggle button
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', () => this.toggleTheme());
    }
    
    // Listen for system theme changes
    if (window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
        if (!localStorage.getItem('theme')) {
          this.theme = e.matches ? 'dark' : 'light';
          document.body.setAttribute('data-theme', this.theme);
          this.updateThemeIcon();
        }
      });
    }
  }
  
  toggleTheme() {
    this.theme = this.theme === 'light' ? 'dark' : 'light';
    document.body.setAttribute('data-theme', this.theme);
    localStorage.setItem('theme', this.theme);
    this.updateThemeIcon();
    
    // Show toast notification
    this.showToast(`Switched to ${this.theme} mode`, 'success');
  }
  
  updateThemeIcon() {
    const lightIcon = document.getElementById('theme-icon-light');
    const darkIcon = document.getElementById('theme-icon-dark');
    
    if (lightIcon && darkIcon) {
      if (this.theme === 'light') {
        lightIcon.classList.remove('hidden');
        darkIcon.classList.add('hidden');
      } else {
        lightIcon.classList.add('hidden');
        darkIcon.classList.remove('hidden');
      }
    }
  }
  
  /* ========================================
     Toast Notifications
     ======================================== */
  
  initToastSystem() {
    // Create global toast method
    window.showToast = (message, type = 'info', duration = 3000) => {
      this.showToast(message, type, duration);
    };
  }
  
  showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    // Icon based on type
    const icons = {
      success: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>',
      error: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>',
      warning: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>',
      info: '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>'
    };
    
    toast.innerHTML = `
      <svg class="toast-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        ${icons[type] || icons.info}
      </svg>
      <span class="toast-message">${message}</span>
      <button class="toast-close" aria-label="Close notification">
        <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    `;
    
    // Add to container
    container.appendChild(toast);
    
    // Close button functionality
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => this.removeToast(toast));
    
    // Auto remove after duration
    setTimeout(() => this.removeToast(toast), duration);
    
    // Announce to screen readers
    const announcement = document.createElement('div');
    announcement.className = 'sr-only';
    announcement.setAttribute('role', 'status');
    announcement.textContent = message;
    container.appendChild(announcement);
    setTimeout(() => announcement.remove(), 100);
  }
  
  removeToast(toast) {
    toast.classList.add('hiding');
    setTimeout(() => toast.remove(), 300);
  }
  
  convertFlashToToasts() {
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(alert => {
      const message = alert.textContent.trim();
      let type = 'info';
      
      if (alert.classList.contains('alert-success')) type = 'success';
      else if (alert.classList.contains('alert-error') || alert.classList.contains('alert-danger')) type = 'error';
      else if (alert.classList.contains('alert-warning')) type = 'warning';
      
      this.showToast(message, type, 5000);
      alert.remove();
    });
  }
  
  /* ========================================
     Pull to Refresh
     ======================================== */
  
  initPullToRefresh() {
    if (!('ontouchstart' in window)) return;
    
    const refreshIndicator = document.getElementById('pull-to-refresh');
    if (!refreshIndicator) return;
    
    let startY = 0;
    let currentY = 0;
    let pulling = false;
    
    document.addEventListener('touchstart', (e) => {
      if (window.scrollY === 0) {
        startY = e.touches[0].pageY;
        pulling = true;
      }
    }, { passive: true });
    
    document.addEventListener('touchmove', (e) => {
      if (!pulling) return;
      
      currentY = e.touches[0].pageY;
      const diff = currentY - startY;
      
      if (diff > 0 && diff < 150) {
        this.pullDistance = diff;
        const opacity = Math.min(diff / 100, 1);
        refreshIndicator.style.opacity = opacity;
        refreshIndicator.style.transform = `translateX(-50%) translateY(${Math.min(diff - 40, 60)}px) rotate(${diff * 2}deg)`;
        
        if (diff > 60) {
          refreshIndicator.classList.add('visible');
        }
      }
    }, { passive: true });
    
    document.addEventListener('touchend', () => {
      if (pulling && this.pullDistance > 100 && !this.isRefreshing) {
        this.triggerRefresh();
      } else {
        this.resetPullToRefresh();
      }
      pulling = false;
      this.pullDistance = 0;
    });
  }
  
  triggerRefresh() {
    const refreshIndicator = document.getElementById('pull-to-refresh');
    if (!refreshIndicator) return;
    
    this.isRefreshing = true;
    refreshIndicator.classList.add('refreshing');
    
    // Simulate refresh (in real app, make API call here)
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  }
  
  resetPullToRefresh() {
    const refreshIndicator = document.getElementById('pull-to-refresh');
    if (!refreshIndicator) return;
    
    refreshIndicator.classList.remove('visible', 'refreshing');
    refreshIndicator.style.opacity = '0';
    refreshIndicator.style.transform = 'translateX(-50%) translateY(-60px)';
  }
  
  /* ========================================
     Swipe Gestures
     ======================================== */
  
  initSwipeGestures() {
    if (!('ontouchstart' in window)) return;
    
    let touchStartX = 0;
    let touchEndX = 0;
    let touchStartY = 0;
    let touchEndY = 0;
    
    document.addEventListener('touchstart', (e) => {
      touchStartX = e.changedTouches[0].screenX;
      touchStartY = e.changedTouches[0].screenY;
    }, { passive: true });
    
    document.addEventListener('touchend', (e) => {
      touchEndX = e.changedTouches[0].screenX;
      touchEndY = e.changedTouches[0].screenY;
      this.handleSwipe(touchStartX, touchEndX, touchStartY, touchEndY);
    }, { passive: true });
  }
  
  handleSwipe(startX, endX, startY, endY) {
    const diffX = endX - startX;
    const diffY = endY - startY;
    const threshold = 100;
    
    // Only handle horizontal swipes
    if (Math.abs(diffX) > Math.abs(diffY) && Math.abs(diffX) > threshold) {
      const currentPath = window.location.pathname;
      
      if (diffX > 0) {
        // Swiped right - go to previous section
        this.navigateToPrevious(currentPath);
      } else {
        // Swiped left - go to next section
        this.navigateToNext(currentPath);
      }
    }
  }
  
  navigateToNext(currentPath) {
    const navOrder = ['/', '/report-game', '/leaderboard', '/tournaments'];
    const currentIndex = navOrder.findIndex(path => currentPath.includes(path.replace('/', '')));
    
    if (currentIndex !== -1 && currentIndex < navOrder.length - 1) {
      window.location.href = navOrder[currentIndex + 1];
    }
  }
  
  navigateToPrevious(currentPath) {
    const navOrder = ['/', '/report-game', '/leaderboard', '/tournaments'];
    const currentIndex = navOrder.findIndex(path => currentPath.includes(path.replace('/', '')));
    
    if (currentIndex > 0) {
      window.location.href = navOrder[currentIndex - 1];
    }
  }
  
  /* ========================================
     Form Enhancements
     ======================================== */
  
  initFormEnhancements() {
    // Add floating label support
    document.querySelectorAll('.form-group input, .form-group select, .form-group textarea').forEach(input => {
      const formGroup = input.closest('.form-group');
      if (!formGroup) return;
      
      // Create floating label wrapper
      const label = formGroup.querySelector('label');
      if (label && !formGroup.classList.contains('form-floating')) {
        const wrapper = document.createElement('div');
        wrapper.className = 'form-floating';
        
        input.placeholder = ' '; // Required for CSS :placeholder-shown
        input.id = input.id || `input-${Math.random().toString(36).substr(2, 9)}`;
        label.setAttribute('for', input.id);
        
        input.parentNode.insertBefore(wrapper, input);
        wrapper.appendChild(input);
        wrapper.appendChild(label);
        
        // Remove from old position
        if (formGroup.contains(label)) {
          formGroup.classList.add('has-floating-label');
        }
      }
    });
    
    // Add input validation feedback
    document.querySelectorAll('input[required], select[required], textarea[required]').forEach(input => {
      input.addEventListener('blur', () => this.validateInput(input));
      input.addEventListener('input', () => {
        if (input.classList.contains('invalid')) {
          this.validateInput(input);
        }
      });
    });
    
    // Enhance form submissions
    document.querySelectorAll('form').forEach(form => {
      form.addEventListener('submit', (e) => this.handleFormSubmit(e, form));
    });
  }
  
  validateInput(input) {
    const isValid = input.checkValidity();
    
    if (!isValid) {
      input.classList.add('invalid');
      input.classList.remove('valid');
    } else if (input.value) {
      input.classList.add('valid');
      input.classList.remove('invalid');
    }
  }
  
  handleFormSubmit(e, form) {
    // Add loading state
    form.classList.add('loading');
    
    const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
    submitButtons.forEach(button => {
      button.disabled = true;
      const originalText = button.textContent || button.value;
      button.dataset.originalText = originalText;
      
      // Add loading spinner
      if (button.tagName === 'BUTTON') {
        button.innerHTML = `
          <svg class="loading-spinner" width="16" height="16" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none" stroke-dasharray="31.415" stroke-dashoffset="10" />
          </svg>
          Loading...
        `;
      }
    });
  }
  
  /* ========================================
     Mobile Interactions
     ======================================== */
  
  initMobileInteractions() {
    // Add active states for mobile buttons
    document.querySelectorAll('.btn, button, a').forEach(element => {
      element.classList.add('ripple');
    });
    
    // Improve touch targets
    document.querySelectorAll('input[type="checkbox"], input[type="radio"]').forEach(input => {
      const parent = input.parentElement;
      if (parent && parent.tagName === 'LABEL') {
        parent.style.minHeight = '44px';
        parent.style.display = 'flex';
        parent.style.alignItems = 'center';
      }
    });
    
    // Mobile menu improvements
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const nav = document.querySelector('.nav');
    
    if (mobileMenuToggle && nav) {
      // Close menu on escape key
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && nav.classList.contains('mobile-menu-open')) {
          mobileMenuToggle.setAttribute('aria-expanded', 'false');
          nav.classList.remove('mobile-menu-open');
        }
      });
      
      // Trap focus when menu is open
      nav.addEventListener('keydown', (e) => {
        if (!nav.classList.contains('mobile-menu-open')) return;
        
        const focusableElements = nav.querySelectorAll('a, button');
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        if (e.key === 'Tab') {
          if (e.shiftKey && document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          } else if (!e.shiftKey && document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      });
    }
  }
  
  /* ========================================
     Ripple Effects
     ======================================== */
  
  initRippleEffects() {
    document.querySelectorAll('.ripple').forEach(element => {
      element.addEventListener('click', function(e) {
        const ripple = document.createElement('span');
        const rect = this.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.classList.add('ripple-effect');
        
        this.appendChild(ripple);
        
        setTimeout(() => {
          ripple.remove();
        }, 600);
      });
    });
  }
  
  /* ========================================
     Skeleton Loading
     ======================================== */
  
  initSkeletonLoading() {
    // Add skeleton loading for async content
    window.showSkeleton = (container, count = 3) => {
      const skeletons = [];
      for (let i = 0; i < count; i++) {
        const skeleton = document.createElement('div');
        skeleton.className = 'skeleton-card skeleton';
        skeletons.push(skeleton);
        container.appendChild(skeleton);
      }
      return skeletons;
    };
    
    window.removeSkeleton = (skeletons) => {
      skeletons.forEach(skeleton => skeleton.remove());
    };
  }
  
  /* ========================================
     Lazy Loading
     ======================================== */
  
  initLazyLoading() {
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            img.classList.remove('lazy');
            observer.unobserve(img);
          }
        });
      });
      
      document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
      });
    }
  }
  
  /* ========================================
     Game Reporting Wizard
     ======================================== */
  
  initGameWizard() {
    const wizard = document.getElementById('game-wizard');
    if (!wizard) return;
    
    let currentStep = 1;
    let gameData = {
      type: 'singles',
      players: {}
    };
    
    const backBtn = document.getElementById('wizard-back');
    const nextBtn = document.getElementById('wizard-next');
    const submitBtn = document.getElementById('wizard-submit');
    
    // Game type selection
    document.querySelectorAll('.game-type-card').forEach(card => {
      card.addEventListener('click', () => {
        document.querySelectorAll('.game-type-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        gameData.type = card.dataset.type;
        document.getElementById('mobile_game_type').value = gameData.type;
      });
    });
    
    // Winner selection
    document.querySelectorAll('.winner-card').forEach(card => {
      card.addEventListener('click', () => {
        document.querySelectorAll('.winner-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        gameData.winner = card.dataset.winner;
      });
    });
    
    // Navigation
    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        if (this.validateStep(currentStep, gameData)) {
          currentStep++;
          this.updateWizardStep(currentStep, gameData);
        }
      });
    }
    
    if (backBtn) {
      backBtn.addEventListener('click', () => {
        currentStep--;
        this.updateWizardStep(currentStep, gameData);
      });
    }
    
    // Initialize player search for mobile
    this.initMobilePlayerSearch('mobile_opponent_search', 'mobile_search_results', 
                                'mobile_opponent_netid', 'mobile_selected_opponent', gameData);
    this.initMobilePlayerSearch('mobile_partner_search', 'mobile_partner_results', 
                                'mobile_partner_netid', 'mobile_selected_partner', gameData);
    this.initMobilePlayerSearch('mobile_opponent1_search', 'mobile_opponent1_results', 
                                'mobile_opponent1_netid', 'mobile_selected_opponent1', gameData);
    this.initMobilePlayerSearch('mobile_opponent2_search', 'mobile_opponent2_results', 
                                'mobile_opponent2_netid', 'mobile_selected_opponent2', gameData);
  }
  
  validateStep(step, gameData) {
    switch(step) {
      case 1:
        if (!gameData.type) {
          this.showToast('Please select a game type', 'error');
          return false;
        }
        break;
      case 2:
        if (gameData.type === 'singles' && !gameData.players.opponent) {
          this.showToast('Please select an opponent', 'error');
          return false;
        }
        if (gameData.type === 'doubles' && !gameData.players.partner) {
          this.showToast('Please select your partner', 'error');
          return false;
        }
        break;
      case 3:
        if (gameData.type === 'doubles' && (!gameData.players.opponent1 || !gameData.players.opponent2)) {
          this.showToast('Please select both opponents', 'error');
          return false;
        }
        if (!gameData.winner) {
          this.showToast('Please select the winner', 'error');
          return false;
        }
        break;
    }
    return true;
  }
  
  updateWizardStep(step, gameData) {
    // Update step indicators
    document.querySelectorAll('.wizard-step').forEach(s => {
      const stepNum = parseInt(s.dataset.step);
      s.classList.toggle('active', stepNum === step);
      s.classList.toggle('completed', stepNum < step);
    });
    
    // Update panels
    document.querySelectorAll('.wizard-panel').forEach(p => p.classList.remove('active'));
    
    // Determine which panel to show
    let panelId;
    if (step === 1) {
      panelId = '1';
    } else if (step === 2) {
      panelId = gameData.type === 'singles' ? '2-singles' : '2-doubles';
    } else if (step === 3) {
      panelId = gameData.type === 'singles' ? 'winner' : '3-doubles';
    } else if (step === 4) {
      panelId = gameData.type === 'doubles' ? 'winner' : 'confirm';
    } else {
      panelId = 'confirm';
    }
    
    const panel = document.querySelector(`[data-panel="${panelId}"]`);
    if (panel) panel.classList.add('active');
    
    // Update navigation buttons
    const backBtn = document.getElementById('wizard-back');
    const nextBtn = document.getElementById('wizard-next');
    const submitBtn = document.getElementById('wizard-submit');
    
    if (backBtn) backBtn.disabled = step === 1;
    
    const isLastStep = (gameData.type === 'singles' && step === 4) || 
                       (gameData.type === 'doubles' && step === 5);
    
    if (isLastStep) {
      nextBtn?.classList.add('hidden');
      submitBtn?.classList.remove('hidden');
      this.updateConfirmation(gameData);
    } else {
      nextBtn?.classList.remove('hidden');
      submitBtn?.classList.add('hidden');
    }
  }
  
  updateConfirmation(gameData) {
    const typeElement = document.getElementById('summary_type');
    const teamsElement = document.getElementById('summary_teams');
    const winnerElement = document.getElementById('summary_winner');
    
    if (typeElement) typeElement.textContent = gameData.type === 'singles' ? 'Singles' : 'Doubles';
    
    if (teamsElement) {
      if (gameData.type === 'singles') {
        teamsElement.innerHTML = `
          <div>You vs ${gameData.players.opponent?.name || 'Unknown'}</div>
        `;
      } else {
        teamsElement.innerHTML = `
          <div>Team 1: You & ${gameData.players.partner?.name || 'Unknown'}</div>
          <div>Team 2: ${gameData.players.opponent1?.name || 'Unknown'} & ${gameData.players.opponent2?.name || 'Unknown'}</div>
        `;
      }
    }
    
    if (winnerElement) {
      if (gameData.winner === 'me' || gameData.winner === 'team1') {
        winnerElement.textContent = 'You/Your Team';
      } else {
        winnerElement.textContent = 'Opponent/Their Team';
      }
    }
  }
  
  initMobilePlayerSearch(searchId, resultsId, netidId, selectedId, gameData) {
    const searchInput = document.getElementById(searchId);
    const resultsDiv = document.getElementById(resultsId);
    const netidInput = document.getElementById(netidId);
    const selectedDiv = document.getElementById(selectedId);
    
    if (!searchInput || !resultsDiv) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', (e) => {
      clearTimeout(searchTimeout);
      const query = e.target.value.trim();
      
      if (query.length < 2) {
        resultsDiv.style.display = 'none';
        return;
      }
      
      searchTimeout = setTimeout(() => {
        fetch(`/users/search?q=${encodeURIComponent(query)}`)
          .then(response => response.json())
          .then(users => {
            if (users.length === 0) {
              resultsDiv.innerHTML = '<div class="search-result-mobile">No users found</div>';
            } else {
              resultsDiv.innerHTML = users.map(user => `
                <div class="search-result-mobile" data-netid="${user.netid}" data-name="${user.name}" data-elo="${user.elo}">
                  <span>${user.name}</span>
                  <span class="player-elo">${user.elo}</span>
                </div>
              `).join('');
              
              resultsDiv.querySelectorAll('.search-result-mobile[data-netid]').forEach(item => {
                item.addEventListener('click', () => {
                  const player = {
                    netid: item.dataset.netid,
                    name: item.dataset.name,
                    elo: item.dataset.elo
                  };
                  
                  // Store in game data
                  const playerKey = searchId.replace('mobile_', '').replace('_search', '');
                  gameData.players[playerKey] = player;
                  
                  // Update hidden input
                  if (netidInput) netidInput.value = player.netid;
                  
                  // Update display
                  if (selectedDiv) {
                    selectedDiv.innerHTML = `
                      <div class="selected-player-card">
                        <span>${player.name}</span>
                        <span class="player-elo">${player.elo}</span>
                      </div>
                    `;
                    selectedDiv.style.display = 'block';
                  }
                  
                  // Clear search
                  searchInput.value = '';
                  resultsDiv.style.display = 'none';
                  
                  // Update winner display if needed
                  if (playerKey === 'opponent') {
                    const opponentDisplay = document.getElementById('opponent_name_display');
                    if (opponentDisplay) opponentDisplay.textContent = player.name;
                  }
                });
              });
            }
            resultsDiv.style.display = 'block';
          });
      }, 300);
    });
  }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  window.charterPoolUI = new CharterPoolUI();
  window.charterPoolUI.initGameWizard();
  console.log('Charter Pool Modern UI initialized!');
});

// Service Worker Registration for PWA
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(registration => console.log('ServiceWorker registered'))
      .catch(err => console.log('ServiceWorker registration failed'));
  });
}
