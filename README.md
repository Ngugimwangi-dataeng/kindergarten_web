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

## Vercel deployment

Import the GitHub repository in Vercel. The repository includes `vercel.json`, `api/index.py`, and `requirements.txt` for Python serverless deployment.

Configure these environment variables in the Vercel project settings:

```text
DATABASE_URL=postgresql://user:password@host:port/database
FLASK_SECRET_KEY=your-random-production-secret
AT_USERNAME=your_africas_talking_username
AT_API_KEY=your_africas_talking_api_key
```

`DATABASE_URL` must point to PostgreSQL accessible from Vercel. Apply `schema.sql` and keep database credentials, SMS keys, and SMTP credentials only in Vercel environment settings or local `.env`, never in the repository.

## Security

Keep `.env`, API keys, database passwords, and Flask secrets out of source control. The repository `.gitignore` excludes local secrets and virtual environments.
