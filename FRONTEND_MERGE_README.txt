NEXUS — MERGED PROJECT

This folder combines the original NEXUS Python backend with the dashboard frontend.

IMPORTANT:
- Keep this entire NEXUS folder together.
- Existing engines/, controller.py, tests/, requirements.txt, uploads/, and reports/ are preserved.
- app.py is the frontend-enabled Flask app and includes GET /.
- templates/index.html, static/css/style.css, and static/js/app.js are installed in the correct locations.

RUN:
1. Open this NEXUS folder in VS Code (File > Open Folder).
2. Activate your virtual environment.
3. Install dependencies if needed: pip install -r requirements.txt
4. Start: python app.py
5. Visit: http://127.0.0.1:5000/

Do not copy the nested package folder into this project. This is already the merged layout.
