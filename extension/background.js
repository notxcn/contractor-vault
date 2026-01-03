/**
 * Contractor Vault - Background Service Worker v3.3
 * Added server-side validation (Kill Switch polling)
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

async function reloadMatchingTabs(targetUrl) {
    if (!targetUrl) return;
    try {
        const domain = extractDomain(targetUrl);
        const root = getRootDomain(domain);

        console.log(`[CV] Attempting to reload tabs for ${domain} (${root})...`);

        const tabs = await chrome.tabs.query({});
        const tabsToReload = tabs.filter(t => t.url && (t.url.includes(domain) || t.url.includes(root)));

        for (const tab of tabsToReload) {
            console.log(`[CV] Reloading tab ${tab.id}: ${tab.title}`);
            try {
                await chrome.tabs.reload(tab.id);
            } catch (ignore) {
                // Tab might have closed
            }
        }
    } catch (e) {
        console.warn('[CV] Error reloading tabs:', e);
    }
}

// ===== SESSION BADGE =====

async function updateBadge() {
    try {
        const { activeSession } = await chrome.storage.session.get('activeSession');

        if (activeSession) {
            const expiresAt = new Date(activeSession.expiresAt);
            const now = new Date();
            const minutesLeft = Math.floor((expiresAt - now) / 60000);
            const secondsLeft = Math.floor((expiresAt - now) / 1000);

            if (secondsLeft <= 0) {
                await chrome.action.setBadgeText({ text: '' });
                await performLogout();
            } else if (minutesLeft <= 1) {
                // Show seconds when under 1 minute
                await chrome.action.setBadgeText({ text: `${Math.max(0, secondsLeft)}s` });
                await chrome.action.setBadgeBackgroundColor({ color: '#FF0000' });
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
                    console.warn(`[CV] Failed to delete cookie ${cookie.name}:`, e);
                }
            }
            console.log('[CV] All cookies deleted.');
        }

        // Show notification with unique ID
        if (activeSession) {
            // Check if we are logging out due to revocation (custom handled in checkExpiry) or normal expiry
            // We'll just show generic if not already handled, but for simplicity we rely on checkExpiry for revocation msg
            // and here for general expiry.

            // We can check a flag or just execute.
            // But to avoid double notification, we can just do it.
            // Or better: performLogout takes an optional message?
        }

        // Note: Notification logic moved to caller or handled here generically if not passed
        // For now we keep the gentle expiry message here, checkExpiry handles revocation specific

        await reloadMatchingTabs(activeSession ? activeSession.targetUrl : null);

        await chrome.storage.session.clear();
        await chrome.action.setBadgeText({ text: '' });

        // Cancel alarms
        await chrome.alarms.clear('checkExpiry');
        await chrome.alarms.clear('preciseExpiry');

        await flushOnLogout();

        console.log('[CV] Auto-logout complete');
    } catch (e) {
        console.error('[CV] Logout error:', e);
    }
}

// ===== EXPIRY CHECK - Runs frequently + Precise =====

async function checkExpiry() {
    try {
        const { activeSession, warningShown, currentToken } = await chrome.storage.session.get(['activeSession', 'warningShown', 'currentToken']);

        if (activeSession) {

            // --- SERVER-SIDE VALIDATION (KILL SWITCH) ---
            if (currentToken) {
                try {
                    // Poll backend to see if token is still valid
                    const res = await fetch(`${API_URL}/api/access/validate/${currentToken}`);
                    if (res.ok) {
                        const status = await res.json();

                        if (!status.valid) {
                            console.log('[CV] Server validation failed:', status.status);

                            // If revoked, show specific aggressive message
                            if (status.status === 'revoked') {
                                await chrome.notifications.create(`revoked-${Date.now()}`, {
                                    type: 'basic',
                                    iconUrl: chrome.runtime.getURL('icons/icon128.png'),
                                    title: '🚫 Access Revoked',
                                    message: 'Your administrator has immediately revoked access to this session.',
                                    priority: 2,
                                    requireInteraction: true
                                });
                            } else {
                                // Expired according to server (maybe clock diff)
                                await chrome.notifications.create(`expired-${Date.now()}`, {
                                    type: 'basic',
                                    iconUrl: chrome.runtime.getURL('icons/icon128.png'),
                                    title: '🔒 Session Expired',
                                    message: 'Your session has expired.',
                                    priority: 2
                                });
                            }

                            await performLogout();
                            return; // Stop processing
                        }
                    }
                } catch (err) {
                    console.warn('[CV] Validation poll failed (offline?):', err);
                    // Continue to local check as fallback
                }
            }

            // --- LOCAL TIME CHECK ---
            const expiresAt = new Date(activeSession.expiresAt);
            const now = new Date();
            const secondsLeft = Math.floor((expiresAt - now) / 1000);

            console.log(`[CV] Expiry check: ${secondsLeft}s left`);

            // Session expired!
            if (secondsLeft <= 0) {
                console.log('[CV] Session expired (local check)!');
                await chrome.notifications.create(`expired-${Date.now()}`, {
                    type: 'basic',
                    iconUrl: chrome.runtime.getURL('icons/icon128.png'),
                    title: '🔒 Session Expired',
                    message: `Time's up! You have been logged out of ${activeSession.name}.`,
                    priority: 2
                });
                await performLogout();
                return;
            }

            // Show warning at 1 minute (60 seconds)
            if (secondsLeft <= 60 && secondsLeft > 0 && !warningShown) {
                const notifId = `warning-${Date.now()}`;
                try {
                    await chrome.notifications.create(notifId, {
                        type: 'basic',
                        iconUrl: chrome.runtime.getURL('icons/icon128.png'),
                        title: '⚠️ Session Expiring Soon!',
                        message: `Your session expires in ${secondsLeft} seconds!`,
                        priority: 2
                    });
                    await chrome.storage.session.set({ warningShown: true });
                } catch (e) {
                    console.warn('[CV] Warning notification error:', e);
                }
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


// ===== DEVICE FINGERPRINTING =====

async function getDeviceContext() {
    try {
        const platform = await chrome.runtime.getPlatformInfo();
        const userAgent = navigator.userAgent;

        // Basic fingerprint
        return {
            os: platform.os,
            arch: platform.arch,
            userAgent: userAgent,
            screen: {
                width: 1920, // Cannot reliably get from service worker
                height: 1080
            },
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
            language: navigator.language
        };
    } catch (e) {
        console.warn('[CV] Device context error:', e);
        return {};
    }
}

async function captureAndStore(domain, name, adminEmail) {
    console.log('[CV] captureAndStore called:', domain, name, adminEmail);

    const cookies = await captureCookies(domain);

    if (cookies.length === 0) {
        throw new Error(`No cookies found for ${domain}. Make sure you're logged in!`);
    }

    const targetUrl = `https://${extractDomain(domain)}`;
    const deviceContext = await getDeviceContext();

    console.log('[CV] Storing session:', { name, targetUrl, cookieCount: cookies.length });

    const response = await fetch(`${API_URL}/api/sessions/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Device-Context': JSON.stringify(deviceContext)
        },
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

    const deviceContext = await getDeviceContext();

    const response = await fetch(`${API_URL}/api/sessions/claim/${token}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Device-Context': JSON.stringify(deviceContext)
        },
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

    // 1. Regular polling safety net + server check (every 15s)
    await chrome.alarms.clear('checkExpiry');
    await chrome.alarms.create('checkExpiry', {
        delayInMinutes: 0.1,
        periodInMinutes: 0.25
    });

    // 2. Exact timestamp alarm (Precise Kickoff)
    await chrome.alarms.clear('preciseExpiry');
    const expiryTime = new Date(data.expires_at).getTime();
    if (expiryTime > Date.now()) {
        console.log(`[CV] Setting precise expiry alarm for: ${new Date(expiryTime).toLocaleString()}`);
        await chrome.alarms.create('preciseExpiry', { when: expiryTime });
    }

    await updateBadge();
    console.log('[CV] Session active, dual alarms set');
    return data;
}

// ===== MESSAGE HANDLER =====

chrome.runtime.onMessage.addListener((msg, sender, respond) => {
    if (msg.type === 'CAPTURE_AND_STORE') {
        captureAndStore(msg.domain, msg.name, msg.adminEmail)
            .then(data => respond({ success: true, data }))
            .catch(e => respond({ success: false, error: e.message }));
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

// ===== ALARM HANDLERS (The Watchdogs) =====

chrome.alarms.onAlarm.addListener(async (alarm) => {
    if (alarm.name === 'checkExpiry') {
        await checkExpiry();
    } else if (alarm.name === 'preciseExpiry') {
        console.log('[CV] Precise expiry alarm fired! Session ended.');
        // Show notification here since performLogout doesn't anymore (to avoid duplicate triggers)
        await chrome.notifications.create(`expired-${Date.now()}`, {
            type: 'basic',
            iconUrl: chrome.runtime.getURL('icons/icon128.png'),
            title: '🔒 Session Expired',
            message: `Time's up! You have been logged out.`,
            priority: 2,
            requireInteraction: true
        });
        await performLogout();
    } else if (alarm.name === 'flushActivity') {
        await flushActivityBuffer();
    }
});

// ===== STARTUP =====

chrome.runtime.onStartup.addListener(async () => {
    await checkExpiry();
    await updateBadge();
});

chrome.runtime.onInstalled.addListener(async () => {
    await updateBadge();
    // Re-register alarms if valid session exists
    const { activeSession } = await chrome.storage.session.get('activeSession');
    if (activeSession) {
        const expiryTime = new Date(activeSession.expiresAt).getTime();
        if (expiryTime > Date.now()) {
            await chrome.alarms.create('checkExpiry', { delayInMinutes: 0.1, periodInMinutes: 0.25 });
            await chrome.alarms.create('preciseExpiry', { when: expiryTime });
        }
    }
});

// ===== SESSION RECORDER (Buffer & Flush) =====

let activityBuffer = [];
let lastUrl = null;
let lastUrlTimestamp = null;

chrome.webNavigation.onCompleted.addListener(async (details) => {
    if (details.frameId !== 0) return;
    try {
        const { activeSession, currentToken } = await chrome.storage.session.get(['activeSession', 'currentToken']);
        if (!activeSession || !currentToken) return;

        let title = null;
        try {
            const tab = await chrome.tabs.get(details.tabId);
            title = tab.title;
        } catch (e) { }

        const now = new Date();
        if (activityBuffer.length > 0 && lastUrl && lastUrlTimestamp) {
            activityBuffer[activityBuffer.length - 1].duration_ms = now.getTime() - lastUrlTimestamp.getTime();
        }

        activityBuffer.push({
            url: details.url,
            title: title,
            transition_type: details.transitionType || null,
            referrer_url: lastUrl,
            timestamp: now.toISOString(),
            duration_ms: null
        });

        lastUrl = details.url;
        lastUrlTimestamp = now;
        console.log(`[CV] Activity logged: ${details.url.substring(0, 50)}...`);
    } catch (e) { console.warn('[CV] Activity logging error:', e); }
});

async function flushActivityBuffer() {
    if (activityBuffer.length === 0) return;
    try {
        const { currentToken } = await chrome.storage.session.get('currentToken');
        if (!currentToken) { activityBuffer = []; return; }

        const batch = { session_token: currentToken, activities: [...activityBuffer] };
        activityBuffer = []; // Clear local buffer immediately

        const response = await fetch(`${API_URL}/api/activity/log`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(batch)
        });

        if (response.ok) {
            const result = await response.json();
            console.log(`[CV] Flushed ${result.logged_count} activities`);
        }
    } catch (e) {
        console.warn('[CV] Activity flush error:', e);
        // Note: We lost the buffer here but that's better than infinite loop of broken retries
    }
}

chrome.alarms.create('flushActivity', { periodInMinutes: 0.167 }); // 10s

async function flushOnLogout() {
    await flushActivityBuffer();
}

console.log('[CV] Background v3.3 ready - Remote Kill Switch');
