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
  
  // Confirmation dialogs for destructive actions
  const confirmButtons = document.querySelectorAll('[onclick*="confirm"]');
  confirmButtons.forEach(button => {
    button.addEventListener('click', (e) => {
      const message = button.getAttribute('onclick').match(/confirm\('(.+?)'\)/)[1];
      if (!confirm(message)) {
        e.preventDefault();
      }
    });
  });
  
  // Table row highlighting
  const tables = document.querySelectorAll('table tbody tr');
  tables.forEach(row => {
    row.addEventListener('mouseenter', () => {
      row.style.backgroundColor = '#f8f9fa';
    });
    row.addEventListener('mouseleave', () => {
      if (!row.classList.contains('highlight')) {
        row.style.backgroundColor = '';
      }
    });
  });
});
