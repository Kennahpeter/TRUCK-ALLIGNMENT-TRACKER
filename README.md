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

## Deploying to Render

This project is ready to deploy to [Render](https://render.com) as-is —
it includes `render.yaml`, `build.sh`, and production-ready settings
(Postgres support, WhiteNoise for static files, Gunicorn as the app server).

### Option A — Blueprint (one click, recommended)

1. Push this project to a GitHub (or GitLab) repository.
2. In the Render dashboard, click **New +** → **Blueprint**.
3. Connect your repository. Render will detect `render.yaml` and set up:
   - A **free PostgreSQL database**
   - A **web service** running `gunicorn`, with `SECRET_KEY` auto-generated
     and `DATABASE_URL` wired to the database automatically.
4. Click **Apply** — Render will build and deploy automatically. The build
   step (`build.sh`) installs dependencies, collects static files, and
   runs migrations (which also seeds the 51-truck fleet).
5. Once deployed, open the **Shell** tab for your service on Render and run:
   ```bash
   python manage.py createsuperuser
   ```
   to create your first admin login.
6. Visit `https://<your-app-name>.onrender.com/login/` and sign in.

### Option B — Manual web service

1. Push this project to GitHub.
2. In Render: **New +** → **Web Service** → connect your repo.
3. Set:
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn truck_alignment_tracker.wsgi:application`
4. Add a **PostgreSQL** database (New + → PostgreSQL), then copy its
   **Internal Database URL** into your web service's environment variables
   as `DATABASE_URL`.
5. Add these environment variables on the web service:
   - `SECRET_KEY` — any long random string
   - `DEBUG` — `False`
   - `PYTHON_VERSION` — `3.12.0` (or your preferred 3.10+ version)
6. Deploy, then use the **Shell** tab to run `python manage.py createsuperuser`.

### Notes on Render's free tier

- Free web services **spin down after inactivity** and take ~30–60 seconds
  to wake up on the next request — normal for a low-traffic internal tool.
- Free Postgres databases on Render **expire after 90 days** unless
  upgraded to a paid plan; export your data or upgrade before then if this
  is used for real fleet records.
- Uploaded/generated files (like exported reports) are not persisted
  across deploys on Render's free tier, since it doesn't have a persistent
  disk. This app doesn't write files to disk at runtime (exports stream
  directly to the browser), so this isn't an issue for the current features.
