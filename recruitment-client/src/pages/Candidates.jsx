import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import authService from '../services/authService';
import matchingService from '../services/matchingService';
import Sidebar from '../components/Sidebar';
import LoadingSpinner from '../components/LoadingSpinner';

// --- Safe normalization helpers (mirrors HRDashboard.jsx patterns) ---
const normalizeSkills = (skills) => {
  if (!skills) return [];
  if (Array.isArray(skills)) return skills;
  if (typeof skills === 'string') return skills.split(',').map(s => s.trim()).filter(Boolean);
  return [];
};

const normalizeScore = (cand) => {
  const raw = cand?.score ?? cand?.matchScore ?? cand?.match_score ?? 0;
  const num = Number(raw);
  return Number.isFinite(num) ? Math.max(0, Math.min(100, num)) : 0;
};

const normalizeName = (cand) => cand?.name || cand?.full_name || cand?.candidate_name || 'Unknown Candidate';
const normalizeEmail = (cand) => cand?.email || cand?.candidate_email || 'No email provided';
const normalizeJob = (cand) => cand?.matchedJob || cand?.jobTitle || cand?.job_title || 'Various';
const normalizeStatus = (cand) => (cand?.status || 'Pending');

const getInitials = (name) => {
  if (!name) return '??';
  return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
};

const getAvatarColorClass = (name) => {
  if (!name) return 'hr-avatar-1';
  const hash = name.charCodeAt(0) % 4;
  return `hr-avatar-${hash + 1}`;
};

const getStatusPillClass = (status) => {
  const s = (status || '').toLowerCase();
  if (s === 'shortlisted') return 'hr-status-shortlisted';
  if (s === 'rejected') return 'hr-status-rejected';
  return 'hr-status-pending';
};

const Candidates = () => {
  const navigate = useNavigate();
  const user = authService.getCurrentUser() || {};

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [candidates, setCandidates] = useState([]);

  // Filters
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [skillFilter, setSkillFilter] = useState('All');
  const [jobFilter, setJobFilter] = useState('All');
  const [minScore, setMinScore] = useState(0);

  // Bulk selection
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [bulkMenuOpen, setBulkMenuOpen] = useState(false);
  const [bulkLoading, setBulkLoading] = useState(false);

  // Detail drawer
  const [activeCandidate, setActiveCandidate] = useState(null);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [drawerDetail, setDrawerDetail] = useState(null);
  const [drawerError, setDrawerError] = useState(null);
  const [noteDraft, setNoteDraft] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await matchingService.getAllMatches();
      setCandidates(Array.isArray(res) ? res : []);
      setSelectedIds(new Set());
    } catch (err) {
      console.error('API Error in Candidates page:', err);
      if (err.response?.status === 401) {
        navigate('/login');
        return;
      }
      setError(err.response?.data?.detail || 'Failed to connect to the server.');
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleLogout = async () => {
    try {
      if (authService?.logout) await authService.logout();
      else localStorage.clear();
    } catch {
      localStorage.clear();
    }
    navigate('/login');
  };

  // --- Derived filter options (built from real data only) ---
  const allSkills = useMemo(() => {
    const set = new Set();
    (candidates || []).forEach(c => normalizeSkills(c.skills || c.matchedSkills || c.matched_skills).forEach(s => set.add(s)));
    return Array.from(set).sort();
  }, [candidates]);

  const allJobs = useMemo(() => {
    const set = new Set();
    (candidates || []).forEach(c => set.add(normalizeJob(c)));
    return Array.from(set).sort();
  }, [candidates]);

  // --- Filtering pipeline ---
  const filteredCandidates = useMemo(() => {
    return (candidates || []).filter((c) => {
      const name = normalizeName(c).toLowerCase();
      const email = normalizeEmail(c).toLowerCase();
      const status = normalizeStatus(c).toLowerCase();
      const job = normalizeJob(c);
      const skills = normalizeSkills(c.skills || c.matchedSkills || c.matched_skills);
      const score = normalizeScore(c);

      if (searchTerm.trim()) {
        const term = searchTerm.trim().toLowerCase();
        if (!name.includes(term) && !email.includes(term)) return false;
      }
      if (statusFilter !== 'All' && status !== statusFilter.toLowerCase()) return false;
      if (skillFilter !== 'All' && !skills.includes(skillFilter)) return false;
      if (jobFilter !== 'All' && job !== jobFilter) return false;
      if (score < minScore) return false;

      return true;
    }).sort((a, b) => normalizeScore(b) - normalizeScore(a));
  }, [candidates, searchTerm, statusFilter, skillFilter, jobFilter, minScore]);

  // --- Bulk selection logic ---
  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIds(new Set(filteredCandidates.map(c => c.id)));
    } else {
      setSelectedIds(new Set());
    }
  };

  const handleSelectRow = (id) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedIds(next);
  };

  const handleStatusUpdate = async (id, status) => {
    try {
      await matchingService.updateMatchStatus(id, status);
      setCandidates(prev => (prev || []).map(c => (c.id === id ? { ...c, status } : c)));
      setActiveCandidate(prev => (prev && prev.id === id ? { ...prev, status } : prev));
    } catch (err) {
      console.error('Failed to update status', err);
    }
  };

  const handleBulkUpdate = async (status) => {
    if (selectedIds.size === 0) return;
    setBulkLoading(true);
    try {
      const idArray = Array.from(selectedIds);
      // Backend has no bulk endpoint yet, so we call the existing single-update endpoint per candidate.
      await Promise.all(idArray.map(id => matchingService.updateMatchStatus(id, status)));
      setCandidates(prev => (prev || []).map(c => (idArray.includes(c.id) ? { ...c, status } : c)));
      setSelectedIds(new Set());
      setBulkMenuOpen(false);
    } catch (err) {
      console.error('Bulk update failed', err);
    } finally {
      setBulkLoading(false);
    }
  };

  // --- Detail drawer ---
  const openDrawer = async (cand) => {
    setActiveCandidate(cand);
    setDrawerDetail(null);
    setDrawerError(null);
    setNoteDraft('');

    const candidateId = cand?.candidate_id ?? cand?.candidateId;
    if (!candidateId) {
      setDrawerError('Detailed match data not available for this candidate.');
      return;
    }

    setDrawerLoading(true);
    try {
      // Re-uses the existing working endpoint; this returns the full list of
      // matches for this specific candidate (jobTitle, score, explanation, etc).
      const matches = await matchingService.getCandidateMatches(candidateId);
      setDrawerDetail(Array.isArray(matches) ? matches : []);
    } catch (err) {
      console.error('Failed to load candidate detail', err);
      setDrawerError('Resume detail not available from current endpoint.');
    } finally {
      setDrawerLoading(false);
    }
  };

  const closeDrawer = () => {
    setActiveCandidate(null);
    setDrawerDetail(null);
    setDrawerError(null);
  };

  const handleExportCsv = () => {
    // Visual-only export: builds a CSV from currently filtered, real data.
    const headers = ['Name', 'Email', 'Skills', 'Best Match', 'Score', 'Status'];
    const rows = filteredCandidates.map(c => [
      normalizeName(c),
      normalizeEmail(c),
      normalizeSkills(c.skills || c.matchedSkills || c.matched_skills).join('; '),
      normalizeJob(c),
      `${normalizeScore(c)}%`,
      normalizeStatus(c),
    ]);
    const csv = [headers, ...rows].map(r => r.map(val => `"${String(val).replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'candidates.csv';
    link.click();
    URL.revokeObjectURL(url);
  };

  if (loading) return <LoadingSpinner message="Loading candidates..." />;

  if (error) {
    return (
      <div className="hr-shell">
        <Sidebar role="hr" active="candidates" user={user} onLogout={handleLogout} />
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
      <Sidebar role="hr" active="candidates" user={user} onLogout={handleLogout} />

      <main className="hr-main">
        <div className="hr-page">

          {/* Header */}
          <header className="hr-header">
            <div>
              <h1 className="hr-title">Candidates</h1>
              <p className="hr-subtitle">Search, review, and manage all applicants</p>
            </div>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button type="button" className="hr-refresh-btn" onClick={loadData}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>
                Refresh
              </button>
              <button type="button" className="hr-refresh-btn" onClick={handleExportCsv}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                Export CSV
              </button>
            </div>
          </header>

          {/* Filters Card */}
          <div className="hr-rankings-card" style={{ marginBottom: '20px' }}>
            <div className="hr-card-body-filters">
              <div className="hr-filter-search">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
                <input
                  type="text"
                  placeholder="Search by name or email..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              <select className="hr-filter-select" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                {['All', 'Pending', 'Shortlisted', 'Rejected'].map(s => <option key={s} value={s}>{s}</option>)}
              </select>

              <select className="hr-filter-select" value={skillFilter} onChange={(e) => setSkillFilter(e.target.value)}>
                <option value="All">All skills</option>
                {allSkills.map(s => <option key={s} value={s}>{s}</option>)}
              </select>

              <select className="hr-filter-select" value={jobFilter} onChange={(e) => setJobFilter(e.target.value)}>
                <option value="All">All matched jobs</option>
                {allJobs.map(j => <option key={j} value={j}>{j}</option>)}
              </select>

              <div className="hr-filter-score">
                <label>Min score: {minScore}%</label>
                <input type="range" min="0" max="100" step="5" value={minScore} onChange={(e) => setMinScore(Number(e.target.value))} />
              </div>
            </div>
          </div>

          {/* Table Card */}
          <div className="hr-rankings-card">
            <div className="hr-card-header">
              <h2>All candidates</h2>
              <div className="hr-bulk-area">
                <div style={{ position: 'relative' }}>
                  <button className="hr-bulk-btn" onClick={() => setBulkMenuOpen(!bulkMenuOpen)} disabled={bulkLoading}>
                    {bulkLoading ? 'Updating...' : 'Bulk actions'}
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="6 9 12 15 18 9"></polyline></svg>
                  </button>
                  {bulkMenuOpen && !bulkLoading && (
                    <div className="hr-bulk-menu">
                      <button onClick={() => handleBulkUpdate('Shortlisted')}>Shortlist selected</button>
                      <button onClick={() => handleBulkUpdate('Rejected')} className="reject">Reject selected</button>
                    </div>
                  )}
                </div>
                {selectedIds.size > 0 && <span className="hr-selected-count">{selectedIds.size} selected</span>}
              </div>
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
                    <th>Candidate</th>
                    <th>Skills</th>
                    <th>Best match</th>
                    <th>Match score</th>
                    <th>Status</th>
                    <th>Resume</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredCandidates.map((cand) => {
                    const name = normalizeName(cand);
                    const email = normalizeEmail(cand);
                    const status = normalizeStatus(cand);
                    const job = normalizeJob(cand);
                    const score = normalizeScore(cand);
                    const skills = normalizeSkills(cand.skills || cand.matchedSkills || cand.matched_skills).slice(0, 5);
                    const isSelected = selectedIds.has(cand.id);
                    const hasResume = skills.length > 0; // best available signal without a dedicated resume-status field

                    return (
                      <tr key={cand.id ?? `cand-${email}`} className={isSelected ? 'selected' : ''}>
                        <td>
                          <input type="checkbox" className="hr-check" checked={isSelected} onChange={() => handleSelectRow(cand.id)} />
                        </td>
                        <td>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <div className={`hr-avatar ${getAvatarColorClass(name)}`}>{getInitials(name)}</div>
                            <div style={{ display: 'flex', flexDirection: 'column' }}>
                              <span style={{ fontWeight: 500, color: 'var(--hr-text)' }}>{name}</span>
                              <span style={{ fontSize: '0.8rem', color: 'var(--hr-muted)' }}>{email}</span>
                            </div>
                          </div>
                        </td>
                        <td>
                          <div className="hr-skill-wrap">
                            {skills.length > 0 ? skills.map(s => <span key={s} className="hr-skill-chip">{s}</span>) : <span style={{ color: 'var(--hr-muted)' }}>-</span>}
                          </div>
                        </td>
                        <td><span className="hr-job-pill">{job}</span></td>
                        <td>
                          <div className="hr-score-wrap">
                            <span className="hr-score-text">{score}%</span>
                            <div className="hr-score-bar"><div className="hr-score-fill" style={{ width: `${score}%` }} /></div>
                          </div>
                        </td>
                        <td><span className={`hr-status-pill ${getStatusPillClass(status)}`}>{status}</span></td>
                        <td>
                          <span style={{ fontSize: '0.85rem', color: hasResume ? 'var(--hr-green)' : 'var(--hr-muted)' }}>
                            {hasResume ? 'Parsed' : 'Not uploaded'}
                          </span>
                        </td>
                        <td>
                          <div className="hr-actions">
                            <button className="hr-btn-view" onClick={() => openDrawer(cand)}>View</button>
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
                        {candidates.length === 0
                          ? 'No candidates in the system yet.'
                          : 'No candidates match the current filters.'}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      </main>

      {/* Detail Drawer */}
      {activeCandidate && (
        <>
          <div className="hr-drawer-overlay" onClick={closeDrawer} />
          <aside className="hr-drawer">
            <div className="hr-drawer-header">
              <h2>{normalizeName(activeCandidate)}</h2>
              <button className="hr-drawer-close" onClick={closeDrawer} aria-label="Close">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
              </button>
            </div>

            <div className="hr-drawer-body">
              <section className="hr-drawer-section">
                <h3>Contact</h3>
                <p><strong>Email:</strong> {normalizeEmail(activeCandidate)}</p>
                <p><strong>Phone:</strong> <span className="hr-muted-text">Not available yet</span></p>
              </section>

              <section className="hr-drawer-section">
                <h3>Resume profile</h3>
                <p><strong>Education:</strong> <span className="hr-muted-text">Resume detail not available from current endpoint.</span></p>
                <p><strong>Experience:</strong> <span className="hr-muted-text">Resume detail not available from current endpoint.</span></p>
                <p><strong>Projects:</strong> <span className="hr-muted-text">Not available yet</span></p>
                <p><strong>Certifications:</strong> <span className="hr-muted-text">Not available yet</span></p>
              </section>

              <section className="hr-drawer-section">
                <h3>Skills</h3>
                <div className="hr-skill-wrap">
                  {normalizeSkills(activeCandidate.skills || activeCandidate.matchedSkills || activeCandidate.matched_skills).length > 0 ? (
                    normalizeSkills(activeCandidate.skills || activeCandidate.matchedSkills || activeCandidate.matched_skills).map(s => (
                      <span key={s} className="hr-skill-chip">{s}</span>
                    ))
                  ) : (
                    <span className="hr-muted-text">No skills listed</span>
                  )}
                </div>
              </section>

              <section className="hr-drawer-section">
                <h3>Matched jobs</h3>
                {drawerLoading && <p className="hr-muted-text">Loading match details...</p>}
                {drawerError && <p className="hr-muted-text">{drawerError}</p>}
                {!drawerLoading && !drawerError && drawerDetail && drawerDetail.length === 0 && (
                  <p className="hr-muted-text">No matches found for this candidate.</p>
                )}
                {!drawerLoading && drawerDetail && drawerDetail.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {drawerDetail.map((m) => {
                      const mScore = normalizeScore(m);
                      const missing = normalizeSkills(m.missingSkills ?? m.missing_skills);
                      const matched = normalizeSkills(m.matchedSkills ?? m.matched_skills);
                      return (
                        <div key={m.id ?? `${m.job_id}-${mScore}`} className="hr-drawer-match-card">
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                            <strong>{m.jobTitle || 'Unknown role'}</strong>
                            <span className="hr-score-text">{mScore}%</span>
                          </div>
                          {m.explanation && <p style={{ margin: '0 0 8px 0', fontSize: '0.85rem', color: 'var(--hr-muted)' }}>{m.explanation}</p>}
                          {matched.length > 0 && (
                            <div className="hr-skill-wrap" style={{ marginBottom: '6px' }}>
                              {matched.map(s => <span key={`m-${s}`} className="hr-skill-chip">{s}</span>)}
                            </div>
                          )}
                          {missing.length > 0 && (
                            <div className="hr-skill-wrap">
                              {missing.map(s => <span key={`x-${s}`} className="hr-skill-chip-missing">{s}</span>)}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </section>

              <section className="hr-drawer-section">
                <h3>Note</h3>
                <textarea
                  className="hr-drawer-note"
                  placeholder="Add a note about this candidate..."
                  value={noteDraft}
                  onChange={(e) => setNoteDraft(e.target.value)}
                  rows={3}
                />
                <p className="hr-drawer-helper">Interview and notes require backend support to persist.</p>
              </section>
            </div>

            <div className="hr-drawer-footer">
              <button className="hr-btn-shortlist" onClick={() => handleStatusUpdate(activeCandidate.id, 'Shortlisted')}>Shortlist</button>
              <button className="hr-btn-reject" onClick={() => handleStatusUpdate(activeCandidate.id, 'Rejected')}>Reject</button>
              <button className="hr-btn-view" disabled title="Interview and notes require backend support to persist.">Move to interview</button>
            </div>
          </aside>
        </>
      )}
    </div>
  );
};

export default Candidates;
