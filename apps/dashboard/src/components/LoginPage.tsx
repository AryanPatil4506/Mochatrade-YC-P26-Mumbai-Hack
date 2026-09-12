import { useState, type FormEvent } from "react";
import { ShieldCheck, Lock, User, AlertCircle } from "lucide-react";

// Demo-only credential gate for the dashboard. This is NOT part of the
// Sentinel security model (see CLAUDE.md — auth/RBAC is explicitly out of
// scope for the engine and API). It's a cosmetic client-side screen so the
// app isn't wide open on a shared demo machine; nothing here influences
// risk_score/decision, and there is no real session/backend auth.
export const DEMO_USERNAME = "admin";
export const DEMO_PASSWORD = "sentinel-demo";

const AUTH_STORAGE_KEY = "sentinel.demo-auth";

export function isAuthenticated(): boolean {
  try {
    return sessionStorage.getItem(AUTH_STORAGE_KEY) === "true";
  } catch {
    return false;
  }
}

function setAuthenticated() {
  try {
    sessionStorage.setItem(AUTH_STORAGE_KEY, "true");
  } catch {
    // sessionStorage unavailable (e.g. private mode) — fall back to
    // in-memory only for this render; App will re-check on reload.
  }
}

export function clearAuthenticated() {
  try {
    sessionStorage.removeItem(AUTH_STORAGE_KEY);
  } catch {
    /* noop */
  }
}

interface Props {
  onSuccess: () => void;
}

export function LoginPage({ onSuccess }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (username === DEMO_USERNAME && password === DEMO_PASSWORD) {
      setError(null);
      setAuthenticated();
      onSuccess();
    } else {
      setError("Invalid credentials. Use the demo login shown below.");
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ground px-4 text-ink">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3 text-center">
          <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-soft text-brand">
            <ShieldCheck size={26} strokeWidth={2.25} />
          </span>
          <div>
            <h1 className="text-lg font-semibold text-ink">Sentinel AI</h1>
            <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-ink-muted">
              Runtime Security Gateway
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="sentinel-card flex flex-col gap-4 p-6">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="username" className="text-xs font-medium text-ink-muted">
              Username
            </label>
            <div className="flex items-center gap-2 rounded-lg border border-border bg-surface-raised px-3 py-2 focus-within:border-brand/60">
              <User size={15} className="shrink-0 text-ink-muted" />
              <input
                id="username"
                autoFocus
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted/60"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="password" className="text-xs font-medium text-ink-muted">
              Password
            </label>
            <div className="flex items-center gap-2 rounded-lg border border-border bg-surface-raised px-3 py-2 focus-within:border-brand/60">
              <Lock size={15} className="shrink-0 text-ink-muted" />
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-ink-muted/60"
              />
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-2 rounded-lg border border-block/30 bg-block/10 px-3 py-2 text-xs text-block">
              <AlertCircle size={14} className="shrink-0" />
              {error}
            </div>
          )}

          <button type="submit" className="sentinel-btn sentinel-btn-primary mt-1 py-2.5 text-sm">
            Sign in
          </button>
        </form>

        <div className="mt-4 rounded-lg border border-border bg-surface/60 px-4 py-3 text-center text-xs text-ink-muted">
          Demo credentials —{" "}
          <span className="font-mono text-ink">{DEMO_USERNAME}</span> /{" "}
          <span className="font-mono text-ink">{DEMO_PASSWORD}</span>
        </div>
      </div>
    </div>
  );
}
