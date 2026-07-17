import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';
import authService from '../services/authService';
import { useNavigate, useLocation } from 'react-router-dom';

const HRLayout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const user = authService.getCurrentUser() || {};
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handleLogout = async () => {
    try {
      if (authService?.logout) await authService.logout();
      else localStorage.clear();
    } catch {
      localStorage.clear();
    }
    navigate('/login');
  };

  // Determine active tab based on path
  const getActiveTab = () => {
    if (location.pathname === '/hr/candidates') return 'candidates';
    if (location.pathname === '/hr/jobs') return 'jobs';
    if (location.pathname === '/hr/analytics') return 'analytics';
    if (location.pathname === '/hr/settings') return 'settings';
    return 'dashboard';
  };

  return (
    <div className={`hr-shell ${isDrawerOpen ? 'drawer-active' : ''}`}>
      {/* Drawer Overlay for Mobile */}
      {isDrawerOpen && (
        <div className="hr-drawer-overlay" onClick={() => setIsDrawerOpen(false)} />
      )}

      {/* Sidebar Container */}
      <div className={`hr-sidebar-wrapper ${isDrawerOpen ? 'open' : ''}`}>
        <Sidebar role="hr" active={getActiveTab()} user={user} onLogout={handleLogout} />
      </div>

      <main className="hr-main">
        {/* Global Top Navigation Header */}
        <header className="hr-topbar">
          {/* Hamburger Menu Toggle for Mobile */}
          <button 
            className="hr-drawer-toggle" 
            onClick={() => setIsDrawerOpen(!isDrawerOpen)}
            aria-label="Toggle navigation menu"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
          </button>

          <div className="hr-topbar-search">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="hr-topbar-search-icon">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <input 
              type="text" 
              placeholder="Search candidates, jobs, or AI insights..." 
              className="hr-topbar-search-input"
            />
          </div>
          <div className="hr-topbar-actions">
            <div className="hr-engine-badge">
              <span className="hr-engine-dot"></span>
              <span className="hr-engine-text">Hybrid Engine Active</span>
            </div>
          </div>
        </header>

        {/* Main Content Area */}
        <div className="hr-page-content">
          {children}
        </div>
      </main>
    </div>
  );
};

export default HRLayout;
