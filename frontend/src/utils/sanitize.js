/**
 * Security sanitization utilities for Solomon AI frontend.
 * Prevents XSS via href, src, and redirect attacks.
 */

/**
 * Validates a URL for use in href attributes.
 * Blocks javascript:, data:, vbscript: protocols.
 */
export function safeHref(url) {
  if (!url || typeof url !== 'string') return '#';
  const trimmed = url.trim().toLowerCase();
  if (trimmed.startsWith('javascript:') || trimmed.startsWith('data:') || trimmed.startsWith('vbscript:')) {
    return '#';
  }
  if (trimmed.startsWith('/') || trimmed.startsWith('http://') || trimmed.startsWith('https://') || trimmed.startsWith('mailto:') || trimmed.startsWith('tel:') || trimmed.startsWith('#')) {
    return url;
  }
  return '#';
}

/**
 * Validates a URL for use in src attributes (iframe, img).
 * Only allows https:// from explicitly allowed domains.
 */
export function safeSrc(url, allowedDomains = []) {
  if (!url || typeof url !== 'string') return '';
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'https:') return '';
    if (allowedDomains.length > 0 && !allowedDomains.some(d => parsed.hostname === d || parsed.hostname.endsWith('.' + d))) {
      return '';
    }
    return url;
  } catch {
    return '';
  }
}

/**
 * Validates a redirect URL. Only allows same-origin or trusted domains.
 */
const TRUSTED_REDIRECT_DOMAINS = [
  'solomonai.us',
  'www.solomonai.us',
  'checkout.stripe.com',
];

export function safeRedirect(url) {
  if (!url || typeof url !== 'string') return '/';
  const trimmed = url.trim();
  // Allow relative paths (same-origin)
  if (trimmed.startsWith('/') && !trimmed.startsWith('//')) {
    return trimmed;
  }
  // Check against trusted domains
  try {
    const parsed = new URL(trimmed);
    if (parsed.protocol === 'https:' && TRUSTED_REDIRECT_DOMAINS.some(d => parsed.hostname === d || parsed.hostname.endsWith('.' + d))) {
      return trimmed;
    }
    // Allow same-origin
    if (parsed.origin === window.location.origin) {
      return trimmed;
    }
  } catch {
    // invalid URL
  }
  return '/';
}
