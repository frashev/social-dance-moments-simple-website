# Troubleshooting: social-dance.org Not Reachable

## ✅ Things That Should Already Be Done:

1. **Cloudflare Tunnel Running**
   - Terminal shows: "Registered tunnel connection"
   - Tunnel ID: `f341793d-9d49-4118-84b3-3d4fc1ae6571`
   - ✅ Yes? Move to next step

2. **FastAPI Running on Port 8000**
   - Should see: Server running on `http://localhost:8000`
   - ✅ Yes? Move to next step

## ❌ What's Still Missing (Most Likely):

### Missing Step 1: Root Domain (@) CNAME Record
Check your **Cloudflare DNS Records** - you should have:
```
Name: @
Type: CNAME
Content: f341793d-9d49-4118-84b3-3d4fc1ae6571.cfargotunnel.com
Proxied: Yes (orange cloud)
```

**👉 IF YOU DON'T HAVE THIS, ADD IT NOW!**

### Missing Step 2: Always Use HTTPS
Check **Cloudflare SSL/TLS > Edge Certificates**:
```
"Always Use HTTPS" toggle: ON (blue)
```

**👉 IF THIS IS OFF, TURN IT ON NOW!**

## How to Add the @ Record (Step-by-Step):

1. Open https://dash.cloudflare.com/
2. Click on **social-dance.org** domain
3. Go to **DNS > Records**
4. Click **+ Add record**
5. Fill in:
   - **Name:** `@`
   - **Type:** CNAME (dropdown)
   - **Content:** `f341793d-9d49-4118-84b3-3d4fc1ae6571.cfargotunnel.com`
   - **Proxied:** Toggle to **ON** (orange cloud)
   - **TTL:** Auto
6. Click **Save**
7. **WAIT 5-10 MINUTES** for DNS to propagate

## After Adding @ Record:
Try these in order:
1. `https://social-dance.org` (should work)
2. `https://www.social-dance.org` (should work)
3. `social-dance.org` (should redirect to https)
4. `www.social-dance.org` (should redirect to https)

## Still Not Working? Check:

- ❓ Did you add the `@` CNAME record? (Not just `www`)
- ❓ Is it set to **Proxied** (orange cloud)?
- ❓ Did you wait at least 5 minutes after saving?
- ❓ Try clearing browser cache or use incognito window
- ❓ Try `https://` first (always use https)

---

**Most Common Mistake:** People add only the `www` record and forget the `@` (root domain) record!

**The `@` record is CRITICAL for `social-dance.org` to work!**

