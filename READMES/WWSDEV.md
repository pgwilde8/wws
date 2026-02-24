


PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db

PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "\dt"
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "\d contacts"
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "SELECT * FROM contacts;"
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wewsdev_db -c "\x" -c "SELECT id, name, email, phone, subject, created_at FROM contachost -d wwsdev_db
SELECT * FROM contacts;
\d contacts  -- View table structure
SELECT COUNT(*) FROM contacts;  -- Count total records
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "SELECT COUNT(*) FROM contacts;"ts ORDER BY created_at DESC LIMIT 10;"
PGPASSWORD='Securepass9' psql -U webadmin -h local

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

  psql -U webadmin -h localhost -d wwsdev_db -c "SELECT id, ticket_id, sender, message, created_at FROM support_messages lead_forward_emails BY created_at DESC LIMIT 5;"

  psql -U webadmin -h localhost -d wwsdev_db -c "SELECT id, client_id, email, created_at FROM lead_forward_emails ORDER BY created_at DESC LIMIT 10;"

  \d+ client_onboarding

                 List of relations
 Schema |        Name         | Type  |  Owner   
--------+---------------------+-------+----------
 public | alembic_version     | table | webadmin
 public | chat_messages       | table | webadmin
 public | chat_sessions       | table | webadmin
 public | client_onboarding   | table | webadmin
 public | clients             | table | webadmin
 public | coupon_redemptions  | table | webadmin
 public | coupon_tier_rules   | table | webadmin
 public | coupons             | table | webadmin
 public | credentials         | table | webadmin
 public | domains             | table | webadmin
 public | invoices            | table | webadmin
 public | lead_forward_emails | table | webadmin
 public | milestones          | table | webadmin
 public | orders              | table | webadmin
 public | plan_events         | table | webadmin
 public | portfolio_files     | table | webadmin
 public | product_prices      | table | webadmin
 public | products            | table | webadmin
 public | projects            | table | webadmin
 public | quiz_submissions    | table | webadmin
 public | rentals             | table | webadmin
 public | service_prices      | table | webadmin
 public | services            | table | webadmin
 public | support_calls       | table | webadmin
 public | support_messages    | table | webadmin
 public | support_tickets     | table | webadmin
 public | testimonials        | table | webadmin
 public | users               | table | webadmin
 public | webhook_events      | table | webadmin
(29 rows)

(venv) root@wws-multi-vm:/srv/projects/wws# psql -U webadmin -h localhost -d wwsdev_db -c "SELECT id, client_id, email, created_at FROM lead_forward_emails ORDER BY created_at DESC LIMIT 10;"
Password for user webadmin: 
 id | client_id |          email           |          created_at           
----+-----------+--------------------------+-------------------------------
  6 |         8 | yyu@webwisesolutions.dev | 2025-12-28 22:53:30.362214+00
  1 |         1 | allstarincome@gmail.com  | 2025-12-27 14:37:29.987666+00
(2 rows)

# Update Jeff Macburnie's testimonial
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "UPDATE testimonials SET website_url = 'https://mountwilsonranch.com' WHERE id = 1;"

# Update Dan Stragapede's testimonial
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "UPDATE testimonials SET website_url = 'https://mobiletintguy.com' WHERE id = 2;"

support ticket:
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "SELECT id, client_id, project_id, subject, status, priority, created_at FROM support_tickets ORDER BY created_at DESC LIMIT 10;"

*: PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db

PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "SELECT id, client_name, client_location FROM testimonials;"

PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "SELECT * FROM TABLE_NAME;"

# See testimonials table
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "SELECT * FROM testimonials;"

# See users table
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "SELECT * FROM users;"

# See contacts table
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "SELECT * FROM contacts;"

# See orders table
PGPASSWORD='Securepass9' psql -U webadmin -h localhost -d wwsdev_db -c "SELECT * FROM orders;"

