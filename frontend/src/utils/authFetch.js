const API_URL = '/api';

/**
 * Authenticated fetch — sends both cookies AND Bearer token.
 * sessionStorage used instead of localStorage for security:
 * - Clears on tab close (limits XSS token theft window)
 * - Primary auth is via httpOnly cookies (same-origin)
 * - Bearer token is fallback for cross-origin / mobile webview
 */
export async function authFetch(path, options = {}) {
  const token = sessionStorage.getItem('session_token');
  const headers = { ...(options.headers || {}) };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = path.startsWith('http') ? path : `${API_URL}${path}`;

  return fetch(url, {
    ...options,
    headers,
  });
}

/**
 * Get stored user data or null.
 */
export function getStoredUser() {
  try {
    const data = sessionStorage.getItem('user_data');
    return data ? JSON.parse(data) : null;
  } catch {
    return null;
  }
}

/**
 * Clear stored auth.
 */
export function clearAuth() {
  sessionStorage.removeItem('session_token');
  sessionStorage.removeItem('user_data');
}
