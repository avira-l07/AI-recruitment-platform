import React, { useEffect, useState } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import authService from './services/authService';
import api from './services/api';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

import LandingPage from './pages/LandingPage';
import Login from './pages/auth/Login';
import Register from './pages/auth/Register';
import CandidateDashboard from './pages/candidate/CandidateDashboard';
import HRDashboard from './pages/hr/HRDashboard';
import JobManagement from './pages/hr/JobManagement';
import Analytics from './pages/hr/Analytics';
import Candidates from './pages/hr/Candidates';
import Settings from './pages/hr/Settings';
import HRLayout from './layouts/HRLayout';

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

function AppRoutes({ currentUser, onLogout }) {
  const location = useLocation();
  const isDashboardShell =
    location.pathname === '/hr/dashboard' ||
    location.pathname === '/candidate/dashboard';
  const showNavbar = !isDashboardShell && !location.pathname.startsWith('/hr/') && !location.pathname.startsWith('/candidate/');

  return (
    <div className="app-container">
      {showNavbar && <Navbar user={currentUser} onLogout={onLogout} />}
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Candidate Portal */}
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
              <CandidateDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/candidate/jobs"
          element={
            <ProtectedRoute requiredRole="candidate">
              <CandidateDashboard />
            </ProtectedRoute>
          }
        />

        {/* HR Portal */}
        <Route
          path="/hr"
          element={
            <ProtectedRoute requiredRole="hr">
              <HRLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="dashboard" replace />} />
          <Route path="dashboard" element={<HRDashboard />} />
          <Route path="candidates" element={<Candidates />} />
          <Route path="jobs" element={<JobManagement />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </div>
  );
}

function App() {
  const [currentUser, setCurrentUser] = useState(authService.getCurrentUser());

  const handleLogout = () => {
    authService.logout();
    setCurrentUser(null);
  };

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token');
      if (token) {
        try {
          await api.get('/auth/verify');
          setCurrentUser(authService.getCurrentUser());
        } catch (err) {
          authService.logout();
          setCurrentUser(null);
        }
      } else {
        setCurrentUser(null);
      }
    };
    checkAuth();
  }, []);

  return <AppRoutes currentUser={currentUser} onLogout={handleLogout} />;
}

export default App;
