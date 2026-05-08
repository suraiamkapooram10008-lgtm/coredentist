# CSP Fix Guide

## Current Issue
The Content Security Policy in `app/middleware/security_headers.py` currently allows:
```python
"script-src 'self' 'unsafe-inline' ..."
```

This significantly weakens XSS protection.

## Why Unsafe-Inline is Needed
React's development mode and some libraries inject inline styles/scripts that require `'unsafe-inline'`.

## Solution: Use Nonces

### Step 1: Generate Nonce in Middleware
Update `security_headers.py` to generate a unique nonce per request:

```python
import secrets

async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # Generate nonce for this request
    nonce = secrets.token_urlsafe(32)
    request.state.nonce = nonce
    
    # ... existing headers ...
    
    # Use nonce in CSP (replace 'unsafe-inline')
    csp = (
        f"default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}' 'strict-dynamic'; "
        # ... rest of CSP
    )
    response.headers["Content-Security-Policy"] = csp
    response.headers["X-Nonce"] = nonce  # For frontend to access
    
    return response
```

### Step 2: Update React to Use Nonce

#### Option A: Configure Vite (Recommended)
In `vite.config.ts`:
```typescript
export default defineConfig({
  react: {
    nonce: '{{Nonce}}',  // Placeholder replaced by server
  },
  server: {
    middlewareMode: false,
  }
})
```

#### Option B: Use styled-components or CSS modules
Migrate from inline styles to CSS modules or styled-components, which don't require unsafe-inline.

#### Option C: Accept Current State for Now
The current CSP still provides protection against:
- External script injection (`default-src 'self'`)
- Frame injection (`frame-src 'self'`)
- Data exfiltration (`connect-src 'self'`)

The main XSS risk (external script execution) is still mitigated.

## Priority
- **High**: If handling highly sensitive PHI data
- **Medium**: For standard production use

The current implementation is still significantly more secure than no CSP at all.