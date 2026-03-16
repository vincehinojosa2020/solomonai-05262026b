const API_URL = '/api';

/**
 * Authenticated fetch — sends both cookies AND Bearer token.
 * This ensures auth works in all scenarios:
 * - Same-origin web (cookies)
 * - Cross-origin / mobile (Bearer token from localStorage)
 */
export async function authFetch(path, options = {}) {
  const token = localStorage.getItem('session_token');
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
    const data = localStorage.getItem('user_data');
    return data ? JSON.parse(data) : null;
  } catch {
    return null;
  }
}

/**
 * Clear stored auth.
 */
export function clearAuth() {
  localStorage.removeItem('session_token');
  localStorage.removeItem('user_data');
}
