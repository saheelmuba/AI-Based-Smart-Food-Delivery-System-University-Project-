// ICST Admin Dashboard — talks to the /api/admin/* endpoints in app.py.
const API = '';                       // same origin as the served page
let TOKEN = localStorage.getItem('icst_admin_token') || null;
let MENU_CACHE = [];
let ORDERS_CACHE = [];

function authHeaders(extra) {
  return Object.assign({ 'Authorization': 'Bearer ' + TOKEN }, extra || {});
}
function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}
function toast(msg, type = 'info') {
  const el = document.createElement('div');
  el.className = 'toast ' + type;
  el.textContent = msg;
  document.getElementById('toast').appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 300); }, 2800);
}

// ---------- Auth ----------
async function adminLogin() {
  const email = document.getElementById('adminEmail').value.trim();
  const password = document.getElementById('adminPassword').value;
  const errEl = document.getElementById('loginError');
  errEl.textContent = '';
  try {
    const res = await fetch(API + '/api/auth/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) { errEl.textContent = data.error || 'Login failed'; return; }
    if (!data.user.is_admin) { errEl.textContent = 'This account is not an administrator.'; return; }
    TOKEN = data.token;
    localStorage.setItem('icst_admin_token', TOKEN);
    document.getElementById('whoami').textContent = '· ' + data.user.name;
    showDashboard();
  } catch (e) { errEl.textContent = 'Network error — is the server running?'; }
}
function adminLogout() {
  TOKEN = null; localStorage.removeItem('icst_admin_token');
  document.getElementById('dashView').classList.add('hidden');
  document.getElementById('loginView').classList.remove('hidden');
}
function showDashboard() {
  document.getElementById('loginView').classList.add('hidden');
  document.getElementById('dashView').classList.remove('hidden');
  loadStats(); loadMenu(); loadOrders(); loadUsers();
}

// ---------- Tabs ----------
function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === name));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.add('hidden'));
  document.getElementById('tab-' + name).classList.remove('hidden');
}

// ---------- Dashboard / stats ----------
async function loadStats() {
  try {
    const res = await fetch(API + '/api/admin/stats', { headers: authHeaders() });
    if (res.status === 403) return adminLogout();
    const s = await res.json();
    document.getElementById('statGrid').innerHTML = [
      ['Revenue', 'Rs. ' + s.revenue, 'fa-sack-dollar'],
      ['Orders', s.orders, 'fa-receipt'],
      ['Menu Items', s.menu_items, 'fa-utensils'],
      ['Users', s.users, 'fa-users'],
    ].map(([l, v, i]) => `<div class="stat-card"><div class="label">${l}</div><div class="value"><i class="fas ${i}"></i>${v}</div></div>`).join('');
    document.getElementById('popularList').innerHTML = (s.popular_items.length
      ? '<table><tbody>' + s.popular_items.map(p => `<tr><td>${esc(p.name)}</td><td style="text-align:right;font-weight:700;color:var(--accent)">${p.qty} sold</td></tr>`).join('') + '</tbody></table>'
      : 'No orders yet.');
    const sb = s.orders_by_status;
    document.getElementById('statusBreakdown').innerHTML = Object.keys(sb).length
      ? Object.entries(sb).map(([k, v]) => `<span class="pill s-${k}" style="margin-right:8px;">${k}: ${v}</span>`).join('')
      : 'No orders yet.';
  } catch (e) { toast('Failed to load stats', 'error'); }
}

// ---------- Menu CRUD ----------
async function loadMenu() {
  const res = await fetch(API + '/api/menu');
  MENU_CACHE = (await res.json()).items || [];
  const cats = [...new Set(MENU_CACHE.map(m => m.category))].sort();
  document.getElementById('menuCatFilter').innerHTML =
    '<option value="">All categories</option>' + cats.map(c => `<option>${esc(c)}</option>`).join('');
  renderMenuTable();
}
function renderMenuTable() {
  const q = (document.getElementById('menuSearch').value || '').toLowerCase();
  const cat = document.getElementById('menuCatFilter').value;
  const rows = MENU_CACHE.filter(m =>
    (!q || m.name.toLowerCase().includes(q)) && (!cat || m.category === cat));
  document.getElementById('menuTableBody').innerHTML = rows.map(m => `
    <tr>
      <td>${m.id}</td>
      <td>${esc(m.emoji || '')} ${esc(m.name)}</td>
      <td>${esc(m.category || '')}</td>
      <td>${esc(m.cuisine || '')}</td>
      <td>Rs.${m.price}</td>
      <td>${m.veg ? '🟢' : '🔴'}</td>
      <td class="row-actions">
        <button class="btn btn-outline btn-sm" onclick="openMenuModal(${m.id})"><i class="fas fa-pen"></i></button>
        <button class="btn btn-danger btn-sm" onclick="deleteMenu(${m.id})"><i class="fas fa-trash"></i></button>
      </td>
    </tr>`).join('') || '<tr><td colspan="7" class="muted">No items match.</td></tr>';
}
function openMenuModal(id) {
  const m = id ? MENU_CACHE.find(x => x.id === id) : {};
  const isEdit = !!id;
  document.getElementById('modalRoot').innerHTML = `
    <div class="modal-overlay" onclick="if(event.target===this)closeModal()">
      <div class="modal">
        <h3>${isEdit ? 'Edit' : 'Add'} Menu Item</h3>
        <div class="field"><label>Name</label><input id="m_name" value="${esc(m.name || '')}"></div>
        <div class="modal-row">
          <div class="field"><label>Price (Rs.)</label><input id="m_price" type="number" value="${m.price || ''}"></div>
          <div class="field"><label>Emoji</label><input id="m_emoji" value="${esc(m.emoji || '🍽️')}"></div>
        </div>
        <div class="modal-row">
          <div class="field"><label>Category</label>
            <select id="m_category">${['Breakfast', 'Lunch', 'Dinner', 'Snack', 'Beverage', 'Dessert'].map(c => `<option ${m.category === c ? 'selected' : ''}>${c}</option>`).join('')}</select></div>
          <div class="field"><label>Cuisine</label>
            <select id="m_cuisine">${['Sri Lankan', 'Indian', 'Chinese', 'Western', 'Italian', 'Arabic', 'Fast Food', 'Seafood', 'Vegetarian', 'Vegan'].map(c => `<option ${m.cuisine === c ? 'selected' : ''}>${c}</option>`).join('')}</select></div>
        </div>
        <div class="modal-row">
          <div class="field"><label>Calories</label><input id="m_calories" type="number" value="${m.calories || 400}"></div>
          <div class="field"><label>Type</label>
            <select id="m_veg"><option value="false" ${!m.veg ? 'selected' : ''}>Non-veg</option><option value="true" ${m.veg ? 'selected' : ''}>Veg</option></select></div>
        </div>
        <div class="modal-actions">
          <button class="btn btn-outline" onclick="closeModal()">Cancel</button>
          <button class="btn btn-primary" onclick="saveMenu(${id || 'null'})">${isEdit ? 'Save' : 'Add'}</button>
        </div>
      </div>
    </div>`;
}
function closeModal() { document.getElementById('modalRoot').innerHTML = ''; }
async function saveMenu(id) {
  const body = {
    name: document.getElementById('m_name').value.trim(),
    price: document.getElementById('m_price').value,
    emoji: document.getElementById('m_emoji').value,
    category: document.getElementById('m_category').value,
    cuisine: document.getElementById('m_cuisine').value,
    calories: document.getElementById('m_calories').value,
    veg: document.getElementById('m_veg').value === 'true',
  };
  if (!body.name || !body.price) { toast('Name and price are required', 'error'); return; }
  const url = id ? API + '/api/admin/menu/' + id : API + '/api/admin/menu';
  const res = await fetch(url, {
    method: id ? 'PUT' : 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(body)
  });
  const data = await res.json();
  if (res.ok) { toast(id ? 'Item updated' : 'Item added', 'success'); closeModal(); loadMenu(); loadStats(); }
  else { toast(data.error || 'Save failed', 'error'); }
}
async function deleteMenu(id) {
  const m = MENU_CACHE.find(x => x.id === id);
  if (!confirm(`Delete "${m ? m.name : id}"? This cannot be undone.`)) return;
  const res = await fetch(API + '/api/admin/menu/' + id, { method: 'DELETE', headers: authHeaders() });
  if (res.ok) { toast('Item deleted', 'success'); loadMenu(); loadStats(); }
  else { toast('Delete failed', 'error'); }
}

// ---------- Orders ----------
async function loadOrders() {
  const res = await fetch(API + '/api/admin/orders', { headers: authHeaders() });
  if (res.status === 403) return adminLogout();
  ORDERS_CACHE = (await res.json()).orders || [];
  renderOrdersTable();
}
function renderOrdersTable() {
  const filter = document.getElementById('orderStatusFilter').value;
  const rows = ORDERS_CACHE.filter(o => !filter || o.status === filter);
  const FLOW = ['placed', 'preparing', 'ready', 'completed', 'cancelled'];
  document.getElementById('ordersTableBody').innerHTML = rows.map(o => {
    const items = (o.items || []).map(i => `${i.qty}× ${esc(i.name)}`).join(', ');
    const opts = FLOW.map(s => `<option ${s === o.status ? 'selected' : ''}>${s}</option>`).join('');
    return `<tr>
      <td>${esc(o.order_id)}<div class="muted">${new Date(o.timestamp).toLocaleString()}</div></td>
      <td>${esc(o.user_name || '—')}<div class="muted">${esc(o.user_email || '')}</div></td>
      <td style="max-width:240px;">${items}</td>
      <td>Rs.${o.total}</td>
      <td><span class="pill s-${o.status}">${o.status}</span></td>
      <td><select onchange="setOrderStatus('${esc(o.order_id)}', this.value)">${opts}</select></td>
    </tr>`;
  }).join('') || '<tr><td colspan="6" class="muted">No orders.</td></tr>';
}
async function setOrderStatus(orderId, status) {
  const res = await fetch(API + '/api/admin/orders/' + orderId + '/status', {
    method: 'POST', headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ status })
  });
  const data = await res.json();
  if (res.ok) { toast('Order ' + orderId + ' → ' + status, 'success'); loadOrders(); loadStats(); }
  else { toast(data.error || 'Update failed', 'error'); }
}

// ---------- Users ----------
async function loadUsers() {
  const res = await fetch(API + '/api/admin/users', { headers: authHeaders() });
  if (res.status === 403) return adminLogout();
  const users = (await res.json()).users || [];
  document.getElementById('usersTableBody').innerHTML = users.map(u => `
    <tr>
      <td>${u.user_id}</td>
      <td>${esc(u.name)}</td>
      <td>${esc(u.email)}</td>
      <td>${u.is_admin ? '<span class="pill s-ready">Admin</span>' : '<span class="pill s-completed">User</span>'}</td>
      <td>${u.order_count}</td>
      <td class="muted">${u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}</td>
    </tr>`).join('') || '<tr><td colspan="6" class="muted">No users.</td></tr>';
}

// ---------- Boot ----------
if (TOKEN) {
  // Validate the stored token by hitting a guarded endpoint.
  fetch(API + '/api/admin/stats', { headers: authHeaders() })
    .then(r => { if (r.ok) showDashboard(); else adminLogout(); })
    .catch(() => adminLogout());
}
