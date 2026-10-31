# Kindergarten Daycare Web Application

A Flask and PostgreSQL daycare management application for attendance, authorized guardians, one-time pickup authorization, care logs, and parent notifications.

## Setup

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install flask python-dotenv psycopg2-binary africastalking
   ```
3. Copy your environment configuration into `.env` and set the database and notification credentials.
4. Apply [schema.sql](schema.sql) to PostgreSQL.
5. Run the application:
   ```bash
   python daycare.py
   ```

The development server uses `http://127.0.0.1:5001` by default.

## Security

Keep `.env`, API keys, database passwords, and Flask secrets out of source control. The repository `.gitignore` excludes local secrets and virtual environments.
