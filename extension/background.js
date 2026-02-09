const API_BASE = 'http://localhost:5000';

async function getToken() {
    return new Promise(resolve => {
        chrome.storage.local.get(['jwt_token'], result => {
            resolve(result.jwt_token || null);
        });
    });
}

async function updateBadge() {
    const token = await getToken();
    if (!token) {
        chrome.action.setBadgeText({ text: '' });
        return;
    }

    try {
        const res = await fetch(API_BASE + '/api/me', {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + token,
            },
        });
        const data = await res.json();
        if (data.ok) {
            const count = data.data.user.total_nos;
            chrome.action.setBadgeText({ text: String(count) });
            chrome.action.setBadgeBackgroundColor({ color: '#e2b714' });
            chrome.action.setBadgeTextColor({ color: '#1a1a2e' });
        } else {
            chrome.action.setBadgeText({ text: '' });
        }
    } catch (e) {
        // Server not reachable — clear badge
        chrome.action.setBadgeText({ text: '' });
    }
}

// Update badge every 5 minutes
chrome.alarms.create('updateBadge', { periodInMinutes: 5 });

chrome.alarms.onAlarm.addListener((alarm) => {
    if (alarm.name === 'updateBadge') {
        updateBadge();
    }
});

// Update badge on install/startup
chrome.runtime.onInstalled.addListener(updateBadge);
chrome.runtime.onStartup.addListener(updateBadge);

// Listen for storage changes (login/logout) to update badge immediately
chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local' && changes.jwt_token) {
        updateBadge();
    }
});
