export const FAKE_SESSION_KEY = "prelegal_fake_session";

export function hasFakeSession(): boolean {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(FAKE_SESSION_KEY) === "true";
}

export function setFakeSession(): void {
  window.localStorage.setItem(FAKE_SESSION_KEY, "true");
}
