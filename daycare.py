"""
Daycare Management System - Full Backend Implementation
File: daycare.py
Framework: Flask 3.x, psycopg2, Africa's Talking SDK (SMS), SMTP / Transactional Email, Werkzeug Security
Channels: Dual SMS + Email (Africa's Talking SMS for Instant Alerts + SMTP / API for Rich Email Digests)
"""

import os
import logging
import secrets
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from contextlib import contextmanager
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load local environment configuration
load_dotenv()

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or "sunflower-local-development-only-change-before-production"
if not os.getenv("FLASK_SECRET_KEY"):
    logging.warning("FLASK_SECRET_KEY is not configured; using a development fallback. Set a stable secret in production.")
EAT_TIMEZONE = ZoneInfo("Africa/Nairobi")

def east_africa_time():
    return datetime.now(EAT_TIMEZONE)

app.config.update(
    SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE=os.getenv("SESSION_COOKIE_SAMESITE", "Lax"),
    WTF_CSRF_SSL_STRICT=False,
    WTF_CSRF_USE_SESSIONS=False,
)
csrf = CSRFProtect(app)

INACTIVE_TIMEOUT_SECONDS = 10 * 60

@app.before_request
def expire_inactive_session():
    if 'user' not in session:
        return None

    last_activity = session.get('last_activity')
    now = datetime.now(timezone.utc).timestamp()
    if last_activity is not None:
        try:
            inactive = now - float(last_activity)
        except (TypeError, ValueError):
            inactive = INACTIVE_TIMEOUT_SECONDS + 1
    else:
        inactive = INACTIVE_TIMEOUT_SECONDS + 1

    if inactive >= INACTIVE_TIMEOUT_SECONDS:
        session.clear()
        session['inactive_logout'] = True
        return redirect(url_for('login'))

    session['last_activity'] = now
    return None

@app.after_request
def add_security_headers(response):
    response.headers.setdefault("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.is_secure or request.headers.get("X-Forwarded-Proto", "").split(",")[0].strip() == "https":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response

# Database Configuration & Context Manager
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    if DATABASE_URL:
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "daycare"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        port=os.getenv("DB_PORT", 5434),
        cursor_factory=RealDictCursor
    )

@contextmanager
def get_db_cursor(commit=False):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            yield cur
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

# 1. Africa's Talking SMS Dispatch Gateway
AT_USERNAME = os.getenv("AT_USERNAME", "sandbox")
AT_API_KEY = os.getenv("AT_API_KEY", "")

def dispatch_sms(recipient_phone, message_body, child_id=None, first_name="", last_name=""):
    """
    Dispatches outbound SMS notifications via Africa's Talking
    and audits the record to `message_logs`.
    """
    delivery_status = "Sent"
    at_msg_id = None

    if not recipient_phone:
        return "Skipped (No Phone)"

    if AT_API_KEY and AT_USERNAME:
        try:
            import africastalking
            africastalking.initialize(AT_USERNAME, AT_API_KEY)
            sms = africastalking.SMS
            response = sms.send(message_body, [recipient_phone])
            logging.info("AT response: %s", response)

            recipients = response.get('SMSMessageData', {}).get('Recipients', [])
            if recipients:
                recipient = recipients[0]
                provider_status = recipient.get('status', 'Failed')
                at_msg_id = recipient.get('messageId')

                if str(provider_status).lower() == 'success':
                    delivery_status = 'Sent'
                else:
                    delivery_status = f"Failed ({provider_status})"
                    logging.error("SMS was not delivered to %s: %s", recipient_phone, provider_status)
            else:
                delivery_status = "Failed (No recipient response)"
                logging.error("SMS was not delivered to %s: Africa's Talking returned no recipient response", recipient_phone)
        except Exception:
            logging.exception("SMS send failed for %s", recipient_phone)
            delivery_status = "Failed (SMS send error)"
    else:
        delivery_status = "Delivered (Dev Sim)"

    # Audit in message_logs
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO message_logs 
                (child_id, recipient_phone, first_name, last_name, channel, direction, message_body, delivery_status, at_message_id)
                VALUES (%s, %s, %s, %s, 'SMS', 'outbound', %s, %s, %s)
            """, (child_id, recipient_phone, first_name, last_name, message_body, delivery_status, at_msg_id))
    except Exception as log_err:
        app.logger.warning(f"Could not write SMS to message_logs: {log_err}")

    return delivery_status

# 2. Email Dispatch Gateway (SMTP / Transactional Service)
def _env_text(name, default=""):
    value = os.getenv(name, default)
    return value.strip().strip('"').strip("'") if value else default

SMTP_SERVER = _env_text("SMTP_SERVER", "smtp.gmail.com")
try:
    SMTP_PORT = int(_env_text("SMTP_PORT", "587"))
except ValueError:
    SMTP_PORT = 465
SMTP_USERNAME = _env_text("SMTP_USERNAME")
SMTP_PASSWORD = _env_text("SMTP_PASSWORD").replace(" ", "")
EMAIL_FROM_ADDRESS = _env_text("EMAIL_FROM_ADDRESS") or SMTP_USERNAME or "notifications@sunfloweracademy.org"
EMAIL_FROM_NAME = _env_text("EMAIL_FROM_NAME", "Sunflower Academy")
RESEND_API_KEY = _env_text("RESEND_API_KEY")

missing_smtp_settings = [
    name for name, configured in (
        ("SMTP_USERNAME", bool(SMTP_USERNAME)),
        ("SMTP_PASSWORD", bool(SMTP_PASSWORD)),
    ) if not configured
]
if missing_smtp_settings:
    logging.warning("SMTP email is disabled because these environment variables are missing: %s", ", ".join(missing_smtp_settings))
else:
    logging.info("SMTP email configuration loaded for %s:%s", SMTP_SERVER, SMTP_PORT)

def dispatch_email(recipient_email, subject, body_text, body_html=None, child_id=None, first_name="", last_name=""):
    """
    Dispatches outbound email notifications using standard SMTP
    (or Gmail App Password / SendGrid / Postmark / Mailgun) and audits in message_logs.
    """
    delivery_status = "Sent"

    if not recipient_email:
        return "Skipped (No Email)"

    if RESEND_API_KEY:
        try:
            response = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": "Bearer " + RESEND_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "from": f"{EMAIL_FROM_NAME} <{EMAIL_FROM_ADDRESS}>",
                    "to": [recipient_email],
                    "subject": subject,
                    "text": body_text,
                    "html": body_html,
                },
                timeout=15,
            )
            if response.ok:
                delivery_status = "Delivered (Resend)"
                logging.info("Email delivered through Resend for %s: %s", recipient_email, response.text)
            else:
                delivery_status = f"Failed (Resend: HTTP {response.status_code})"
                logging.error("Email failed through Resend for %s: %s", recipient_email, response.text)
        except Exception:
            logging.exception("Resend email send failed for %s", recipient_email)
            delivery_status = "Failed (Email API send error)"
    elif SMTP_USERNAME and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_FROM_ADDRESS}>"
            msg["To"] = recipient_email
            msg.attach(MIMEText(body_text, "plain"))
            if body_html:
                msg.attach(MIMEText(body_html, "html"))

            smtp_class = smtplib.SMTP_SSL if SMTP_PORT == 465 else smtplib.SMTP
            with smtp_class(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                if SMTP_PORT != 465:
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                send_result = server.sendmail(EMAIL_FROM_ADDRESS, [recipient_email], msg.as_string())

            if send_result:
                delivery_status = f"Failed (SMTP rejected recipient: {send_result})"
                logging.error("Email was not delivered to %s: SMTP rejected recipient - %s", recipient_email, send_result)
            else:
                delivery_status = "Delivered (SMTP)"
        except Exception:
            logging.exception("Email send failed for %s", recipient_email)
            delivery_status = "Failed (Email send error)"
    else:
        delivery_status = "Failed (SMTP not configured)"
        logging.error("Email was not sent to %s: no email provider is configured", recipient_email)

    # Audit in message_logs
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO message_logs 
                (child_id, recipient_email, first_name, last_name, channel, direction, subject, message_body, delivery_status)
                VALUES (%s, %s, %s, %s, 'Email', 'outbound', %s, %s, %s)
            """, (child_id, recipient_email, first_name, last_name, subject, body_text, delivery_status))
    except Exception as log_err:
        app.logger.warning(f"Could not write Email to message_logs: {log_err}")

    return delivery_status

# 3. Unified Multi-Channel Dispatch Router (Dual SMS + Email)
def dispatch_parent_notification(child, subject, message_text, message_html=None):
    """
    Dispatches message across SMS, Email, or Both depending on parent preference.
    """
    phone = child.get('parent_phone')
    email = child.get('parent_email')
    pref = child.get('preferred_channel', 'Both')
    child_id = child.get('id')
    first = child.get('first_name', '')
    last = child.get('last_name', '')

    sms_res = None
    email_res = None

    if pref in ('SMS', 'Both') and phone:
        sms_res = dispatch_sms(phone, message_text, child_id=child_id, first_name=first, last_name=last)

    if pref in ('Email', 'Both') and email:
        email_res = dispatch_email(email, subject, message_text, body_html=message_html, child_id=child_id, first_name=first, last_name=last)

    return {"sms": sms_res, "email": email_res}

# Authentication Decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Please sign in to access this portal.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'manager':
            flash("Action restricted to School Managers.")
            return redirect(url_for('teacher_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.pop('inactive_logout', False):
        flash("You were signed out automatically after 10 minutes of inactivity.", "warning")

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        with get_db_cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cur.fetchone()

        if user and check_password_hash(user['password_hash'], password):
            session['user'] = user['username']
            session['role'] = user['role']
            session['user_id'] = user['id']
            session['last_activity'] = datetime.now(timezone.utc).timestamp()
            session.pop('inactive_logout', None)
            flash(f"Welcome back, {user['username']}!")
            if user['role'] == 'manager':
                return redirect(url_for('manager_dashboard'))
            return redirect(url_for('teacher_dashboard'))
        
        flash("Invalid username or password.")
    return render_template('login.html')

@app.route('/reset-admin-password', methods=['POST'])
def reset_admin_password():
    username = request.form.get('username', '').strip()
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not username or not current_password or not new_password or not confirm_password:
        flash("Complete every administrator password-reset field.", "warning")
        return redirect(url_for('login'))

    if new_password != confirm_password:
        flash("The new passwords do not match.", "warning")
        return redirect(url_for('login'))

    if len(new_password) < 8:
        flash("The new password must be at least 8 characters long.", "warning")
        return redirect(url_for('login'))

    if current_password == new_password:
        flash("Choose a new password that is different from the current password.", "warning")
        return redirect(url_for('login'))

    with get_db_cursor() as cur:
        cur.execute("SELECT id, password_hash, role FROM users WHERE username = %s", (username,))
        user = cur.fetchone()

    if not user:
        flash("Administrator account was not found.", "danger")
        return redirect(url_for('login'))

    if user['role'] != 'manager':
        flash("Teacher passwords can only be reset by the administrator.", "danger")
        return redirect(url_for('login'))

    if not check_password_hash(user['password_hash'], current_password):
        flash("The current administrator password is incorrect.", "danger")
        return redirect(url_for('login'))

    with get_db_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s AND role = 'manager'",
            (generate_password_hash(new_password), user['id']),
        )

    session.clear()
    flash("Administrator password reset successfully. Please sign in with the new password.", "success")
    return redirect(url_for('login'))

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash("You have been signed out.")
    return redirect(url_for('login'))

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/robots.txt')
def robots_txt():
    from flask import Response
    return Response("User-agent: GPTBot\nDisallow: /\nUser-agent: CCBot\nDisallow: /\nUser-agent: anthropic-ai\nDisallow: /\nUser-agent: *\nDisallow: /login\n", mimetype='text/plain')

# Manager Dashboard (Desktop Operations Hub)
@app.route('/')
@app.route('/dashboard')
@login_required
def manager_dashboard():
    if session.get('role') != 'manager':
        return redirect(url_for('teacher_dashboard'))

    with get_db_cursor() as cur:
        # 1. Fetch classroom roster with guardians, email & phone
        cur.execute("""
            SELECT c.*, 
                   COUNT(g.id) as guardian_count,
                   (SELECT full_name FROM authorized_guardians WHERE child_id = c.id AND is_primary = TRUE LIMIT 1) as primary_guardian,
                   (SELECT phone_number FROM authorized_guardians WHERE child_id = c.id AND is_primary = TRUE LIMIT 1) as primary_phone,
                   (SELECT email FROM authorized_guardians WHERE child_id = c.id AND is_primary = TRUE LIMIT 1) as primary_email
            FROM children c
            LEFT JOIN authorized_guardians g ON c.id = g.child_id
            GROUP BY c.id
            ORDER BY c.first_name ASC
        """)
        children = cur.fetchall()

        # 2. Daily Care Activity Feed
        cur.execute("""
            SELECT l.*, c.first_name, c.last_name, c.room_name
            FROM daily_care_logs l
            JOIN children c ON l.child_id = c.id
            ORDER BY l.logged_at DESC
            LIMIT 15
        """)
        care_logs = cur.fetchall()

        # 3. Multi-Channel Message Logs (SMS + Email)
        cur.execute("SELECT * FROM message_logs ORDER BY received_at DESC LIMIT 20")
        logs = cur.fetchall()

    total = len(children)
    present = sum(1 for c in children if c['current_status'] == 'Checked In')
    absent = total - present

    return render_template(
        'dashboard.html',
        children=children,
        care_logs=care_logs,
        logs=logs,
        stats={'total': total, 'present': present, 'absent': absent},
        username=session.get('user')
    )

# Teacher Mobile Floor App View
@app.route('/teacher-dashboard')
@login_required
def teacher_dashboard():
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT c.*,
                   (SELECT full_name FROM authorized_guardians WHERE child_id = c.id AND is_primary = TRUE LIMIT 1) as primary_guardian,
                   (SELECT relationship FROM authorized_guardians WHERE child_id = c.id AND is_primary = TRUE LIMIT 1) as primary_rel
            FROM children c
            ORDER BY c.current_status DESC, c.first_name ASC
        """)
        children = cur.fetchall()

    total = len(children)
    present = sum(1 for c in children if c['current_status'] == 'Checked In')
    absent = total - present

    return render_template(
        'teacher_dashboard.html',
        children=children,
        stats={'total': total, 'present': present, 'absent': absent},
        username=session.get('user')
    )

# Attendance Status Toggle & Express Actions (Dual SMS + Email Notification)
@app.route('/update-status', methods=['POST'])
@login_required
def update_status():
    child_id = request.form.get('child_id')
    action = request.form.get('action') # 'Check In' or 'Checked Out'
    teacher = session.get('user', 'Staff')

    new_status = 'Checked In' if action == 'Check In' else 'Checked Out'
    now_str = east_africa_time().strftime('%H:%M')

    with get_db_cursor(commit=True) as cur:
        cur.execute("""
            UPDATE children 
            SET current_status = %s, 
                last_status_time = CURRENT_TIMESTAMP,
                last_action_by = %s
            WHERE id = %s
            RETURNING id, first_name, last_name, parent_phone, parent_email, preferred_channel
        """, (new_status, teacher, child_id))
        child = cur.fetchone()

        # Audit handshake
        cur.execute("""
            INSERT INTO attendance_handshakes (child_id, action_type, teacher_username)
            VALUES (%s, %s, %s)
        """, (child_id, 'CHECK_IN' if new_status == 'Checked In' else 'CHECK_OUT', teacher))

    if child:
        subject = f"Attendance Update: {child['first_name']} marked {new_status}"
        msg_text = f"Sunflower Academy: {child['first_name']} {child['last_name']} was safely marked {new_status} at {now_str} by {teacher}."
        msg_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; padding: 20px; border: 1px solid #e2e8f0; border-radius: 10px;">
            <h2 style="color: #0f4c81; margin-top:0;">Sunflower Daycare Academy</h2>
            <p style="font-size: 15px; color: #1e293b;">Hello Parent,</p>
            <p style="font-size: 15px; color: #1e293b;">
                <strong>{child['first_name']} {child['last_name']}</strong> was safely marked 
                <span style="background: {'#dcfce7' if new_status=='Checked In' else '#f1f5f9'}; color: {'#15803d' if new_status=='Checked In' else '#475569'}; padding: 3px 8px; border-radius: 4px; font-weight: bold;">{new_status}</span>
                at <strong>{now_str}</strong>.
            </p>
            <p style="font-size: 13px; color: #64748b;">Witnessed & Logged by Educator: {teacher}</p>
            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 15px 0;">
            <p style="font-size: 11px; color: #94a3b8;">Sunflower Academy Attendance & Safety Notification Service</p>
        </div>
        """
        dispatch_parent_notification(child, subject, msg_text, msg_html)
        flash(f"{child['first_name']} status updated to {new_status}. Parent notified via {child['preferred_channel']}.")

    return redirect(request.referrer or url_for('teacher_dashboard'))

# Guardian Pickup Verification (Handoff Chain of Custody)
@app.route('/child/<int:child_id>/guardians', methods=['GET'])
@login_required
def get_child_guardians(child_id):
    """API endpoint to fetch verified guardians for verification modal"""
    with get_db_cursor() as cur:
        cur.execute("""
            SELECT id, full_name, relationship, phone_number, email, is_primary,
                   access_type, pickup_expires_at, pickup_used_at
            FROM authorized_guardians WHERE child_id = %s
            ORDER BY is_primary DESC, full_name ASC
        """, (child_id,))
        guardians = cur.fetchall()
    return jsonify({'guardians': guardians})

@app.route('/verify-pickup-checkout', methods=['POST'])
@login_required
def verify_pickup_checkout():
    child_id = request.form.get('child_id')
    guardian_id = request.form.get('guardian_id')
    departure_notes = request.form.get('departure_notes', '')
    teacher = session.get('user', 'Staff')
    now_str = east_africa_time().strftime('%H:%M')

    with get_db_cursor(commit=True) as cur:
        # Fetch guardian details and enforce one-time pickup authorization.
        cur.execute("""
            SELECT full_name, relationship, child_id, verification_pin, access_type,
                   pickup_expires_at, pickup_used_at, verification_attempts
            FROM authorized_guardians WHERE id = %s
        """, (guardian_id,))
        guardian = cur.fetchone()

        if not guardian or str(guardian['child_id']) != str(child_id):
            flash('The selected guardian is not authorized for this child.')
            return redirect(request.referrer or url_for('teacher_dashboard'))

        one_time = guardian['access_type'] == 'One-Time'
        if one_time:
            pin = request.form.get('pickup_pin', '').strip()
            if guardian['pickup_used_at']:
                flash('This one-time pickup authorization has already been used.')
                return redirect(request.referrer or url_for('teacher_dashboard'))
            if guardian['pickup_expires_at'] and guardian['pickup_expires_at'] <= datetime.now(timezone.utc):
                flash('This one-time pickup authorization has expired.')
                return redirect(request.referrer or url_for('teacher_dashboard'))
            if not pin or not secrets.compare_digest(pin, guardian['verification_pin'] or ''):
                cur.execute("UPDATE authorized_guardians SET verification_attempts = COALESCE(verification_attempts, 0) + 1 WHERE id = %s", (guardian_id,))
                flash('Invalid or missing one-time pickup PIN.')
                return redirect(request.referrer or url_for('teacher_dashboard'))

        guardian_name = f"{guardian['full_name']} ({guardian['relationship']})"

        # Update child status
        cur.execute("""
            UPDATE children 
            SET current_status = 'Checked Out', 
                last_status_time = CURRENT_TIMESTAMP,
                last_action_by = %s
            WHERE id = %s
            RETURNING id, first_name, last_name, parent_phone, parent_email, preferred_channel
        """, (teacher, child_id))
        child = cur.fetchone()

        # Audit handshake
        cur.execute("""
            INSERT INTO attendance_handshakes (child_id, action_type, guardian_id, guardian_name_snapshot, teacher_username, departure_notes)
            VALUES (%s, 'CHECK_OUT', %s, %s, %s, %s)
        """, (child_id, guardian_id, guardian_name, teacher, departure_notes))
        if one_time:
            cur.execute("UPDATE authorized_guardians SET pickup_used_at = CURRENT_TIMESTAMP WHERE id = %s", (guardian_id,))

    if child:
        subject = f"Safe Pickup Confirmation: {child['first_name']} Handed Off"
        msg_text = f"Sunflower Academy: {child['first_name']} was safely checked out at {now_str} by verified guardian {guardian_name}. Staff witness: {teacher}."
        msg_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; padding: 20px; border: 1px solid #e2e8f0; border-radius: 10px;">
            <h2 style="color: #0f4c81; margin-top:0;">Pickup Hand-off Confirmation</h2>
            <p style="font-size: 15px; color: #1e293b;">
                <strong>{child['first_name']} {child['last_name']}</strong> was safely checked out from campus at <strong>{now_str}</strong>.
            </p>
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; margin: 12px 0;">
                <p style="margin: 0; font-size: 14px; color: #334155;"><strong>Authorized Guardian:</strong> {guardian_name}</p>
                <p style="margin: 4px 0 0; font-size: 13px; color: #64748b;"><strong>Staff Witness:</strong> {teacher}</p>
                {f'<p style="margin: 4px 0 0; font-size: 13px; color: #64748b;"><strong>Notes:</strong> {departure_notes}</p>' if departure_notes else ''}
            </div>
            <p style="font-size: 11px; color: #94a3b8;">Official Chain-of-Custody Verification Record</p>
        </div>
        """
        dispatch_parent_notification(child, subject, msg_text, msg_html)
        flash(f"{child['first_name']} verified and checked out with {guardian_name}. Parent notified via {child['preferred_channel']}.")

    return redirect(request.referrer or url_for('teacher_dashboard'))

# Daily Care Activity Logging (Nap, Meal, Diaper, Incident -> Email Digest)
@app.route('/log-care-activity', methods=['POST'])
@login_required
def log_care_activity():
    child_id = request.form.get('child_id')
    category = request.form.get('category') # 'nap', 'meal', 'diaper', 'incident'
    title = request.form.get('title')
    details = request.form.get('details', '')
    metric_value = request.form.get('metric_value', '')
    notify_parent = request.form.get('notify_parent', 'false').lower() == 'true'
    teacher = session.get('user', 'Teacher')

    with get_db_cursor(commit=True) as cur:
        cur.execute("""
            INSERT INTO daily_care_logs (child_id, teacher_username, category, title, details, metric_value, parent_notified, notification_channel)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'Email')
        """, (child_id, teacher, category, title, details, metric_value, notify_parent))

        if notify_parent:
            cur.execute("SELECT id, first_name, last_name, parent_phone, parent_email, preferred_channel FROM children WHERE id = %s", (child_id,))
            child = cur.fetchone()
            if child:
                subject = f"Daily Milestone: {child['first_name']} - {title}"
                msg_text = f"Sunflower Daily Care: {child['first_name']} - {title} ({metric_value}). {details} (Logged by {teacher})"
                msg_html = f"""
                <div style="font-family: Arial, sans-serif; max-width: 500px; padding: 20px; border: 1px solid #e2e8f0; border-radius: 10px;">
                    <h3 style="color: #0f4c81; margin-top:0;">{child['first_name']}'s Daily Care Update</h3>
                    <p style="font-size: 15px; color: #1e293b;"><strong>{title}</strong></p>
                    <p style="font-size: 14px; color: #475569;">{details}</p>
                    {f'<p style="font-size: 13px; color: #0f4c81; font-weight: bold;">Metric: {metric_value}</p>' if metric_value else ''}
                    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 15px 0;">
                    <p style="font-size: 11px; color: #94a3b8;">Logged by {teacher} • Sunflower Daycare Academy</p>
                </div>
                """
                dispatch_parent_notification(child, subject, msg_text, msg_html)

    flash(f"Care milestone ({category.capitalize()}) recorded.")
    return redirect(request.referrer or url_for('teacher_dashboard'))

# Emergency Broadcast (SMS + Email High-Priority Deployment)
@app.route('/trigger-emergency', methods=['POST'])
@login_required
def trigger_emergency():
    child_id = request.form.get('child_id')
    teacher = session.get('user', 'Staff')

    with get_db_cursor(commit=True) as cur:
        cur.execute("""
            UPDATE children 
            SET current_status = 'Urgent Alert', 
                last_status_time = CURRENT_TIMESTAMP,
                last_action_by = %s
            WHERE id = %s
            RETURNING id, first_name, last_name, parent_phone, parent_email
        """, (teacher, child_id))
        child = cur.fetchone()

    if child:
        msg_text = f"URGENT ALERT: Sunflower Academy needs your immediate attention regarding {child['first_name']} {child['last_name']}. Please call the center immediately."
        subject = f"URGENT ALERT regarding {child['first_name']} {child['last_name']}"
        msg_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 500px; padding: 20px; border: 2px solid #dc2626; border-radius: 10px; background: #fef2f2;">
            <h2 style="color: #b91c1c; margin-top:0;">🚨 URGENT DAYCARE BROADCAST</h2>
            <p style="font-size: 16px; color: #991b1b; font-weight: bold;">
                Sunflower Academy requires your immediate attention regarding {child['first_name']} {child['last_name']}.
            </p>
            <p style="font-size: 14px; color: #7f1d1d;">
                Please contact the campus office immediately.
            </p>
            <p style="font-size: 12px; color: #991b1b;">Dispatched at {east_africa_time().strftime('%H:%M')} (EAT) by {teacher}</p>
        </div>
        """
        # In emergencies, broadcast across BOTH SMS and Email simultaneously
        if child.get('parent_phone'):
            dispatch_sms(child['parent_phone'], msg_text, child_id=child_id, first_name=child['first_name'], last_name=child['last_name'])
        if child.get('parent_email'):
            dispatch_email(child['parent_email'], subject, msg_text, body_html=msg_html, child_id=child_id, first_name=child['first_name'], last_name=child['last_name'])

        flash(f"EMERGENCY BROADCAST deployed to {child['first_name']}'s parents via SMS and Email.", "danger")

    return redirect(request.referrer or url_for('teacher_dashboard'))

@app.route('/test-email', methods=['POST'])
@manager_required
def test_email_delivery():
    recipient = request.form.get('recipient_email', '').strip() or SMTP_USERNAME
    if not recipient:
        flash('Enter an email address or configure SMTP_USERNAME.', 'danger')
        return redirect(request.referrer or url_for('dashboard'))

    status = dispatch_email(
        recipient,
        'Sunflower Academy SMTP Test',
        'This is a test email from the Sunflower Academy notification system.',
        body_html='<h2>SMTP test successful</h2><p>Sunflower Academy can send email notifications.</p>',
    )
    category = 'success' if status == 'Delivered (SMTP)' else 'danger'
    flash(f'SMTP test result: {status}', category)
    return redirect(request.referrer or url_for('dashboard'))

# Administrative Management Routes (Manager Role Required)
@app.route('/add-family', methods=['POST'])
@manager_required
def add_family():
    child_first = request.form.get('child_first', '').strip()
    child_last = request.form.get('child_last', '').strip()
    room_name = request.form.get('room_name', 'Toddler Room B').strip()
    allergy_info = request.form.get('allergy_info', '').strip() or None
    parent_first = request.form.get('parent_first', '').strip()
    parent_last = request.form.get('parent_last', '').strip()
    parent_phone = request.form.get('parent_phone', '').strip()
    parent_email = request.form.get('parent_email', '').strip() or None
    preferred_channel = request.form.get('preferred_channel', 'Both')

    with get_db_cursor(commit=True) as cur:
        cur.execute("""
            INSERT INTO children (first_name, last_name, room_name, allergy_info, parent_first_name, parent_last_name, parent_phone, parent_email, preferred_channel)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (child_first, child_last, room_name, allergy_info, parent_first, parent_last, parent_phone, parent_email, preferred_channel))
        child_id = cur.fetchone()['id']

        # Automatically enroll primary guardian
        cur.execute("""
            INSERT INTO authorized_guardians (child_id, full_name, relationship, phone_number, email, is_primary)
            VALUES (%s, %s, 'Parent', %s, %s, TRUE)
        """, (child_id, f"{parent_first} {parent_last}", parent_phone, parent_email))

    flash(f"Enrolled {child_first} {child_last} in {room_name} (Channel: {preferred_channel}).")
    return redirect(url_for('manager_dashboard'))

@app.route('/authorize-one-time-pickup', methods=['POST'])
@manager_required
def authorize_one_time_pickup():
    child_id = request.form.get('child_id')
    full_name = request.form.get('full_name', '').strip()
    relationship = request.form.get('relationship', 'Authorized Contact').strip()
    phone = request.form.get('phone_number', '').strip()
    email = request.form.get('email', '').strip() or None
    government_id_type = request.form.get('government_id_type', 'National ID').strip()
    national_id_number = request.form.get('national_id_number', '').strip() or None
    photo_url = request.form.get('photo_url', '').strip() or None
    notes = request.form.get('notes', '').strip() or None
    try:
        valid_hours = min(max(int(request.form.get('valid_hours', '24') or 24), 1), 168)
    except (TypeError, ValueError):
        valid_hours = 24

    if not child_id or not full_name or not phone:
        flash('Child, guardian name, and phone number are required.')
        return redirect(request.referrer or url_for('manager_dashboard'))

    access_pin = ''.join(str(secrets.randbelow(10)) for _ in range(6))
    expires_at = datetime.now(timezone.utc) + timedelta(hours=valid_hours)

    with get_db_cursor(commit=True) as cur:
        cur.execute("""
            INSERT INTO authorized_guardians
                (child_id, full_name, relationship, phone_number, email, is_primary, government_id_type,
                 national_id_number, photo_url, notes, verification_pin, access_type, pickup_expires_at, authorized_by)
            VALUES (%s, %s, %s, %s, %s, FALSE, %s, %s, %s, %s, %s, 'One-Time', %s, %s)
        """, (child_id, full_name, relationship, phone, email, government_id_type,
              national_id_number, photo_url, notes, access_pin, expires_at, session.get('user')))

        cur.execute("SELECT first_name, last_name FROM children WHERE id = %s", (child_id,))
        child = cur.fetchone()

    child_name = f"{child['first_name']} {child['last_name']}" if child else 'your child'
    message = (f"Sunflower Academy: You are authorized to collect {child_name}. "
               f"Use one-time pickup PIN {access_pin}. Valid for {valid_hours} hour(s) and expires after the first pickup.")
    dispatch_sms(phone, message)
    if email:
        dispatch_email(email, f"One-Time Pickup Authorization for {child_name}", message,
                       body_html=f"<p>{message}</p>")

    flash(f"One-time pickup authorized for {full_name}. PIN sent to their phone{(' and email' if email else '')}.")
    return redirect(request.referrer or url_for('manager_dashboard'))


@app.route('/add-guardian', methods=['POST'])
@manager_required
def add_guardian():
    child_id = request.form.get('child_id')
    full_name = request.form.get('full_name', '').strip()
    relationship = request.form.get('relationship', 'Authorized Contact').strip()
    phone = request.form.get('phone_number', '').strip()
    email = request.form.get('email', '').strip() or None
    gov_id = request.form.get('government_id_type', 'National ID').strip()
    national_id = request.form.get('national_id_number', '').strip() or None
    photo_url = request.form.get('photo_url', '').strip() or None
    notes = request.form.get('notes', '').strip() or None
    id_verified = request.form.get('id_verified') == 'on'

    with get_db_cursor(commit=True) as cur:
        cur.execute("""
            INSERT INTO authorized_guardians
                (child_id, full_name, relationship, phone_number, email, is_primary,
                 id_verified, government_id_type, national_id_number, photo_url, notes, authorized_by)
            VALUES (%s, %s, %s, %s, %s, FALSE, %s, %s, %s, %s, %s, %s)
        """, (child_id, full_name, relationship, phone, email, id_verified,
              gov_id, national_id, photo_url, notes, session.get('user')))

    flash(f"Authorized pickup guardian {full_name} added.")
    return redirect(request.referrer or url_for('manager_dashboard'))

@app.route('/add-teacher', methods=['POST'])
@manager_required
def add_teacher():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    if len(password) < 8:
        flash("Password must be at least 8 characters long.")
        return redirect(url_for('manager_dashboard'))

    pw_hash = generate_password_hash(password)
    try:
        with get_db_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO users (username, password_hash, role)
                VALUES (%s, %s, 'teacher')
            """, (username, pw_hash))
        flash(f"Teacher account '{username}' successfully created.")
    except psycopg2.IntegrityError:
        flash(f"Username '{username}' is already in use.")

    return redirect(url_for('manager_dashboard'))

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "0") == "1")
