import Keycloak from "keycloak-js";

// Local/dev-only bypass - never enable when Keycloak is meant to be enforced.
export const AUTH_DISABLED = import.meta.env.VITE_AUTH_DISABLED === "true";

export const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL || "http://localhost:8081",
  realm: import.meta.env.VITE_KEYCLOAK_REALM || "rulescope",
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID || "rulescope-frontend",
});

export async function initKeycloak(): Promise<void> {
  if (AUTH_DISABLED) return;
  try {
    await keycloak.init({ onLoad: "login-required", pkceMethod: "S256" });
    // Keep the token fresh in the background.
    setInterval(() => {
      keycloak.updateToken(60).catch(() => keycloak.login());
    }, 30000);
  } catch {
    // If Keycloak is unreachable, let the app render its own error state.
  }
}

export function hasRole(role: string): boolean {
  if (AUTH_DISABLED) return true;
  return keycloak.hasRealmRole(role);
}

export function currentUsername(): string {
  if (AUTH_DISABLED) return "local-dev";
  return keycloak.tokenParsed?.preferred_username ?? "unknown";
}

export function logout(): void {
  if (AUTH_DISABLED) return;
  keycloak.logout();
}
