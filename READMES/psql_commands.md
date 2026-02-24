# PostgreSQL Commands for users and client_onboarding Tables



PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db


## Describe Table Structure

### Users Table
```sql
-- Describe the users table structure
\d users

-- Or get detailed column information
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;
```

### Client Onboarding Table
```sql
-- Describe the client_onboarding table structure
\d client_onboarding

-- Or get detailed column information
SELECT 
    column_name, 
    data_type, 
    is_nullable, 
    column_default
FROM information_schema.columns 
WHERE table_name = 'client_onboarding' 
ORDER BY ordinal_position;
```

## Query Users Table

```sql
-- View all 
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db
SELECT id, email, role, created_at FROM users;


-- View specific user by email
SELECT id, email, role, created_at FROM users WHERE email = 'user@example.com';

-- View specific user by ID
SELECT id, email, role, created_at FROM users WHERE id = 1;

-- Count total users
SELECT COUNT(*) FROM users;

-- Count users by role
SELECT role, COUNT(*) FROM users GROUP BY role;
```

## Query Client Onboarding Table

```sql
-- View all onboarding records
SELECT 
    client_id,
    full_name,
    business_name,
    industry,
    domain_name,
    lead_forward_email,
    wants_payments,
    wants_sms,
    uses_cloudflare,
    created_at
FROM client_onboarding;

-- View complete onboarding record for a specific client
SELECT * FROM client_onboarding WHERE client_id = 1;

-- View onboarding records with user email (join)
SELECT 
    u.email,
    co.full_name,
    co.business_name,
    co.industry,
    co.domain_name,
    co.lead_forward_email,
    co.created_at
FROM client_onboarding co
JOIN users u ON co.client_id = u.id
ORDER BY co.created_at DESC;

-- View clients who want payments enabled
SELECT 
    u.email,
    co.business_name,
    co.domain_name
FROM client_onboarding co
JOIN users u ON co.client_id = u.id
WHERE co.wants_payments = true;

-- View clients who want SMS enabled
SELECT 
    u.email,
    co.business_name,
    co.domain_name,
    co.calling_direction
FROM client_onboarding co
JOIN users u ON co.client_id = u.id
WHERE co.wants_sms = true;

-- View clients using Cloudflare
SELECT 
    u.email,
    co.business_name,
    co.domain_name,
    co.cloudflare_email
FROM client_onboarding co
JOIN users u ON co.client_id = u.id
WHERE co.uses_cloudflare = true;
```

## Combined Queries

```sql
-- View users with their onboarding status
SELECT 
    u.id,
    u.email,
    u.role,
    u.created_at as user_created_at,
    CASE 
        WHEN co.client_id IS NOT NULL THEN 'Onboarded'
        ELSE 'Not Onboarded'
    END as onboarding_status,
    co.business_name,
    co.domain_name,
    co.created_at as onboarding_created_at
FROM users u
LEFT JOIN client_onboarding co ON u.id = co.client_id
ORDER BY u.created_at DESC;

-- View recent onboarding submissions
SELECT 
    u.email,
    co.full_name,
    co.business_name,
    co.industry,
    co.domain_name,
    co.lead_forward_email,
    co.wants_payments,
    co.wants_sms,
    co.uses_cloudflare,
    co.created_at
FROM client_onboarding co
JOIN users u ON co.client_id = u.id
ORDER BY co.created_at DESC
LIMIT 10;
```

## Useful Maintenance Queries

```sql
-- Find users without onboarding records
SELECT u.id, u.email, u.created_at
FROM users u
LEFT JOIN client_onboarding co ON u.id = co.client_id
WHERE co.client_id IS NULL;

-- Count onboarding records by date
SELECT 
    DATE(created_at) as date,
    COUNT(*) as count
FROM client_onboarding
GROUP BY DATE(created_at)
ORDER BY date DESC;

-- View onboarding records missing required fields
SELECT 
    client_id,
    business_name,
    domain_name,
    CASE 
        WHEN domain_name IS NULL OR domain_name = '' THEN 'Missing domain'
        WHEN lead_forward_email IS NULL OR lead_forward_email = '' THEN 'Missing email'
        ELSE 'OK'
    END as status
FROM client_onboarding;
```

orders:
SELECT 
    id,
    plan,
    buyer_email,
    status,
    welcome_sent,
    stripe_session_id,
    stripe_payment_intent_id,
    created_at
FROM orders
ORDER BY created_at DESC;

