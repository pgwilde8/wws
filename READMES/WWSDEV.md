PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "\dt"
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "\d contacts"
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "SELECT * FROM contacts;"
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wewsdev_db -c "\x" -c "SELECT id, name, email, phone, subject, created_at FROM contacts ORDER BY created_at DESC LIMIT 10;"
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db
SELECT * FROM contacts;
\d contacts  -- View table structure
SELECT COUNT(*) FROM contacts;  -- Count total records
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "SELECT COUNT(*) FROM contacts;"

PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d  wwsdev_db -c "\dt"

PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "SELECT * FROM contacts;"

PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "SELECT id, name, build_package_id FROM client_projects ORDER BY id DESC LIMIT 10;"

PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "SELECT id, name, build_package_id FROM client_projects WHERE name ILIKE '%Stacy Mills%';"

PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "SELECT id, name FROM build_packages WHERE name ILIKE '%Scale%';"

PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "UPDATE client_projects SET build_package_id = <SCALE_PACKAGE_ID> WHERE id = <PROJECT_ID>;"

PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "UPDATE client_projects SET build_package_id = <SCALE_PACKAGE_ID> WHERE id = <PROJECT_ID>;"

echo "CREATE TABLE IF NOT EXISTS lead_forward_emails (
  id SERIAL PRIMARY KEY,
  client_id INTEGER,
  email TEXT

  or

  CREATE TABLE IF NOT EXISTS lead_forward_emails (
  id SERIAL PRIMARY KEY,
  client_id INTEGER,
  email TEXT UNIQUE NOT NULL,
  created_at TIMESTAMPTZ

  support:
  psql -U webadmin -h localhost -d wwsdev_db -c "SELECT id, client_id, project_id, subject, status, priority, created_at FROM support_tickets ORDER BY created_at DESC LIMIT 5;"

  psql -U webadmin -h localhost -d wwsdev_db -c "SELECT id, ticket_id, sender, message, created_at FROM support_messages ORDER BY created_at DESC LIMIT 5;"

               List of relations
 Schema |        Name        | Type  |  Owner   
--------+--------------------+-------+----------
 public | chat_messages      | table | webadmin
 public | chat_sessions      | table | webadmin
 public | clients            | table | webadmin
 public | coupon_redemptions | table | webadmin
 public | coupon_tier_rules  | table | webadmin
 public | coupons            | table | webadmin
 public | credentials        | table | webadmin
 public | domains            | table | webadmin
 public | invoices           | table | webadmin
 public | milestones         | table | webadmin
 public | orders             | table | webadmin
 public | plan_events        | table | webadmin
 public | product_prices     | table | webadmin
 public | products           | table | webadmin
 public | projects           | table | webadmin
 public | quiz_submissions   | table | webadmin
 public | rentals            | table | webadmin
 public | service_prices     | table | webadmin
 public | services           | table | webadmin
 public | support_calls      | table | webadmin
 public | support_messages   | table | webadmin
 public | support_tickets    | table | webadmin
 public | testimonials       | table | webadmin
 public | users              | table | webadmin
 public | webhook_events     | table | webadmin
(25 rows)