```javascript
/**
 * Contractor Vault - Popup v4
 * Properly fixed error handling
 */

const BASE_URL = 'https://contractor-vault-production.up.railway.app';

// State
let capturedSessionId = null;

// DOM helpers
const $ = id => document.getElementById(id);

/**
 * Parse error detail from FastAPI response
 * FastAPI can return: string, or array of {loc, msg, type}
 */
function parseErrorDetail(detail) {
    if (!detail) return 'Unknown error';

    // If it's a string, return as-is
    if (typeof detail === 'string') return detail;

    // If it's an array (validation errors), extract messages
    if (Array.isArray(detail)) {
        return detail.map(err => {
            if (typeof err === 'string') return err;
            if (err.msg) return err.msg;
            return JSON.stringify(err);
        }).join('. ');
    }

    // If it's an object with a message
    if (detail.message) return detail.message;
    if (detail.msg) return detail.msg;

    // Fallback: stringify
    return JSON.stringify(detail);
}

function showSection(id) {
    ['main-menu', 'share-flow', 'claim-flow', 'active-session'].forEach(s => {
        $(s).classList.add('hidden');
    });
    $(id).classList.remove('hidden');
}

function showStatus(id, message, type) {
    const el = $(id);
    el.textContent = String(message);
    el.className = `status ${ type } `;
    el.classList.remove('hidden');
}

function hideStatus(id) {
    $(id).classList.add('hidden');
}

// Check for existing session
async function init() {
    try {
        const response = await chrome.runtime.sendMessage({ type: 'GET_STATUS' });
        if (response?.hasSession && response.session) {
            $('session-site').textContent = response.session.name || response.session.targetUrl;
            $('session-expires').textContent = new Date(response.session.expiresAt).toLocaleString();
            $('btn-open').href = response.session.targetUrl;
            showSection('active-session');
        }
    } catch (e) {
        console.log('No active session');
    }
}

// Navigation
$('btn-share').onclick = () => {
    showSection('share-flow');
    $('step1').classList.remove('hidden');
    $('step2').classList.add('hidden');
    $('step3').classList.add('hidden');
    hideStatus('share-status');
    capturedSessionId = null;
};

$('btn-claim').onclick = () => {
    showSection('claim-flow');
    hideStatus('claim-status');
};

$('btn-back-share').onclick = () => showSection('main-menu');
$('btn-back-claim').onclick = () => showSection('main-menu');

// Admin Link
$('btn-admin').onclick = () => {
    chrome.tabs.create({ url: 'https://contractor-vault.vercel.app' });
};

// Share Secret Link
$('btn-share-secret').onclick = () => {
    chrome.tabs.create({ url: 'https://contractor-vault.vercel.app/?tab=secrets' });
};

// SHARE: Step 1 - Capture
$('btn-capture').onclick = async () => {
    const btn = $('btn-capture');
    btn.disabled = true;
    btn.textContent = '⏳ Capturing...';
    showStatus('share-status', '⏳ Capturing cookies...', 'loading');

    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab?.url) throw new Error('No active tab found');

        const url = new URL(tab.url);
        const domain = url.hostname;

        console.log('Capturing session for domain:', domain);

        const response = await chrome.runtime.sendMessage({
            type: 'CAPTURE_AND_STORE',
            domain: domain,
            name: `${ domain } Session`,
            adminEmail: 'admin@contractor-vault.local',
        });

        console.log('Capture response:', response);

        if (!response || !response.success) {
            const errorMsg = response?.error || 'Failed to capture session';
            throw new Error(typeof errorMsg === 'object' ? JSON.stringify(errorMsg) : errorMsg);
        }

        capturedSessionId = response.data.id;
        console.log('Session captured with ID:', capturedSessionId);

        showStatus('share-status', `✅ Captured ${ response.data.cookie_count } cookies from ${ domain } `, 'success');

        // Move to step 2
        $('step1').classList.add('hidden');
        $('step2').classList.remove('hidden');

    } catch (error) {
        console.error('Capture error:', error);
        showStatus('share-status', `❌ ${ error.message || error } `, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Capture Current Site';
    }
};

// SHARE: Step 2 - Generate code
$('btn-generate').onclick = async () => {
    if (!capturedSessionId) {
        showStatus('share-status', '❌ Please capture a session first. Click "Back" and start over.', 'error');
        return;
    }

    const btn = $('btn-generate');
    btn.disabled = true;
    btn.textContent = '⏳ Generating...';
    showStatus('share-status', '⏳ Generating access code...', 'loading');

    try {
        const duration = parseInt($('duration').value);
        const email = $('contractor-email').value.trim() || 'contractor@temp.local';

        console.log('Generating token for session:', capturedSessionId);

        const response = await fetch(`${ API_URL } /api/sessions / generate - token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                credential_id: capturedSessionId,
                contractor_email: email,
                duration_minutes: duration,
                allowed_ip: $('allowed-ip').value.trim() || null,
                is_one_time: $('is-one-time').checked,
                admin_email: 'admin@contractor-vault.local',
            }),
        });

        console.log('Token response status:', response.status);

        if (!response.ok) {
            let errorMessage = `Server error(${ response.status })`;
            try {
                const errorData = await response.json();
                console.log('Error response:', errorData);
                errorMessage = parseErrorDetail(errorData.detail);
            } catch (e) {
                console.log('Could not parse error response');
            }
            throw new Error(errorMessage);
        }

        const data = await response.json();
        console.log('Token generated:', data);

        const token = data.claim_url.split('/').pop();

        $('access-code').value = token;
        showStatus('share-status', '✅ Access code generated! Send it to your contractor.', 'success');

        // Move to step 3
        $('step2').classList.add('hidden');
        $('step3').classList.remove('hidden');

    } catch (error) {
        console.error('Generate error:', error);
        showStatus('share-status', `❌ ${ error.message || error } `, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Generate Access Code';
    }
};

// Copy button
$('btn-copy').onclick = async () => {
    const code = $('access-code').value;
    await navigator.clipboard.writeText(code);
    $('btn-copy').textContent = '✓ Copied!';
    setTimeout(() => $('btn-copy').textContent = '📋 Copy', 2000);
};

// CLAIM: Activate access
$('btn-activate').onclick = async () => {
    const token = $('claim-code').value.trim();
    if (!token) {
        showStatus('claim-status', '❌ Please enter an access code', 'error');
        return;
    }

    const btn = $('btn-activate');
    btn.disabled = true;
    btn.textContent = '⏳ Activating...';
    showStatus('claim-status', '⏳ Activating access...', 'loading');

    try {
        const response = await chrome.runtime.sendMessage({
            type: 'CLAIM_SESSION',
            token: token,
        });

        if (!response || !response.success) {
            const errorMsg = response?.error || 'Failed to claim';
            throw new Error(typeof errorMsg === 'object' ? JSON.stringify(errorMsg) : errorMsg);
        }

        showStatus('claim-status', `✅ ${ response.data.message || 'Access activated!' } `, 'success');

        setTimeout(() => {
            $('session-site').textContent = response.data.session_name;
            $('session-expires').textContent = new Date(response.data.expires_at).toLocaleString();
            $('btn-open').href = response.data.target_url;
            showSection('active-session');
        }, 1500);

    } catch (error) {
        console.error('Claim error:', error);
        showStatus('claim-status', `❌ ${ error.message || error } `, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '🔓 Activate Access';
    }
};

// Init
init();
