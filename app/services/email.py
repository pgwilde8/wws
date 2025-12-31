"""Email service for sending contact form notifications."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Any
from contextlib import contextmanager

from fastapi.templating import Jinja2Templates

from app.core.config import settings
# These models may not exist in all deployments; fall back to Any to avoid import errors
try:
    from app.db.models.contact import Contact
except Exception:  # pragma: no cover
    Contact = Any  # type: ignore
try:
    from app.db.models.call_booking import CallBooking
except Exception:  # pragma: no cover
    CallBooking = Any  # type: ignore

# Initialize Jinja2 templates for emails
templates = Jinja2Templates(directory="app/templates")


@contextmanager
def get_smtp_server():
    """Context manager for SMTP server connection that handles both SSL (465) and STARTTLS (587)."""
    if settings.SMTP_PORT == 465:
        # Port 465 requires SSL from the start
        server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
    else:
        # Port 587 uses STARTTLS
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30)
        server.starttls()
    
    try:
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        yield server
    finally:
        try:
            server.quit()
        except:
            server.close()


async def send_contact_email(contact: Contact) -> bool:
    """Send email notification for contact form submission."""
    
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("SMTP credentials not configured, skipping email")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = settings.CONTACT_EMAIL
        msg["Subject"] = f"New Contact Form Submission: {contact.subject or 'No Subject'}"
        
        # Create email body
        body = f"""
New contact form submission received:

Name: {contact.name}
Email: {contact.email}
Phone: {contact.phone or 'Not provided'}
Subject: {contact.subject or 'Not provided'}

Message:
{contact.message}

---
Submitted at: {contact.created_at}
IP Address: {contact.ip_address or 'Not available'}
"""
        
        msg.attach(MIMEText(body, "plain"))
        
        # Send email
        with get_smtp_server() as server:
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        raise


async def send_auto_reply(contact: Contact) -> bool:
    """Send automatic reply to contact form submitter."""
    
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        return False
    
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = contact.email
        msg["Subject"] = "Thank you for contacting WebWise Solutions"
        
        body = f"""
Dear {contact.name},

Thank you for contacting WebWise Solutions. We have received your message and will get back to you as soon as possible.

Best regards,
WebWise Solutions Team
"""
        
        msg.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"Error sending auto-reply: {e}")
        return False


async def send_call_booking_email(call_booking: CallBooking) -> bool:
    """Send email notification for call booking request."""
    
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("SMTP credentials not configured, skipping email")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = settings.CONTACT_EMAIL
        msg["Subject"] = f"New Call Booking Request - {call_booking.name}"
        
        # Create email body
        body = f"""
New call booking request received:

Name: {call_booking.name}
Email: {call_booking.email}
Phone: {call_booking.phone}
Preferred Date: {call_booking.preferred_date}
Preferred Time: {call_booking.preferred_time}
Timezone: {call_booking.timezone or 'Not specified'}
"""
        if call_booking.message:
            body += f"\nMessage:\n{call_booking.message}\n"
        
        body += f"\n---\nSubmitted at: {call_booking.created_at}"
        
        msg.attach(MIMEText(body, "plain"))
        
        # Send email
        with get_smtp_server() as server:
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"Error sending call booking email: {e}")
        raise


async def send_call_booking_confirmation(call_booking: CallBooking) -> bool:
    """Send confirmation email to user for their call booking."""
    
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("SMTP credentials not configured, skipping email")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = call_booking.email
        if getattr(settings, "CALL_BOOKED_EMAIL", None):
            msg["Bcc"] = settings.CALL_BOOKED_EMAIL
        msg["Subject"] = "Your Call with WebWise Solutions is Scheduled!"
        
        # Create email body with nice formatting
        body = f"""
Hi {call_booking.name},

Thank you for scheduling a call with WebWise Solutions!

Your call details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 Date: {call_booking.preferred_date}
🕐 Time: {call_booking.preferred_time} {call_booking.timezone or 'EST'}
"""
        if call_booking.message:
            body += f"📝 Topic: {call_booking.message}\n"
        
        body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What's Next:
1. We'll will call you at the scheduled time.
2. Prepare any questions about your project

Looking forward to speaking with you!

If you need to reschedule, just reply to this email or leave a voice mail at: 848-225-7510.

Best regards,
The WebWise Solutions Team

---
WebWise Solutions
Building Automated Businesses That Work
https://webwisesolutions.dev
"""
        
        msg.attach(MIMEText(body, "plain"))
        
        # Send email
        with get_smtp_server() as server:
            server.send_message(msg)
        
        print(f"✅ Confirmation email sent to {call_booking.email}")
        return True
        
    except Exception as e:
        print(f"Error sending call booking confirmation: {e}")
        # Don't raise - this is not critical
        return False


async def send_welcome_email(customer_email: str, customer_name: Optional[str] = None, plan_name: Optional[str] = None, dashboard_link: Optional[str] = None, temp_password: Optional[str] = None) -> bool:
    """Send welcome email to customer after successful purchase."""
    
    try:
        # Immediate logging to confirm function is called
        print(f"=== send_welcome_email() CALLED ===")
        print(f"Recipient: {customer_email}")
        print(f"Name: {customer_name}")
        print(f"Plan: {plan_name}")
        print(f"Dashboard Link: {dashboard_link}")
        
        # Check SMTP configuration
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            print(f"ERROR: SMTP credentials not configured. SMTP_USER: {bool(settings.SMTP_USER)}, SMTP_PASSWORD: {bool(settings.SMTP_PASSWORD)}")
            print(f"SMTP_HOST: {settings.SMTP_HOST}, SMTP_PORT: {settings.SMTP_PORT}")
            return False
        
        # Retry logic for sending email
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(1, max_retries + 1):
            try:
                print(f"[Attempt {attempt}/{max_retries}] Preparing welcome email for {customer_email}")
                
                # Prepare template context
                context = {
                    "customer_name": customer_name,
                    "customer_email": customer_email,
                    "plan_name": plan_name,
                    "dashboard_link": dashboard_link,
                    "temp_password": temp_password
                }
                
                # Render HTML template
                html_template = templates.get_template("emails/welcome.html")
                html_body = html_template.render(context)
                
                # Render plain text template
                text_template = templates.get_template("emails/welcome.txt")
                text_body = text_template.render(context)
                
                # Create email message (multipart/alternative to avoid duplicate render)
                msg = MIMEMultipart("alternative")
                msg["From"] = settings.SMTP_FROM_EMAIL
                msg["To"] = customer_email
                msg["Subject"] = "Welcome to WebWise Solutions - Your Build Has Started!"
                
                # Attach both plain text and HTML versions
                msg.attach(MIMEText(text_body, "plain"))
                msg.attach(MIMEText(html_body, "html"))
                
                # Send email with improved connection handling
                print(f"[Attempt {attempt}] Connecting to SMTP server: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
                
                # Port 465 requires SSL from the start, port 587 uses STARTTLS
                if settings.SMTP_PORT == 465:
                    # Use SMTP_SSL for port 465
                    print(f"[Attempt {attempt}] Using SSL connection (port 465)...")
                    server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=60)
                else:
                    # Use regular SMTP with STARTTLS for port 587
                    print(f"[Attempt {attempt}] Using STARTTLS connection (port {settings.SMTP_PORT})...")
                    server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=60)
                
                try:
                    # Enable debug output only on first attempt
                    if attempt == 1:
                        server.set_debuglevel(1)
                    
                    # Only use starttls for non-SSL ports (587)
                    if settings.SMTP_PORT != 465:
                        print(f"[Attempt {attempt}] Starting TLS...")
                        server.starttls()
                    
                    print(f"[Attempt {attempt}] Logging in as {settings.SMTP_USER}...")
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    
                    print(f"[Attempt {attempt}] Sending email message...")
                    server.send_message(msg)
                    
                    print(f"✓ Welcome email sent successfully to {customer_email} (attempt {attempt})")
                    return True
                    
                finally:
                    # Always close the connection properly
                    try:
                        server.quit()
                    except:
                        server.close()
            
            except smtplib.SMTPAuthenticationError as e:
                print(f"ERROR: SMTP Authentication failed (attempt {attempt}): {e}")
                print(f"Check SMTP_USER and SMTP_PASSWORD in .env file")
                if attempt == max_retries:
                    return False
                import time
                time.sleep(retry_delay)
                
            except (smtplib.SMTPException, ConnectionError, OSError) as e:
                print(f"ERROR: SMTP connection error (attempt {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    print(f"Retrying in {retry_delay} seconds...")
                    import time
                    time.sleep(retry_delay)
                else:
                    print(f"Failed to send email after {max_retries} attempts")
                    return False
                    
            except Exception as e:
                print(f"ERROR: Unexpected error sending welcome email to {customer_email} (attempt {attempt}): {e}")
                import traceback
                traceback.print_exc()
                if attempt == max_retries:
                    return False
                import time
                time.sleep(retry_delay)
        
        return False
        
    except Exception as e:
        # Catch any top-level errors (e.g., import errors, template errors, etc.)
        print(f"CRITICAL ERROR in send_welcome_email(): {e}")
        import traceback
        traceback.print_exc()
        return False


async def send_idea_submission_email(contact: Contact, idea_data) -> bool:
    """Send email notification for project idea submission from start-your-project page."""
    
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("SMTP credentials not configured, skipping email")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = settings.VISION_EMAIL
        msg["Subject"] = f"New Project Idea Submission: {idea_data.project_type}"
        
        # Create email body with formatted details
        body = f"""
🚀 NEW PROJECT IDEA SUBMISSION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONTACT INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Name: {contact.name}
Email: {contact.email}
Phone: {contact.phone or 'Not provided'}

PROJECT DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project Type: {idea_data.project_type}
Budget Range: {idea_data.budget or 'Not specified'}
Timeline: {idea_data.timeline or 'Not specified'}

IDEA DESCRIPTION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{idea_data.idea_description}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Submitted: {contact.created_at}
IP Address: {contact.ip_address or 'Not available'}
Source: /start-your-project page

🎯 ACTION REQUIRED: Respond within 24 hours as promised!
"""
        
        msg.attach(MIMEText(body, "plain"))
        
        # Send email
        with get_smtp_server() as server:
            server.send_message(msg)
        
        print(f"✅ Idea submission email sent successfully to {settings.VISION_EMAIL}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending idea submission email: {e}")
        import traceback
        traceback.print_exc()
        raise

