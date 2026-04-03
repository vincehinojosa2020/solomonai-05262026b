import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_URL } from '@/lib/utils';

export default function AuthCallback() {
  const navigate = useNavigate();
  const hasProcessed = useRef(false);

  useEffect(() => {
    // Prevent double processing in StrictMode
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processAuth = async () => {
      try {
        // Extract session_id from URL fragment
        const hash = window.location.hash;
        const sessionIdMatch = hash.match(/session_id=([^&]+)/);
        
        if (!sessionIdMatch) {
          console.error('No session_id in URL');
          navigate('/login');
          return;
        }

        const sessionId = sessionIdMatch[1];

        // Exchange session_id for session data via backend
        const response = await fetch(`${API_URL}/auth/session`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId }),
          
        });

        if (!response.ok) {
          throw new Error('Failed to exchange session');
        }

        const userData = await response.json();
        
        // Store session token in sessionStorage for API calls
        if (userData.session_token) {
          sessionStorage.setItem('session_token', userData.session_token);
          sessionStorage.setItem('user_data', JSON.stringify(userData));
          sessionStorage.setItem('user_role', userData.role || 'member');
        }

        // Clear the hash
        window.history.replaceState(null, '', window.location.pathname);

        // Route based on role
        const role = userData.role || 'member';
        if (role === 'member') {
          navigate('/portal', { state: { user: userData }, replace: true });
        } else if (role === 'platform_admin') {
          navigate('/platform', { state: { user: userData }, replace: true });
        } else {
          navigate('/dashboard', { state: { user: userData }, replace: true });
        }
      } catch (error) {
        console.error('Auth callback error:', error);
        navigate('/login');
      }
    };

    processAuth();
  }, [navigate]);

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p className="text-sm text-slate-400">Authenticating...</p>
      </div>
    </div>
  );
}
