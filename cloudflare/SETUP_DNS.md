# Setup DNS for social-dance.org with Cloudflare Tunnel

## What's happening:
✅ Tunnel is running successfully
❌ DNS routing is not configured yet

## Error 1016 means:
Cloudflare can't find the DNS record for `social-dance.org`

## How to fix:

### Step 1: Log in to Cloudflare Dashboard
1. Go to https://dash.cloudflare.com/
2. Select your account
3. Select the `social-dance.org` domain

### Step 2: Create DNS Record
1. Go to **DNS** section
2. Click **Add Record**
3. Fill in:
   - **Type:** CNAME
   - **Name:** @ (or social-dance.org)
   - **Target:** `f341793d-9d49-4118-84b3-3d4fc1ae6571.cfargotunnel.com`
   - **Proxy status:** Proxied (orange cloud)
   - **TTL:** Auto

### Step 3: Alternative - Use Cloudflare Web UI
1. In Cloudflare Dashboard, go to your domain
2. Navigate to **DNS > Records**
3. Add CNAME record:
   ```
   Name: social-dance.org
   Type: CNAME
   Content: f341793d-9d49-4118-84b3-3d4fc1ae6571.cfargotunnel.com
   Proxied: Yes
   ```

### Step 4: Verify
After 5-10 minutes, visit https://social-dance.org and you should see your app!

## Your Tunnel ID:
`f341793d-9d49-4118-84b3-3d4fc1ae6571`

## Your Domain:
`social-dance.org`

## Local Service:
`http://localhost:8000`

---

**Note:** The tunnel is already running and working. You just need to add the DNS record to route traffic to it.

