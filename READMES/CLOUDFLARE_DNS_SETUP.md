# Cloudflare DNS Automation Setup Guide

## Overview

This system automatically configures DNS records in Cloudflare when clients submit their domain names through the dashboard. It eliminates manual DNS setup and scales to handle unlimited client domains.

## How It Works

### Client Flow

1. **Client submits domain** via dashboard form (`/client/dashboard`)
2. **Domain saved** to database (`live_domain` field)
3. **Background task triggered** to configure Cloudflare DNS
4. **DNS records created automatically:**
   - A record: `@` → `134.199.242.254` (your server IP)
   - CNAME: `www` → `domain.com`
   - MX records: Email routing to MXRoute
   - SPF record: Email authentication
5. **Client receives email** with nameservers to update at their registrar
6. **Client updates nameservers** at Namecheap/GoDaddy/etc.
7. **Domain goes live** after DNS propagation (24-48 hours)

### Technical Flow

```
Client Dashboard Form
    ↓
PATCH /api/client/projects/{id}
    ↓
update_project() detects new domain
    ↓
Background task: configure_domain_and_notify()
    ↓
CloudflareService.configure_domain_dns()
    ↓
Cloudflare API calls:
  - Create zone (if needed)
  - Create A record
  - Create CNAME record
  - Create MX records
  - Create SPF record
    ↓
Email sent to client with nameservers
    ↓
Activity log updated
```

## Setup Instructions

### Step 1: Create Cloudflare Account API Token

1. **Log into Cloudflare Dashboard**
   - Go to: https://dash.cloudflare.com/

2. **Navigate to API Tokens**
   - Click your profile icon (top right)
   - Go to: **My Profile** → **API Tokens**
   - Or direct link: https://dash.cloudflare.com/profile/api-tokens

3. **Create Account API Token**
   - Click **"Create Token"**
   - Click **"Create Custom Token"**
   - **Token Name:** `WebWise Solutions DNS Management`
   - **Permissions:**
     - **Zone** → **Read, Edit**
     - **DNS** → **Read, Edit**
     - **Account** → **Read** (to list zones)
   - **Account Resources:** Select your account
   - **Zone Resources:** Include all zones (or specific ones)
   - **Optional:** Set expiration date
   - Click **"Continue to summary"**
   - Review and click **"Create Token"**

4. **Copy the Token**
   - ⚠️ **IMPORTANT:** Copy the token immediately - you won't see it again!
   - It looks like: `abc123def456ghi789jkl012mno345pqr678stu901vwx234yz`

### Step 2: Get Your Cloudflare Account ID

1. **In Cloudflare Dashboard**
   - Go to any domain/zone
   - Scroll down to **"API"** section (right sidebar)
   - Copy your **Account ID**
   - It looks like: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

### Step 3: Add to Environment Variables

Add these to your `.env` file:

```bash
# Cloudflare API Configuration
CLOUDFLARE_API_TOKEN=your_token_here
CLOUDFLARE_ACCOUNT_ID=your_account_id_here
```

**Example:**
```bash
CLOUDFLARE_API_TOKEN=abc123def456ghi789jkl012mno345pqr678stu901vwx234yz
CLOUDFLARE_ACCOUNT_ID=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

### Step 4: Install Required Package

The code uses `httpx` for async HTTP requests. Install it if not already installed:

```bash
pip install httpx
```

Or add to `requirements.txt`:
```
httpx>=0.24.0
```

### Step 5: Restart Your Service

After adding environment variables, restart your FastAPI service:

```bash
sudo systemctl restart webwisesolutions
```

## Configuration Details

### Server IP Address

The default server IP is `134.199.242.254` (your DigitalOcean static IP). This is configured in:

- `app/services/cloudflare.py` → `configure_domain_dns()` function
- Can be overridden per domain if needed

### Email Configuration

MX records are automatically configured to use MXRoute:
- Primary MX: `heracles.mxrouting.net` (Priority 10)
- Secondary MX: `heracles-relay.mxrouting.net` (Priority 20)
- SPF record: `v=spf1 include:mxroute.com -all`

### DNS Records Created

For each client domain, the system creates:

1. **A Record** (`@`)
   - Points to: `134.199.242.254`
   - TTL: 3600 seconds

2. **CNAME Record** (`www`)
   - Points to: `domain.com`
   - TTL: 3600 seconds

3. **MX Record** (`@`)
   - Primary: `heracles.mxrouting.net` (Priority 10)
   - Secondary: `heracles-relay.mxrouting.net` (Priority 20)
   - TTL: 3600 seconds

4. **TXT Record** (`@`) - SPF
   - Content: `v=spf1 include:mxroute.com -all`
   - TTL: 3600 seconds

## Code Structure

### Files Created/Modified

1. **`app/services/cloudflare.py`** (NEW)
   - `CloudflareService` class: Main API client
   - `configure_client_domain()`: Convenience function
   - Handles all Cloudflare API interactions

2. **`app/core/config.py`** (MODIFIED)
   - Added `CLOUDFLARE_API_TOKEN` setting
   - Added `CLOUDFLARE_ACCOUNT_ID` setting

3. **`app/api/routes/client.py`** (MODIFIED)
   - Updated `update_project()` to detect domain submissions
   - Added `configure_domain_and_notify()` background task
   - Triggers DNS configuration automatically

4. **`app/templates/client/dashboard.html`** (MODIFIED)
   - Added domain setup form
   - Client can submit domain name
   - Shows Cloudflare setup instructions

## API Reference

### CloudflareService Methods

#### `get_zone(domain: str) -> Optional[Dict]`
Get existing zone information.

#### `create_zone(domain: str) -> Dict`
Create a new zone (add domain to Cloudflare).

#### `get_or_create_zone(domain: str) -> Dict`
Get existing zone or create new one.

#### `create_dns_record(zone_id, record_type, name, content, ttl, priority) -> Dict`
Create a single DNS record.

#### `configure_domain_dns(domain, server_ip, mx_host, mx_priority) -> Dict`
Complete DNS setup for a domain (creates all records).

### Convenience Function

#### `configure_client_domain(domain: str, server_ip: str) -> Dict`
Simple wrapper to configure a client domain.

## Testing

### Test Domain Configuration

You can test the integration manually:

```python
from app.services.cloudflare import configure_client_domain

# Test with a domain
result = await configure_client_domain("test.example.com")
print(result)
# Output: {
#   "zone_id": "...",
#   "zone_name": "test.example.com",
#   "nameservers": ["ns1.cloudflare.com", "ns2.cloudflare.com"],
#   "status": "pending"
# }
```

### Check Activity Logs

After a domain is configured, check the activity log:

```sql
SELECT * FROM activity_logs 
WHERE event = 'dns_configured' 
ORDER BY created_at DESC;
```

## Troubleshooting

### Common Issues

#### 1. "Cloudflare API token is required"
**Solution:** Add `CLOUDFLARE_API_TOKEN` to your `.env` file

#### 2. "Cloudflare account ID is required to create zones"
**Solution:** Add `CLOUDFLARE_ACCOUNT_ID` to your `.env` file

#### 3. "HTTP 401: Unauthorized"
**Solution:** 
- Check that your API token is correct
- Verify token hasn't expired
- Ensure token has correct permissions (Zone: Read/Edit, DNS: Read/Edit)

#### 4. "HTTP 403: Forbidden"
**Solution:**
- Token may not have permission for the account
- Check token permissions in Cloudflare dashboard
- Ensure account ID matches the token's account

#### 5. Domain already exists in Cloudflare
**Solution:** The code handles this automatically - it will use the existing zone

#### 6. DNS records already exist
**Solution:** The code checks for existing records and skips creating duplicates

### Debugging

Enable debug logging:

```python
import logging
logging.getLogger("app.services.cloudflare").setLevel(logging.DEBUG)
```

Check logs:
```bash
sudo journalctl -u webwisesolutions -f
```

## Security Notes

1. **API Token Security:**
   - Never commit tokens to git
   - Store in `.env` file (already in `.gitignore`)
   - Use Account API Tokens (not User API Tokens) for durability
   - Set expiration dates for tokens if desired

2. **Permissions:**
   - Token only needs Zone and DNS permissions
   - Don't grant unnecessary permissions (like Account: Edit)

3. **Error Handling:**
   - API errors are logged but don't crash the application
   - Failed DNS configurations are logged in activity log
   - Client still receives response even if DNS setup fails

## Email Notifications

When DNS is configured, clients receive an email with:

- Domain name
- Cloudflare nameservers (to update at registrar)
- Instructions for updating nameservers
- What DNS records were configured
- Timeline expectations (24-48 hours for propagation)

Email is sent via MXRoute SMTP (configured in `app/services/email.py`).

## Manual DNS Management

If you need to manually manage DNS for a domain:

```python
from app.services.cloudflare import CloudflareService

service = CloudflareService()

# Get zone
zone = await service.get_zone("example.com")
zone_id = zone["id"]

# Create custom record
await service.create_dns_record(
    zone_id=zone_id,
    record_type="A",
    name="subdomain",
    content="1.2.3.4"
)

# List all records
records = await service.list_dns_records(zone_id)
```

## Future Enhancements

Potential improvements:

1. **DKIM Record Creation:** Automatically create DKIM records for email
2. **DMARC Record Creation:** Add DMARC policy records
3. **SSL Certificate Automation:** Auto-provision SSL via Cloudflare
4. **DNS Health Checks:** Monitor DNS propagation status
5. **Retry Logic:** Retry failed DNS configurations
6. **Webhook Integration:** Cloudflare webhooks for zone status updates
7. **Multi-Account Support:** Support multiple Cloudflare accounts

## Support

For issues or questions:
- Check Cloudflare API documentation: https://developers.cloudflare.com/api/
- Review activity logs in database
- Check application logs: `sudo journalctl -u webwisesolutions -f`

## Summary

✅ **Automated DNS setup** - No manual configuration needed  
✅ **Scales infinitely** - Handle 1 or 1000 domains the same way  
✅ **Professional experience** - Clients get instant DNS configuration  
✅ **Error resilient** - Failures don't crash the app  
✅ **Fully logged** - All actions tracked in activity log  
✅ **Email notifications** - Clients automatically notified  

The system is production-ready and will automatically configure DNS for every client domain submission!

WebWise DNS Automations API token summary
This API token will affect the below accounts and zones, along with their respective permissions


Webwises@webwisesolutions.dev's Account - Account Settings:Read
All zones - DNS Settings:Edit, Zone Settings:Read
Client IP Address Filtering

Is in - 134.199.242.254, 129.212.147.207
TTL

Start Date - December 9, 2025
End Date - December 31, 2026

webwises@webwisesolutions.dev
Blue12Stone$

