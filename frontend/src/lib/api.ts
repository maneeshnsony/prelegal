import { RenderedDocument } from "@/lib/documentTypes";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface LoginResponse {
  user_id: number;
  email: string;
}

export interface ChatResponse {
  reply: string;
  document_type: string | null;
  fields: Record<string, string>;
}

export interface DraftResponse {
  document_type: string | null;
  fields: Record<string, string>;
  messages: ChatMessage[];
}

async function parseOrThrow<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function login(email: string): Promise<LoginResponse> {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  return parseOrThrow<LoginResponse>(response);
}

export async function getDraft(userId: number): Promise<DraftResponse> {
  const response = await fetch(`/api/documents/draft?user_id=${userId}`);
  return parseOrThrow<DraftResponse>(response);
}

export async function sendChatMessage(userId: number, message: string): Promise<ChatResponse> {
  const response = await fetch("/api/documents/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, message }),
  });
  return parseOrThrow<ChatResponse>(response);
}

export async function getRenderedDraft(userId: number): Promise<RenderedDocument> {
  const response = await fetch(`/api/documents/draft/render?user_id=${userId}`);
  if (response.status === 409) {
    throw new Error("Document type not chosen yet");
  }
  return parseOrThrow<RenderedDocument>(response);
}
