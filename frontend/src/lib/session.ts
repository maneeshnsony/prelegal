const SESSION_KEY = "prelegal_session";

interface Session {
  userId: number;
  email: string;
  token: string;
}

export function getSession(): Session | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

export function getToken(): string | null {
  return getSession()?.token ?? null;
}

export function setSession(userId: number, email: string, token: string): void {
  window.localStorage.setItem(SESSION_KEY, JSON.stringify({ userId, email, token }));
}

export function clearSession(): void {
  window.localStorage.removeItem(SESSION_KEY);
}
