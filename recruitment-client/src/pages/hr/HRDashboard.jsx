import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Sparkles, UserPlus, FileText, Activity, AlertCircle, Briefcase, Ban, RotateCcw, CheckSquare, Star, XOctagon, Wifi, WifiOff } from 'lucide-react';
import authService from '../../services/authService';
import analyticsService from '../../services/analyticsService';
import matchingService from '../../services/matchingService';
import { useHRRealtime } from '../../hooks/useHRRealtime';

// Import Reusable Design System Components
import ActionHeader from '../../components/ActionHeader';
import StatisticsCard from '../../components/StatisticsCard';
import Pipeline from '../../components/Pipeline';
import RecruitAIEngine from '../../components/RecruitAIEngine';
import AIInsights from '../../components/AIInsights';
import RecruitAIAssistant from '../../components/RecruitAIAssistant';
import CandidateCard from '../../components/CandidateCard';
import ReviewAlert from '../../components/ReviewAlert';
import SectionHeader from '../../components/SectionHeader';
import LoadingSkeleton from '../../components/LoadingSkeleton';
import ErrorState from '../../components/ErrorState';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const normalizeSkills = (skills) => {
  if (!skills) return [];
  if (Array.isArray(skills)) return skills;
  if (typeof skills === 'string') return skills.split(',').map(s => s.trim()).filter(Boolean);
  return [];
};

const normalizeName = (cand) => cand?.name || cand?.full_name || cand?.candidate_name || 'Unknown Candidate';
const normalizeJob = (cand) => cand?.matchedJob || cand?.jobTitle || cand?.job_title || 'Various';

const LiveActivityFeed = ({ events, streamStatus }) => {
  const getEventIcon = (type) => {
    switch (type) {
      case 'candidate_registered': return <UserPlus size={14} style={{ color: '#3B82F6' }} />;
      case 'resume_parsing_started': return <Activity size={14} style={{ color: '#60A5FA' }} />;
      case 'resume_parsed': return <CheckSquare size={14} style={{ color: '#34D399' }} />;
      case 'local_analysis_completed': return <Activity size={14} style={{ color: '#10B981' }} />;
      case 'gemini_generation_started': return <Sparkles size={14} style={{ color: '#FCD34D' }} />;
      case 'gemini_generation_completed': return <Sparkles size={14} style={{ color: '#F59E0B' }} />;
      case 'gemini_quota_exceeded': return <AlertCircle size={14} style={{ color: '#EF4444' }} />;
      case 'gemini_timeout': return <AlertCircle size={14} style={{ color: '#EF4444' }} />;
      case 'gemini_generation_failed': return <AlertCircle size={14} style={{ color: '#EF4444' }} />;
      case 'job_created': return <Briefcase size={14} style={{ color: '#3B82F6' }} />;
      case 'job_closed': return <Ban size={14} style={{ color: '#6B7280' }} />;
      case 'job_reopened': return <RotateCcw size={14} style={{ color: '#10B981' }} />;
      case 'matching_applied': return <CheckSquare size={14} style={{ color: '#F59E0B' }} />;
      case 'matching_shortlisted': return <Star size={14} style={{ color: '#10B981' }} />;
      case 'matching_rejected': return <XOctagon size={14} style={{ color: '#EF4444' }} />;
      default: return <Activity size={14} style={{ color: '#6B7280' }} />;
    }
  };

  const getEventLabel = (e) => {
    const d = e.details || {};
    switch (e.event_type) {
      case 'candidate_registered': return `New Candidate: ${d.full_name || 'Anonymous'}`;
      case 'resume_parsing_started': return `Resume parsing started: ${d.file_name || 'resume.pdf'}`;
      case 'resume_parsed': return `Resume text parsed successfully`;
      case 'local_analysis_completed': return `Local analysis: Score ${d.quality_score || 0}%`;
      case 'gemini_generation_started': return `Gemini suggestions started`;
      case 'gemini_generation_completed': return `Gemini suggestions generated`;
      case 'gemini_quota_exceeded': return `Gemini quota exceeded fallback`;
      case 'gemini_timeout': return `Gemini connection timeout fallback`;
      case 'gemini_generation_failed': return `Gemini suggestions failed`;
      case 'job_created': return `Job created: ${d.title || 'Software Developer'}`;
      case 'job_closed': return `Job closed: ${d.title || 'Job ID ' + d.job_id}`;
      case 'job_reopened': return `Job reopened: ${d.title || 'Job ID ' + d.job_id}`;
      case 'matching_applied': return `Applied: ${d.job_title || 'Role'} (${d.score || 0}%)`;
      case 'matching_shortlisted': return `Shortlisted Candidate #${e.candidate_id || d.match_id}`;
      case 'matching_rejected': return `Rejected Candidate #${e.candidate_id || d.match_id}`;
      default: return e.event_type;
    }
  };

  return (
    <div style={{
      backgroundColor: '#0F172A',
      color: '#FFFFFF',
      borderRadius: 'var(--radius-lg)',
      padding: 'var(--space-5)',
      border: '1px solid #1E293B',
      boxShadow: 'var(--elevation-2)',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      minHeight: '260px'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
        <h3 style={{ margin: 0, fontSize: 'var(--font-md)', fontWeight: 'var(--weight-semibold)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          Live Event Feed
        </h3>
        <span style={{ fontSize: 'var(--font-xs)', display: 'flex', alignItems: 'center', gap: '4px', color: streamStatus === 'connected' ? '#10B981' : '#EF4444' }}>
          {streamStatus === 'connected' ? <Wifi size={13} /> : <WifiOff size={13} />}
          {streamStatus === 'connected' ? 'Live' : 'Offline'}
        </span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto', flex: 1, maxHeight: '180px', paddingRight: '4px' }} className="activity-scroll">
        {events.length === 0 ? (
          <p style={{ margin: 'auto', fontSize: 'var(--font-xs)', color: '#64748B', textAlign: 'center' }}>Awaiting activity stream events...</p>
        ) : (
          events.map((e, idx) => (
            <div key={e.id || idx} style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center', backgroundColor: '#1E293B', padding: '6px 10px', borderRadius: 'var(--radius-md)', border: '1px solid rgba(255,255,255,0.02)' }}>
              <span>{getEventIcon(e.event_type)}</span>
              <div style={{ flex: 1, fontSize: 'var(--font-xs)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={getEventLabel(e)}>
                {getEventLabel(e)}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

const HRDashboard = () => {
  const user = authService.getCurrentUser() || {};
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const [matches, setMatches] = useState([]);
  
  const [aiStatus, setAiStatus] = useState(null);

  const loadAiStatus = useCallback(async () => {
    try {
      const res = await analyticsService.getAiStatus();
      setAiStatus(res);
    } catch (e) {
      console.warn("Failed to load AI engine status", e);
    }
  }, []);

  const loadData = useCallback(async (showLoader = true) => {
    if (showLoader) setLoading(true);
    setError(null);
    try {
      const [overview, allMatches] = await Promise.all([
        analyticsService.getOverview(),
        matchingService.getAllMatches(),
        loadAiStatus()
      ]);
      setStats(overview);
      setMatches(Array.isArray(allMatches) ? allMatches : []);
    } catch (err) {
      setError('Failed to fetch dashboard intelligence.');
    } finally {
      if (showLoader) setLoading(false);
    }
  }, [loadAiStatus]);

  const handleNewEvent = useCallback((event) => {
    loadData(false);
  }, [loadData]);

  const { events, streamStatus } = useHRRealtime(handleNewEvent);

  useEffect(() => {
    loadData(true);
  }, [loadData]);

  const handleShortlist = async (id) => {
    try {
      await matchingService.updateMatchStatus(id, 'Shortlisted');
      setMatches(prev => prev.map(c => c.id === id ? { ...c, status: 'Shortlisted' } : c));
    } catch (err) {
      console.error('Failed to update status', err);
    }
  };

  const handleStatusUpdate = async (id, status) => {
    try {
      await matchingService.updateMatchStatus(id, status);
      setMatches(prev => prev.map(c => c.id === id ? { ...c, status } : c));
    } catch (err) {
      console.error('Failed to update status', err);
    }
  };

  // Derive dynamic recruitment pipeline from matches database
  const getPipelineStages = () => {
    const total = stats?.total_candidates ?? stats?.totalCandidates ?? matches.length;
    const reviewed = matches.filter(m => (m.score ?? m.matchScore) > 0).length;
    const pendingReview = matches.filter(m => (m.status || 'Pending').toLowerCase() === 'pending').length;
    const shortlisted = matches.filter(m => (m.status || '').toLowerCase() === 'shortlisted').length;
    const interview = matches.filter(m => (m.status || '').toLowerCase() === 'interview').length;
    
    return [
      { label: 'Applied', count: total },
      { label: 'AI Reviewed', count: reviewed },
      { label: 'Manual Review', count: pendingReview, isAlert: pendingReview > 0 },
      { label: 'Shortlisted', count: shortlisted },
      { label: 'Interview', count: interview }
    ];
  };

  if (loading) {
    return (
      <div className="hr-page">
        <ActionHeader title="Overview" subtitle="Loading recruitment metrics..." />
        <LoadingSkeleton type="grid" count={3} />
      </div>
    );
  }

  if (error) {
    return <ErrorState message={error} onRetry={() => loadData(true)} />;
  }

  const totalCandidates = stats?.total_candidates ?? stats?.totalCandidates ?? 0;
  const totalJobs = stats?.total_jobs ?? stats?.totalJobs ?? 0;
  const shortlistedCount = matches.filter(m => (m.status || '').toLowerCase() === 'shortlisted').length;
  const pendingCount = matches.filter(m => (m.status || 'Pending').toLowerCase() === 'pending').length;

  // Map AI Engine status dynamic metrics
  const activeGenerations = aiStatus?.active_generations ?? 0;
  const failedAnalyses = aiStatus?.failed_analyses ?? 0;
  const geminiEngineState = activeGenerations > 0 ? 'generating' : failedAnalyses > 0 ? 'failed' : 'completed';
  const hybridEngineState = activeGenerations > 0 ? 'generating' : 'completed';

  return (
    <div className="hr-page">
      {/* 1. Page Header */}
      <ActionHeader 
        title={`Welcome back, ${user.name || user.fullName || 'Aviral'} 👋`}
        subtitle="Here is what requires your attention today."
        actions={
          <button type="button" className="hr-refresh-btn" onClick={() => loadData(true)}>
            ↻ Refresh Dashboard
          </button>
        }
      />

      {/* 2. Safety Callout Banner */}
      <ReviewAlert 
        title="AI safety notice" 
        message="AI recommendations support decisions only. Final hiring calls require HR professional review." 
        type="warning"
      />

      {/* 3. Pipeline Section */}
      <div style={{ marginBottom: 'var(--space-6)', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)', boxShadow: 'var(--elevation-1)' }}>
        <SectionHeader title="Active Recruitment Pipeline" style={{ marginBottom: 'var(--space-4)' }} />
        <Pipeline stages={getPipelineStages()} />
      </div>

      {/* 4. Statistics Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-4)', marginBottom: 'var(--space-6)' }}>
        <StatisticsCard label="Total Candidates" value={totalCandidates} iconBgClass="hr-icon-blue" helperText="Registered applicant base" icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle></svg>} />
        <StatisticsCard label="Total Jobs" value={totalJobs} iconBgClass="hr-icon-muted" helperText="Active corporate openings" icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>} />
        <StatisticsCard label="AI Reviewed" value={matches.length} iconBgClass="hr-icon-green" helperText="ATS score evaluations completed" trendColor="green" icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>} />
        <StatisticsCard label="Manual Review" value={pendingCount} iconBgClass="hr-icon-red" helperText="Awaiting shortlist/reject decisions" trendColor={pendingCount > 0 ? 'red' : 'green'} icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line></svg>} />
      </div>

      {/* 5. Core AI Status, Feed and Chat Panels */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1.2fr', gap: 'var(--space-4)', marginBottom: 'var(--space-6)', alignItems: 'stretch' }}>
        <RecruitAIEngine mode="hybrid" localStatus="completed" geminiStatus={geminiEngineState} hybridStatus={hybridEngineState} lastSync="Synced" />
        <LiveActivityFeed events={events} streamStatus={streamStatus} />
        <RecruitAIAssistant onSendMessage={(msg) => console.log(`Assistant input: ${msg}`)} />
      </div>

      {/* 6. Top Candidates */}
      <div style={{ marginBottom: 'var(--space-6)' }}>
        <SectionHeader title="Top Matches & Evaluations" />
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 'var(--space-4)' }}>
          {matches.slice(0, 3).map((cand) => (
            <CandidateCard 
              key={cand.id}
              name={normalizeName(cand)}
              role={normalizeJob(cand)}
              score={cand.score ?? cand.matchScore ?? 0}
              aiSource={cand.aiSource}
              matchedSkills={normalizeSkills(cand.matchedSkills || cand.matched_skills)}
              missingSkills={normalizeSkills(cand.missingSkills || cand.missing_skills)}
              confidence={cand.fitLabel || 'High'}
              status={cand.status}
              onAiSummary={() => console.log("AI details:", cand)}
              onReview={() => console.log("Review details:", cand)}
              onShortlist={() => handleShortlist(cand.id)}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default HRDashboard;
