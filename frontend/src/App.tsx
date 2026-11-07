import React from 'react';
import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import ReportIssue from './pages/ReportIssue';
import IssueDetails from './pages/IssueDetails';
import Analytics from './pages/Analytics';
import Login from './pages/Login';
import Register from './pages/Register';
import RepairVerification from './pages/RepairVerification';
import GeographicIntelligence from './pages/GeographicIntelligence';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import VerifyEmail from './pages/VerifyEmail';
import AllIssues from './pages/AllIssues';
import AIReports from './pages/AIReports';
import Profile from './pages/Profile';
import Admin from './pages/Admin';
import GpsCamera from './pages/GpsCamera';
import GpsGallery from './pages/GpsGallery';
import PublicIssue from './pages/PublicIssue';
import MyCivicReports from './pages/MyCivicReports';
import CivicDesk from './pages/CivicDesk';
import { useAuthStore } from './hooks/useAuthStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30_000,
    },
  },
});

function Protected({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((state) => state.token);
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function AppShell() {
  const pathname = useLocation().pathname;
  const isDashboard = [
    '/dashboard', '/reports', '/issues', '/ai-reports', '/analytics',
    '/geographic', '/geographic-intelligence', '/verification', '/repair-verification',
    '/profile', '/admin', '/settings', '/report', '/report-issue',
    '/gps-camera', '/gps-gallery', '/report-public-issue', '/my-reports',
    '/gram-panchayat', '/taluk-panchayat', '/zilla-panchayat',
  ].some((path) => pathname === path) || pathname.startsWith('/issue/');

  return (
    <div className={`min-h-screen flex flex-col ${isDashboard ? 'bg-[#080d17]' : 'bg-gray-50'}`}>
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
          <Route path="/reports" element={<Protected><AllIssues /></Protected>} />
          <Route path="/issues" element={<Protected><AllIssues /></Protected>} />
          <Route path="/report" element={<Protected><ReportIssue /></Protected>} />
          <Route path="/report-issue" element={<Protected><ReportIssue /></Protected>} />
          <Route path="/issue/:id" element={<Protected><IssueDetails /></Protected>} />
          <Route path="/analytics" element={<Protected><Analytics /></Protected>} />
          <Route path="/geographic" element={<Protected><GeographicIntelligence /></Protected>} />
          <Route path="/geographic-intelligence" element={<Protected><GeographicIntelligence /></Protected>} />
          <Route path="/verification" element={<Protected><RepairVerification /></Protected>} />
          <Route path="/repair-verification" element={<Protected><RepairVerification /></Protected>} />
          <Route path="/ai-reports" element={<Protected><AIReports /></Protected>} />
          <Route path="/profile" element={<Protected><Profile /></Protected>} />
          <Route path="/settings" element={<Protected><Profile /></Protected>} />
          <Route path="/admin" element={<Protected><Admin /></Protected>} />
          <Route path="/gps-camera" element={<Protected><GpsCamera /></Protected>} />
          <Route path="/gps-gallery" element={<Protected><GpsGallery /></Protected>} />
          <Route path="/report-public-issue" element={<Protected><PublicIssue /></Protected>} />
          <Route path="/my-reports" element={<Protected><MyCivicReports /></Protected>} />
          <Route path="/gram-panchayat" element={<Protected><CivicDesk level="gp" /></Protected>} />
          <Route path="/taluk-panchayat" element={<Protected><CivicDesk level="taluk" /></Protected>} />
          <Route path="/zilla-panchayat" element={<Protected><CivicDesk level="zilla" /></Protected>} />
          <Route path="*" element={
            <div className="py-20 text-center">
              <h1 className="mb-4 text-6xl font-bold text-gray-200">404</h1>
              <p className="mb-6 text-gray-500">Page not found</p>
              <a href="/" className="btn-primary">Back to Dashboard</a>
            </div>
          } />
        </Routes>
      </main>
      {!isDashboard && <Footer />}
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppShell />
      </BrowserRouter>
    </QueryClientProvider>
  );
}
