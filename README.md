# NEXUS — Data Intelligence Platform

**Version:** 1.0.0  
**Tagline:** Your Data. Your Insights. Your Decisions.

NEXUS is a Python data-analysis application built around reusable engines for dataset loading, inspection, cleaning, analytics, visualizations, and PDF reporting.

## Project structure

```text
NEXUS/
├── app.py
├── controller.py
├── engines/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── data_inspector.py
│   ├── data_cleaner.py
│   ├── analytics.py
│   ├── visualization.py
│   └── report_engine.py
├── tests/
│   └── test_api.py
├── templates/
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── uploads/
├── reports/
├── requirements.txt
└── README.md
```

## Setup (Windows / VS Code)

1. Install Python 3.11 or newer.
2. Open this folder in VS Code.
3. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .venv\Scripts\activate
   ```

4. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Run the API:

   ```powershell
   python app.py
   ```

6. Check `http://127.0.0.1:5000/api/health`.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Backend health |
| GET | `/api/status` | Pipeline state |
| POST | `/api/upload` | Upload CSV or Excel (`file` form field) |
| POST | `/api/inspect` | Inspect the active dataset |
| POST | `/api/clean` | Clean the active dataset |
| POST | `/api/analyze` | Generate analytics |
| POST | `/api/visualizations` | Generate Plotly charts |
| POST | `/api/report` | Generate a PDF report |
| GET | `/api/reports/<filename>` | Download a generated PDF |

### Cleaning request example

The API expects operations in this form:

```json
{
  "operations": [
    {
      "name": "remove_duplicates",
      "parameters": {}
    },
    {
      "name": "trim_whitespace",
      "parameters": {
        "columns": ["Name", "Department"]
      }
    }
  ]
}
```

Available operation names are `remove_duplicates`, `handle_missing_values`, `convert_data_types`, and `trim_whitespace`. Each operation's `parameters` must match the corresponding engine method arguments.

## Run tests

```powershell
python -m unittest discover -s tests -v
```

## Important limitations

- This is a development-stage application, not a production deployment.
- The current controller holds one active dataset in process memory; it is not multi-user or multi-tenant.
- Authentication, authorization, persistent project storage, database-backed job tracking, CSRF protection, rate limiting, and production server configuration are not implemented.
- Uploaded files are stored locally. Add retention and cleanup policies before deployment.
- The Flask development server is for local development only.
- The existing PDF engine creates tabular reports; it does not yet embed the interactive Plotly charts.
- Review data-cleaning choices before using them on important source data.


## User accounts (authentication stage)

NEXUS now requires an account before the dashboard and dataset API can be used.
On first launch, open the app and choose **Create an account**. Register with your
name, email address and a password of at least 8 characters. Passwords are stored
as Werkzeug password hashes in the local SQLite database `nexus_users.db`; plain
text passwords are not stored. The Flask session uses a persistent local secret
in `.nexus_secret_key` (both local files are excluded from Git by `.gitignore`).

To sign out, use the account menu in the dashboard. Account settings currently
show the signed-in name and email; password change and recovery are not included
in this stage. For deployment beyond local development, configure a strong
`NEXUS_SECRET_KEY`, enable HTTPS (`NEXUS_HTTPS=1`), and use a production WSGI
server. The built-in Flask development server is for local testing only.
