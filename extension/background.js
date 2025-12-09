/**
 * Contractor Vault - Background Service Worker v2.5
 * Fixed notification IDs and icon issues
 */

const API_URL = 'https://contractor-vault-production.up.railway.app';

// ===== UTILITY FUNCTIONS =====

function extractDomain(input) {
    return input.trim().replace(/^https?:\/\//, '').split('/')[0].split(':')[0];
}

function getRootDomain(domain) {
    const parts = domain.split('.');
    return parts.length >= 2 ? parts.slice(-2).join('.') : domain;
}

// ===== SESSION BADGE =====

async function updateBadge() {
    try {
        const { activeSession } = await chrome.storage.session.get('activeSession');

        if (activeSession) {
            const expiresAt = new Date(activeSession.expiresAt);
            const now = new Date();
            const minutesLeft = Math.floor((expiresAt - now) / 60000);

            if (minutesLeft <= 0) {
                await chrome.action.setBadgeText({ text: '' });
                await performLogout();
            } else if (minutesLeft <= 5) {
                await chrome.action.setBadgeText({ text: `${minutesLeft}m` });
                await chrome.action.setBadgeBackgroundColor({ color: '#FFA500' });
            } else {
                await chrome.action.setBadgeText({ text: '✓' });
                await chrome.action.setBadgeBackgroundColor({ color: '#4CAF50' });
            }
        } else {
            await chrome.action.setBadgeText({ text: '' });
        }
    } catch (e) {
        console.warn('[CV] Badge update error:', e);
    }
}

// ===== AUTO-LOGOUT: Delete cookies on expiry =====

async function performLogout() {
    console.log('[CV] Performing auto-logout...');

    try {
        const { activeSession, injectedCookies } = await chrome.storage.session.get(['activeSession', 'injectedCookies']);

        if (injectedCookies && injectedCookies.length > 0) {
            console.log(`[CV] Deleting ${injectedCookies.length} cookies...`);

            for (const cookie of injectedCookies) {
                try {
                    const protocol = cookie.secure ? 'https' : 'http';
                    const domain = cookie.domain.startsWith('.') ? cookie.domain.slice(1) : cookie.domain;
                    const url = `${protocol}://${domain}${cookie.path || '/'}`;

                    await chrome.cookies.remove({ url, name: cookie.name });
                } catch (e) {
                    // Ignore individual cookie deletion errors
                }
            }
        }

        // Show notification with unique ID
        if (activeSession) {
            const notifId = `expired-${Date.now()}`;
            await chrome.notifications.create(notifId, {
                type: 'basic',
                iconUrl: chrome.runtime.getURL('icons/icon128.png'),
                title: 'Session Expired - Logged Out',
                message: `Your session for ${activeSession.name} has expired.`,
                priority: 2
            });
        }

        await chrome.storage.session.clear();
        await chrome.action.setBadgeText({ text: '' });

        console.log('[CV] Auto-logout complete');
    } catch (e) {
        console.error('[CV] Logout error:', e);
    }
}

// ===== EXPIRY WARNING =====

async function checkExpiry() {
    try {
        const { activeSession, warningShown } = await chrome.storage.session.get(['activeSession', 'warningShown']);

        if (activeSession) {
            const expiresAt = new Date(activeSession.expiresAt);
            const now = new Date();
            const minutesLeft = Math.floor((expiresAt - now) / 60000);

            // Show warning at 5 minutes OR 1 minute (for short sessions)
            const shouldWarn = (minutesLeft <= 5 && minutesLeft > 0 && !warningShown) ||
                (minutesLeft <= 1 && minutesLeft > 0);

            if (shouldWarn && !warningShown) {
                const notifId = `warning-${Date.now()}`;
                await chrome.notifications.create(notifId, {
                    type: 'basic',
                    iconUrl: chrome.runtime.getURL('icons/icon128.png'),
                    title: '⚠️ Session Expiring Soon!',
                    message: minutesLeft <= 1
                        ? `Your session expires in less than 1 minute!`
                        : `Your session expires in ${minutesLeft} minutes!`,
                    priority: 2
                });
                await chrome.storage.session.set({ warningShown: true });
            }

            // Session expired
            if (minutesLeft <= 0) {
                await performLogout();
            }

            await updateBadge();
        }
    } catch (e) {
        console.warn('[CV] Expiry check error:', e);
    }
}

// ===== COOKIE FUNCTIONS =====

async function captureCookies(input) {
    const domain = extractDomain(input);
    const rootDomain = getRootDomain(domain);

    console.log('[CV] Capturing cookies for:', domain, 'root:', rootDomain);

    const patterns = [rootDomain, `.${rootDomain}`, domain, `.${domain}`];

    // Add Steam-specific domains
    if (rootDomain.includes('steampowered') || rootDomain.includes('steam')) {
        patterns.push('steamcommunity.com', '.steamcommunity.com', 'store.steampowered.com', '.steampowered.com');
    }

    console.log('[CV] Cookie patterns:', patterns);

    const results = await Promise.all(
        patterns.map(d => chrome.cookies.getAll({ domain: d }).catch(() => []))
    );

    const cookieMap = new Map();
    for (const cookies of results) {
        for (const c of cookies) {
            cookieMap.set(`${c.domain}|${c.name}`, c);
        }
    }

    const cookieData = Array.from(cookieMap.values()).map(c => ({
        name: c.name,
        value: c.value,
        domain: c.domain,
        path: c.path,
        secure: c.secure,
        httpOnly: c.httpOnly,
        sameSite: c.sameSite || 'lax',
        expirationDate: c.expirationDate,
    }));

    console.log(`[CV] Captured ${cookieData.length} cookies`);
    return cookieData;
}

async function captureAndStore(domain, name, adminEmail) {
    console.log('[CV] captureAndStore called:', domain, name, adminEmail);

    const cookies = await captureCookies(domain);

    if (cookies.length === 0) {
        throw new Error(`No cookies found for ${domain}. Make sure you're logged in!`);
    }

    const targetUrl = `https://${extractDomain(domain)}`;

    console.log('[CV] Storing session:', { name, targetUrl, cookieCount: cookies.length });

    const response = await fetch(`${API_URL}/api/sessions/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            name,
            target_url: targetUrl,
            cookies,
            created_by: adminEmail,
        }),
    });

    console.log('[CV] Store response status:', response.status);

    if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Server error' }));
        console.error('[CV] Store error:', err);
        throw new Error(err.detail || 'Failed to store session');
    }

    const data = await response.json();
    console.log('[CV] Session stored:', data);
    return data;
}

async function injectCookies(cookies, targetUrl) {
    const results = [];
    const injectedCookies = [];

    for (const cookie of cookies) {
        try {
            const protocol = cookie.secure ? 'https' : 'http';
            const domain = cookie.domain.startsWith('.') ? cookie.domain.slice(1) : cookie.domain;

            await chrome.cookies.set({
                url: `${protocol}://${domain}${cookie.path || '/'}`,
                name: cookie.name,
                value: cookie.value,
                domain: cookie.domain,
                path: cookie.path || '/',
                secure: cookie.secure,
                httpOnly: cookie.httpOnly,
                sameSite: cookie.sameSite || 'lax',
                ...(cookie.expirationDate && { expirationDate: cookie.expirationDate }),
            });

            injectedCookies.push({
                name: cookie.name,
                domain: cookie.domain,
                path: cookie.path || '/',
                secure: cookie.secure,
            });

            results.push({ name: cookie.name, success: true });
        } catch (e) {
            results.push({ name: cookie.name, success: false, error: e.message });
        }
    }

    await chrome.storage.session.set({ injectedCookies });
    return results;
}

async function claimSession(token) {
    console.log('[CV] Claiming session with token:', token.substring(0, 10) + '...');

    const response = await fetch(`${API_URL}/api/sessions/claim/${token}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
    });

    console.log('[CV] Claim response status:', response.status);

    if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Server error' }));
        throw new Error(err.detail || 'Invalid or expired token');
    }

    const data = await response.json();
    console.log('[CV] Session claimed:', data.session_name);

    await injectCookies(data.cookies, data.target_url);

    await chrome.storage.session.set({
        activeSession: {
            name: data.session_name,
            targetUrl: data.target_url,
            expiresAt: data.expires_at,
        },
        currentToken: token,
        warningShown: false,
    });

    // Set up expiry check alarm
    await chrome.alarms.create('checkExpiry', { periodInMinutes: 1 });
    await updateBadge();

    return data;
}

// ===== MESSAGE HANDLER =====

chrome.runtime.onMessage.addListener((msg, sender, respond) => {
    console.log('[CV] Message received:', msg.type);

    if (msg.type === 'CAPTURE_AND_STORE') {
        captureAndStore(msg.domain, msg.name, msg.adminEmail)
            .then(data => {
                console.log('[CV] CAPTURE_AND_STORE success');
                respond({ success: true, data });
            })
            .catch(e => {
                console.error('[CV] CAPTURE_AND_STORE error:', e);
                respond({ success: false, error: e.message });
            });
        return true;
    }

    if (msg.type === 'CLAIM_SESSION') {
        claimSession(msg.token)
            .then(data => respond({ success: true, data }))
            .catch(e => respond({ success: false, error: e.message }));
        return true;
    }

    if (msg.type === 'GET_STATUS') {
        chrome.storage.session.get('activeSession').then(({ activeSession }) => {
            respond({ success: true, hasSession: !!activeSession, session: activeSession });
        });
        return true;
    }

    if (msg.type === 'FORCE_LOGOUT') {
        performLogout()
            .then(() => respond({ success: true }))
            .catch(e => respond({ success: false, error: e.message }));
        return true;
    }

    return false;
});

// ===== ALARM HANDLERS =====

chrome.alarms.onAlarm.addListener(async (alarm) => {
    if (alarm.name === 'checkExpiry') {
        await checkExpiry();
    }
});

// ===== STARTUP =====

chrome.runtime.onStartup.addListener(async () => {
    console.log('[CV] Extension startup');
    await checkExpiry();
    await updateBadge();
});

chrome.runtime.onInstalled.addListener(async () => {
    console.log('[CV] Extension installed/updated');
    await updateBadge();
    await chrome.alarms.create('checkExpiry', { periodInMinutes: 1 });
});

console.log('[CV] Background v2.5 ready');
