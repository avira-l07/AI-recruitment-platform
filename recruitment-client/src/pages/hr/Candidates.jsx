import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import matchingService from '../../services/matchingService';

// Custom design components
import ActionHeader from '../../components/ActionHeader';
import SearchBar from '../../components/SearchBar';
import CandidateGrid from '../../components/CandidateGrid';
import AiSummaryDrawer from '../../components/AiSummaryDrawer';
import ResumeReviewDrawer from '../../components/ResumeReviewDrawer';
import EmptyState from '../../components/EmptyState';
import LoadingSkeleton from '../../components/LoadingSkeleton';
import ErrorState from '../../components/ErrorState';
import ReviewAlert from '../../components/ReviewAlert';

const normalizeSkills = (skills) => {
  if (!skills) return [];
  if (Array.isArray(skills)) return skills;
  if (typeof skills === 'string') return skills.split(',').map(s => s.trim()).filter(Boolean);
  return [];
};

const normalizeScore = (cand) => {
  const raw = cand?.score ?? cand?.matchScore ?? cand?.match_score ?? 0;
  return Number.isFinite(Number(raw)) ? Math.max(0, Math.min(100, Number(raw))) : 0;
};

const normalizeName = (cand) => cand?.name || cand?.full_name || cand?.candidate_name || 'Unknown Candidate';
const normalizeEmail = (cand) => cand?.email || cand?.candidate_email || 'No email';
const normalizeJob = (cand) => cand?.matchedJob || cand?.jobTitle || cand?.job_title || 'Various';
const normalizeStatus = (cand) => (cand?.status || 'Pending');

const Candidates = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [feedback, setFeedback] = useState('');

  // Filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('All');
  const [minScore, setMinScore] = useState(0);

  // Selection & Detail Drawer states
  const [selectedIds, setSelectedIds] = useState(new Set());
  
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [activeDrawer, setActiveDrawer] = useState(null); // 'ai-summary', 'resume-review', null
  const [drawerDetail, setDrawerDetail] = useState([]);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [drawerError, setDrawerError] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await matchingService.getAllMatches();
      setCandidates(Array.isArray(res) ? res : []);
      setSelectedIds(new Set());
    } catch (err) {
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

  const filteredCandidates = useMemo(() => {
    return (candidates || []).filter(c => {
      const name = normalizeName(c).toLowerCase();
      const email = normalizeEmail(c).toLowerCase();
      const status = normalizeStatus(c).toLowerCase();
      const score = normalizeScore(c);

      if (searchTerm.trim() && !name.includes(searchTerm.toLowerCase()) && !email.includes(searchTerm.toLowerCase())) return false;
      if (statusFilter !== 'All' && status !== statusFilter.toLowerCase()) return false;
      if (score < minScore) return false;
      return true;
    }).sort((a, b) => normalizeScore(b) - normalizeScore(a));
  }, [candidates, searchTerm, statusFilter, minScore]);

  const handleSelectAll = (e) => {
    setSelectedIds(e.target.checked ? new Set(filteredCandidates.map(c => c.id)) : new Set());
  };

  const handleSelectRow = (id) => {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelectedIds(next);
  };

  const handleStatusUpdate = async (id, status) => {
    const previous = candidates;
    setCandidates(prev => prev.map(c => c.id === id ? { ...c, status } : c));
    setSelectedCandidate(prev => prev && prev.id === id ? { ...prev, status } : prev);
    try {
      await matchingService.updateMatchStatus(id, status);
      setFeedback(`Application moved to ${status}.`);
    } catch (err) {
      setCandidates(previous);
      setFeedback(err.response?.data?.detail || 'Status update failed. Previous state was restored.');
    }
    window.setTimeout(() => setFeedback(''), 3500);
  };

  const openAiSummary = async (cand) => {
    setSelectedCandidate(cand);
    setActiveDrawer('ai-summary');
    setDrawerDetail([]);
    setDrawerError(null);
    setDrawerLoading(true);

    const lookupId = cand?.user_id ?? cand?.userId ?? cand?.candidate_user_id ?? cand?.candidateId;
    if (!lookupId) {
      setDrawerError('Candidate profile mismatch.');
      setDrawerLoading(false);
      return;
    }

    try {
      const matches = await matchingService.getCandidateMatches(lookupId);
      setDrawerDetail(Array.isArray(matches) ? matches : []);
    } catch (err) {
      setDrawerError('Detailed evaluation is currently unavailable.');
    } finally {
      setDrawerLoading(false);
    }
  };

  const openResumeReview = (cand) => {
    setSelectedCandidate(cand);
    setActiveDrawer('resume-review');
  };

  const closeDrawer = () => {
    setSelectedCandidate(null);
    setActiveDrawer(null);
    setDrawerDetail([]);
    setDrawerError(null);
    setDrawerLoading(false);
  };

  if (loading) {
    return (
      <div className="hr-page">
        <ActionHeader title="Candidates" subtitle="Search and review applicants" />
        <div style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-6)' }}>
          <LoadingSkeleton type="grid" count={4} />
        </div>
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadData} />;
  }

  return (
    <div className="hr-page">
      <ActionHeader 
        title="Candidates" 
        subtitle="Search, review, and evaluate all applicants" 
        actions={
          <button type="button" className="hr-refresh-btn" onClick={loadData}>
            ↻ Refresh
          </button>
        }
      />

      <ReviewAlert title="AI transparency" message="Every application displays the recorded Local AI, Gemini, Hybrid, or fallback source." type="success" />
      {feedback && <ReviewAlert title="Update" message={feedback} type={feedback.includes('failed') ? 'warning' : 'success'} />}

      {/* Filters */}
      <div style={{ display: 'flex', gap: 'var(--space-4)', marginBottom: 'var(--space-5)', flexWrap: 'wrap', alignItems: 'center', backgroundColor: 'var(--color-surface)', padding: 'var(--space-4)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)' }}>
        <div style={{ flex: 1, minWidth: '240px' }}>
          <SearchBar value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} placeholder="Search candidate name or email..." />
        </div>
        <select 
          value={statusFilter} 
          onChange={(e) => setStatusFilter(e.target.value)} 
          style={{ padding: '8px 12px', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', outline: 'none', backgroundColor: 'var(--color-surface)', fontSize: 'var(--font-sm)', cursor: 'pointer' }}
        >
          {['All', 'Applied', 'AI Review', 'Manual Review', 'Shortlisted', 'Interview', 'Offer', 'Hired', 'Rejected', 'Withdrawn'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', fontSize: 'var(--font-xs)' }}>
          <span>Min Score: {minScore}%</span>
          <input type="range" min="0" max="100" step="10" value={minScore} onChange={(e) => setMinScore(Number(e.target.value))} />
        </div>
      </div>

      {/* Table Card */}
      <div style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)', boxShadow: 'var(--elevation-1)' }}>
        <CandidateGrid 
          selectAllChecked={filteredCandidates.length > 0 && selectedIds.size === filteredCandidates.length}
          onSelectAll={handleSelectAll}
        >
          {filteredCandidates.map((cand) => {
            const name = normalizeName(cand);
            const score = normalizeScore(cand);
            const isSelected = selectedIds.has(cand.id);
            return (
              <tr key={cand.id} style={{ borderBottom: '1px solid var(--color-border)', backgroundColor: isSelected ? 'rgba(79, 70, 229, 0.02)' : 'transparent' }}>
                <td style={{ padding: 'var(--space-4) var(--space-5)' }}>
                  <input type="checkbox" checked={isSelected} onChange={() => handleSelectRow(cand.id)} />
                </td>
                <td style={{ padding: 'var(--space-4) var(--space-5)', fontWeight: 'var(--weight-semibold)', fontSize: 'var(--font-sm)' }}>
                  {cand.id}
                </td>
                <td style={{ padding: 'var(--space-4) var(--space-5)' }}>
                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <span style={{ fontWeight: 'var(--weight-medium)', color: 'var(--color-text)' }}>{name}</span>
                    <span style={{ fontSize: 'var(--font-xs)', color: 'var(--color-muted)' }}>{normalizeEmail(cand)}</span>
                  </div>
                </td>
                <td style={{ padding: 'var(--space-4) var(--space-5)' }}>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                    {normalizeSkills(cand.skills || cand.matchedSkills).slice(0, 3).map(s => (
                      <span key={s} style={{ backgroundColor: 'var(--color-background)', border: '1px solid var(--color-border)', fontSize: '11px', padding: '2px 8px', borderRadius: '4px', color: 'var(--color-text)' }}>{s}</span>
                    ))}
                  </div>
                </td>
                <td style={{ padding: 'var(--space-4) var(--space-5)' }}>
                  <span style={{ fontSize: 'var(--font-xs)', color: 'var(--color-primary)', fontWeight: 'var(--weight-semibold)' }}>{normalizeJob(cand)}</span>
                </td>
                <td style={{ padding: 'var(--space-4) var(--space-5)', fontWeight: 'var(--weight-bold)', color: score >= 75 ? 'var(--color-success)' : score >= 50 ? 'var(--color-warning)' : 'var(--color-danger)' }}>
                  {score}%
                </td>
                <td style={{ padding: 'var(--space-4) var(--space-5)', fontSize: 'var(--font-xs)', color: 'var(--color-muted)' }}>
                  {cand.aiSource === 'hybrid' ? 'Hybrid AI' : cand.aiSource === 'gemini' ? 'Gemini AI' : cand.aiSource === 'local_fallback' ? 'Local Fallback' : 'Local AI'}
                </td>
                <td style={{ padding: 'var(--space-4) var(--space-5)' }}>
                  <span style={{ fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-semibold)', color: normalizeStatus(cand) === 'Shortlisted' ? 'var(--color-success)' : normalizeStatus(cand) === 'Rejected' ? 'var(--color-danger)' : 'var(--color-warning)' }}>
                    {normalizeStatus(cand)}
                  </span>
                </td>
                <td style={{ padding: 'var(--space-4) var(--space-5)' }}>
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button onClick={() => openAiSummary(cand)} style={{ border: '1px solid var(--color-border)', background: 'none', padding: '4px 10px', borderRadius: '4px', cursor: 'pointer', fontSize: 'var(--font-xs)' }}>AI Summary</button>
                    <button onClick={() => openResumeReview(cand)} style={{ border: '1px solid var(--color-border)', background: 'none', padding: '4px 10px', borderRadius: '4px', cursor: 'pointer', fontSize: 'var(--font-xs)' }}>Review</button>
                    <button onClick={() => handleStatusUpdate(cand.id, 'Shortlisted')} style={{ backgroundColor: 'var(--color-primary)', color: '#fff', border: 'none', padding: '4px 10px', borderRadius: '4px', cursor: 'pointer', fontSize: 'var(--font-xs)' }}>Shortlist</button>
                  </div>
                </td>
              </tr>
            );
          })}
        </CandidateGrid>

        {filteredCandidates.length === 0 && (
          <EmptyState message="No candidates match filters." subMessage="Try adjusting the search query, min score, or status." />
        )}
      </div>

      {/* AI Summary Drawer */}
      <AiSummaryDrawer
        isOpen={activeDrawer === 'ai-summary'}
        onClose={closeDrawer}
        candidate={selectedCandidate}
        detail={drawerDetail}
        loading={drawerLoading}
        error={drawerError}
        onStatusUpdate={handleStatusUpdate}
        onRetry={() => selectedCandidate && openAiSummary(selectedCandidate)}
      />

      {/* Resume Review Drawer */}
      <ResumeReviewDrawer
        isOpen={activeDrawer === 'resume-review'}
        onClose={closeDrawer}
        applicationId={selectedCandidate?.application_id || selectedCandidate?.id}
        candidate={selectedCandidate}
        onStatusUpdate={handleStatusUpdate}
      />
    </div>
  );
};

export default Candidates;
