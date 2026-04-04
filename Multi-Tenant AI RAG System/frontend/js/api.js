/* ── API Client & Auth ─────────────────────────────────────────────────── */
const API = '/api/v1';

const api = {
  _token() { return localStorage.getItem('token'); },
  _refresh() { return localStorage.getItem('refresh_token'); },

  async _fetch(path, opts = {}) {
    const headers = opts.headers || {};
    if (!headers['Content-Type'] && !(opts.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }
    const token = this._token();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API}${path}`, { ...opts, headers });

    if (res.status === 401 && path !== '/auth/login' && path !== '/auth/refresh') {
      // Try refresh
      const refreshed = await this.refreshToken();
      if (refreshed) {
        headers['Authorization'] = `Bearer ${this._token()}`;
        return fetch(`${API}${path}`, { ...opts, headers });
      }
      auth.logout();
      return res;
    }
    return res;
  },

  async get(path) { return this._fetch(path); },

  async post(path, body) {
    const opts = { method: 'POST' };
    if (body instanceof FormData) {
      opts.body = body;
    } else {
      opts.body = JSON.stringify(body);
    }
    return this._fetch(path, opts);
  },

  async patch(path, body) {
    return this._fetch(path, { method: 'PATCH', body: JSON.stringify(body) });
  },

  async put(path, body) {
    return this._fetch(path, { method: 'PUT', body: JSON.stringify(body) });
  },

  async del(path) {
    return this._fetch(path, { method: 'DELETE' });
  },

  async refreshToken() {
    const rt = this._refresh();
    if (!rt) return false;
    try {
      const res = await fetch(`${API}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: rt }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      localStorage.setItem('token', data.access_token);
      if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token);
      return true;
    } catch { return false; }
  },
};

/* ── Auth helpers ──────────────────────────────────────────────────────── */
const auth = {
  isLoggedIn() { return !!localStorage.getItem('token'); },
  getUser() {
    const u = localStorage.getItem('user');
    return u ? JSON.parse(u) : null;
  },
  setUser(user) { localStorage.setItem('user', JSON.stringify(user)); },
  isAdmin() { const u = this.getUser(); return u && u.role === 'admin'; },

  async login(email, password) {
    const res = await fetch(`${API}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Login failed');
    }
    const data = await res.json();
    localStorage.setItem('token', data.access_token);
    if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token);
    // Fetch user info
    const meRes = await api.get('/auth/me');
    if (meRes.ok) {
      const user = await meRes.json();
      this.setUser(user);
    }
    return data;
  },

  async register(payload) {
    const res = await fetch(`${API}/auth/register-tenant-admin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Registration failed');
    }
    return res.json();
  },

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    router.navigate('login');
  },
};

/* ── Toast notifications ──────────────────────────────────────────────── */
const toast = {
  _container: null,
  _getContainer() {
    if (!this._container) {
      this._container = document.createElement('div');
      this._container.className = 'toast-container';
      document.body.appendChild(this._container);
    }
    return this._container;
  },
  show(message, type = 'info') {
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.textContent = message;
    this._getContainer().appendChild(el);
    setTimeout(() => el.remove(), 4000);
  },
  success(msg) { this.show(msg, 'success'); },
  error(msg) { this.show(msg, 'error'); },
  info(msg) { this.show(msg, 'info'); },
};

/* ── Simple Router ────────────────────────────────────────────────────── */
const router = {
  routes: {},
  register(name, handler) { this.routes[name] = handler; },
  navigate(name, params = {}) {
    window.location.hash = `#${name}`;
    this._params = params;
    this.render();
  },
  getParams() { return this._params || {}; },
  current() { return (window.location.hash || '#login').slice(1).split('?')[0]; },
  render() {
    const page = this.current();
    // Clear document polling when navigating away from documents
    if (page !== 'documents' && window._docPollInterval) {
      clearInterval(window._docPollInterval);
      window._docPollInterval = null;
    }
    // Auth guard
    const publicPages = ['login', 'register'];
    if (!publicPages.includes(page) && !auth.isLoggedIn()) {
      this.navigate('login');
      return;
    }
    if (publicPages.includes(page) && auth.isLoggedIn()) {
      this.navigate('dashboard');
      return;
    }
    const handler = this.routes[page];
    if (handler) {
      handler();
    } else {
      this.navigate('dashboard');
    }
  },
};

window.addEventListener('hashchange', () => router.render());

/* ── Util: format bytes ───────────────────────────────────────────────── */
function formatBytes(bytes) {
  if (!bytes) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function timeAgo(dateStr) {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  const sec = Math.floor((Date.now() - d.getTime()) / 1000);
  if (sec < 60) return 'μόλις τώρα';
  if (sec < 3600) return Math.floor(sec / 60) + ' λεπτά πριν';
  if (sec < 86400) return Math.floor(sec / 3600) + ' ώρες πριν';
  return Math.floor(sec / 86400) + ' ημέρες πριν';
}

function escapeHtml(text) {
  const d = document.createElement('div');
  d.textContent = text;
  return d.innerHTML;
}

/* ── Offline Detection ────────────────────────────────────────────────── */
const connectivity = {
  _banner: null,
  init() {
    window.addEventListener('online', () => this.update(true));
    window.addEventListener('offline', () => this.update(false));
  },
  update(isOnline) {
    if (!isOnline) {
      if (!this._banner) {
        this._banner = document.createElement('div');
        this._banner.className = 'offline-banner';
        this._banner.textContent = 'Εκτός σύνδεσης — ελέγξτε τη σύνδεσή σας στο internet';
        document.body.prepend(this._banner);
      }
    } else {
      if (this._banner) {
        this._banner.remove();
        this._banner = null;
        toast.success('Η σύνδεση αποκαταστάθηκε');
      }
    }
  },
};
connectivity.init();
