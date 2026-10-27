import { isDashboardRequestAuthorized } from "@/lib/dashboard-auth";

const baseUrl = process.env.BACKEND_URL ?? "http://127.0.0.1:8000/api/v1";

async function proxyRequest(request: Request, context: { params: Promise<{ path: string[] }> }) {
  if (!isDashboardRequestAuthorized(request.headers.get("authorization"))) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }
  const { path } = await context.params;
  const sourceUrl = new URL(request.url);
  const target = `${baseUrl}/${path.join("/")}${sourceUrl.search}`;
  const body = ["GET", "HEAD"].includes(request.method) ? undefined : await request.text();
  const response = await fetch(target, {
    method: request.method,
    body,
    headers: { "Content-Type": request.headers.get("content-type") ?? "application/json", "X-API-Key": process.env.APP_API_KEY ?? "" },
    cache: "no-store",
  });
  return new Response(response.body, { status: response.status, headers: { "Content-Type": response.headers.get("content-type") ?? "application/json" } });
}

export const GET = proxyRequest;
export const POST = proxyRequest;
export const PATCH = proxyRequest;
export const PUT = proxyRequest;
export const DELETE = proxyRequest;
