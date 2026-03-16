BOBBIE Web (Node + React)

This directory contains a minimal Express backend and a Vite+React frontend that can replace the Streamlit UI.

Quick start (from the repo root):

1. Install server deps

```bash
cd web/server
npm install
```

2. Install client deps

```bash
cd ../client
npm install
```

3. Start the backend (default port 3001)

```bash
cd ../server
npm start
```

4. Start the frontend (default Vite port 5173)

```bash
cd ../client
npm run dev
```

The React dev server proxies `/api/*` to the backend.

Notes:
- The backend endpoint `/api/run` spawns the project's Python runner using `./.venv/bin/python run_assessment.py`. Ensure the virtualenv is present and active or available at that path.
- Artifacts are read from `artifacts/final_run` and the run log is written to `artifacts/final_run/web_run.log`.
