# NEXUS Frontend Foundation — Stage 1

## Included
- Official clean light theme (white workspace, light-grey sidebar, blue accents).
- Existing seven dashboard views and backend API integration preserved.
- Responsive navigation and dashboard layout.
- Notification bell at the top-right, immediately left of the account profile.
- Notification dropdown with unread indicator, event list, and mark-all-as-read.
- Account-profile dropdown placeholder.
- Light-theme Plotly chart text and surfaces.

## Important scope note
This stage establishes the dashboard shell and its client-side notification interface. Notifications currently live in browser memory for the active page session; they are not yet persisted in a database. The account menu is a UI placeholder. Login, registration, password hashing, sessions, authorization, and protected API routes are a separate authentication stage and must be completed before exposing NEXUS to users or deploying it publicly.

## Run
From the NEXUS project directory:

```bash
python -m venv .venv
# Windows PowerShell
.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open the local URL printed by Flask (normally http://127.0.0.1:5000).

## Stage 1 checks performed
- JavaScript syntax check: passed (`node --check static/js/app.js`).
- Python compile check: passed (`python -m compileall`).
- HTML parse check: passed.
- Duplicate HTML ID check: passed.
- Required dashboard, notification and profile control IDs: passed.

The existing backend pytest suite could not be rerun in this packaging environment because Flask is not installed here. Install the project's `requirements.txt` in the local virtual environment, then run `python -m pytest -q`.
