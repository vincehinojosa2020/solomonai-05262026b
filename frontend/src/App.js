import { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import AppShell from "@/components/layout/AppShell";
import ProtectedRoute from "@/components/ProtectedRoute";
import LoginPage from "@/pages/LoginPage";
import AuthCallback from "@/pages/AuthCallback";
import Dashboard from "@/pages/Dashboard";
import PeopleList from "@/pages/PeopleList";
import PersonDetail from "@/pages/PersonDetail";
import GroupsList from "@/pages/GroupsList";
import GroupDetail from "@/pages/GroupDetail";
import GivingDashboard from "@/pages/GivingDashboard";
import AttendancePage from "@/pages/AttendancePage";
import CommunicationsPage from "@/pages/CommunicationsPage";
import ReportsPage from "@/pages/ReportsPage";
import SettingsPage from "@/pages/SettingsPage";
import EventsPage from "@/pages/EventsPage";
import { API_URL } from "@/lib/utils";

// Router wrapper to detect session_id in URL
function AppRouter() {
  const location = useLocation();
  const [isSeeding, setIsSeeding] = useState(false);
  const [isSeeded, setIsSeeded] = useState(false);

  useEffect(() => {
    // Seed database on first load
    const seedDatabase = async () => {
      try {
        setIsSeeding(true);
        const response = await fetch(`${API_URL}/seed`, { method: 'POST' });
        const data = await response.json();
        console.log('Seed result:', data);
        setIsSeeded(true);
      } catch (error) {
        console.error('Failed to seed database:', error);
      } finally {
        setIsSeeding(false);
      }
    };
    seedDatabase();
  }, []);

  // Check URL fragment for session_id synchronously (prevents race conditions)
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  if (isSeeding && !isSeeded) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white font-medium">Initializing SAMSON...</p>
          <p className="text-slate-400 text-sm mt-1">Creating demo data for Abundant Church</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      
      {/* Protected routes */}
      <Route element={
        <ProtectedRoute>
          <AppShell />
        </ProtectedRoute>
      }>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/people" element={<PeopleList />} />
        <Route path="/people/:personId" element={<PersonDetail />} />
        <Route path="/households" element={<PeopleList type="households" />} />
        <Route path="/groups" element={<GroupsList />} />
        <Route path="/groups/:groupId" element={<GroupDetail />} />
        <Route path="/events" element={<EventsPage />} />
        <Route path="/attendance" element={<AttendancePage />} />
        <Route path="/giving" element={<GivingDashboard />} />
        <Route path="/communications" element={<CommunicationsPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
      
      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
      <Toaster position="bottom-right" richColors />
    </div>
  );
}

export default App;
