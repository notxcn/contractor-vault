# Testing & Verification Guide

## 1. How to Update the Extension
Since we modified `background.js` and `popup.html`, you must reload the extension in Chrome:

1. Open Chrome and navigate to `chrome://extensions`.
2. Ensure **Developer mode** is enabled (toggle in top right).
3. Find **Contractor Vault** in the list.
4. Click the **Refresh** icon (circular arrow) on the card.
   - *Note: If you haven't loaded it yet, click "Load unpacked" and select the `extension` folder.*

## 2. Automated E2E Tests
I have created a script `backend/tests/e2e_acquisition_features.py` that verifies:
- **Secrets**: Create -> Share -> Claim flow.
- **Device Trust**: Fingerprint capturing and trust scoring.
- **SaaS Discovery**: App catalog adding and detection.

### Run the tests:
```bash
cd backend
python tests/e2e_acquisition_features.py
```

## 3. Manual Verification Steps
### Secrets
1. Go to Dashboard -> **Secrets** tab.
2. Click "New Secret", add an API Key.
3. Click "Share", set duration to 1 hour.
4. Copy the link/token.
5. In Extension, click "I Have an Access Code" and paste the token.
6. Verify access is granted.

### Device Trust
1. After the step above, go to Dashboard -> **Devices**.
2. You should see your current browser listed.
3. Specifics: Check that "Trust Score" is visible.
