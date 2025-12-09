# Contractor Vault Backend

SOC2-compliant Transient Identity Manager API.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Generate Fernet key
python -c "from cryptography.fernet import Fernet; print(f'FERNET_KEY={Fernet.generate_key().decode()}')"

# Generate JWT secret
# On Windows PowerShell:
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Maximum 256 }) -as [byte[]])

# Or using Python:
python -c "import secrets; print(f'JWT_SECRET={secrets.token_hex(32)}')"
```

### 3. Run the Server

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or directly
python -m app.main
```

### 4. Access API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## API Endpoints

### Access Control
- `POST /api/access/generate-access-token` - Create time-bombed token
- `POST /api/access/claim/{token}` - Claim token and get credentials
- `POST /api/access/revoke/{token_id}` - Revoke specific token
- `POST /api/access/revoke-all/{contractor_email}` - Kill switch

### Credentials
- `POST /api/credentials/` - Create credential
- `GET /api/credentials/` - List credentials
- `GET /api/credentials/{id}` - Get credential
- `PATCH /api/credentials/{id}` - Update credential
- `DELETE /api/credentials/{id}` - Delete credential

### Audit
- `GET /api/audit/logs` - Query audit logs
- `GET /api/audit/export-logs` - Export CSV
- `GET /api/audit/logs/{id}` - Get specific log

## SOC2 Compliance Features

- ✅ All sensitive data encrypted at rest (Fernet)
- ✅ Immutable audit log with UUID keys
- ✅ IP address tracking for forensics
- ✅ Time-limited access tokens
- ✅ Kill switch for emergency revocation
- ✅ No plaintext passwords in logs
- ✅ Environment-based key management
