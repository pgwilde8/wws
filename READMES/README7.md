What happens when a user buys a plan

They pay in Stripe using a price ID like your Starter/Growth/Scale tiers.

Your backend creates a purchase record in DB (linked to the Stripe price ID).

The system emails the user login credentials + dashboard link (you generate this email in your code, not Gmail API).

The user logs in and lands on /dashboard.

What the client sees in their dashboard

The UI includes:

Plan they purchased (name + price tier)

Current status → starts as "onboarding" or "onboarding" rendered as "Onboarding"

Credential input forms for:

OpenAI API Key

Twilio / SMS credentials (Twilio or similar provider)

SMTP email settings (either text inputs or direct file upload, but text is fine)

Domain name + email provider link section (Namecheap, Cloudflare, etc.)

Email upload or input field that updates the SMTP/SMTP env variable

This becomes SMTP_USER_EMAIL in your .env

This is the email your system will send from (SMTP auth)

A helper link section pointing to Namecheap so they can buy:

a domain

and a business email

Optional upload areas for:

business logo

site images

product/service descriptions

extra notes for onboarding

How this connects to admin (your side)

You also built this:

Admin UI exists at:

/admin/projects

/admin/clients

/admin/webhooks

/admin/support

The admin dashboard has a client card for each user

You manually update the client’s status in admin:

Initially it may show "onboarding" or "onboarding"

Once the client gives you keys and domain/email info, you edit their user record manually

Change status to something like:

"active"

"building"

"deployed"

"supporting"

etc.

This manual update route you created earlier looks like:

@admin_router.patch("/clients/{client_id}/status")
async def update_client_status(client_id: int, status: str, session=Depends(get_session)):
    client = await session.get(Client, client_id)
    client.status = status
    await session.commit()


So the admin has full control over client status.

What you still plan to enhance next

You want to add:

For clients

see which plan they bought

view status as "Onboarding" at first

submit API keys & SMTP email

upload branding assets

buy domain/email from Namecheap (via dashboard link)

no code access required

For admin

view all clients + status

manually update a client’s status

assign them to projects

see purchases + price tier

access chat history & support tickets

deploy & support sites

NOT automatically change client creds (admin does manual update only)

Future additions

Purchases table linked to client dashboard UI

Admin filtering & sorting for projects/clients

More automation wiring for onboarding, support, and deployments

A product/service catalog table later if you want dynamic Stripe products users can create

Optional Stripe Connect later, but not required now

Summary of your data model (already built)
Table	Purpose
users	login accounts + status + purchased plan
purchases	stores Stripe price ID, plan tier, timestamps
chat_sessions	stores thread ID + session ID
chat_messages	full chat history for each session
webhook_events	Stripe webhook logs
support_tickets (next)	support history tied to client
What’s next for you now

The most useful next stage is to build:

/admin/clients UI enhancements
/support_tickets table + API
/stripe checkout + success pages
/client purchases UI card