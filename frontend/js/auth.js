(function () {
  const AUTH_KEY = 'contractlens_auth';
  const DEMO_USER = { email: 'demo@contractlens.ai', name: 'Demo User' };
  const DEMO_PASSWORD = 'demo123';

  function getAuth() {
    try {
      return JSON.parse(localStorage.getItem(AUTH_KEY) || sessionStorage.getItem(AUTH_KEY) || 'null');
    } catch (_) { return null; }
  }

  function setAuth(user, remember) {
    const payload = JSON.stringify({ ...user, loggedInAt: new Date().toISOString() });
    (remember ? localStorage : sessionStorage).setItem(AUTH_KEY, payload);
    if (remember) sessionStorage.removeItem(AUTH_KEY);
    else localStorage.removeItem(AUTH_KEY);
  }

  function logout() {
    localStorage.removeItem(AUTH_KEY);
    sessionStorage.removeItem(AUTH_KEY);
    window.location.href = '/pages/login.html';
  }

  function requireAuth() {
    if (!getAuth()) {
      const path = window.location.pathname;
      if (!path.endsWith('/login.html')) window.location.replace('/pages/login.html');
      return false;
    }
    return true;
  }

  window.ContractLensAuth = { getAuth, setAuth, logout, requireAuth };

  const form = document.getElementById('loginForm');
  if (!form) return;

  if (getAuth()) {
    window.location.replace('/pages/dashboard.html');
    return;
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();
    const email = document.getElementById('email').value.trim().toLowerCase();
    const password = document.getElementById('password').value;
    const remember = document.getElementById('remember').checked;
    const error = document.getElementById('loginError');
    const button = document.getElementById('loginBtn');

    error.style.display = 'none';
    button.disabled = true;
    button.textContent = 'Signing in…';

    setTimeout(function () {
      if (email === DEMO_USER.email && password === DEMO_PASSWORD) {
        setAuth(DEMO_USER, remember);
        window.location.href = '/pages/dashboard.html';
        return;
      }
      error.textContent = 'Invalid email or password. Use the demo credentials shown below.';
      error.style.display = 'block';
      button.disabled = false;
      button.textContent = 'Sign in';
    }, 450);
  });
})();
