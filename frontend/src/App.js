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
import MediaManagerPage from "@/pages/MediaManagerPage";
import GroupsManagerPage from "@/pages/GroupsManagerPage";
import EventsManagerPage from "@/pages/EventsManagerPage";
import ThinkificPage from "@/pages/ThinkificPage";
import AbundantPathwaysAdmin from "@/pages/AbundantPathwaysAdmin";
import MerchAdminPage from "@/pages/MerchAdminPage";
import CafeAdminPage from "@/pages/CafeAdminPage";
import MeetingsAdminPage from "@/pages/MeetingsAdminPage";
import LeadershipNotesPage from "@/pages/LeadershipNotesPage";
import DeveloperAPIPage from "@/pages/admin/DeveloperAPIPage";
import GroupLeaderDashboard from "@/pages/admin/GroupLeaderDashboard";
import KidsCheckinAdmin from "@/pages/KidsCheckinAdmin";
// Portal Pages
import PortalHome from "@/pages/portal/PortalHome";
import PortalGive from "@/pages/portal/PortalGive";
import PortalGroups from "@/pages/portal/PortalGroups";
import PortalEvents from "@/pages/portal/PortalEvents";
import PortalMe from "@/pages/portal/PortalMe";
import PortalLibrary from "@/pages/portal/PortalLibrary";
import PortalWatch from "@/pages/portal/PortalWatch";
import PortalThinkific from "@/pages/portal/PortalThinkific";
import PortalPathways from "@/pages/portal/PortalPathways";
import PortalPathwaysCourse from "@/pages/portal/PortalPathwaysCourse";
import PortalMerch from "@/pages/portal/PortalMerch";
import PortalCafe from "@/pages/portal/PortalCafe";
import PortalMeetings from "@/pages/portal/PortalMeetings";
import PortalKidsCheckin from "@/pages/portal/PortalKidsCheckin";
import PortalPrayer from "@/pages/portal/PortalPrayer";
import PWAInstallPrompt from "@/components/PWAInstallPrompt";

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
        <Route path="/platform" element={<PlatformDashboard />} />
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
        <Route path="/media" element={<MediaManagerPage />} />
        <Route path="/thinkific" element={<ThinkificPage />} />
        <Route path="/abundant-pathways" element={<AbundantPathwaysAdmin />} />
        <Route path="/merch" element={<MerchAdminPage />} />
        <Route path="/cafe" element={<CafeAdminPage />} />
        <Route path="/meetings" element={<MeetingsAdminPage />} />
        <Route path="/notes" element={<LeadershipNotesPage />} />
        <Route path="/developer" element={<DeveloperAPIPage />} />
        <Route path="/kids-checkin" element={<KidsCheckinAdmin />} />
        <Route path="/admin/groups" element={<GroupsManagerPage />} />
        <Route path="/admin/groups/:groupId/dashboard" element={<GroupLeaderDashboard />} />
        <Route path="/admin/events" element={<EventsManagerPage />} />
      </Route>
      
      {/* Member Portal routes */}
      <Route path="/portal" element={<PortalLayout />}>
        <Route index element={<PortalHome />} />
        <Route path="give" element={<PortalGive />} />
        <Route path="watch" element={<PortalWatch />} />
        <Route path="library" element={<PortalLibrary />} />
        <Route path="kids" element={<PortalKidsCheckin />} />
        <Route path="thinkific" element={<PortalThinkific />} />
        <Route path="pathways" element={<PortalPathways />} />
        <Route path="pathways/:courseId" element={<PortalPathwaysCourse />} />
        <Route path="merch" element={<PortalMerch />} />
        <Route path="cafe" element={<PortalCafe />} />
        <Route path="meetings" element={<PortalMeetings />} />
        <Route path="prayer" element={<PortalPrayer />} />
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
        <PWAInstallPrompt />
      </BrowserRouter>
      <Toaster position="bottom-right" richColors />
    </div>
  );
}

export default App;
