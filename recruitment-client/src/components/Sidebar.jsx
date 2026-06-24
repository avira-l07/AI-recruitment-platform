import React from 'react';
import { useNavigate } from 'react-router-dom';

const Sidebar = ({ role, active, onSelect, user, onLogout }) => {
  const navigate = useNavigate();

  const handleCandidateSelect = (key) => {
    if (key === 'upload') navigate('/candidate/upload');
    else if (key === 'jobs') navigate('/candidate/jobs');
    else if (onSelect) onSelect(key);
    else navigate('/candidate/dashboard');
  };

  const handleHRSelect = (key) => {
    if (onSelect) onSelect(key);
    else navigate(`/hr/${key === 'dashboard' ? 'dashboard' : key}`);
  };

  const getInitial = () => {
    if (!user) return 'U';
    return (user.name || user.fullName || user.email || 'U').charAt(0).toUpperCase();
  };

  // --- HR SIDEBAR ---
  if (role === 'hr') {
    const hrItems = [
      { key: 'dashboard', label: 'Dashboard', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg> },
      { key: 'jobs', label: 'Job Management', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg> },
      { key: 'candidates', label: 'Candidates', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg> },
      { key: 'analytics', label: 'Analytics', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg> },
      { key: 'settings', label: 'Settings', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg> }
    ];

    return (
      <aside className="hr-sidebar">
        <div className="hr-sidebar-logo">
          RecruitAI <span style={{ color: '#6d5dfc', fontWeight: '400' }}>HR</span>
        </div>

        <nav className="hr-sidebar-nav">
          {hrItems.map(item => (
            <button
              key={item.key}
              type="button"
              className={`hr-sidebar-link ${active === item.key ? 'active' : ''}`}
              onClick={() => handleHRSelect(item.key)}
            >
              <div className="hr-sidebar-link-left">
                <span className="hr-sidebar-icon">{item.icon}</span>
                {item.label}
              </div>
              {item.key !== 'dashboard' && (
                <svg className="hr-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 18 15 12 9 6"></polyline></svg>
              )}
            </button>
          ))}
        </nav>

        {user && (
          <div className="hr-user-block">
            <div className="hr-user-avatar">{getInitial()}</div>
            <div className="hr-user-info">
              <span className="hr-user-name">{user.name || user.fullName || 'Avi'}</span>
              <span className="hr-user-role">Human Resources</span>
            </div>
            {onLogout && (
              <button type="button" className="hr-logout-btn" onClick={onLogout} title="Logout">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
              </button>
            )}
          </div>
        )}
      </aside>
    );
  }

  // --- CANDIDATE SIDEBAR ---
  const candidateItems = [
    { key: 'dashboard', label: 'Dashboard', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg> },
    { key: 'upload', label: 'Upload resume', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><polyline points="9 15 12 12 15 15"></polyline></svg> },
    { key: 'jobs', label: 'Browse jobs', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg> },
    { key: 'matches', label: 'My matches', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg> },
    { key: 'notifications', label: 'Notifications', icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg> }
  ];

  return (
    <aside className="candidate-sidebar">
      <div className="candidate-sidebar-logo">RecruitAI</div>
      <nav className="candidate-sidebar-nav">
        {candidateItems.map(item => (
          <button
            key={item.key}
            type="button"
            className={`candidate-sidebar-link ${active === item.key ? 'active' : ''}`}
            onClick={() => handleCandidateSelect(item.key)}
          >
            <span className="candidate-sidebar-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>
      {user && (
        <div className="candidate-user-block">
          <div className="candidate-avatar">{getInitial()}</div>
          <div className="candidate-user-info">
            <span className="candidate-user-name">{user.name || user.fullName || 'Candidate'}</span>
            <span className="candidate-user-role">Candidate Portal</span>
          </div>
          {onLogout && (
            <button type="button" className="candidate-logout-btn" onClick={onLogout} title="Logout">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
            </button>
          )}
        </div>
      )}
    </aside>
  );
};

export default Sidebar;