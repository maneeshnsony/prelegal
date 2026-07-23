export const USER_ID_KEY = "prelegal_user_id";

export function getUserId(): number | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(USER_ID_KEY);
  if (!raw) return null;
  const id = Number(raw);
  return Number.isFinite(id) ? id : null;
}

export function setUserId(id: number): void {
  window.localStorage.setItem(USER_ID_KEY, String(id));
}

export function clearSession(): void {
  window.localStorage.removeItem(USER_ID_KEY);
}
