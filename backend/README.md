# Sentinel AI Unified Backend

This backend combines the existing Part 3 policy and human-approval gateway with the existing Part 4 sandbox executor, mock tools, attack simulator, and audit layer.

## Run

From the repository root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
$env:PYTHONPATH = "$PWD\backend"
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8008
```

Swagger UI is available at `http://127.0.0.1:8008/docs`.

## APIs

Part 3:

- `POST /api/policy/evaluate`
- `POST /api/policy/evaluate-and-execute`
- `POST /api/policy/execute`
- `/api/approvals/*`

Part 4:

- `GET /part4/health`
- `/part4/execute`
- `/part4/audit/{request_id}`
- `/part4/attacks/*`

The original `Part-3/` and `part4/` folders remain unchanged until the unified backend has been verified.
