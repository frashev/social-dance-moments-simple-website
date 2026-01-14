# Setup DNS for social-dance.org with Cloudflare Tunnel

## Current Status:
✅ Tunnel is running
✅ https://www.social-dance.org works
❌ www.social-dance.org (HTTP) - doesn't work
❌ social-dance.org (both HTTP & HTTPS) - doesn't work
❌ https://social-dance.org (HTTPS root) - doesn't work

## The Fix: TWO Things Needed

### Step 1: Add ROOT DOMAIN (@) CNAME Record
Go to **Cloudflare Dashboard > DNS > Records** and add:

| Name | Type | Content | Proxied |
|------|------|---------|---------|
| `@` | CNAME | `f341793d-9d49-4118-84b3-3d4fc1ae6571.cfargotunnel.com` | ✅ Yes |

This makes `social-dance.org` (root domain) work.

### Step 2: Enable SSL/TLS Auto Redirect
1. Go to **Cloudflare Dashboard**
2. Select **social-dance.org** domain
3. Go to **SSL/TLS > Edge Certificates**
4. Find **"Always Use HTTPS"** toggle
5. Turn it **ON** (blue)

This redirects all HTTP traffic to HTTPS automatically.

### Result After Setup:
After 5-10 minutes, ALL of these will work:
- ✅ `social-dance.org` → redirects to `https://social-dance.org`
- ✅ `www.social-dance.org` → redirects to `https://www.social-dance.org`
- ✅ `https://social-dance.org`
- ✅ `https://www.social-dance.org`

## Your Configuration:
- **Tunnel ID:** `f341793d-9d49-4118-84b3-3d4fc1ae6571`
- **Domain:** `social-dance.org`
- **Local Service:** `http://localhost:8000`

## DNS Records You Should Have:
```
@ (root)    CNAME    f341793d-9d49-4118-84b3-3d4fc1ae6571.cfargotunnel.com    Proxied ✅
www         CNAME    f341793d-9d49-4118-84b3-3d4fc1ae6571.cfargotunnel.com    Proxied ✅
```

## SSL/TLS Settings:
```
Always Use HTTPS: ON (Enabled) ✅
```

---

**Summary:** Add `@` record + enable "Always Use HTTPS" and all URL variants will work! 🎯

