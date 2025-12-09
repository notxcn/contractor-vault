# Contractor Vault - System Architecture

## High-Level Architecture

```mermaid
flowchart TB
    subgraph Users["👥 Users"]
        Admin["🔑 Admin<br/>(Session Owner)"]
        Contractor["👷 Contractor<br/>(Session Consumer)"]
    end

    subgraph Extension["🧩 Chrome Extension"]
        Popup["Popup UI"]
        BG["Background Worker"]
        Cookie["Cookie Manager"]
    end

    subgraph Cloud["☁️ Cloud Infrastructure"]
        subgraph API["FastAPI Backend"]
            Sessions["/api/sessions"]
            Tokens["/api/sessions/generate-token"]
            Claim["/api/sessions/claim/{token}"]
            Audit["/api/audit-log"]
        end
        
        DB[(PostgreSQL)]
        
        subgraph Security["🔒 Security Layer"]
            RateLimit["Rate Limiter<br/>slowapi"]
            CORS["CORS Filter"]
            Encrypt["Fernet Encryption"]
        end
    end

    subgraph Dashboard["📊 Admin Dashboard"]
        NextJS["Next.js App"]
    end

    Admin --> Popup
    Popup --> BG
    BG --> Cookie
    BG -->|Store Session| Sessions
    BG -->|Generate Token| Tokens
    
    Contractor --> Popup
    BG -->|Claim Token| Claim
    
    Sessions --> Security
    Tokens --> Security
    Claim --> Security
    Security --> DB
    
    NextJS --> Sessions
    NextJS --> Audit
```

---

## Data Flow

```mermaid
sequenceDiagram
    participant A as Admin
    participant E as Extension
    participant API as Backend API
    participant DB as Database
    participant C as Contractor

    Note over A,C: Session Sharing Flow
    
    A->>E: Click "Share My Login"
    E->>E: Capture cookies from browser
    E->>API: POST /api/sessions (encrypted cookies)
    API->>DB: Store encrypted session
    API-->>E: session_id
    
    A->>E: Click "Generate Access Code"
    E->>API: POST /api/sessions/generate-token
    API->>DB: Create time-limited token
    API-->>E: access_token
    
    A->>C: Share access code (Slack, email, etc.)
    
    C->>E: Enter access code
    E->>API: POST /api/sessions/claim/{token}
    API->>DB: Validate token, get cookies
    API->>API: Decrypt cookies
    API-->>E: Decrypted cookies
    E->>E: Inject cookies into browser
    
    Note over C: Contractor now logged in!
```

---

## Deployment Architecture

```mermaid
flowchart LR
    subgraph Client["Client Side"]
        Chrome["Chrome Browser"]
        Ext["Extension<br/>(Chrome Web Store)"]
    end

    subgraph Vercel["Vercel"]
        Next["Dashboard<br/>(Next.js)"]
    end

    subgraph Railway["Railway"]
        FastAPI["API Server<br/>(FastAPI)"]
        Postgres[(PostgreSQL)]
    end

    Chrome --> Ext
    Ext -->|HTTPS| FastAPI
    Next -->|HTTPS| FastAPI
    FastAPI --> Postgres
```

---

## Security Model

| Layer | Protection |
|-------|------------|
| **Transport** | HTTPS/TLS encryption |
| **Authentication** | JWT tokens with expiry |
| **Data at Rest** | Fernet symmetric encryption |
| **Rate Limiting** | 5-30 req/min per IP |
| **CORS** | Restricted to extension + dashboard |
| **Audit Trail** | All actions logged immutably |

---

## Component Details

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend API** | FastAPI + SQLAlchemy | Session storage, token management |
| **Database** | PostgreSQL (prod) / SQLite (dev) | Encrypted session storage |
| **Extension** | Chrome Manifest V3 | Cookie capture & injection |
| **Dashboard** | Next.js + Tailwind | Admin monitoring |
| **Rate Limiter** | slowapi | Abuse prevention |
| **Encryption** | Fernet (AES-128-CBC) | Cookie encryption |
