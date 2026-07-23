import { NdaFormData } from "@/lib/ndaTemplate";

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
  fields: NdaFormData;
}

export interface DraftResponse {
  fields: NdaFormData;
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
  const response = await fetch(`/api/nda/draft?user_id=${userId}`);
  return parseOrThrow<DraftResponse>(response);
}

export async function sendChatMessage(
  userId: number,
  message: string
): Promise<ChatResponse> {
  const response = await fetch("/api/nda/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, message }),
  });
  return parseOrThrow<ChatResponse>(response);
}
