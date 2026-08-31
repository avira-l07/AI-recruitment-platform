import React, { useState, useEffect, useCallback, useRef } from 'react';
import Sidebar from '../components/Sidebar';
import authService from '../services/authService';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useHRRealtime } from '../hooks/useHRRealtime';
import aiService from '../services/aiService';
import notificationService from '../services/notificationService';
import searchService from '../services/searchService';
import NotificationBell from '../components/NotificationBell';
import { useBlindScreening } from '../context/BlindScreeningContext';
import { X, Search, Bell, Cpu, Check, AlertTriangle, XCircle, Menu, Shield, ShieldCheck } from 'lucide-react';
import './HRLayout.css';

const HRLayout = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const user = authService.getCurrentUser() || {};
  const { isBlindMode, toggleBlindMode } = useBlindScreening();
  
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [showEngineStatus, setShowEngineStatus] = useState(false);
  const [aiStatus, setAiStatus] = useState(null);
  
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [showSearchResults, setShowSearchResults] = useState(false);

  const searchContainerRef = useRef(null);

  // Fetch AI status from backend
  const loadAiStatus = useCallback(async () => {
    try {
      const status = await aiService.getStatus();
      setAiStatus(status);
    } catch (err) {
      console.warn("Failed to load AI engine status:", err);
    }
  }, []);

  // Fetch notifications from backend
  const loadNotifications = useCallback(async () => {
    try {
      const response = await notificationService.getNotifications();
      if (response && Array.isArray(response.items)) {
        setNotifications(response.items);
        setUnreadCount(response.unread_count || 0);
      }
    } catch (err) {
      console.warn("Failed to load notifications:", err);
    }
  }, []);

  // Handle marking a notification as read
  const handleMarkRead = async (item) => {
    try {
      await notificationService.markRead(item.id);
      loadNotifications();
    } catch (err) {
      console.error("Mark read failed:", err);
    }
  };

  // Handle marking all notifications as read
  const handleMarkAllRead = async () => {
    try {
      await notificationService.markAllRead();
      loadNotifications();
    } catch (err) {
      console.error("Mark all read failed:", err);
    }
  };

  // Handle real-time SSE stream events at layout level
  const handleSSEEvent = useCallback((event) => {
    // Broadcast event to child pages (like HRDashboard)
    window.dispatchEvent(new CustomEvent('hr-realtime-event', { detail: event }));

    // Auto-refresh layout specific counters
    if (event.event_type === 'notification_created') {
      loadNotifications();
    } else if ([
      'analysis_started',
      'hybrid_completed',
      'gemini_completed',
      'fallback_activated',
      'local_completed',
      'analysis_failed'
    ].includes(event.event_type)) {
      loadAiStatus();
    }
  }, [loadAiStatus, loadNotifications]);

  // Connect layout-level SSE stream
  useHRRealtime(handleSSEEvent);

  useEffect(() => {
    loadAiStatus();
    loadNotifications();

    // Close search dropdown on click outside
    const clickOutside = (e) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target)) {
        setShowSearchResults(false);
      }
    };
    document.addEventListener('mousedown', clickOutside);
    return () => document.removeEventListener('mousedown', clickOutside);
  }, [loadAiStatus, loadNotifications]);

  const handleLogout = async () => {
    try {
      authService.logout();
    } catch {
      localStorage.clear();
    }
    navigate('/login');
  };

  const getActiveTab = () => {
    if (location.pathname === '/hr/candidates') return 'candidates';
    if (location.pathname === '/hr/jobs') return 'jobs';
    if (location.pathname === '/hr/analytics') return 'analytics';
    if (location.pathname === '/hr/settings') return 'settings';
    return 'dashboard';
  };

  // Global search implementation
  const handleSearchChange = async (e) => {
    const value = e.target.value;
    setSearchQuery(value);
    if (value.trim().length >= 2) {
      try {
        const data = await searchService.search(value.trim());
        setSearchResults(data);
        setShowSearchResults(true);
      } catch (err) {
        console.error("Search API error:", err);
      }
    } else {
      setSearchResults(null);
      setShowSearchResults(false);
    }
  };

  // Dynamic status button label resolver
  const getAiStatusLabel = () => {
    if (!aiStatus) return 'AI status unavailable';
    
    const stage = aiStatus.current_stage || 'idle';
    const local = aiStatus.local_ai?.status || 'available';
    const gemini = aiStatus.gemini?.status || 'not_configured';
    const fallbackActive = aiStatus.fallback_active || false;

    if (stage === 'local_running') return 'Local AI running';
    if (stage === 'combining') return 'Hybrid combining';
    if (stage === 'failed') return 'Local AI available'; // standard available fallback text
    
    if (fallbackActive || (local === 'completed' && gemini === 'rate_limited')) {
      return 'Local fallback active';
    }
    if (local === 'completed' && gemini === 'completed') {
      return 'Hybrid completed';
    }
    if (gemini === 'rate_limited') return 'Gemini rate limited';
    if (gemini === 'running') return 'Gemini running';
    
    if (stage === 'idle' || aiStatus.mode === 'idle') {
      if (gemini === 'configured_not_tested') return 'Gemini configured';
      return 'AI system idle';
    }
    
    return 'Local AI available';
  };

  const statusLabel = getAiStatusLabel();
  
  const getBadgeTone = (label) => {
    const l = label.toLowerCase();
    if (l.includes('rate limited') || l.includes('warning') || l.includes('failed') || l.includes('unavailable')) return 'warning';
    if (l.includes('running') || l.includes('combining')) return 'success';
    if (l.includes('completed') || l.includes('available')) return 'success';
    return 'muted';
  };

  const badgeTone = getBadgeTone(statusLabel);

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
            <Menu size={22} />
          </button>

          {/* Search bar wrapper */}
          <div ref={searchContainerRef} className="hr-topbar-search-container">
            <div className="hr-topbar-search-wrapper">
              <Search size={16} className="hr-topbar-search-icon" />
              <input 
                type="text" 
                value={searchQuery}
                onChange={handleSearchChange}
                placeholder="Search candidates, jobs, or AI insights..." 
                className="hr-topbar-search-input"
              />
            </div>
            
            {showSearchResults && searchResults && (
              <div className="hr-search-dropdown">
                <div className="hr-search-dropdown-header">
                  <span>Search Results</span>
                  <button onClick={() => setShowSearchResults(false)}><X size={12} /></button>
                </div>
                <div className="hr-search-dropdown-body">
                  {searchResults.candidates?.length > 0 && (
                    <div className="hr-search-section">
                      <h4>Candidates</h4>
                      {searchResults.candidates.map(c => (
                        <div key={c.id} className="hr-search-result-item" onClick={() => {
                          setShowSearchResults(false);
                          navigate('/hr/candidates');
                        }}>
                          <span className="hr-search-result-title">{c.name}</span>
                          <span className="hr-search-result-sub">{c.email}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {searchResults.jobs?.length > 0 && (
                    <div className="hr-search-section">
                      <h4>Jobs</h4>
                      {searchResults.jobs.map(j => (
                        <div key={j.id} className="hr-search-result-item" onClick={() => {
                          setShowSearchResults(false);
                          navigate('/hr/jobs');
                        }}>
                          <span className="hr-search-result-title">{j.title}</span>
                          <span className="hr-search-result-sub">Status: {j.status}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  {(!searchResults.candidates?.length && !searchResults.jobs?.length) && (
                    <p style={{ fontSize: '11.5px', color: '#74809A', padding: '6px 8px', margin: 0 }}>No matches found.</p>
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="hr-topbar-actions">
            {/* Fair Review / Blind Screening Toggle */}
            <div className="hr-fair-review-toggle-wrapper">
              <button
                type="button"
                role="switch"
                aria-checked={isBlindMode}
                onClick={toggleBlindMode}
                className={`hr-fair-review-toggle-btn ${isBlindMode ? 'active' : ''}`}
                title={isBlindMode ? "Fair Review Mode is ON (Candidate PII is concealed to prevent bias)" : "Fair Review Mode is OFF (Click to conceal PII and evaluate purely on skills & merit)"}
              >
                <div className="hr-fair-review-toggle-icon">
                  {isBlindMode ? <ShieldCheck size={14} /> : <Shield size={14} />}
                </div>
                <span className="hr-fair-review-toggle-text">
                  Fair Review: <strong>{isBlindMode ? 'ON' : 'OFF'}</strong>
                </span>
                <span className={`hr-fair-review-switch-pill ${isBlindMode ? 'on' : 'off'}`}>
                  <span className="hr-fair-review-switch-thumb" />
                </span>
              </button>
            </div>

            {/* AI Status Badge & Popover */}
            <div className="hr-engine-status-button-wrapper">
              <button 
                onClick={() => setShowEngineStatus(!showEngineStatus)}
                className={`hr-engine-status-btn ${badgeTone}`}
              >
                <span className={`hr-engine-pulse-dot ${badgeTone}`}></span>
                {statusLabel}
              </button>

              {showEngineStatus && (
                <div className={`hr-engine-popover-menu ${badgeTone === 'warning' ? 'warning-border' : badgeTone === 'danger' ? 'danger-border' : ''}`}>
                  <div className="hr-popover-header">
                    <h3>AI Engine Status</h3>
                    <button onClick={() => setShowEngineStatus(false)} className="hr-popover-close">
                      <X size={14} />
                    </button>
                  </div>
                  
                  <div className="hr-popover-section">
                    <div className="hr-popover-row">
                      <span>RecruitAI Engine</span>
                      <span className={`hr-popover-status-badge ${aiStatus?.current_stage === 'idle' ? 'idle' : 'active'}`}>
                        {aiStatus?.current_stage === 'idle' ? 'Idle' : 'Active'}
                      </span>
                    </div>
                    <p className="hr-popover-mode-desc">
                      Current mode: {(aiStatus?.mode || 'idle').replaceAll('_', ' ')} — {aiStatus?.current_stage === 'idle' ? 'awaiting applications' : 'processing...'}
                    </p>
                  </div>

                  <div className="hr-popover-section">
                    <div className="hr-popover-row">
                      <span>Local AI</span>
                      <span className="hr-popover-status-badge active">Active</span>
                    </div>
                    <div className="hr-popover-capabilities-grid">
                      {['Resume parser', 'ATS scoring', 'Skill matching', 'Summary'].map(skill => (
                        <div key={skill} className="hr-popover-capability-item">
                          <Check size={8} /> {skill}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="hr-popover-section">
                    <div className="hr-popover-row">
                      <span>Gemini Engine</span>
                      <span className={`hr-popover-status-badge ${aiStatus?.gemini?.status}`}>
                        {(aiStatus?.gemini?.status || 'not_configured').replaceAll('_', ' ')}
                      </span>
                    </div>
                    <p className="hr-popover-gemini-desc">
                      {aiStatus?.gemini?.status === 'rate_limited' 
                        ? 'API quota reached. Fallback to Local AI is active. Resets in 4h 23m.' 
                        : aiStatus?.gemini?.status === 'not_configured' 
                          ? 'Gemini is not configured. Falling back to Local AI.' 
                          : 'Gemini model is configured and active for content generation.'}
                    </p>
                    {aiStatus?.gemini?.error_code && (
                      <span className="hr-popover-error-badge">
                        Error code: {aiStatus.gemini.error_code}
                      </span>
                    )}
                  </div>

                  <div className="hr-popover-footer">
                    <div>Average analysis: {aiStatus?.average_analysis_time == null ? 'N/A' : `${aiStatus.average_analysis_time}s`}</div>
                    <div>Last updated: {aiStatus?.last_updated ? new Date(aiStatus.last_updated).toLocaleTimeString() : 'N/A'}</div>
                  </div>
                </div>
              )}
            </div>

            {/* Notification Bell */}
            <NotificationBell 
              notifications={notifications}
              unreadCount={unreadCount}
              onMarkRead={handleMarkRead}
              onMarkAllRead={handleMarkAllRead}
            />
          </div>
        </header>

        {/* Main Content Area */}
        <div className="hr-page-content">
          {children || <Outlet />}
        </div>
      </main>
    </div>
  );
};

export default HRLayout;

