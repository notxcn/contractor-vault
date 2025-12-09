# Contractor Vault

Secure session sharing for contractors - bypass 2FA safely.

## Quick Start (Development)

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

## Chrome Extension

Load the `extension/` folder in Chrome:
1. Go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked"
4. Select the `extension/` folder

## Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template)

Or manually:
```bash
cd backend
railway login
railway init
railway up
```

Then update `extension/background.js` with your Railway URL.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `FERNET_KEY` | Encryption key (auto-generated if not set) |
| `JWT_SECRET` | JWT signing secret |
| `DATABASE_URL` | PostgreSQL URL (optional, uses SQLite by default) |
| `DEBUG` | Set to `false` for production |

## License

MIT
