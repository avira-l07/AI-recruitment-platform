import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import authService from './services/authService';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import Register from './pages/Register';
import CandidateDashboard from './pages/CandidateDashboard';
import ResumeUpload from './pages/ResumeUpload';
import BrowseJobs from './pages/BrowseJobs';
import HRDashboard from './pages/HRDashboard';
import JobManagement from './pages/JobManagement';
import Analytics from './pages/Analytics';
import Candidates from './pages/Candidates';

const ProtectedRoute = ({ children, requiredRole }) => {
  const token = localStorage.getItem('token');
  const user = authService.getCurrentUser();

  if (!token || !user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

const LegacyLayout = ({ children, role }) => (
  <div className="dashboard-shell">
    <Sidebar role={role} />
    <main className="dashboard-main">
      {children}
    </main>
  </div>
);

function AppRoutes() {
  const location = useLocation();
  const isDashboardShell =
    location.pathname === '/hr/dashboard' ||
    location.pathname === '/candidate/dashboard';
  const showNavbar = !isDashboardShell && !location.pathname.startsWith('/hr/') && !location.pathname.startsWith('/candidate/');

  return (
    <div className="app-container">
      {showNavbar && <Navbar />}
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route
          path="/candidate/dashboard"
          element={
            <ProtectedRoute requiredRole="candidate">
              <CandidateDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/candidate/upload"
          element={
            <ProtectedRoute requiredRole="candidate">
              <LegacyLayout role="candidate">
                <ResumeUpload />
              </LegacyLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/candidate/jobs"
          element={
            <ProtectedRoute requiredRole="candidate">
              <BrowseJobs />
            </ProtectedRoute>
          }
        />

        <Route
          path="/hr/dashboard"
          element={
            <ProtectedRoute requiredRole="hr">
              <HRDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/hr/candidates"
          element={
            <ProtectedRoute requiredRole="hr">
              <Candidates />
            </ProtectedRoute>
          }
        />
        <Route
          path="/hr/jobs"
          element={
            <ProtectedRoute requiredRole="hr">
              <LegacyLayout role="hr">
                <JobManagement />
              </LegacyLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/hr/analytics"
          element={
            <ProtectedRoute requiredRole="hr">
              <LegacyLayout role="hr">
                <Analytics />
              </LegacyLayout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </div>
  );
}

function App() {
  return <AppRoutes />;
}

export default App;