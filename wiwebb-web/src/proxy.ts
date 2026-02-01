import { NextResponse, type NextRequest } from 'next/server'
import acceptLanguage from 'accept-language'
import { fallbackLng, languages, cookieName, headerName } from './app/[lng]/i18n/settings'

acceptLanguage.languages([...languages])

export const config = {
  // Avoid matching for static files, API routes, etc.
  matcher: ['/((?!api|_next/static|_next/image|assets|favicon.ico|sw.js|site.webmanifest).*)']
}

/**
 * Validates that a language code is supported
 * @param lng - Language code to validate
 * @returns The language code if valid, undefined otherwise
 */
function validateLanguage(lng: string | null | undefined): string | undefined {
  if (!lng) return undefined
  // Ensure the language is in our supported languages list
  return (languages as readonly string[]).includes(lng) ? lng : undefined
}

export default function proxy(req: NextRequest) {
  // Ignore paths with "icon" or "chrome"
  if (req.nextUrl.pathname.indexOf('icon') > -1 || req.nextUrl.pathname.indexOf('chrome') > -1) {
    return NextResponse.next()
  }

  let lng: string | undefined

  // Detection order matches client: path, cookie, header
  // 1. Try to get language from URL path first (highest priority)
  const lngInPath = languages.find((loc) => req.nextUrl.pathname.startsWith(`/${loc}`))
  if (lngInPath) {
    lng = lngInPath
  }

  // 2. Try to get language from cookie (validated)
  if (!lng && req.cookies.has(cookieName)) {
    const cookieValue = req.cookies.get(cookieName)?.value
    lng = validateLanguage(cookieValue)
  }

  // 3. Check the Accept-Language header
  if (!lng) {
    const acceptLangHeader = req.headers.get('Accept-Language')
    const parsedLang = acceptLanguage.get(acceptLangHeader ?? undefined) ?? undefined
    lng = validateLanguage(parsedLang)
  }

  // 4. Default to fallback language if still undefined
  if (!lng) {
    lng = fallbackLng
  }

  const headers = new Headers(req.headers)
  headers.set(headerName, lng)

  // If the language is not in the path, redirect to include it
  if (
    !lngInPath &&
    !req.nextUrl.pathname.startsWith('/_next')
  ) {
    return NextResponse.redirect(
      new URL(`/${lng}${req.nextUrl.pathname}${req.nextUrl.search}`, req.url)
    )
  }

  // If a referer exists, try to detect the language from there and set the cookie accordingly
  if (req.headers.has('referer')) {
    const refererUrl = new URL(req.headers.get('referer')!)
    const lngInReferer = languages.find((l) => refererUrl.pathname.startsWith(`/${l}`))
    const response = NextResponse.next({ headers })
    // Only set cookie if the language is valid and supported
    if (lngInReferer && validateLanguage(lngInReferer)) {
      response.cookies.set(cookieName, lngInReferer, {
        sameSite: 'lax',
        secure: process.env.NODE_ENV === 'production',
        maxAge: 60 * 60 * 24 * 365, // 1 year
      })
    }
    return response
  }

  return NextResponse.next({ headers })
}