# Committing to `mochatrade/frontend` & Running Sentinel Locally

## 1. Commit the current changes to `frontend` and push

You're currently on `desktop_application` with the Groq-migration + CLAUDE.md
cleanup changes uncommitted. The `mochatrade` remote already has a
`frontend` branch (`remotes/mochatrade/frontend`), so create a local branch
tracking it, commit there, and push.

```bash
# 1. Create a local branch named "frontend" tracking mochatrade/frontend
git checkout -b frontend mochatrade/frontend

# 2. Bring your uncommitted changes across (they're currently sitting in the
#    working tree on desktop_application, and git carries uncommitted
#    changes with you across a checkout as long as nothing conflicts)
#    -> If step 1 complains about local changes blocking the checkout, stash
#       first: `git stash`, run step 1, then `git stash pop`.

# 3. Stage everything
git add -A

# 4. Review what's staged before committing
git status
git diff --cached --stat

# 5. Commit
git commit -m "Switch agent LLM proposal calls to Groq; remove CLAUDE.md
references from in-code comments

- services/agent/llm/client.py now targets Groq's OpenAI-compatible API
  (GROQ_API_KEY, GROQ_MODEL default qwen/qwen3.8-27b, GROQ_BASE_URL)
- Added python-dotenv support: all three services load .env at startup
- Added .env.example documenting the Groq env vars
- Rewrote ~30 code comments/docstrings that referenced CLAUDE.md so they
  read standalone; CLAUDE.md itself is unchanged"

# 6. Push to the frontend branch on mochatrade
git push mochatrade frontend
```

If `mochatrade/frontend` has moved since you branched (someone else pushed),
`git push` will reject with a non-fast-forward error — run `git pull
--rebase mochatrade frontend` first, resolve anything that conflicts, then
push again.

### If you'd rather not create a new local branch

You can instead commit directly on your current branch and push it to the
remote's `frontend` branch:

```bash
git add -A
git commit -m "..."
git push mochatrade desktop_application:frontend
```

---

## 2. Set up your environment (one-time)

```bash
# Python deps
pip install -e ".[dev]"
python -m spacy download en_core_web_sm

# Frontend deps
cd apps/dashboard
npm install
cd ../..
```

Create `.env` at the repo root (copy `.env.example`) and fill in your Groq
key:

```
GROQ_API_KEY=gsk_...
```

`.env` is gitignored — it never gets committed.

---

## 3. Start the backend services

```bash
./scripts/run_all.sh
```

This launches all three FastAPI services with hot-reload:

| Service | Port | Purpose |
|---|---|---|
| Agent | 8001 | LangGraph agent, sessions/messages, SSE |
| Gateway | 8002 | Detection + decision engine, approvals, policy |
| Executor | 8003 | Capability-token verification, tool execution, audit |

Ctrl-C stops all three. Confirm they're up:

```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

(Windows/PowerShell: `run_all.sh` is a bash script — run it via Git Bash, or
start each service manually in three terminals:

```powershell
python -m uvicorn services.executor.api:app --port 8003 --reload
python -m uvicorn services.gateway.api:app --port 8002 --reload
python -m uvicorn services.agent.api:app --port 8001 --reload
```
)

---

## 4. Start the frontend dashboard

```bash
cd apps/dashboard
npm run dev
```

Vite will print the local URL (typically `http://localhost:5173`). The
dashboard talks to the gateway/executor over the SSE endpoints described in
`CLAUDE.md`, so the backend services must already be running.

---

## 5. Run the test suite

```bash
pytest -q
```

Should show `61 passed` (as of this branch). No `GROQ_API_KEY` is required
for tests — `services/agent/llm/client.py` falls back to a deterministic
offline stub when the key is unset, which is what the test suite exercises.

---

## 6. Try the attack simulation lab

With all three services running:

```bash
curl -X POST http://localhost:8003/v1/lab/run/prompt_injection
curl -X POST http://localhost:8003/v1/lab/run/privilege_abuse
curl -X POST http://localhost:8003/v1/lab/run/destructive_sql
curl -X POST http://localhost:8003/v1/lab/run/data_exfiltration
```

Each sends a crafted `ProposedAction` through the real gateway → executor
pipeline (no shortcuts) and returns the decision + execution outcome.
