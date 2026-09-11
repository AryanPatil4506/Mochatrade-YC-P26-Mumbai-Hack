import { AGENT_BASE, request } from "./client";
import type { CreateSessionResponse, SessionSnapshot, SimulateCompromiseResult } from "../types/api";

export function createSession(agent_id: string): Promise<CreateSessionResponse> {
  return request(AGENT_BASE, "/v1/agent/sessions", {
    method: "POST",
    body: JSON.stringify({ agent_id }),
  });
}

export function sendMessage(session_id: string, user_request: string): Promise<{ accepted: boolean; session_id: string }> {
  return request(AGENT_BASE, "/v1/agent/messages", {
    method: "POST",
    body: JSON.stringify({ session_id, user_request }),
  });
}

export function getSession(session_id: string): Promise<SessionSnapshot> {
  return request(AGENT_BASE, `/v1/agent/sessions/${session_id}`);
}

export function simulateCompromise(): Promise<SimulateCompromiseResult> {
  return request(AGENT_BASE, "/v1/agent/simulate-compromise", { method: "POST" });
}

export function sessionEventsUrl(session_id: string): string {
  return `${AGENT_BASE}/v1/agent/sessions/${session_id}/events`;
}
