# Security & Data Protection Guidelines

## 🔒 Secrets Management

### Never Commit Secrets
- `.env` file is in `.gitignore` — keep it that way
- API keys, tokens, and passwords should ONLY exist locally
- GitHub will scan for secrets automatically via push protection

### API Key Setup
1. Create `.env` in project root with your keys:
   ```env
   CLAUDE_API_KEY=sk-ant-api03-xxxxx
   GROQ_API_KEY=gsk_xxxxx
   GEMINI_API_KEY=AIza_xxxxx
   ```

2. Never share these keys in:
   - Code commits
   - Issue descriptions
   - Pull requests
   - Chat/messages

3. If a key is accidentally exposed:
   - Revoke it immediately from the provider's dashboard
   - Rotate (generate a new one)
   - Update your `.env` locally
   - Notify the team

### Checking What's in Git
```bash
# See what files are tracked
git ls-files

# Check for secrets with git-grep
git grep -i "api.?key" HEAD

# Audit recent commits
git log -p --all -S "GROQ_API_KEY" 
```

---

## 📊 Dataset Privacy

### BIDS Dataset (ds004196)
- Contains **real EEG data from human subjects**
- **NOT committed to GitHub** — too large (~50GB+) and needs privacy controls
- Downloaded on-demand via `openneuro-py` or manually

### Handling De-Identified Data
- This dataset has personal data removed (no names, dates, etc.)
- Still treat as protected information
- Don't share copies without authorization
- Follow institutional IRB (Institutional Review Board) guidelines

### Dataset Locations
```bash
# Local valid paths (checked in order):
- ./ds004196/                    ← preferred
- ./brain_data/ds004196/         ← alternative
- Brain_data/                    ← loose layout

# Automatically ignored in git:
ds004196/
brain_data/
```

---

## 🛡️ CORS Security

### Current Configuration
```python
# backend/main.py
CORSMiddleware(
    allow_origins=[
        "http://localhost:5173",      # Vite dev
        "http://127.0.0.1:5173"       # Alt localhost
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Production Deployment
Before deploying to production, update CORS:
```python
# ❌ DO NOT USE IN PRODUCTION
allow_origins=["*"]  # Unsafe!

# ✅ CORRECT PRODUCTION CONFIG
allow_origins=[
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

---

## 🔍 Streaming & Buffering

### SSE (Server-Sent Events)  
The `/api/load` endpoint streams progress updates without buffering:
```python
headers={
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",      # Don't buffer
    "Connection": "keep-alive",       # Keep connection open
}
```

### Streaming Chat
The `/api/chat` endpoint streams character-by-character responses:
```python
headers={
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",      # Disables gzip/buffer
    "Content-Type": "text/plain",
}
```

Frontend properly handles streaming with TextDecoder:
```javascript
const decoder = new TextDecoder('utf-8');
while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value, { stream: true });
    // Append chunk to message
}
```

---

## 🚨 Common Pitfalls

### ❌ Committed Secrets Found?
**Do NOT just delete the file!** It remains in git history.

**Fix it:**
```bash
# Option 1: Using git-filter-repo (recommended)
pip install git-filter-repo
git filter-repo --invert-paths --path .env

# Option 2: Using git rebase (risky, rewrites history)
# BFG is another option: https://rtyley.github.io/bfg-repo-cleaner/
```

### ❌ API Key Exposed in Code?
```javascript
// ❌ WRONG - Key in source code
const API_KEY = "sk-ant-api03-xxx";

// ✅ CORRECT - Key in environment
const API_KEY = process.env.CLAUDE_API_KEY;
```

### ❌ Large Dataset in `.gitignore` But Still Tracked?
```bash
# Remove from tracking (keep local copy)
git rm --cached ds004196/

# Ensure .gitignore has the entry
echo "ds004196/" >> .gitignore

# Commit
git add .gitignore
git commit -m "chore: ignore large dataset"
```

---

## ✅ Security Checklist

- [ ] `.env` file is in `.gitignore`
- [ ] No API keys appear in any committed files
- [ ] `ds004196/` is in `.gitignore`
- [ ] CORS config is specific (not `*`) for production
- [ ] No personal data is logged to stdout
- [ ] Streaming endpoints have no-buffer headers
- [ ] All dependencies are from trusted sources
- [ ] No hardcoded secrets in environment variables
- [ ] Team members have separate `.env` files
- [ ] Sensitive files are documented in SECURITY.md (this file!)

---

## 📚 Resources

- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [BIDS Format Specification](https://bids-standard.github.io/)
- [OpenNeuro Dataset Registry](https://openneuro.org/)
- [FastAPI CORS Docs](https://fastapi.tiangolo.com/tutorial/cors/)

---

**Last Updated:** April 3, 2026  
**Maintainer:** Atman Team
