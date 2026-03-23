import { useState, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { authFetch, getStoredUser } from '@/utils/authFetch';

export default function ProtectedRoute({ children, requiredRole }) {
  const location = useLocation();
  const [authState, setAuthState] = useState({
    isAuthenticated: location.state?.user ? true : null,
    user: location.state?.user || null,
    isLoading: !location.state?.user
  });

  useEffect(() => {
    // Skip if user data was passed from login
    if (location.state?.user) {
      setAuthState({
        isAuthenticated: true,
        user: location.state.user,
        isLoading: false
      });
      return;
    }

    const checkAuth = async () => {
      try {
        const response = await authFetch('/auth/me');

        if (!response.ok) {
          throw new Error('Not authenticated');
        }

        const userData = await response.json();
        setAuthState({
          isAuthenticated: true,
          user: userData,
          isLoading: false
        });
      } catch (error) {
        // Fallback: try stored user data
        const stored = getStoredUser();
        if (stored && stored.session_token) {
          setAuthState({
            isAuthenticated: true,
            user: stored,
            isLoading: false
          });
        } else {
          setAuthState({
            isAuthenticated: false,
            user: null,
            isLoading: false
          });
        }
      }
    };

    checkAuth();
  }, [location.state]);

  const { isAuthenticated, user, isLoading } = authState;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-sm text-slate-500">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole) {
    const userRole = user?.role || 'admin';
    const hasAdminPerms = user?.permissions?.some(p => p.startsWith('admin.'));
    if (requiredRole === 'admin' && userRole === 'member' && !hasAdminPerms) {
      return <Navigate to="/portal" replace />;
    }
  }

  return children;
}
