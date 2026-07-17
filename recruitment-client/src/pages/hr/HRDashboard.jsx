import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { BrainCircuit, BriefcaseBusiness, ClipboardCheck, Users } from 'lucide-react';

import ActionHeader from '../../components/ActionHeader';
import CandidateCard from '../../components/CandidateCard';
import CandidateDrawer from '../../components/CandidateDrawer';
import ErrorState from '../../components/ErrorState';
import LoadingSkeleton from '../../components/LoadingSkeleton';
import Pipeline from '../../components/Pipeline';
import RecruitAIAssistant from '../../components/RecruitAIAssistant';
import RecruitAIEngine from '../../components/RecruitAIEngine';
import ReviewAlert from '../../components/ReviewAlert';
import SectionHeader from '../../components/SectionHeader';
import StatisticsCard from '../../components/StatisticsCard';
import aiService from '../../services/aiService';
import analyticsService from '../../services/analyticsService';
import authService from '../../services/authService';
import matchingService from '../../services/matchingService';

const normalizeSkills = (skills) => {
  if (!skills) return [];
  if (Array.isArray(skills)) return skills;
  return String(skills).split(',').map((skill) => skill.trim()).filter(Boolean);
};

const HRDashboard = () => {
  const user = authService.getCurrentUser() || {};
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [warning, setWarning] = useState('');
  const [feedback, setFeedback] = useState('');
  const [stats, setStats] = useState({});
  const [pipeline, setPipeline] = useState({});
  const [matches, setMatches] = useState([]);
  const [aiStatus, setAiStatus] = useState(null);
  const [activeCandidate, setActiveCandidate] = useState(null);
  const [drawerDetail, setDrawerDetail] = useState([]);
  const [drawerLoading, setDrawerLoading] = useState(false);
  const [drawerError, setDrawerError] = useState('');
  const [noteDraft, setNoteDraft] = useState('');

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    setWarning('');
    const results = await Promise.allSettled([
      analyticsService.getOverview(),
      analyticsService.getPipeline(),
      matchingService.getAllMatches(),
      aiService.getStatus(),
    ]);

    if (results[0].status === 'fulfilled') setStats(results[0].value || {});
    if (results[1].status === 'fulfilled') setPipeline(results[1].value || {});
    if (results[2].status === 'fulfilled') setMatches(Array.isArray(results[2].value) ? results[2].value : []);
    if (results[3].status === 'fulfilled') setAiStatus(results[3].value);

    const failed = results
      .map((result, index) => result.status === 'rejected' ? ['analytics overview', 'pipeline', 'candidate matches', 'AI status'][index] : null)
      .filter(Boolean);
    if (failed.length === results.length) setError('The HR dashboard could not load from the backend.');
    else if (failed.length) setWarning(`Some dashboard data is unavailable: ${failed.join(', ')}.`);
    setLoading(false);
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const pipelineStages = useMemo(() => [
    { label: 'Applied', count: pipeline.applied || 0 },
    { label: 'AI Review', count: pipeline.ai_review || 0 },
    { label: 'Manual Review', count: pipeline.manual_review || 0, isAlert: (pipeline.manual_review || 0) > 0 },
    { label: 'Shortlisted', count: pipeline.shortlisted || 0 },
    { label: 'Interview', count: pipeline.interview || 0 },
    { label: 'Offer', count: pipeline.offer || 0 },
  ], [pipeline]);

  const updateStatus = async (id, status) => {
    const previous = matches;
    setMatches((items) => items.map((item) => item.id === id ? { ...item, status } : item));
    setActiveCandidate((item) => item?.id === id ? { ...item, status } : item);
    try {
      await matchingService.updateMatchStatus(id, status);
      setFeedback(`Application moved to ${status}.`);
      window.setTimeout(() => setFeedback(''), 3000);
      const nextPipeline = await analyticsService.getPipeline();
      setPipeline(nextPipeline);
    } catch (err) {
      setMatches(previous);
      setFeedback(err.response?.data?.detail || 'Status update failed. Previous state was restored.');
    }
  };

  const openCandidate = async (candidate) => {
    setActiveCandidate(candidate);
    setDrawerDetail([candidate]);
    setDrawerError('');
    setNoteDraft('');
    const userId = candidate.user_id || candidate.userId;
    if (!userId) return;
    setDrawerLoading(true);
    try {
      const details = await matchingService.getCandidateMatches(userId);
      setDrawerDetail(details);
    } catch {
      setDrawerError('Detailed candidate evaluation is temporarily unavailable.');
    } finally {
      setDrawerLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="hr-page">
        <ActionHeader title="Overview" subtitle="Loading recruitment metrics…" />
        <LoadingSkeleton type="grid" count={4} />
      </div>
    );
  }
  if (error) return <ErrorState message={error} onRetry={loadData} />;

  return (
    <div className="hr-page">
      <ActionHeader
        title={`Welcome back, ${user.name || user.fullName || 'HR'} 👋`}
        subtitle="Live recruitment data and transparent AI status."
        actions={<button type="button" className="hr-refresh-btn" onClick={loadData}>↻ Refresh Dashboard</button>}
      />

      {warning && <ReviewAlert title="Partial data warning" message={warning} type="warning" />}
      {feedback && <ReviewAlert title="Update" message={feedback} type={feedback.includes('failed') ? 'warning' : 'success'} />}
      <ReviewAlert title="AI safety notice" message="AI recommendations support decisions only. Final hiring decisions require professional HR review." type="warning" />

      <section className="hr-section-card">
        <SectionHeader title="Active Recruitment Pipeline" />
        <Pipeline stages={pipelineStages} />
      </section>

      <div className="hr-stat-grid">
        <StatisticsCard label="Applications" value={stats.total_applications || 0} iconBgClass="hr-icon-blue" helperText="Real submitted applications" icon={<Users size={20} />} />
        <StatisticsCard label="Active Jobs" value={stats.active_jobs || 0} iconBgClass="hr-icon-muted" helperText={`${stats.total_jobs || 0} jobs in total`} icon={<BriefcaseBusiness size={20} />} />
        <StatisticsCard label="AI Analyses" value={stats.ai_analyses_completed || 0} iconBgClass="hr-icon-green" helperText={`${stats.hybrid_analyses || 0} hybrid · ${stats.fallback_analyses || 0} fallback`} icon={<BrainCircuit size={20} />} />
        <StatisticsCard label="Manual Review" value={stats.manual_review || 0} iconBgClass="hr-icon-red" helperText="Awaiting an HR decision" trendColor={(stats.manual_review || 0) > 0 ? 'red' : 'green'} icon={<ClipboardCheck size={20} />} />
      </div>

      <div className="hr-ai-grid">
        <RecruitAIEngine status={aiStatus} />
        <RecruitAIAssistant onSendMessage={aiService.askRecruiter} />
      </div>

      <section className="hr-dashboard-candidates">
        <SectionHeader title="Top Matches & Evaluations" />
        {matches.length === 0 ? (
          <p className="hr-empty-inline">No analyzed applications yet.</p>
        ) : (
          <div className="hr-candidate-grid">
            {matches.slice().sort((a, b) => (b.matchScore || 0) - (a.matchScore || 0)).slice(0, 6).map((candidate) => (
              <CandidateCard
                key={candidate.id}
                name={candidate.name}
                role={candidate.jobTitle}
                score={candidate.matchScore || 0}
                aiSource={candidate.aiSource}
                matchedSkills={normalizeSkills(candidate.matchedSkills)}
                missingSkills={normalizeSkills(candidate.missingSkills)}
                confidence={candidate.confidenceLabel || 'Not available'}
                status={candidate.status}
                fallbackReason={candidate.fallbackReason}
                onAiSummary={() => openCandidate(candidate)}
                onReview={() => openCandidate(candidate)}
                onShortlist={() => updateStatus(candidate.id, 'Shortlisted')}
              />
            ))}
          </div>
        )}
      </section>

      <CandidateDrawer
        isOpen={Boolean(activeCandidate)}
        onClose={() => setActiveCandidate(null)}
        candidate={activeCandidate}
        detail={drawerDetail}
        loading={drawerLoading}
        error={drawerError}
        onStatusUpdate={updateStatus}
        noteDraft={noteDraft}
        onNoteChange={setNoteDraft}
      />
    </div>
  );
};

export default HRDashboard;
