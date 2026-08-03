# TruckAlignmentTracker

A Django web application for tracking truck wheel-alignment service records
across a fleet — dashboard metrics, charts, filtered reports, PDF/Excel/CSV
export, and login-protected access.

## Features

- **Login required** — every page (dashboard, add, edit, reports, exports)
  requires signing in at `/login/`.
- **Fleet-based Truck dropdown** — the 51-unit D&A Hauliers fleet register
  (`Truck` model) drives the Truck ID dropdown on Add/Edit Alignment, with
  the matching trailer auto-filled on selection.
- **User Management** (`/users/`, admin/staff only) — create technician or
  admin accounts, activate/deactivate, or delete users, all from the app
  (no need to touch `/admin/`).
- **Dashboard** — total alignments, this-month count, overdue trucks
  (no alignment in 90+ days), average mileage, 10 most recent records, and
  two Chart.js bar charts (by technician, by top-10 trucks).
- **Add Alignment** — form for logging a new alignment (date/time default
  to "now"); Truck ID is chosen from the fleet list, Trailer ID auto-fills.
- **Edit / Delete** — update or remove existing records (delete requires
  confirmation).
- **Reports** — filter by date range, technician, and truck ID; export the
  filtered results to PDF, Excel, or CSV, or print a clean report view.
- **Admin** — full Django admin for the `Alignment` and `Truck` models with
  search and filters.

## Requirements

- Python 3.10+
- pip

## Setup

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Apply database migrations (this also seeds the 51-truck fleet list)
python manage.py migrate

# 4. Create your first admin login (required — the whole site is login-protected)
python manage.py createsuperuser

# 5. Run the development server
python manage.py runserver
```

Then open **http://127.0.0.1:8000/login/** and sign in with the superuser
you just created.

- Login: `/login/`
- Dashboard: `/`
- Add Alignment: `/add/`
- Reports: `/reports/`
- Manage Users: `/users/` (admin/staff accounts only)
- Django Admin: `/admin/`

Once logged in as an admin, use **Manage Users** in the navbar to create
technician accounts for everyone else — no command line needed after the
first superuser.

## Project Structure

```
truck_alignment_tracker/
├── manage.py
├── requirements.txt
├── truck_alignment_tracker/      # Project settings, urls, wsgi/asgi
└── alignments/                   # App: models, views, forms, admin, templates, static
    ├── models.py                 # Alignment model
    ├── admin.py
    ├── forms.py                  # AlignmentForm, ReportFilterForm
    ├── views.py                  # dashboard, add/edit/delete, reports, exports
    ├── urls.py
    ├── migrations/
    ├── templates/alignments/     # base.html, dashboard.html, add_alignment.html,
    │                              # reports.html, alignment_confirm_delete.html
    └── static/alignments/
        ├── css/style.css
        └── js/
```

## Notes

- `DEBUG` defaults to `True` locally; set `DEBUG=False` via environment
  variable in production (Render does this automatically, see below).
- `SECRET_KEY` reads from the `SECRET_KEY` environment variable; falls back
  to a placeholder for local development only.
- The database uses `DATABASE_URL` if set (Postgres in production), and
  falls back to local SQLite otherwise.
- Mileage is validated server-side to require a positive number.

## Database: Neon PostgreSQL (free, doesn't expire)

This project uses **Neon** for its database rather than Render's own
built-in Postgres. Render's free Postgres expires 30 days after creation;
Neon's free tier is a permanent (non-trial) plan, so your fleet alignment
records won't be at risk of being deleted.

### 1. Create the Neon database

1. Go to [neon.tech](https://neon.tech) and sign up (no credit card needed).
2. Click **Create a project**. Name it something like `truck-alignment-tracker`.
3. Once created, Neon shows a **connection string** that looks like:
   ```
   postgresql://username:password@ep-xxxx-xxxx.region.aws.neon.tech/dbname?sslmode=require
   ```
4. Copy that full string — you'll paste it into Render in the next step.

### 2. Deploy to Render

1. Push this project to GitHub (see below if you haven't yet).
2. In the Render dashboard, click **New +** → **Blueprint**.
3. Connect your repository. Render reads `render.yaml` and sets up a
   **web service** running `gunicorn`, with `SECRET_KEY` auto-generated.
   It will also prompt you for a `DATABASE_URL` value — this is where you
   paste the Neon connection string you copied above.
4. Click **Apply**. Render builds and deploys automatically — the build
   step (`build.sh`) installs dependencies, collects static files, and
   runs migrations against your Neon database (which also seeds the
   51-truck fleet).
5. Once deployed, open the **Shell** tab for your service on Render and run:
   ```bash
   python manage.py createsuperuser
   ```
   to create your first admin login.
6. Visit `https://<your-app-name>.onrender.com/login/` and sign in.

If you ever need to find or reset your `DATABASE_URL` on Render afterward:
your service's **Environment** tab → edit the `DATABASE_URL` variable.

### Manual web service (alternative to Blueprint)

1. Push this project to GitHub.
2. In Render: **New +** → **Web Service** → connect your repo.
3. Set:
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn truck_alignment_tracker.wsgi:application`
4. Add these environment variables on the web service:
   - `DATABASE_URL` — your Neon connection string from step 1 above
   - `SECRET_KEY` — any long random string
   - `DEBUG` — `False`
   - `PYTHON_VERSION` — `3.12.0` (or your preferred 3.10+ version)
5. Deploy, then use the **Shell** tab to run `python manage.py createsuperuser`.

### Notes on the free setup

- Render's free web service **spins down after ~15 minutes of inactivity**
  and takes ~30–60 seconds to wake up on the next request — normal for a
  low-traffic internal tool, and doesn't put your data at risk since the
  app itself holds no data (it's all in Neon).
- Neon's free tier gives **0.5 GB storage and 100 compute-hours a month**,
  with the database scaling to zero when idle (a ~300–500ms delay on the
  first query after idle time) — plenty for this app's usage. It does
  **not** expire.
- Uploaded/generated files (like exported reports) are not persisted on
  disk on Render's free tier. This app doesn't need that — exports stream
  directly to the browser rather than being saved server-side.
- If usage grows significantly (many technicians, heavy daily use), revisit
  both Render's and Neon's paid tiers — but for a single-fleet internal
  tool like this, the free combination should hold up well.
