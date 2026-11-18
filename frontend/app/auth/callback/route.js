import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET(request) {
  const requestUrl = new URL(request.url);
  const code = requestUrl.searchParams.get("code");
  const next = requestUrl.searchParams.get("next");
  const oauthError = requestUrl.searchParams.get("error");
  const errorDescription = requestUrl.searchParams.get("error_description");

  const forwardedHost = request.headers.get("x-forwarded-host");
  const forwardedProto = request.headers.get("x-forwarded-proto") || "https";
  const origin = forwardedHost
    ? `${forwardedProto}://${forwardedHost}`
    : requestUrl.origin;

  const destination =
    next && next.startsWith("/") && !next.startsWith("//")
      ? next
      : "/dashboard";

  if (oauthError) {
    const message = errorDescription || oauthError;
    return NextResponse.redirect(
      new URL(`/login?error=${encodeURIComponent(message)}`, origin)
    );
  }

  if (code) {
    try {
      const supabase = await createClient();
      const { error } = await supabase.auth.exchangeCodeForSession(code);

      if (!error) {
        return NextResponse.redirect(new URL(destination, origin));
      } else {
        console.error("OAuth code exchange error:", error.message);
        return NextResponse.redirect(
          new URL(`/login?error=${encodeURIComponent(error.message)}`, origin)
        );
      }
    } catch (err) {
      console.error("OAuth callback exception:", err);
      return NextResponse.redirect(
        new URL("/login?error=authentication_failed", origin)
      );
    }
  }

  return NextResponse.redirect(
    new URL("/login?error=no_authorization_code", origin)
  );
}
