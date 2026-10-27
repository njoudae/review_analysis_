import type { Organization } from "./types";
import { requireDashboardAuth } from "./dashboard-auth";

const baseUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000/api/v1";
const apiKey = process.env.APP_API_KEY ?? "change-me-in-production";

export async function backendFetch<T>(path: string, init?: RequestInit): Promise<T> {
  await requireDashboardAuth();
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": apiKey,
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    const message = await response.text();
    throw new Error(`Backend ${response.status}: ${message}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export async function getOrganization(): Promise<Organization | null> {
  const organizations = await backendFetch<Organization[]>("/organizations");
  const preferred = process.env.DEFAULT_ORGANIZATION_ID;
  return organizations.find((item) => item.id === preferred) ?? organizations[0] ?? null;
}
