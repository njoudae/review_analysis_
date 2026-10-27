import { createHash, timingSafeEqual } from "node:crypto";
import { headers } from "next/headers";

const username = process.env.DASHBOARD_USER;
const password = process.env.DASHBOARD_PASSWORD;

export function isDashboardAuthConfigured() {
  return Boolean(username && password);
}

function safeEqual(left: string, right: string) {
  const leftHash = createHash("sha256").update(left).digest();
  const rightHash = createHash("sha256").update(right).digest();
  return timingSafeEqual(leftHash, rightHash);
}

export function isDashboardRequestAuthorized(authorization: string | null) {
  if (!isDashboardAuthConfigured()) {
    return process.env.NODE_ENV !== "production";
  }
  if (!authorization?.startsWith("Basic ")) return false;

  try {
    const decoded = Buffer.from(authorization.slice(6), "base64").toString("utf8");
    const separator = decoded.indexOf(":");
    if (separator < 0) return false;
    return safeEqual(decoded.slice(0, separator), username!) && safeEqual(decoded.slice(separator + 1), password!);
  } catch {
    return false;
  }
}

export async function requireDashboardAuth() {
  const requestHeaders = await headers();
  if (!isDashboardRequestAuthorized(requestHeaders.get("authorization"))) {
    throw new Error("Unauthorized dashboard request");
  }
}
