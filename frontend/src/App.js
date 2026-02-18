import { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import AppShell from "@/components/layout/AppShell";
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

function App() {
  const [isSeeding, setIsSeeding] = useState(false);
  const [isSeeded, setIsSeeded] = useState(false);

  useEffect(() => {
    // Check and seed database on first load
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

  if (isSeeding && !isSeeded) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-600 font-medium">Setting up Samson...</p>
          <p className="text-slate-400 text-sm mt-1">Creating demo data for Abundant Church</p>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
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
        </Routes>
      </BrowserRouter>
      <Toaster position="bottom-right" richColors />
    </div>
  );
}

export default App;
