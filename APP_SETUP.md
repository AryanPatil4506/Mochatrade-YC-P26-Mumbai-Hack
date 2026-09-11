# Sentinel AI — Setup & Run Guide

## 1. Overview & Architecture

Sentinel AI is an AI Agent Governance Platform consisting of:
1. **Python/FastAPI Microservices** (Port 8001, 8002, 8003)
2. **Flutter Mobile App** (`sentinel_ai/`)

```
[ Flutter Mobile App ]
      │
      ├── :8001 ── Agent Service   (Sessions, Chat, SSE transcript)
      ├── :8002 ── Gateway Service (Evaluation, Approvals Queue, Policies)
      └── :8003 ── Executor Service(Action Execution, Audit Logs, Attack Labs, Global SSE)
```

---

## 2. Prerequisites

- **Python**: 3.11+ (Detected: Python 3.13)
- **Flutter SDK**: 3.24+ (Installed at: `C:\Users\asaad\developement\flutter\bin`)
- **Android Studio / Emulator** or a physical Android/iOS device.

> **Tip (Windows PATH):** Add `C:\Users\asaad\developement\flutter\bin` to your User Environment `PATH` so `flutter` works in any terminal.

---

## 3. Backend Setup & Start

### Step 3.1: Install Python Dependencies
Open PowerShell/Command Prompt at repository root (`Hackathon/`):
```powershell
python -m pip install -e .
python -m pip install -r requirements.txt # if available
```
Or directly install core dependencies:
```powershell
pip install "fastapi>=0.110.0" "uvicorn[standard]>=0.28.0" "httpx>=0.27.0" "pydantic>=2" "pyyaml>=6.0" "sse-starlette>=2.0.0" "langgraph" "langchain-core"
```

### Step 3.2: Launch All 3 Microservices
You can launch the services simultaneously using PowerShell from `Hackathon/`:

```powershell
# Terminal 1 - Executor Service (:8003)
python -m uvicorn services.executor.api:app --host 0.0.0.0 --port 8003 --reload

# Terminal 2 - Gateway Service (:8002)
python -m uvicorn services.gateway.api:app --host 0.0.0.0 --port 8002 --reload

# Terminal 3 - Agent Service (:8001)
python -m uvicorn services.agent.api:app --host 0.0.0.0 --port 8001 --reload
```

*Or on Git Bash / WSL:*
```bash
bash scripts/run_all.sh
```

### Verify backend health:
- `http://localhost:8001/health` → `{"status":"ok","service":"agent"}`
- `http://localhost:8002/health` → `{"status":"ok","service":"gateway"}`
- `http://localhost:8003/health` → `{"status":"ok","service":"executor"}`

---

## 4. Flutter Mobile App Setup

Navigate to the Flutter directory:
```powershell
cd sentinel_ai
```

### Step 4.1: Install Flutter Packages
```powershell
& "C:\Users\asaad\developement\flutter\bin\flutter.bat" pub get
```

### Step 4.2: Configuring Backend URLs
The app uses `--dart-define` to configure the base URLs (defined in `lib/core/config/app_config.dart`):

| Target | Agent URL (:8001) | Gateway URL (:8002) | Executor URL (:8003) |
|---|---|---|---|
| **Android Emulator** (Default) | `http://10.0.2.2:8001` | `http://10.0.2.2:8002` | `http://10.0.2.2:8003` |
| **Physical Device / LAN** | `http://<YOUR_LAN_IP>:8001` | `http://<YOUR_LAN_IP>:8002` | `http://<YOUR_LAN_IP>:8003` |
| **iOS Simulator** | `http://127.0.0.1:8001` | `http://127.0.0.1:8002` | `http://127.0.0.1:8003` |

---

## 5. Running the App

### Option A: Android Emulator
Android emulator maps `10.0.2.2` to the host machine's `localhost`.
```powershell
& "C:\Users\asaad\developement\flutter\bin\flutter.bat" run
```

### Option B: Physical Device
Find your local IP (run `ipconfig` on Windows, e.g. `192.168.1.50`), and run:
```powershell
& "C:\Users\asaad\developement\flutter\bin\flutter.bat" run `
  --dart-define=AGENT_URL=http://192.168.1.50:8001 `
  --dart-define=GATEWAY_URL=http://192.168.1.50:8002 `
  --dart-define=EXECUTOR_URL=http://192.168.1.50:8003
```

---

## 6. Common Troubleshooting & Debugging

1. **`flutter` command not found:**
   - Flutter SDK is installed at `C:\Users\asaad\developement\flutter\bin`. Add this path to your Windows Environment System/User `Path` variable and restart your terminal.

2. **Connection Refused (`SocketException`) on Android Emulator:**
   - Ensure you use `10.0.2.2` instead of `localhost` or `127.0.0.1`.
   - Ensure the uvicorn processes are bound to `--host 0.0.0.0`.

3. **Connection Refused on Physical Device:**
   - Both phone and PC must be on the same Wi-Fi network.
   - Windows Defender Firewall might block ports 8001-8003. Add an inbound rule allowing Python/ports 8001, 8002, 8003.

4. **SSE stream dropped / Reconnecting:**
   - The app's `SseClient` has automatic backoff reconnection every 3 seconds (`AppConfig.sseReconnectDelay`).
   - Check if backend service :8003 (`/v1/events`) or :8001 (`/v1/agent/sessions/{id}/events`) is alive.
