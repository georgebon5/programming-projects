/* ── Page Renderers ────────────────────────────────────────────────────── */

function renderLayout(content, activePage) {
  const user = auth.getUser() || {};
  const isAdmin = user.role === 'admin';
  const app = document.getElementById('app');

  app.innerHTML = `
    <nav class="sidebar" id="sidebar">
      <div class="sidebar-logo">
        <h2>🤖 RAG System</h2>
        <small>Multi-Tenant AI</small>
      </div>
      <div class="sidebar-nav">
        <a href="#dashboard" class="${activePage === 'dashboard' ? 'active' : ''}">
          <span class="icon">📊</span> Dashboard
        </a>
        <a href="#documents" class="${activePage === 'documents' ? 'active' : ''}">
          <span class="icon">📄</span> Έγγραφα
        </a>
        <a href="#chat" class="${activePage === 'chat' ? 'active' : ''}">
          <span class="icon">💬</span> Chat AI
        </a>
        ${isAdmin ? `
        <a href="#users" class="${activePage === 'users' ? 'active' : ''}">
          <span class="icon">👥</span> Χρήστες
        </a>
        <a href="#api-keys" class="${activePage === 'api-keys' ? 'active' : ''}">
          <span class="icon">🔑</span> API Keys
        </a>
        <a href="#audit" class="${activePage === 'audit' ? 'active' : ''}">
          <span class="icon">📋</span> Audit Log
        </a>
        <a href="#settings" class="${activePage === 'settings' ? 'active' : ''}">
          <span class="icon">⚙️</span> Ρυθμίσεις
        </a>
        ` : ''}
      </div>
      <div class="sidebar-footer">
        <div class="user-info">
          <strong>${escapeHtml(user.username || '')}</strong>
          ${escapeHtml(user.email || '')}
        </div>
        <div style="display:flex;gap:6px">
          <button class="btn btn-ghost btn-sm" style="flex:1" onclick="router.navigate('profile')">👤 Προφίλ</button>
          <button class="btn btn-ghost btn-sm" style="flex:1" onclick="auth.logout()">Αποσύνδεση</button>
        </div>
      </div>
    </nav>
    <main class="main-content" id="page-content">
      ${content}
    </main>
  `;
}

/* ── LOGIN ────────────────────────────────────────────────────────────── */
router.register('login', () => {
  document.getElementById('app').innerHTML = `
    <div class="auth-wrapper">
      <div class="auth-card">
        <h1>🤖 RAG System</h1>
        <p class="subtitle">Σύνδεση στο σύστημα</p>
        <form id="login-form">
          <div class="form-group">
            <label>Email</label>
            <input type="email" id="login-email" required placeholder="admin@example.com">
          </div>
          <div class="form-group">
            <label>Κωδικός</label>
            <input type="password" id="login-password" required placeholder="••••••••">
          </div>
          <button type="submit" class="btn btn-primary btn-block" id="login-btn">Σύνδεση</button>
        </form>
        <p class="toggle">Δεν έχεις λογαριασμό; <a href="#register">Εγγραφή</a></p>
      </div>
    </div>
  `;
  document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('login-btn');
    btn.disabled = true;
    btn.textContent = 'Σύνδεση...';
    try {
      await auth.login(
        document.getElementById('login-email').value,
        document.getElementById('login-password').value
      );
      toast.success('Επιτυχής σύνδεση!');
      router.navigate('dashboard');
    } catch (err) {
      toast.error(err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = 'Σύνδεση';
    }
  });
});

/* ── REGISTER ─────────────────────────────────────────────────────────── */
router.register('register', () => {
  document.getElementById('app').innerHTML = `
    <div class="auth-wrapper">
      <div class="auth-card">
        <h1>🤖 Εγγραφή</h1>
        <p class="subtitle">Δημιουργία νέου tenant & admin</p>
        <form id="register-form">
          <div class="form-group">
            <label>Όνομα Οργανισμού</label>
            <input type="text" id="reg-tenant-name" required placeholder="π.χ. My Company">
          </div>
          <div class="form-group">
            <label>Slug <span style="font-weight:400;color:var(--text-muted)">(δημιουργείται αυτόματα)</span></label>
            <input type="text" id="reg-tenant-slug" required placeholder="my-company" pattern="^[a-z0-9][a-z0-9-]*$" readonly style="opacity:.7;cursor:default">
            <small style="color:var(--text-muted);font-size:11px">Μόνο αγγλικα πεζά, αριθμοί και παύλες</small>
          </div>
          <div class="form-group">
            <label>Username</label>
            <input type="text" id="reg-username" required placeholder="π.χ. admin">
          </div>
          <div class="form-group">
            <label>Email</label>
            <input type="email" id="reg-email" required placeholder="π.χ. admin@company.com">
          </div>
          <div class="form-group">
            <label>Κωδικός</label>
            <input type="password" id="reg-password" required placeholder="Κεφαλαίο, πεζό, αριθμός, σύμβολο" minlength="8">
            <small style="color:var(--text-muted);font-size:11px">Τουλάχιστον 8 χαρακτήρες, 1 κεφαλαίο, 1 πεζό, 1 αριθμός, 1 σύμβολο</small>
          </div>
          <div id="reg-error" style="color:var(--danger);font-size:13px;margin-bottom:12px;display:none"></div>
          <button type="submit" class="btn btn-primary btn-block" id="reg-btn">Εγγραφή</button>
        </form>
        <p class="toggle">Έχεις ήδη λογαριασμό; <a href="#login">Σύνδεση</a></p>
      </div>
    </div>
  `;

  // Auto-generate slug from tenant name
  document.getElementById('reg-tenant-name').addEventListener('input', (e) => {
    const slug = e.target.value
      .toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')  // strip accents
      .replace(/[^a-z0-9\s-]/g, '')  // remove non-latin chars
      .trim()
      .replace(/\s+/g, '-')          // spaces → hyphens
      .replace(/-+/g, '-');           // collapse multiple hyphens
    document.getElementById('reg-tenant-slug').value = slug;
  });

  document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errEl = document.getElementById('reg-error');
    errEl.style.display = 'none';
    const btn = document.getElementById('reg-btn');
    btn.disabled = true;
    btn.textContent = 'Εγγραφή...';

    const slug = document.getElementById('reg-tenant-slug').value;
    if (!slug || !/^[a-z0-9][a-z0-9-]*$/.test(slug)) {
      errEl.textContent = 'Το slug πρέπει να περιέχει μόνο αγγλικά πεζά γράμματα, αριθμούς και παύλες.';
      errEl.style.display = 'block';
      btn.disabled = false;
      btn.textContent = 'Εγγραφή';
      return;
    }

    try {
      await auth.register({
        tenant_name: document.getElementById('reg-tenant-name').value,
        tenant_slug: slug,
        username: document.getElementById('reg-username').value,
        email: document.getElementById('reg-email').value,
        password: document.getElementById('reg-password').value,
      });
      toast.success('Επιτυχής εγγραφή! Συνδέσου τώρα.');
      router.navigate('login');
    } catch (err) {
      errEl.textContent = err.message;
      errEl.style.display = 'block';
      toast.error(err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = 'Εγγραφή';
    }
  });
});

/* ── PROFILE ──────────────────────────────────────────────────────────── */
router.register('profile', async () => {
  renderLayout('<div class="empty-state"><div class="spinner"></div></div>', 'profile');

  const user = auth.getUser() || {};

  document.getElementById('page-content').innerHTML = `
    <div class="page-header"><h1>👤 Το Προφίλ μου</h1></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px">
      <div class="card">
        <h3 style="margin-bottom:16px">Πληροφορίες Λογαριασμού</h3>
        <div class="profile-info">
          <div class="form-group">
            <label>Username</label>
            <input value="${escapeHtml(user.username || '')}" readonly style="opacity:.7">
          </div>
          <div class="form-group">
            <label>Email</label>
            <input value="${escapeHtml(user.email || '')}" readonly style="opacity:.7">
          </div>
          <div class="form-group">
            <label>Ρόλος</label>
            <input value="${user.role || ''}" readonly style="opacity:.7">
          </div>
          <div class="form-group">
            <label>Μέλος από</label>
            <input value="${user.created_at ? new Date(user.created_at).toLocaleDateString('el') : '-'}" readonly style="opacity:.7">
          </div>
        </div>
      </div>
      <div class="card">
        <h3 style="margin-bottom:16px">Αλλαγή Κωδικού</h3>
        <form id="password-form">
          <div class="form-group">
            <label>Τρέχων Κωδικός</label>
            <input type="password" id="pw-current" required placeholder="••••••••">
          </div>
          <div class="form-group">
            <label>Νέος Κωδικός</label>
            <input type="password" id="pw-new" required minlength="8" placeholder="Κεφαλαίο, πεζό, αριθμός, σύμβολο">
            <small style="color:var(--text-muted);font-size:11px">Τουλάχιστον 8 χαρακτήρες, κεφαλαίο, πεζό γράμμα, αριθμός, σύμβολο</small>
          </div>
          <div class="form-group">
            <label>Επιβεβαίωση Νέου Κωδικού</label>
            <input type="password" id="pw-confirm" required minlength="8" placeholder="••••••••">
          </div>
          <div id="pw-error" style="color:var(--danger);font-size:13px;margin-bottom:12px;display:none"></div>
          <button type="submit" class="btn btn-primary">Αλλαγή Κωδικού</button>
        </form>
      </div>
    </div>
    <div style="margin-top:24px;display:flex;gap:12px">
      <button class="btn btn-ghost" onclick="exportMyData()">📥 Εξαγωγή Δεδομένων (GDPR)</button>
    </div>
  `;

  document.getElementById('password-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errEl = document.getElementById('pw-error');
    errEl.style.display = 'none';
    const newPw = document.getElementById('pw-new').value;
    const confirmPw = document.getElementById('pw-confirm').value;
    if (newPw !== confirmPw) {
      errEl.textContent = 'Οι κωδικοί δεν ταιριάζουν';
      errEl.style.display = 'block';
      return;
    }
    try {
      const res = await api.put('/users/me/password', {
        current_password: document.getElementById('pw-current').value,
        new_password: newPw,
      });
      if (res.ok || res.status === 204) {
        toast.success('Ο κωδικός άλλαξε επιτυχώς!');
        document.getElementById('password-form').reset();
      } else {
        const err = await res.json().catch(() => ({}));
        errEl.textContent = err.detail || 'Σφάλμα αλλαγής κωδικού';
        errEl.style.display = 'block';
      }
    } catch { toast.error('Σφάλμα δικτύου'); }
  });
});

async function exportMyData() {
  toast.info('Εξαγωγή δεδομένων...');
  try {
    const res = await api.get('/me/export');
    if (res.ok) {
      const data = await res.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `my-data-export-${new Date().toISOString().slice(0,10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Τα δεδομένα εξήχθησαν!');
    } else {
      toast.error('Σφάλμα εξαγωγής');
    }
  } catch { toast.error('Σφάλμα δικτύου'); }
}

/* ── DASHBOARD ────────────────────────────────────────────────────────── */
router.register('dashboard', async () => {
  renderLayout('<div class="empty-state"><div class="spinner"></div><p>Φόρτωση...</p></div>', 'dashboard');

  let statsHtml = '';
  let activityHtml = '';

  if (auth.isAdmin()) {
    const res = await api.get('/admin/dashboard/');
    if (res.ok) {
      const d = await res.json();
      const s = d.stats;
      statsHtml = `
        <div class="stats-grid">
          <div class="stat-card"><div class="stat-icon">👥</div><div class="stat-value">${s.total_users}</div><div class="stat-label">Χρήστες</div></div>
          <div class="stat-card"><div class="stat-icon">📄</div><div class="stat-value">${s.total_documents}</div><div class="stat-label">Έγγραφα</div></div>
          <div class="stat-card"><div class="stat-icon">✅</div><div class="stat-value">${s.processed_documents}</div><div class="stat-label">Επεξεργασμένα</div></div>
          <div class="stat-card"><div class="stat-icon">💬</div><div class="stat-value">${s.total_conversations}</div><div class="stat-label">Συνομιλίες</div></div>
          <div class="stat-card"><div class="stat-icon">📦</div><div class="stat-value">${formatBytes(s.storage_bytes)}</div><div class="stat-label">Αποθήκευση</div></div>
          <div class="stat-card"><div class="stat-icon">🧩</div><div class="stat-value">${s.total_chunks}</div><div class="stat-label">Chunks</div></div>
        </div>
      `;
      if (d.recent_activity && d.recent_activity.length) {
        activityHtml = `
          <div class="card" style="margin-top:16px">
            <h3 style="margin-bottom:12px">Πρόσφατη Δραστηριότητα</h3>
            <ul class="activity-list">
              ${d.recent_activity.map(a => `<li><span>${escapeHtml(a.description)}</span><span class="time">${timeAgo(a.timestamp)}</span></li>`).join('')}
            </ul>
          </div>
        `;
      }
    }
  }

  // Usage info for all users
  const usageRes = await api.get('/admin/settings/usage');
  let usageHtml = '';
  if (usageRes.ok) {
    const u = await usageRes.json();
    usageHtml = `
      <div class="card" style="margin-top:16px">
        <h3 style="margin-bottom:12px">Χρήση</h3>
        <table>
          <tr><td>Χρήστες</td><td><strong>${u.users.current}</strong> / ${u.users.limit}</td></tr>
          <tr><td>Έγγραφα</td><td><strong>${u.documents.current}</strong> / ${u.documents.limit}</td></tr>
          <tr><td>Αποθήκευση</td><td><strong>${u.storage_mb.current} MB</strong> / ${u.storage_mb.limit} MB</td></tr>
          <tr><td>Chat σήμερα</td><td><strong>${u.chat_messages_today.current}</strong> / ${u.chat_messages_today.limit}</td></tr>
        </table>
      </div>
    `;
  }

  document.getElementById('page-content').innerHTML = `
    <div class="page-header"><h1>📊 Dashboard</h1></div>
    ${statsHtml}
    ${usageHtml}
    ${activityHtml}
  `;
});

/* ── DOCUMENTS ────────────────────────────────────────────────────────── */
router.register('documents', async () => {
  renderLayout('<div class="empty-state"><div class="spinner"></div></div>', 'documents');

  const res = await api.get('/documents/?limit=100');
  const data = res.ok ? await res.json() : { documents: [], total: 0 };

  const statusBadge = (s) => {
    const m = { completed: 'success', processing: 'info', uploaded: 'warning', failed: 'danger' };
    return `<span class="badge badge-${m[s] || 'muted'}">${s}</span>`;
  };

  const user = auth.getUser();
  const canUpload = user && (user.role === 'admin' || user.role === 'member');

  document.getElementById('page-content').innerHTML = `
    <div class="page-header">
      <h1>📄 Έγγραφα (${data.total})</h1>
    </div>
    ${canUpload ? `
    <div class="upload-zone" id="upload-zone">
      <div class="icon">📁</div>
      <p>Σύρε αρχεία εδώ ή κάνε κλικ για upload</p>
      <p style="font-size:12px;color:var(--text-muted);margin-top:4px">.pdf, .txt, .md, .docx — μέχρι 50MB</p>
      <input type="file" id="file-input" hidden accept=".pdf,.txt,.md,.docx">
    </div>
    ` : ''}
    ${data.documents.length ? `
    <div class="card">
      <div class="table-wrapper">
        <table>
          <thead>
            <tr><th>Αρχείο</th><th>Μέγεθος</th><th>Κατάσταση</th><th>Chunks</th><th>Ημερομηνία</th><th></th></tr>
          </thead>
          <tbody>
            ${data.documents.map(d => `
              <tr>
                <td>${escapeHtml(d.original_filename)}</td>
                <td>${formatBytes(d.file_size_bytes)}</td>
                <td>${statusBadge(d.status)}</td>
                <td>${d.total_chunks || '-'}</td>
                <td>${timeAgo(d.created_at)}</td>
                <td style="display:flex;gap:4px">
                  ${d.status === 'failed' || d.status === 'uploaded' ? `<button class="btn btn-ghost btn-sm" onclick="reprocessDocument('${d.id}')" title="Επανεπεξεργασία">🔄</button>` : ''}
                  <button class="btn btn-danger btn-sm" onclick="deleteDocument('${d.id}')">🗑️</button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
    ` : '<div class="empty-state"><div class="icon">📄</div><h3>Δεν υπάρχουν έγγραφα</h3><p>Ανέβασε το πρώτο σου αρχείο!</p></div>'}
  `;

  // Upload handlers
  if (canUpload) {
    const zone = document.getElementById('upload-zone');
    const input = document.getElementById('file-input');

    zone.addEventListener('click', () => input.click());
    zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('dragover'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
    zone.addEventListener('drop', (e) => {
      e.preventDefault();
      zone.classList.remove('dragover');
      if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
    });
    input.addEventListener('change', () => { if (input.files.length) uploadFile(input.files[0]); });
  }
});

async function uploadFile(file) {
  const fd = new FormData();
  fd.append('file', file);
  toast.info(`Ανέβασμα: ${file.name}...`);
  try {
    const res = await api.post('/documents/upload', fd);
    if (res.ok) {
      toast.success('Το αρχείο ανέβηκε! Επεξεργασία...');
      setTimeout(() => router.navigate('documents'), 1500);
    } else {
      const err = await res.json().catch(() => ({}));
      toast.error(err.detail || 'Σφάλμα upload');
    }
  } catch (e) { toast.error('Σφάλμα δικτύου'); }
}

async function deleteDocument(id) {
  if (!confirm('Σίγουρα θέλεις να διαγράψεις αυτό το έγγραφο;')) return;
  const res = await api.del(`/documents/${id}`);
  if (res.ok || res.status === 204) {
    toast.success('Το έγγραφο διαγράφηκε');
    router.navigate('documents');
  } else {
    toast.error('Σφάλμα διαγραφής');
  }
}

async function reprocessDocument(id) {
  toast.info('Επανεπεξεργασία εγγράφου...');
  try {
    const res = await api.post(`/documents/${id}/process`);
    if (res.ok) {
      toast.success('Η επεξεργασία ξεκίνησε!');
      setTimeout(() => router.navigate('documents'), 1500);
    } else {
      const err = await res.json().catch(() => ({}));
      toast.error(err.detail || 'Σφάλμα επεξεργασίας');
    }
  } catch { toast.error('Σφάλμα δικτύου'); }
}

/* ── CHAT ─────────────────────────────────────────────────────────────── */
let currentConversationId = null;

router.register('chat', async () => {
  currentConversationId = null;
  renderLayout('', 'chat');

  // Fetch conversation list
  let conversations = [];
  try {
    const convRes = await api.get('/chat/');
    if (convRes.ok) {
      const convData = await convRes.json();
      conversations = convData.conversations || [];
    }
  } catch {}

  document.getElementById('page-content').innerHTML = `
    <div class="page-header">
      <h1>💬 Chat AI</h1>
      <button class="btn btn-primary btn-sm" onclick="startNewConversation()">+ Νέα Συνομιλία</button>
    </div>
    <div class="chat-layout">
      <div class="chat-sidebar" id="chat-sidebar">
        <div class="chat-sidebar-header">Ιστορικό Συνομιλιών</div>
        <div class="chat-sidebar-list" id="conv-list">
          ${conversations.length ? conversations.map(c => `
            <div class="conv-item" data-id="${escapeHtml(c.conversation_id)}" onclick="loadConversation('${escapeHtml(c.conversation_id)}')">
              <div class="conv-preview">${escapeHtml(c.preview || 'Χωρίς προεπισκόπηση')}</div>
              <div class="conv-meta">
                <span>${c.message_count} μνμ</span>
                <span>${c.last_message_at ? timeAgo(c.last_message_at) : ''}</span>
              </div>
              <button class="conv-delete" onclick="event.stopPropagation();deleteConversation('${escapeHtml(c.conversation_id)}')" title="Διαγραφή">×</button>
            </div>
          `).join('') : '<div class="conv-empty">Δεν υπάρχουν συνομιλίες</div>'}
        </div>
      </div>
      <div class="chat-main">
        <div class="chat-container">
          <div class="chat-messages" id="chat-messages">
            <div class="empty-state">
              <div class="icon">🤖</div>
              <h3>Ρώτα οτιδήποτε για τα έγγραφά σου</h3>
              <p>Τα αποτελέσματα βασίζονται στα έγγραφα που έχεις ανεβάσει</p>
            </div>
          </div>
          <div class="chat-input-area">
            <input type="text" id="chat-input" placeholder="Γράψε την ερώτησή σου..." autofocus>
            <button class="btn btn-primary" id="chat-send" onclick="sendChat()">Αποστολή</button>
          </div>
        </div>
      </div>
    </div>
  `;

  document.getElementById('chat-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
  });
});

function startNewConversation() {
  currentConversationId = null;
  const msgs = document.getElementById('chat-messages');
  if (msgs) {
    msgs.innerHTML = `
      <div class="empty-state">
        <div class="icon">🤖</div>
        <h3>Ρώτα οτιδήποτε για τα έγγραφά σου</h3>
        <p>Νέα συνομιλία — γράψε μια ερώτηση!</p>
      </div>
    `;
  }
  // Remove active state from conv list
  document.querySelectorAll('.conv-item').forEach(el => el.classList.remove('active'));
}

async function loadConversation(convId) {
  currentConversationId = convId;
  const msgs = document.getElementById('chat-messages');
  msgs.innerHTML = '<div class="empty-state"><div class="spinner"></div></div>';

  // Active state
  document.querySelectorAll('.conv-item').forEach(el => {
    el.classList.toggle('active', el.dataset.id === convId);
  });

  try {
    const res = await api.get(`/chat/${encodeURIComponent(convId)}`);
    if (res.ok) {
      const data = await res.json();
      msgs.innerHTML = '';
      data.messages.forEach(m => {
        const cls = m.role === 'user' ? 'user' : 'assistant';
        msgs.innerHTML += `<div class="chat-bubble ${cls}">${formatChatMessage(m.content)}</div>`;
      });
      msgs.scrollTop = msgs.scrollHeight;
    } else {
      msgs.innerHTML = '<div class="empty-state"><p>Σφάλμα φόρτωσης</p></div>';
    }
  } catch {
    msgs.innerHTML = '<div class="empty-state"><p>Σφάλμα δικτύου</p></div>';
  }
}

async function deleteConversation(convId) {
  if (!confirm('Σίγουρα θέλεις να διαγράψεις αυτή τη συνομιλία;')) return;
  try {
    const res = await api.del(`/chat/${encodeURIComponent(convId)}`);
    if (res.ok || res.status === 204) {
      toast.success('Η συνομιλία διαγράφηκε');
      if (currentConversationId === convId) {
        currentConversationId = null;
      }
      router.navigate('chat');
    } else {
      toast.error('Σφάλμα διαγραφής');
    }
  } catch { toast.error('Σφάλμα δικτύου'); }
}

function formatChatMessage(text) {
  // Simple markdown-like formatting
  let html = escapeHtml(text);
  // Bold: **text**
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Italic: *text* or _text_
  html = html.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');
  html = html.replace(/_(.+?)_/g, '<em>$1</em>');
  // Code blocks: ```...```
  html = html.replace(/```([\s\S]*?)```/g, '<pre style="background:rgba(0,0,0,.3);padding:10px;border-radius:6px;overflow-x:auto;margin:8px 0;font-size:13px"><code>$1</code></pre>');
  // Inline code: `text`
  html = html.replace(/`([^`]+)`/g, '<code style="background:rgba(0,0,0,.3);padding:2px 6px;border-radius:4px;font-size:13px">$1</code>');
  // Line breaks
  html = html.replace(/\n/g, '<br>');
  return html;
}

async function sendChat() {
  const input = document.getElementById('chat-input');
  const q = input.value.trim();
  if (!q) return;

  const msgs = document.getElementById('chat-messages');
  const emptyState = msgs.querySelector('.empty-state');
  if (emptyState) emptyState.remove();

  msgs.innerHTML += `<div class="chat-bubble user">${escapeHtml(q)}</div>`;
  input.value = '';
  input.disabled = true;
  document.getElementById('chat-send').disabled = true;
  msgs.scrollTop = msgs.scrollHeight;

  msgs.innerHTML += `<div class="chat-bubble assistant" id="chat-loading"><div class="spinner"></div> Σκέφτομαι...</div>`;
  msgs.scrollTop = msgs.scrollHeight;

  try {
    const body = { question: q };
    if (currentConversationId) body.conversation_id = currentConversationId;

    const res = await api.post('/chat/', body);
    document.getElementById('chat-loading')?.remove();

    if (res.ok) {
      const data = await res.json();
      const isNewConversation = !currentConversationId;
      currentConversationId = data.conversation_id;

      let sourcesHtml = '';
      if (data.sources && data.sources.length) {
        sourcesHtml = `<div class="sources">📎 Πηγές: ${data.sources.map(s =>
          escapeHtml(s.text?.substring(0, 80) + '...')
        ).join(' | ')}</div>`;
      }
      msgs.innerHTML += `<div class="chat-bubble assistant">${formatChatMessage(data.answer)}${sourcesHtml}</div>`;

      // Update conversation sidebar if new conversation
      if (isNewConversation) {
        const convList = document.getElementById('conv-list');
        if (convList) {
          const emptyEl = convList.querySelector('.conv-empty');
          if (emptyEl) emptyEl.remove();
          convList.insertAdjacentHTML('afterbegin', `
            <div class="conv-item active" data-id="${escapeHtml(data.conversation_id)}" onclick="loadConversation('${escapeHtml(data.conversation_id)}')">
              <div class="conv-preview">${escapeHtml(q.substring(0, 100))}${q.length > 100 ? '...' : ''}</div>
              <div class="conv-meta"><span>2 μνμ</span><span>μόλις τώρα</span></div>
              <button class="conv-delete" onclick="event.stopPropagation();deleteConversation('${escapeHtml(data.conversation_id)}')" title="Διαγραφή">×</button>
            </div>
          `);
        }
      }
    } else {
      const err = await res.json().catch(() => ({}));
      msgs.innerHTML += `<div class="chat-bubble assistant" style="color:var(--danger)">${escapeHtml(err.detail || 'Σφάλμα')}</div>`;
    }
  } catch (e) {
    document.getElementById('chat-loading')?.remove();
    msgs.innerHTML += `<div class="chat-bubble assistant" style="color:var(--danger)">Σφάλμα δικτύου</div>`;
  }

  input.disabled = false;
  document.getElementById('chat-send').disabled = false;
  input.focus();
  msgs.scrollTop = msgs.scrollHeight;
}

/* ── USERS (Admin) ────────────────────────────────────────────────────── */
router.register('users', async () => {
  if (!auth.isAdmin()) { router.navigate('dashboard'); return; }
  renderLayout('<div class="empty-state"><div class="spinner"></div></div>', 'users');

  const res = await api.get('/users/?limit=100');
  const data = res.ok ? await res.json() : { users: [], total: 0 };

  document.getElementById('page-content').innerHTML = `
    <div class="page-header">
      <h1>👥 Χρήστες (${data.total})</h1>
      <button class="btn btn-primary btn-sm" onclick="showInviteModal()">+ Πρόσκληση</button>
    </div>
    <div class="card">
      <div class="table-wrapper">
        <table>
          <thead><tr><th>Username</th><th>Email</th><th>Ρόλος</th><th>Κατάσταση</th><th>Εγγραφή</th><th></th></tr></thead>
          <tbody>
            ${data.users.map(u => `
              <tr>
                <td><strong>${escapeHtml(u.username)}</strong></td>
                <td>${escapeHtml(u.email)}</td>
                <td><span class="badge ${u.role === 'admin' ? 'badge-info' : u.role === 'member' ? 'badge-success' : 'badge-muted'}">${u.role}</span></td>
                <td>${u.is_active ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-danger">Inactive</span>'}</td>
                <td>${timeAgo(u.created_at)}</td>
                <td>
                  ${u.id !== auth.getUser()?.id ? `<button class="btn btn-danger btn-sm" onclick="deleteUser('${u.id}')">🗑️</button>` : ''}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
    <div id="modal-container"></div>
  `;
});

function showInviteModal() {
  document.getElementById('modal-container').innerHTML = `
    <div class="modal-backdrop" onclick="this.remove()">
      <div class="modal" onclick="event.stopPropagation()">
        <h2>Πρόσκληση Χρήστη</h2>
        <form id="invite-form">
          <div class="form-group"><label>Username</label><input id="inv-username" required></div>
          <div class="form-group"><label>Email</label><input type="email" id="inv-email" required></div>
          <div class="form-group"><label>Κωδικός</label><input type="password" id="inv-password" required minlength="8"></div>
          <div class="form-group">
            <label>Ρόλος</label>
            <select id="inv-role"><option value="member">Member</option><option value="viewer">Viewer</option><option value="admin">Admin</option></select>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn btn-ghost" onclick="document.querySelector('.modal-backdrop').remove()">Ακύρωση</button>
            <button type="submit" class="btn btn-primary">Πρόσκληση</button>
          </div>
        </form>
      </div>
    </div>
  `;
  document.getElementById('invite-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
      const res = await api.post('/users/invite', {
        username: document.getElementById('inv-username').value,
        email: document.getElementById('inv-email').value,
        password: document.getElementById('inv-password').value,
        role: document.getElementById('inv-role').value,
      });
      if (res.ok) {
        toast.success('Ο χρήστης προσκλήθηκε!');
        document.querySelector('.modal-backdrop')?.remove();
        router.navigate('users');
      } else {
        const err = await res.json().catch(() => ({}));
        toast.error(err.detail || 'Σφάλμα');
      }
    } catch { toast.error('Σφάλμα δικτύου'); }
  });
}

async function deleteUser(id) {
  if (!confirm('Σίγουρα θέλεις να διαγράψεις αυτόν τον χρήστη;')) return;
  const res = await api.del(`/users/${id}`);
  if (res.ok || res.status === 204) {
    toast.success('Ο χρήστης διαγράφηκε');
    router.navigate('users');
  } else { toast.error('Σφάλμα διαγραφής'); }
}

/* ── API KEYS ─────────────────────────────────────────────────────────── */
router.register('api-keys', async () => {
  if (!auth.isAdmin()) { router.navigate('dashboard'); return; }
  renderLayout('<div class="empty-state"><div class="spinner"></div></div>', 'api-keys');

  const res = await api.get('/api-keys/');
  const keys = res.ok ? await res.json() : [];

  document.getElementById('page-content').innerHTML = `
    <div class="page-header">
      <h1>🔑 API Keys</h1>
      <button class="btn btn-primary btn-sm" onclick="showCreateKeyModal()">+ Νέο Κλειδί</button>
    </div>
    ${keys.length ? `
    <div class="card">
      <div class="table-wrapper">
        <table>
          <thead><tr><th>Όνομα</th><th>Prefix</th><th>Κατάσταση</th><th>Τελευταία χρήση</th><th>Λήξη</th><th></th></tr></thead>
          <tbody>
            ${keys.map(k => `
              <tr>
                <td><strong>${escapeHtml(k.name)}</strong></td>
                <td><code>${escapeHtml(k.key_prefix)}...</code></td>
                <td>${k.is_active ? '<span class="badge badge-success">Active</span>' : '<span class="badge badge-danger">Revoked</span>'}</td>
                <td>${k.last_used_at ? timeAgo(k.last_used_at) : '-'}</td>
                <td>${k.expires_at ? new Date(k.expires_at).toLocaleDateString('el') : 'Ποτέ'}</td>
                <td>${k.is_active ? `<button class="btn btn-danger btn-sm" onclick="revokeKey('${k.id}')">Ανάκληση</button>` : ''}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
    ` : '<div class="empty-state"><div class="icon">🔑</div><h3>Δεν υπάρχουν API keys</h3></div>'}
    <div id="modal-container"></div>
  `;
});

function showCreateKeyModal() {
  document.getElementById('modal-container').innerHTML = `
    <div class="modal-backdrop" onclick="this.remove()">
      <div class="modal" onclick="event.stopPropagation()">
        <h2>Νέο API Key</h2>
        <form id="key-form">
          <div class="form-group"><label>Όνομα</label><input id="key-name" required placeholder="Production Key"></div>
          <div class="modal-actions">
            <button type="button" class="btn btn-ghost" onclick="document.querySelector('.modal-backdrop').remove()">Ακύρωση</button>
            <button type="submit" class="btn btn-primary">Δημιουργία</button>
          </div>
        </form>
      </div>
    </div>
  `;
  document.getElementById('key-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const res = await api.post('/api-keys/', { name: document.getElementById('key-name').value });
    if (res.ok) {
      const data = await res.json();
      document.querySelector('.modal-backdrop').remove();
      document.getElementById('modal-container').innerHTML = `
        <div class="modal-backdrop">
          <div class="modal">
            <h2>🔑 Κλειδί δημιουργήθηκε!</h2>
            <p style="color:var(--warning);margin-bottom:12px;font-size:13px">⚠️ Αντίγραψέ το τώρα — δε θα εμφανιστεί ξανά!</p>
            <div class="form-group">
              <input value="${escapeHtml(data.raw_key)}" readonly onclick="this.select()" style="font-family:monospace;font-size:12px">
            </div>
            <div class="modal-actions">
              <button class="btn btn-primary" onclick="document.querySelector('.modal-backdrop').remove();router.navigate('api-keys')">OK</button>
            </div>
          </div>
        </div>
      `;
    } else {
      const err = await res.json().catch(() => ({}));
      toast.error(err.detail || 'Σφάλμα');
    }
  });
}

async function revokeKey(id) {
  if (!confirm('Σίγουρα θέλεις να ανακαλέσεις αυτό το κλειδί;')) return;
  const res = await api.del(`/api-keys/${id}`);
  if (res.ok || res.status === 204) { toast.success('Το κλειδί ανακλήθηκε'); router.navigate('api-keys'); }
  else { toast.error('Σφάλμα'); }
}

/* ── AUDIT LOG ────────────────────────────────────────────────────────── */
router.register('audit', async () => {
  if (!auth.isAdmin()) { router.navigate('dashboard'); return; }
  renderLayout('<div class="empty-state"><div class="spinner"></div></div>', 'audit');

  const res = await api.get('/admin/audit-logs/?limit=100');
  const data = res.ok ? await res.json() : { logs: [], total: 0 };

  document.getElementById('page-content').innerHTML = `
    <div class="page-header"><h1>📋 Audit Log (${data.total})</h1></div>
    ${data.logs.length ? `
    <div class="card">
      <div class="table-wrapper">
        <table>
          <thead><tr><th>Ενέργεια</th><th>Τύπος</th><th>Resource</th><th>Πότε</th></tr></thead>
          <tbody>
            ${data.logs.map(l => `
              <tr>
                <td><span class="badge badge-info">${escapeHtml(l.action)}</span></td>
                <td>${escapeHtml(l.resource_type || '-')}</td>
                <td style="font-size:12px;font-family:monospace">${escapeHtml(l.resource_id?.substring(0, 8) || '-')}</td>
                <td>${timeAgo(l.created_at)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
    ` : '<div class="empty-state"><div class="icon">📋</div><h3>Δεν υπάρχουν logs</h3></div>'}
  `;
});

/* ── SETTINGS (Admin) ─────────────────────────────────────────────────── */
router.register('settings', async () => {
  if (!auth.isAdmin()) { router.navigate('dashboard'); return; }
  renderLayout('<div class="empty-state"><div class="spinner"></div></div>', 'settings');

  const res = await api.get('/admin/settings/');
  if (!res.ok) { document.getElementById('page-content').innerHTML = '<p>Σφάλμα φόρτωσης</p>'; return; }
  const s = await res.json();

  document.getElementById('page-content').innerHTML = `
    <div class="page-header"><h1>⚙️ Ρυθμίσεις Tenant</h1></div>
    <div class="card">
      <form id="settings-form">
        <div class="form-group"><label>Μέγιστοι χρήστες</label><input type="number" id="set-max-users" value="${s.max_users}" min="1"></div>
        <div class="form-group"><label>Μέγιστα έγγραφα</label><input type="number" id="set-max-docs" value="${s.max_documents}" min="1"></div>
        <div class="form-group"><label>Μέγιστη αποθήκευση (MB)</label><input type="number" id="set-max-storage" value="${s.max_storage_mb}" min="1"></div>
        <div class="form-group"><label>Chat μηνύματα / ημέρα</label><input type="number" id="set-max-chat" value="${s.max_chat_messages_per_day}" min="1"></div>
        <div class="form-group" style="display:flex;gap:20px;align-items:center">
          <label style="margin:0"><input type="checkbox" id="set-chat-on" ${s.chat_enabled ? 'checked' : ''}> Chat ενεργό</label>
          <label style="margin:0"><input type="checkbox" id="set-upload-on" ${s.file_upload_enabled ? 'checked' : ''}> Upload ενεργό</label>
        </div>
        <button type="submit" class="btn btn-primary">Αποθήκευση</button>
      </form>
    </div>
  `;

  document.getElementById('settings-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const res = await api.patch('/admin/settings/', {
      max_users: parseInt(document.getElementById('set-max-users').value),
      max_documents: parseInt(document.getElementById('set-max-docs').value),
      max_storage_mb: parseInt(document.getElementById('set-max-storage').value),
      max_chat_messages_per_day: parseInt(document.getElementById('set-max-chat').value),
      chat_enabled: document.getElementById('set-chat-on').checked,
      file_upload_enabled: document.getElementById('set-upload-on').checked,
    });
    if (res.ok) toast.success('Οι ρυθμίσεις αποθηκεύτηκαν!');
    else toast.error('Σφάλμα αποθήκευσης');
  });
});

/* ── Boot ──────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => router.render());
