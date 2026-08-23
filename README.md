# Reminder That Reaches — Full-Stack Application

A production-quality full-stack web application built for Calder County's policy-driven appointment reminder system challenge.

---

## Project Overview

The system receives appointment bookings (`appointments.csv`) and resident contact profiles (`contacts.csv`), stores them in a local **SQLite** database, and exposes a RESTful **FastAPI** backend with a modern **React (Vite)** dashboard.

It enforces centralized contact policy rules, quiet hours (20:00–08:00 deferrals), landline safety, localized template selection, deduplication, and Direction CR-2026/11 rolling 7-day contact limits while distinguishing delivery evidence from confirmed human reach.

---

## Technology Stack

- **Backend**: Python 3.8+, FastAPI, SQLAlchemy, Pydantic, SQLite (`reminder.db`), Uvicorn
- **Frontend**: React 18, Vite, React Router 6, Recharts, Axios, Lucide React
- **Data & Mock Channels**: `appointments.csv`, `contacts.csv`, `channels/channels.py`

---

## Regulatory Compliance (Direction CR-2026/11)

- **Max 2 Contacts in Rolling 7 Days**: Per resident across ALL channels (SMS, Voice, Email).
- **Every Outbound Attempt Counts**: Succeeded or failed outbound attempts (SMS rejected, Email bounce, Voice voicemail/unanswered) count towards the resident's 2-contact threshold.
- **Pre-Dispatch Evaluation**: Contacts are withheld (`permitted=False`) if count >= 2 in the preceding 168 hours. Evidence and audit logs are recorded.

---

## Database Schemas (SQLite)

- `residents`: Contact profiles, opt-out flags, preferred language, verification date.
- `appointments`: Scheduled appointment details, location, service type, status.
- `reminders`: Core reminder execution tracking (`Pending`, `Reached`, `Delivered`, `Failed`, `Deferred`, `Blocked`).
- `reminder_attempts`: Individual attempt dispatches per channel with provider detail & reach classification.
- `audit_logs`: Centralized audit decision trail.
- `policies`: Configurable policy values (`quiet_hours_start`, `quiet_hours_end`, `max_attempts`, `channel_priority`).

---

## Localhost URLs

- **React Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)
- **FastAPI Backend REST API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## One-Command Windows Launch

To launch both backend and frontend automatically on Windows:

```cmd
start-dev.bat
```

---

## Manual Step-by-Step Setup

### 1. Backend Setup

```cmd
# Navigate to backend
cd backend

# Create virtual environment (optional)
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Seed SQLite database
python seed_database.py

# Launch FastAPI server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup

```cmd
# Navigate to frontend
cd frontend

# Install npm dependencies
npm install

# Start Vite dev server
npm run dev
```

---

## Running Automated Backend Tests

```cmd
python -m pytest backend/tests/test_policy.py
```

---

## Reach Definition & Fallback

- **SMS**: Carrier `delivered` is delivery evidence (`reached = False`). Landlines in mobile fields are automatically blocked.
- **Voice**: `answered` + `human` is **Confirmed Human Reach** (`reached = True`). `voicemail_left` or `no_answer` do NOT count as human reach and trigger fallback to Email.
- **Email**: `delivered` is delivery success (`reached = False`).
- **Fallback Chain**: `SMS -> Voice -> Email`. Terminates immediately upon confirmed human reach, channel exhaustion, max attempts (3), regulatory 7-day limit (max 2 contacts), or lead time threshold (< 30 min).
