(function() {
  'use strict';
  document.addEventListener('submit', function(e) {
    var form = e.target;
    if (!form || form.tagName !== 'FORM') return;
    var btn = form.querySelector('button[type="submit"], input[type="submit"]');
    if (!btn || btn.dataset.noLoading) return;
    btn.disabled = true;
    btn.dataset.originalText = btn.textContent;
    btn.innerHTML = '<span class="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2 align-middle"></span>Submitting\u2026';
    btn.classList.add('opacity-70', 'cursor-not-allowed');
    setTimeout(function() {
      btn.disabled = false;
      btn.textContent = btn.dataset.originalText || 'Submit';
      btn.classList.remove('opacity-70', 'cursor-not-allowed');
    }, 5000);
  });
})();
