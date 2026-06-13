import { type NextRequest, NextResponse } from "next/server"

const PUBLIC_PATHS = ["/", "/pricing", "/login", "/signup"]
const AUTH_API = process.env.NEXT_PUBLIC_FINGRAPH_API_URL || "http://localhost:8000"

function getAccessToken(request: NextRequest): string | null {
  const fromCookie = request.cookies.get("fingraph_access_token")
  if (fromCookie) return fromCookie.value
  const authHeader = request.headers.get("Authorization")
  if (authHeader?.startsWith("Bearer ")) return authHeader.slice(7)
  return null
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  const isPublic = PUBLIC_PATHS.some((p) => pathname === p || pathname.startsWith("/auth/"))
  const isStatic =
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    pathname.endsWith(".svg") ||
    pathname.endsWith(".png") ||
    pathname.endsWith(".jpg")

  if (isStatic || isPublic) {
    return NextResponse.next({ request })
  }

  const token = getAccessToken(request)

  if (!token) {
    const url = request.nextUrl.clone()
    url.pathname = "/login"
    url.searchParams.set("callback", pathname)
    return NextResponse.redirect(url)
  }

  try {
    const res = await fetch(`${AUTH_API}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      signal: AbortSignal.timeout(5000),
    })
    if (!res.ok) {
      const url = request.nextUrl.clone()
      url.pathname = "/login"
      url.searchParams.set("callback", pathname)
      const response = NextResponse.redirect(url)
      response.cookies.delete("fingraph_access_token")
      response.cookies.delete("fingraph_refresh_token")
      return response
    }
  } catch {
    // If backend is unreachable, let the request through
    // The client-side auth will handle the redirect
  }

  return NextResponse.next({ request })
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
}
