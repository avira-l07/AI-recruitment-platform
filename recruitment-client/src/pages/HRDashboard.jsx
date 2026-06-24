import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../services/authService';
import analyticsService from '../services/analyticsService';
import matchingService from '../services/matchingService';
import Sidebar from '../components/Sidebar';
import LoadingSpinner from '../components/LoadingSpinner';

const HRDashboard = () => {
  const navigate = useNavigate();
  const user = authService.getCurrentUser() || {};

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [activeTab, setActiveTab] = useState('All');
  
  // Bulk selection state
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [bulkMenuOpen, setBulkMenuOpen] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const statsRes = await analyticsService.getOverview();
      const candidatesRes = await matchingService.getAllMatches();
      
      setStats(statsRes);
      setCandidates(candidatesRes || []);
      setSelectedIds(new Set()); // Reset selections on load
    } catch (err) {
      console.error("API Error in HR Dashboard:", err);
      if (err.response?.status === 401) {
        navigate('/login');
        return;
      }
      setError(err.response?.data?.detail || "Failed to connect to the server.");
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handle single row update
  const handleStatusUpdate = async (id, status) => {
    try {
      await matchingService.updateMatchStatus(id, status);
      // Optimistic update
      setCandidates(prev => (prev || []).map(c => c.id === id ? { ...c, status } : c));
      // Optionally reload: loadData();
    } catch (err) {
      console.error("Failed to update status", err);
    }
  };

  // Handle bulk updates
  const handleBulkUpdate = async (status) => {
    if (selectedIds.size === 0) return;
    try {
      const idArray = Array.from(selectedIds);
      await Promise.all(idArray.map(id => matchingService.updateMatchStatus(id, status)));
      setCandidates(prev => (prev || []).map(c => idArray.includes(c.id) ? { ...c, status } : c));
      setSelectedIds(new Set());
      setBulkMenuOpen(false);
    } catch (err) {
      console.error("Bulk update failed", err);
    }
  };

  const handleLogout = async () => {
    try {
      if (authService?.logout) await authService.logout();
      else localStorage.clear();
    } catch {
      localStorage.clear();
    }
    navigate('/login');
  };

  const getInitials = (name) => {
    if (!name) return '??';
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  };

  const getAvatarColorClass = (name) => {
    if (!name) return 'hr-avatar-1';
    const hash = name.charCodeAt(0) % 4;
    return `hr-avatar-${hash + 1}`; // Distributes colors cleanly
  };

  const normalizeSkills = (skills) => {
    if (!skills) return [];
    if (Array.isArray(skills)) return skills;
    if (typeof skills === 'string') return skills.split(',').map(s => s.trim()).filter(Boolean);
    return [];
  };

  const getStatusPillClass = (status) => {
    const s = (status || '').toLowerCase();
    if (s === 'shortlisted') return 'hr-status-shortlisted';
    if (s === 'rejected') return 'hr-status-rejected';
    if (s === 'pending') return 'hr-status-pending';
    return 'hr-status-pending';
  };

  // Data processing
  const sortedCandidates = [...(candidates || [])].sort(
    (a, b) => (b.score ?? b.matchScore ?? b.match_score ?? 0) - (a.score ?? a.matchScore ?? a.match_score ?? 0)
  );

  const filteredCandidates = activeTab === 'All'
    ? sortedCandidates
    : sortedCandidates.filter(c => (c.status || '').toLowerCase() === activeTab.toLowerCase());

  // Checkbox logic
  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(new Set(filteredCandidates.map(c => c.id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  const handleSelectRow = (id) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) newSelected.delete(id);
    else newSelected.add(id);
    setSelectedIds(newSelected);
  };

  // Stats formatting
  const totalCandidates = stats?.total_candidates ?? stats?.totalCandidates ?? 0;
  const totalJobs = stats?.total_jobs ?? stats?.totalJobs ?? 0;
  const shortlisted = stats?.shortlisted_candidates ?? stats?.shortlisted ?? 0;
  const rejected = stats?.rejected_candidates ?? stats?.rejected ?? 0;
  
  const shortlistedPercent = totalCandidates > 0 ? Math.round((shortlisted / totalCandidates) * 100) : 0;
  const rejectedPercent = totalCandidates > 0 ? Math.round((rejected / totalCandidates) * 100) : 0;

  if (loading) return <LoadingSpinner message="Loading analytics and candidate data..." />;

  if (error) {
    return (
      <div className="hr-shell">
        <Sidebar role="hr" active="dashboard" user={user} onLogout={handleLogout} />
        <main className="hr-main">
          <div className="hr-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '80vh' }}>
            <div style={{ backgroundColor: '#FEECEC', border: '1px solid #FCA5A5', borderRadius: '12px', padding: '32px', textAlign: 'center', maxWidth: '500px' }}>
              <h2 style={{ color: '#991B1B', marginBottom: '8px' }}>Connection Error</h2>
              <p style={{ color: '#B91C1C', marginBottom: '24px' }}>{error}</p>
              <button className="hr-refresh-btn" style={{ margin: '0 auto' }} onClick={loadData}>↻ Try Again</button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="hr-shell">
      <Sidebar role="hr" active="dashboard" user={user} onLogout={handleLogout} />
      
      <main className="hr-main">
        <div className="hr-page">
          
          {/* Header */}
          <header className="hr-header">
            <div>
              <h1 className="hr-title">Overview</h1>
              <p className="hr-subtitle">Manage your recruitment pipeline</p>
            </div>
            <button type="button" className="hr-refresh-btn" onClick={loadData}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
              Refresh
            </button>
          </header>

          {/* Stats Grid */}
          <div className="hr-stats-grid">
            <div className="hr-stat-card">
              <div className="hr-stat-top">
                <div className="hr-stat-icon hr-icon-blue">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                </div>
                <span className="hr-stat-label">Total Candidates</span>
              </div>
              <div className="hr-stat-value">{totalCandidates}</div>
              <div className="hr-stat-helper green">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>
                Live database count
              </div>
            </div>

            <div className="hr-stat-card">
              <div className="hr-stat-top">
                <div className="hr-stat-icon hr-icon-muted">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
                </div>
                <span className="hr-stat-label">Total Jobs</span>
              </div>
              <div className="hr-stat-value">{totalJobs}</div>
              <div className="hr-stat-helper"><span className="hr-dot"></span>{totalJobs} active</div>
            </div>

            <div className="hr-stat-card">
              <div className="hr-stat-top">
                <div className="hr-stat-icon hr-icon-green">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                </div>
                <span className="hr-stat-label">Shortlisted</span>
              </div>
              <div className="hr-stat-value">{shortlisted}</div>
              <div className="hr-stat-helper green">{shortlistedPercent}% of total candidates</div>
            </div>

            <div className="hr-stat-card">
              <div className="hr-stat-top">
                <div className="hr-stat-icon hr-icon-red">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
                </div>
                <span className="hr-stat-label">Rejected</span>
              </div>
              <div className="hr-stat-value">{rejected}</div>
              <div className="hr-stat-helper">{rejectedPercent}% of total candidates</div>
            </div>
          </div>

          {/* Safety Note */}
          <div className="hr-safety-note">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
            </svg>
            <p><strong>AI safety note</strong> — AI recommendations support decisions only. Final hiring calls need HR review.</p>
          </div>

          {/* Rankings Table Card */}
          <div className="hr-rankings-card">
            
            <div className="hr-card-header">
              <h2>Candidate rankings</h2>
              
              <div className="hr-bulk-area">
                <div style={{ position: 'relative' }}>
                  <button className="hr-bulk-btn" onClick={() => setBulkMenuOpen(!bulkMenuOpen)}>
                    Bulk actions
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
                  </button>
                  {bulkMenuOpen && (
                    <div className="hr-bulk-menu">
                      <button onClick={() => handleBulkUpdate('Shortlisted')}>Shortlist Selected</button>
                      <button onClick={() => handleBulkUpdate('Rejected')} className="reject">Reject Selected</button>
                    </div>
                  )}
                </div>
                {selectedIds.size > 0 && <span className="hr-selected-count">{selectedIds.size} selected</span>}
              </div>
            </div>

            <div className="hr-tabs">
              {['All', 'Shortlisted', 'Pending', 'Rejected'].map(tab => (
                <button
                  key={tab}
                  type="button"
                  className={`hr-tab ${activeTab === tab ? 'active' : ''}`}
                  onClick={() => { setActiveTab(tab); setSelectedIds(new Set()); }}
                >
                  {tab}
                </button>
              ))}
            </div>

            <div className="hr-table-wrapper">
              <table className="hr-table">
                <thead>
                  <tr>
                    <th style={{ width: '40px' }}>
                      <input 
                        type="checkbox" 
                        className="hr-check"
                        onChange={handleSelectAll}
                        checked={filteredCandidates.length > 0 && selectedIds.size === filteredCandidates.length}
                      />
                    </th>
                    <th>Rank</th>
                    <th>Candidate</th>
                    <th>Skills</th>
                    <th>Matched job</th>
                    <th>Score <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{width:12, height:12, display:'inline', marginLeft:4, opacity:0.5}}><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg></th>
                    <th>Status</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCandidates.map((cand) => {
                    const actualRank = sortedCandidates.findIndex(c => c.id === cand.id) + 1;
                    const score = Math.max(0, Math.min(100, cand.score ?? cand.matchScore ?? cand.match_score ?? 0));
                    const isSelected = selectedIds.has(cand.id);
                    const skills = normalizeSkills(cand.skills || cand.matchedSkills || cand.matched_skills).slice(0, 4);
                    const name = cand.name || cand.full_name || cand.candidate_name || 'Unknown Candidate';
                    const email = cand.email || cand.candidate_email || 'No email provided';
                    const job = cand.matchedJob || cand.jobTitle || cand.job_title || 'Various';

                    return (
                      <tr key={cand.id ?? `cand-${actualRank}`} className={isSelected ? 'selected' : ''}>
                        <td>
                          <input 
                            type="checkbox" 
                            className="hr-check" 
                            checked={isSelected}
                            onChange={() => handleSelectRow(cand.id)}
                          />
                        </td>
                        <td style={{ color: 'var(--hr-muted)', fontSize: '0.9rem' }}>
                          #{actualRank}
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <div className={`hr-avatar ${getAvatarColorClass(name)}`}>
                              {getInitials(name)}
                            </div>
                            <div style={{ display: 'flex', flexDirection: 'column' }}>
                              <span style={{ fontWeight: '500', color: 'var(--hr-text)' }}>{name}</span>
                              <span style={{ fontSize: '0.8rem', color: 'var(--hr-muted)' }}>{email}</span>
                            </div>
                          </div>
                        </td>
                        <td>
                          <div className="hr-skill-wrap">
                            {skills.length > 0 ? skills.map(s => <span key={s} className="hr-skill-chip">{s}</span>) : <span className="hr-muted">-</span>}
                          </div>
                        </td>
                        <td>
                          <span className="hr-job-pill">{job}</span>
                        </td>
                        <td>
                          <div className="hr-score-wrap">
                            <span className="hr-score-text">{score}%</span>
                            <div className="hr-score-bar">
                              <div className="hr-score-fill" style={{ width: `${score}%` }} />
                            </div>
                          </div>
                        </td>
                        <td>
                          <span className={`hr-status-pill ${getStatusPillClass(cand.status)}`}>
                            {cand.status || 'Pending'}
                          </span>
                        </td>
                        <td>
                          <div className="hr-actions">
                            <button className="hr-btn-view" onClick={() => console.log('View candidate', cand.id)}>View</button>
                            <button className="hr-btn-shortlist" onClick={() => handleStatusUpdate(cand.id, 'Shortlisted')}>Shortlist</button>
                            <button className="hr-btn-reject" onClick={() => handleStatusUpdate(cand.id, 'Rejected')}>Reject</button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}

                  {filteredCandidates.length === 0 && (
                    <tr>
                      <td colSpan="8" style={{ textAlign: 'center', padding: '48px 16px', color: 'var(--hr-muted)' }}>
                        No candidates found for this filter.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            
            {/* Pagination Visual Footer */}
            {filteredCandidates.length > 0 && (
              <div className="hr-pagination">
                <span className="hr-page-text">Showing 1–{filteredCandidates.length} of {totalCandidates} candidates</span>
                <div className="hr-page-controls">
                  <button className="hr-page-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="15 18 9 12 15 6"></polyline></svg></button>
                  <button className="hr-page-btn active">1</button>
                  <button className="hr-page-btn">2</button>
                  <button className="hr-page-btn">3</button>
                  <span className="hr-page-dots">...</span>
                  <button className="hr-page-btn">43</button>
                  <button className="hr-page-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"></polyline></svg></button>
                </div>
              </div>
            )}
          </div>

          {/* Bottom Shortcut Cards */}
          <div className="hr-shortcuts-grid">
            <div className="hr-shortcut-card">
              <div className="hr-shortcut-icon blue"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg></div>
              <div>
                <h3>Job Management</h3>
                <p>Create jobs, manage openings, and track pipeline.</p>
                <button onClick={() => console.log('Route to jobs')}>View all jobs →</button>
              </div>
            </div>
            <div className="hr-shortcut-card">
              <div className="hr-shortcut-icon green"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg></div>
              <div>
                <h3>Candidates</h3>
                <p>Search, filter, and manage all candidates.</p>
                <button onClick={() => console.log('Route to candidates')}>Browse candidates →</button>
              </div>
            </div>
            <div className="hr-shortcut-card">
              <div className="hr-shortcut-icon blue"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg></div>
              <div>
                <h3>Analytics</h3>
                <p>Visualize hiring metrics and pipeline insights.</p>
                <button onClick={() => console.log('Route to analytics')}>View reports →</button>
              </div>
            </div>
            <div className="hr-shortcut-card">
              <div className="hr-shortcut-icon yellow"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg></div>
              <div>
                <h3>Alerts</h3>
                <p>Pending submissions and review reminders.</p>
                <button onClick={() => console.log('Route to alerts')}>View alerts →</button>
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
  );
};

export default HRDashboard;