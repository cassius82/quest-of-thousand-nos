// ─── Config ───────────────────────────────────────────────────────────
const API_BASE = 'http://localhost:5000';
const DOMAINS = ['general','career','sales','creative','entrepreneurship','social','writing','networking'];
const DIFF_LABELS = {1:'Easy',2:'Medium',3:'Hard',4:'Expert'};

// ─── Storage ─────────────────────────────────────────────────────────
async function getToken() {
    return new Promise(resolve => {
        chrome.storage.local.get(['jwt_token'], result => {
            resolve(result.jwt_token || null);
        });
    });
}

async function setToken(token) {
    return new Promise(resolve => {
        chrome.storage.local.set({ jwt_token: token }, resolve);
    });
}

async function clearToken() {
    return new Promise(resolve => {
        chrome.storage.local.remove(['jwt_token'], resolve);
    });
}

// ─── API ─────────────────────────────────────────────────────────────
async function api(path, opts = {}) {
    const url = API_BASE + path;
    const headers = { 'Content-Type': 'application/json' };
    const token = await getToken();
    if (token) headers['Authorization'] = 'Bearer ' + token;
    try {
        const res = await fetch(url, { ...opts, headers });
        const data = await res.json();
        if (res.status === 401) {
            await clearToken();
            renderLogin();
            return { ok: false, error: 'Session expired.' };
        }
        return data;
    } catch (e) {
        return { ok: false, error: 'Cannot connect to server.' };
    }
}

// ─── Helpers ─────────────────────────────────────────────────────────
function titleCase(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

function domainOptions(selected) {
    return DOMAINS.map(d =>
        `<option value="${d}" ${selected === d ? 'selected' : ''}>${titleCase(d)}</option>`
    ).join('');
}

function flash(msg, type = 'success') {
    const el = document.getElementById('flash');
    if (!el) return;
    el.className = 'flash flash-' + type;
    el.textContent = msg;
    el.style.display = 'block';
    setTimeout(() => { el.style.display = 'none'; }, 3000);
}

// ─── Badge Update ────────────────────────────────────────────────────
async function updateBadge() {
    const token = await getToken();
    if (!token) {
        chrome.action.setBadgeText({ text: '' });
        return;
    }
    const res = await api('/api/me');
    if (res.ok) {
        const count = res.data.user.total_nos;
        chrome.action.setBadgeText({ text: String(count) });
        chrome.action.setBadgeBackgroundColor({ color: '#e2b714' });
        chrome.action.setBadgeTextColor({ color: '#1a1a2e' });
    }
}

// ─── Render Login ────────────────────────────────────────────────────
function renderLogin() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div class="header">
            <h1>1000 No's</h1>
            <p>Rejection Therapy Tracker</p>
        </div>
        <div id="flash" style="display:none"></div>
        <div class="auth-section">
            <h2>Log In</h2>
            <form id="login-form">
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" required autofocus>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" required>
                </div>
                <button type="submit" class="btn btn-primary">Log In</button>
            </form>
            <p class="auth-footer">New here? <a id="show-register">Create account</a></p>
        </div>
    `;
    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const res = await api('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password }),
        });
        if (res.ok) {
            await setToken(res.data.token);
            await updateBadge();
            renderDashboard();
        } else {
            flash(res.error, 'error');
        }
    });
    document.getElementById('show-register').addEventListener('click', renderRegister);
}

// ─── Render Register ─────────────────────────────────────────────────
function renderRegister() {
    const app = document.getElementById('app');
    app.innerHTML = `
        <div class="header">
            <h1>1000 No's</h1>
            <p>Begin Your Quest</p>
        </div>
        <div id="flash" style="display:none"></div>
        <div class="auth-section">
            <h2>Create Account</h2>
            <form id="register-form">
                <div class="form-group">
                    <label for="display_name">Your Name</label>
                    <input type="text" id="display_name" required autofocus>
                </div>
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" required>
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" required minlength="6">
                </div>
                <div class="form-group">
                    <label for="quest_domain">Quest Domain</label>
                    <select id="quest_domain">${domainOptions('general')}</select>
                </div>
                <button type="submit" class="btn btn-primary">Start the Quest</button>
            </form>
            <p class="auth-footer">Already have an account? <a id="show-login">Log in</a></p>
        </div>
    `;
    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const res = await api('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify({
                display_name: document.getElementById('display_name').value,
                email: document.getElementById('email').value,
                password: document.getElementById('password').value,
                quest_domain: document.getElementById('quest_domain').value,
            }),
        });
        if (res.ok) {
            await setToken(res.data.token);
            await updateBadge();
            renderDashboard();
        } else {
            flash(res.error, 'error');
        }
    });
    document.getElementById('show-login').addEventListener('click', renderLogin);
}

// ─── Render Dashboard ────────────────────────────────────────────────
async function renderDashboard() {
    const app = document.getElementById('app');
    app.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:2rem 0;">Loading...</p>';

    const res = await api('/api/me');
    if (!res.ok) {
        if (res.error === 'Session expired.') return;
        app.innerHTML = `<p style="color:var(--error);text-align:center;">${res.error}</p>`;
        return;
    }

    const { user, daily, weekly } = res.data;
    const pct = Math.min(100, (user.total_nos / 1000 * 100)).toFixed(1);

    app.innerHTML = `
        <div class="header">
            <h1>1000 No's</h1>
            <p>Hello, ${user.display_name}</p>
        </div>
        <div id="flash" style="display:none"></div>
        <div class="counter-section">
            <div class="counter-big">${user.total_nos.toLocaleString()}</div>
            <div class="counter-label">No's Collected</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${pct}%"></div>
            </div>
            <div class="progress-text">${user.total_nos.toLocaleString()} / 1,000</div>
        </div>
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-val">${daily.nos}</div>
                <div class="stat-lbl">Today</div>
            </div>
            <div class="stat-box">
                <div class="stat-val">${weekly.nos}</div>
                <div class="stat-lbl">This Week</div>
            </div>
            <div class="stat-box">
                <div class="stat-val">${user.current_streak}</div>
                <div class="stat-lbl">Streak</div>
            </div>
            <div class="stat-box">
                <div class="stat-val">${user.total_wins}</div>
                <div class="stat-lbl">Wins</div>
            </div>
        </div>
        <div class="section-title">Quick Log</div>
        <form id="quick-log-form">
            <div class="form-group">
                <label for="description">What did you attempt?</label>
                <textarea id="description" rows="2" required placeholder="I asked for..."></textarea>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label for="nos_count">No's</label>
                    <input type="number" id="nos_count" value="1" min="1" max="100">
                </div>
                <div class="form-group">
                    <label for="quest_domain">Domain</label>
                    <select id="quest_domain">${domainOptions(user.quest_domain)}</select>
                </div>
            </div>
            <button type="submit" class="btn btn-primary">Log This No</button>
        </form>
        <div class="settings-row">
            <a class="logout-link" id="logout-link">Log out</a>
        </div>
    `;

    document.getElementById('quick-log-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const nos = parseInt(document.getElementById('nos_count').value) || 1;
        const logRes = await api('/api/attempts', {
            method: 'POST',
            body: JSON.stringify({
                description: document.getElementById('description').value,
                nos_count: nos,
                quest_domain: document.getElementById('quest_domain').value,
            }),
        });
        if (logRes.ok) {
            flash(`+${nos} No${nos > 1 ? "'s" : ""}! Keep going.`);
            await updateBadge();
            setTimeout(() => renderDashboard(), 1500);
        } else {
            flash(logRes.error, 'error');
        }
    });

    document.getElementById('logout-link').addEventListener('click', async () => {
        await clearToken();
        chrome.action.setBadgeText({ text: '' });
        renderLogin();
    });
}

// ─── Init ────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    const token = await getToken();
    if (token) {
        renderDashboard();
    } else {
        renderLogin();
    }
});
