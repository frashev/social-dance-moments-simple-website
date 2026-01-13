"""
Email notification service for workshop registrations and reminders.
Uses SMTP or SendGrid for sending emails.
"""

import os
from typing import Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@danceapp.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")

# Email templates
REGISTRATION_CONFIRMATION = """
Hello {username},

You have successfully registered for the {style} workshop!

📍 Location: {location}, {city}
📅 Date: {date}
🕐 Time: {time}
👨‍🏫 Instructor: {instructor}

We look forward to seeing you there!

---
Dance Song Recommender
"""

WORKSHOP_REMINDER = """
Hello {username},

This is a reminder that your {style} workshop is coming up tomorrow!

📍 Location: {location}, {city}
📅 Date: {date}
🕐 Time: {time}

See you there! 💃

---
Dance Song Recommender
"""


def send_email(recipient_email: str, subject: str, body: str) -> bool:
    """
    Send email using SMTP.
    Returns True if successful, False otherwise.
    """
    if not SENDER_PASSWORD:
        logger.warning("SENDER_PASSWORD not configured. Email sending disabled.")
        return False

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        # Create message
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        logger.info(f"Email sent to {recipient_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False


def send_registration_confirmation(username: str, email: str, workshop: dict) -> bool:
    """Send confirmation email after workshop registration."""
    body = REGISTRATION_CONFIRMATION.format(
        username=username,
        style=workshop.get("style", "Dance").upper(),
        location=workshop.get("location", "TBD"),
        city=workshop.get("city", "TBD"),
        date=workshop.get("date", "TBD"),
        time=workshop.get("time", "TBD"),
        instructor=workshop.get("instructor_name", "TBA")
    )

    subject = f"Registration Confirmed: {workshop.get('style', 'Dance')} Workshop"
    return send_email(email, subject, body)


def send_workshop_reminder(username: str, email: str, workshop: dict) -> bool:
    """Send reminder email 24 hours before workshop."""
    body = WORKSHOP_REMINDER.format(
        username=username,
        style=workshop.get("style", "Dance").upper(),
        location=workshop.get("location", "TBD"),
        city=workshop.get("city", "TBD"),
        date=workshop.get("date", "TBD"),
        time=workshop.get("time", "TBD")
    )

    subject = f"Reminder: {workshop.get('style', 'Dance')} Workshop Tomorrow!"
    return send_email(email, subject, body)


def schedule_reminders():
    """
    Schedule reminder emails for workshops happening tomorrow.
    This should be called by APScheduler every day at 9 AM.
    """
    from .database import get_db

    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    with get_db() as conn:
        c = conn.cursor()

        # Get all registrations for tomorrow's workshops
        c.execute("""
            SELECT u.username, u.email, w.*
            FROM registrations r
            JOIN users u ON r.user_id = u.id
            JOIN workshops w ON r.workshop_id = w.id
            WHERE w.date = ? AND r.notify_enabled = 1
        """, (tomorrow,))

        registrations = c.fetchall()

    sent = 0
    for reg in registrations:
        workshop = {
            "style": reg["style"],
            "location": reg["location"],
            "city": reg["city"],
            "date": reg["date"],
            "time": reg["time"]
        }

        if send_workshop_reminder(reg["username"], reg["email"], workshop):
            sent += 1

    logger.info(f"Sent {sent} reminder emails for tomorrow's workshops")
    return sent

