import { NextRequest, NextResponse } from "next/server";
import { isDashboardAuthConfigured, isDashboardRequestAuthorized } from "@/lib/dashboard-auth";

export function proxy(request: NextRequest) {
  if (process.env.NODE_ENV === "production" && !isDashboardAuthConfigured()) {
    return NextResponse.json(
      { error: "Dashboard authentication is not configured" },
      { status: 503 },
    );
  }

  if (!isDashboardRequestAuthorized(request.headers.get("authorization"))) {
    return new NextResponse("Authentication required", {
      status: 401,
      headers: { "WWW-Authenticate": 'Basic realm="CX Intelligence", charset="UTF-8"' },
    });
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
