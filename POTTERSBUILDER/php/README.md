# POTTERSBUILDER — PHP frontend

This folder contains a minimal PHP frontend that posts user queries to the local POTTERSBUILDER Python API (`/query`) and displays retrieved contexts and (optionally) synthesized answers.

Requirements
- A running POTTERSBUILDER API (FastAPI) on `http://127.0.0.1:8000` (or set `PB_API_URL` to the API URL).
- PHP (7.4+) with cURL enabled.

Quick start (PowerShell)

1) Start the Python API (in another shell):
```powershell
uvicorn src.api:app --reload --port 8000
```

2) Serve the PHP frontend with PHP's built-in server:
```powershell
cd php
php -S 127.0.0.1:8080
# open http://127.0.0.1:8080 in your browser
```

3) (Optional) If your API is on another host/port, set `PB_API_URL` in the environment or edit `config.php`.

Notes
- The PHP frontend is intentionally lightweight and delegates all retrieval/synthesis to the Python API. This keeps PHP simple and avoids cross-language dependency issues.
