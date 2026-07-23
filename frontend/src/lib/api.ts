import { RenderedDocument } from "@/lib/documentTypes";
import { getToken } from "@/lib/session";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AuthResponse {
  user_id: number;
  email: string;
  token: string;
}

export interface ChatResponse {
  reply: string;
  document_type: string | null;
  fields: Record<string, string>;
}

export interface DraftResponse {
  id: number;
  document_type: string | null;
  fields: Record<string, string>;
  messages: ChatMessage[];
}

export interface DraftSummary {
  id: number;
  document_type: string | null;
  title: string;
  updated_at: string;
  is_complete: boolean;
}

function authHeaders(): HeadersInit {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function parseOrThrow<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function signup(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch("/api/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return parseOrThrow<AuthResponse>(response);
}

export async function login(email: string, password: string): Promise<AuthResponse> {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return parseOrThrow<AuthResponse>(response);
}

export async function listDocuments(): Promise<DraftSummary[]> {
  const response = await fetch("/api/documents", { headers: authHeaders() });
  return parseOrThrow<DraftSummary[]>(response);
}

export async function createDocument(): Promise<DraftResponse> {
  const response = await fetch("/api/documents", { method: "POST", headers: authHeaders() });
  return parseOrThrow<DraftResponse>(response);
}

export async function getDraft(draftId: number): Promise<DraftResponse> {
  const response = await fetch(`/api/documents/${draftId}`, { headers: authHeaders() });
  return parseOrThrow<DraftResponse>(response);
}

export async function sendChatMessage(draftId: number, message: string): Promise<ChatResponse> {
  const response = await fetch(`/api/documents/${draftId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify({ message }),
  });
  return parseOrThrow<ChatResponse>(response);
}

export async function getRenderedDraft(draftId: number): Promise<RenderedDocument> {
  const response = await fetch(`/api/documents/${draftId}/render`, { headers: authHeaders() });
  if (response.status === 409) {
    throw new Error("Document type not chosen yet");
  }
  return parseOrThrow<RenderedDocument>(response);
}
