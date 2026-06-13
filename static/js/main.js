// ── Auto-dismiss alerts ──────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert.close();
    }, 4000);
  });

  // ── Set min datetime for expiry input to now ──────
  const expiryInput = document.querySelector('input[name="expires_at"]');
  if (expiryInput) {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    expiryInput.min = now.toISOString().slice(0, 16);
  }

  // ── Confirm before marking done ───────────────────
  document.querySelectorAll('.confirm-action').forEach(btn => {
    btn.addEventListener('click', e => {
      if (!confirm(btn.dataset.confirm || 'Are you sure?')) {
        e.preventDefault();
      }
    });
  });

  // ── Category badge color on browse filter ────────
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });

  // ── Live quantity unit label ───────────────────────
  const qtyInput = document.querySelector('input[name="quantity"]');
  if (qtyInput) {
    qtyInput.addEventListener('input', () => {
      const label = document.getElementById('qty-label');
      if (label) label.textContent = qtyInput.value ? qtyInput.value + ' kg' : '';
    });
  }

  // ── Navbar active link highlight ──────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });
});

// ── Countdown timer for listings expiry ──────────────
function startCountdowns() {
  document.querySelectorAll('[data-expires]').forEach(el => {
    const expires = new Date(el.dataset.expires);
    function tick() {
      const diff = expires - new Date();
      if (diff <= 0) {
        el.textContent = 'Expired';
        el.classList.add('text-danger');
        return;
      }
      const h = Math.floor(diff / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      el.textContent = h > 0 ? `${h}h ${m}m left` : `${m}m left`;
      if (diff < 3600000) el.classList.add('text-warning');
    }
    tick();
    setInterval(tick, 60000);
  });
}
document.addEventListener('DOMContentLoaded', startCountdowns);
