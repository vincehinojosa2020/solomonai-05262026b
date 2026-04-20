/**
 * Security sanitization utilities for Solomon AI frontend.
 * Prevents XSS, open-redirect, and protocol-smuggling attacks
 * flowing through href / src / redirect / mailto / tel / blob sinks.
 *
 * One source of truth — import from here instead of inlining regexes.
 */

/* ------------------------------------------------------------------ */
/*  href — for <a href={...}> and window.location on user-action links */
/* ------------------------------------------------------------------ */

/**
 * Blocks javascript:, data:, vbscript:, file:, and other dangerous protocols.
 * Allows: relative paths (/ or #...), http(s)://, mailto:, tel:.
 */
export function safeHref(url) {
  if (!url || typeof url !== 'string') return '#';
  const trimmed = url.trim();
  const lower = trimmed.toLowerCase();

  // Explicit deny list
  if (
    lower.startsWith('javascript:') ||
    lower.startsWith('data:') ||
    lower.startsWith('vbscript:') ||
    lower.startsWith('file:') ||
    lower.startsWith('blob:')
  ) {
    return '#';
  }

  // Same-origin relative paths
  if (trimmed.startsWith('/') && !trimmed.startsWith('//')) return trimmed;
  if (trimmed.startsWith('#')) return trimmed;

  // Mailto / tel — delegate to their validators so a malicious email can't
  // sneak payloads in via this entry point.
  if (lower.startsWith('mailto:')) return safeMailto(trimmed.slice(7));
  if (lower.startsWith('tel:')) return safeTel(trimmed.slice(4));

  // Explicit http(s) only — anything else is rejected
  try {
    const parsed = new URL(trimmed);
    if (parsed.protocol === 'http:' || parsed.protocol === 'https:') {
      return trimmed;
    }
  } catch {
    /* fallthrough */
  }
  return '#';
}

/* ------------------------------------------------------------------ */
/*  mailto: / tel:                                                     */
/* ------------------------------------------------------------------ */

const EMAIL_RE = /^[^\s@<>"'`]+@[^\s@<>"'`]+\.[^\s@<>"'`]+$/;
const PHONE_RE = /^[+0-9()\- .]{3,}$/;

/**
 * Returns a safe mailto: href or '#' if the email is malformed.
 * Uses encodeURIComponent on the local@domain to prevent header injection.
 */
export function safeMailto(email) {
  if (!email || typeof email !== 'string') return '#';
  const trimmed = email.trim();
  if (!EMAIL_RE.test(trimmed)) return '#';
  return `mailto:${encodeURIComponent(trimmed).replace(/%40/g, '@')}`;
}

/**
 * Returns a safe tel: href or '#' if the phone number contains unexpected chars.
 */
export function safeTel(phone) {
  if (!phone || typeof phone !== 'string') return '#';
  const trimmed = phone.trim();
  if (!PHONE_RE.test(trimmed)) return '#';
  return `tel:${trimmed.replace(/[^+0-9]/g, '')}`;
}

/* ------------------------------------------------------------------ */
/*  src — generic (back-compat) + specialized helpers                  */
/* ------------------------------------------------------------------ */

/**
 * Back-compat: validates a URL for use in src attributes. Only allows https://
 * from explicitly allowed domains when provided. Kept for existing callers.
 */
export function safeSrc(url, allowedDomains = []) {
  if (!url || typeof url !== 'string') return '';
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'https:') return '';
    if (
      allowedDomains.length > 0 &&
      !allowedDomains.some((d) => parsed.hostname === d || parsed.hostname.endsWith('.' + d))
    ) {
      return '';
    }
    return url;
  } catch {
    return '';
  }
}

/**
 * For <img src={...}>. Allows:
 *   - https:// URLs
 *   - data:image/* (for inline base64 previews)
 *   - blob: URLs (object URLs from the same origin)
 *   - same-origin relative paths (/uploads/..., /api/...)
 * Everything else → empty string (browser will show the alt text / fallback).
 */
export function safeImgSrc(url, fallback = '') {
  if (!url || typeof url !== 'string') return fallback;
  const trimmed = url.trim();
  const lower = trimmed.toLowerCase();

  if (lower.startsWith('javascript:') || lower.startsWith('vbscript:')) return fallback;

  // data:image/*;base64,... only — no arbitrary data: URIs
  if (lower.startsWith('data:image/')) return trimmed;

  // blob: object URLs
  if (lower.startsWith('blob:')) return trimmed;

  // Same-origin absolute paths
  if (trimmed.startsWith('/') && !trimmed.startsWith('//')) return trimmed;

  // https://
  try {
    const parsed = new URL(trimmed);
    if (parsed.protocol === 'https:') return trimmed;
  } catch {
    /* fallthrough */
  }
  return fallback;
}

/**
 * For <iframe src={...}>. Strictly requires https:// and a hostname
 * that matches one of the allowed hosts (exact match or suffix ".host").
 * Empty allowedHosts → always return '' (safe default: no iframe).
 */
export function safeIframeSrc(url, allowedHosts = []) {
  if (!url || typeof url !== 'string' || allowedHosts.length === 0) return '';
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'https:') return '';
    const host = parsed.hostname.toLowerCase();
    const ok = allowedHosts.some((h) => {
      const needle = h.toLowerCase();
      return host === needle || host.endsWith('.' + needle);
    });
    return ok ? url : '';
  } catch {
    return '';
  }
}

/* ------------------------------------------------------------------ */
/*  Redirect — for window.location.href = ...                          */
/* ------------------------------------------------------------------ */

const TRUSTED_REDIRECT_HOSTS = [
  'solomonai.us',
  'www.solomonai.us',
  'checkout.stripe.com',
];

/**
 * Strict redirect guard. Only permits:
 *   - Same-origin relative paths starting with / (but not //)
 *   - https:// URLs whose hostname is an *exact* match to a trusted host
 *     (subdomains require an explicit entry; no .endsWith trick)
 *   - Same-origin absolute URLs
 * Everything else returns '/' so a bad actor cannot force an external redirect.
 */
export function safeRedirect(url) {
  if (!url || typeof url !== 'string') return '/';
  const trimmed = url.trim();

  // Relative same-origin path (most common case from internal state)
  if (trimmed.startsWith('/') && !trimmed.startsWith('//')) return trimmed;

  try {
    const parsed = new URL(trimmed);
    if (parsed.protocol !== 'https:') return '/';

    const host = parsed.hostname.toLowerCase();
    if (TRUSTED_REDIRECT_HOSTS.includes(host)) return trimmed;

    if (typeof window !== 'undefined' && parsed.origin === window.location.origin) {
      return trimmed;
    }
  } catch {
    /* fallthrough */
  }
  return '/';
}

/**
 * Stripe Checkout URL guard — stricter than generic redirect because we
 * know the exact expected hostname. Uses URL parsing (no fragile startsWith)
 * so `https://checkout.stripe.com.evil.com/` is rejected.
 */
export function safeStripeCheckoutUrl(url) {
  if (!url || typeof url !== 'string') return '';
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'https:') return '';
    if (parsed.hostname !== 'checkout.stripe.com') return '';
    return url;
  } catch {
    return '';
  }
}

/* ------------------------------------------------------------------ */
/*  Blob download guard                                                */
/* ------------------------------------------------------------------ */

/**
 * Guards a Response object before constructing a blob download URL.
 * Throws if the content-type is not in the expected allowlist. Pairs with
 * the <a>.href = URL.createObjectURL(blob) pattern — see PortalGive / PortalMe.
 */
export async function blobFromResponse(response, allowedMimeTypes = []) {
  if (!response || !response.ok) throw new Error('Bad response');
  const ct = (response.headers.get('Content-Type') || '').split(';')[0].trim().toLowerCase();
  if (allowedMimeTypes.length && !allowedMimeTypes.includes(ct)) {
    throw new Error(`Unexpected content-type: ${ct}`);
  }
  return response.blob();
}
