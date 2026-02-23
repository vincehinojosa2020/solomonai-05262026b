import { useEffect, useState } from "react";
import "@/App.css";
import "@/library.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import AppShell from "@/components/layout/AppShell";
import PortalLayout from "@/components/layout/PortalLayout";
import ProtectedRoute from "@/components/ProtectedRoute";
import LoginPage from "@/pages/LoginPage";
import SignUpPage from "@/pages/SignUpPage";
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
import IntegrationsPage from "@/pages/IntegrationsPage";
import PlatformDashboard from "@/pages/PlatformDashboard";
// Portal Pages
import PortalHome from "@/pages/portal/PortalHome";
import PortalGive from "@/pages/portal/PortalGive";
import PortalGroups from "@/pages/portal/PortalGroups";
import PortalEvents from "@/pages/portal/PortalEvents";
import PortalMe from "@/pages/portal/PortalMe";
import PortalLibrary from "@/pages/portal/PortalLibrary";
import { API_URL } from "@/lib/utils";

// Router wrapper to detect session_id in URL
function AppRouter() {
  const location = useLocation();

  // Check URL fragment for session_id synchronously (prevents race conditions)
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }


  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignUpPage />} />
      <Route path="/register" element={<Navigate to="/signup" replace />} />
      
      {/* Admin Protected routes */}
      <Route element={
        <ProtectedRoute requiredRole="admin">
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
        <Route path="/integrations" element={<IntegrationsPage />} />
      </Route>
      
      {/* Member Portal routes */}
      <Route path="/portal" element={<PortalLayout />}>
        <Route index element={<PortalHome />} />
        <Route path="give" element={<PortalGive />} />
        <Route path="watch" element={<Navigate to="/portal/library" replace />} />
        <Route path="library" element={<PortalLibrary />} />
        <Route path="groups" element={<PortalGroups />} />
        <Route path="events" element={<PortalEvents />} />
        <Route path="me" element={<PortalMe />} />
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
