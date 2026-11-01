"""
Daycare Management System - Full Backend Implementation
File: daycare.py
Framework: Flask 3.x, psycopg2, Africa's Talking SDK (SMS), SMTP / Transactional Email, Werkzeug Security
Channels: Dual SMS + Email (Africa's Talking SMS for Instant Alerts + SMTP / API for Rich Email Digests)
"""

import os
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, jsonify, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load local environment configuration
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))

# ==============================================================================
# Database Configuration & Context Manager
# ==============================================================================
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

# ==============================================================================
# 1. Africa's Talking SMS Dispatch Gateway
# ==============================================================================
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
            recipients = response.get('SMSMessageData', {}).get('Recipients', [])
            if recipients:
                delivery_status = recipients[0].get('status', 'Sent')
                at_msg_id = recipients[0].get('messageId')
        except Exception as exc:
            app.logger.error(f"Africa's Talking SMS dispatch failed: {exc}")
            delivery_status = "Failed (Local Simulation)"
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

# ==============================================================================
# 2. Email Dispatch Gateway (SMTP / Transactional Service)
# ==============================================================================
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM_ADDRESS = os.getenv("EMAIL_FROM_ADDRESS", "notifications@sunfloweracademy.org")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "Sunflower Academy")

def dispatch_email(recipient_email, subject, body_text, body_html=None, child_id=None, first_name="", last_name=""):
    """
    Dispatches outbound email notifications using standard SMTP
    (or Gmail App Password / SendGrid / Postmark / Mailgun) and audits in message_logs.
    """
    delivery_status = "Sent"

    if not recipient_email:
        return "Skipped (No Email)"

    if SMTP_USERNAME and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_FROM_ADDRESS}>"
            msg["To"] = recipient_email

            part_text = MIMEText(body_text, "plain")
            msg.attach(part_text)

            if body_html:
                part_html = MIMEText(body_html, "html")
                msg.attach(part_html)

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.sendmail(EMAIL_FROM_ADDRESS, [recipient_email], msg.as_string())
            delivery_status = "Delivered (SMTP)"
        except Exception as mail_err:
            app.logger.error(f"Email dispatch error: {mail_err}")
            delivery_status = "Failed (Local Simulation)"
    else:
        delivery_status = "Delivered (Dev Sim Email)"

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

# ==============================================================================
# 3. Unified Multi-Channel Dispatch Router (Dual SMS + Email)
# ==============================================================================
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

# ==============================================================================
# Authentication Decorators
# ==============================================================================
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

# ==============================================================================
# Authentication Routes
# ==============================================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
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
            flash(f"Welcome back, {user['username']}!")
            if user['role'] == 'manager':
                return redirect(url_for('manager_dashboard'))
            return redirect(url_for('teacher_dashboard'))
        
        flash("Invalid username or password.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been signed out.")
    return redirect(url_for('login'))

# ==============================================================================
# Manager Dashboard (Desktop Operations Hub)
# ==============================================================================
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

# ==============================================================================
# Teacher Mobile Floor App View
# ==============================================================================
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

# ==============================================================================
# Attendance Status Toggle & Express Actions (Dual SMS + Email Notification)
# ==============================================================================
@app.route('/update-status', methods=['POST'])
@login_required
def update_status():
    child_id = request.form.get('child_id')
    action = request.form.get('action') # 'Check In' or 'Checked Out'
    teacher = session.get('user', 'Staff')

    new_status = 'Checked In' if action == 'Check In' else 'Checked Out'
    now_str = datetime.now().strftime('%I:%M %p')

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

# ==============================================================================
# Guardian Pickup Verification (Handoff Chain of Custody)
# ==============================================================================
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
    now_str = datetime.now().strftime('%I:%M %p')

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

# ==============================================================================
# Daily Care Activity Logging (Nap, Meal, Diaper, Incident -> Email Digest)
# ==============================================================================
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

# ==============================================================================
# Emergency Broadcast (SMS + Email High-Priority Deployment)
# ==============================================================================
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
            <p style="font-size: 12px; color: #991b1b;">Dispatched at {datetime.now().strftime('%I:%M %p')} by {teacher}</p>
        </div>
        """
        # In emergencies, broadcast across BOTH SMS and Email simultaneously
        if child.get('parent_phone'):
            dispatch_sms(child['parent_phone'], msg_text, child_id=child_id, first_name=child['first_name'], last_name=child['last_name'])
        if child.get('parent_email'):
            dispatch_email(child['parent_email'], subject, msg_text, body_html=msg_html, child_id=child_id, first_name=child['first_name'], last_name=child['last_name'])

        flash(f"EMERGENCY BROADCAST deployed to {child['first_name']}'s parents via SMS and Email.", "danger")

    return redirect(request.referrer or url_for('teacher_dashboard'))

# ==============================================================================
# Administrative Management Routes (Manager Role Required)
# ==============================================================================
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
