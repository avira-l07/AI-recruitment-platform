import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, ShieldAlert, AlertTriangle, RefreshCw, History, 
  CheckCircle2, XCircle, Save, Loader2, Sparkles, UserCheck 
} from 'lucide-react';
import verificationService from '../../services/verificationService';
import TrustScoreGauge from './TrustScoreGauge';
import CompanyVerificationCard from './CompanyVerificationCard';
import ProjectVerificationTable from './ProjectVerificationTable';
import TimelineVisualization from './TimelineVisualization';
import EvidenceGraph from './EvidenceGraph';
import EvidenceSourcesTable from './EvidenceSourcesTable';
import AiReasoningCard from './AiReasoningCard';
import ResumeAuthenticityCard from './ResumeAuthenticityCard';
import VerificationHistoryModal from './VerificationHistoryModal';
import './VerificationTab.css';

const STAGES = [
  'Searching Company Registry',
  'Validating Repository Links',
  'Analyzing Technical Projects',
  'Building Chronological Timeline',
  'Generating AI Grounded Reasoning',
  'Calculating Enterprise Trust Score'
];

const VerificationTab = ({ candidateId, candidate, isBlindMode = false }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reverifying, setReverifying] = useState(false);
  const [stageIndex, setStageIndex] = useState(0);
  const [error, setError] = useState('');
  
  // HR Decision state
  const [decision, setDecision] = useState('');
  const [notes, setNotes] = useState('');
  const [savingDecision, setSavingDecision] = useState(false);
  const [decisionSuccess, setDecisionSuccess] = useState(false);

  // History modal
  const [showHistory, setShowHistory] = useState(false);

  const fetchVerification = async (isReverify = false) => {
    if (isReverify) {
      setReverifying(true);
    } else {
      setLoading(true);
    }
    setError('');

    // Simulate progress stages
    let stageInterval;
    if (isReverify || !data) {
      setStageIndex(0);
      stageInterval = setInterval(() => {
        setStageIndex((prev) => (prev < STAGES.length - 1 ? prev + 1 : prev));
      }, 400);
    }

    try {
      let res;
      if (isReverify && data?.id) {
        res = await verificationService.reverify(data.id);
      } else {
        res = await verificationService.getCandidateVerification(candidateId);
      }
      setData(res);
      setDecision(res.hr_decision || '');
      setNotes(res.hr_decision_notes || '');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load experience verification data.');
    } finally {
      if (stageInterval) clearInterval(stageInterval);
      setLoading(false);
      setReverifying(false);
    }
  };

  useEffect(() => {
    if (candidateId) {
      fetchVerification(false);
    }
  }, [candidateId, isBlindMode]);

  const handleDecisionSubmit = async (selectedDecision) => {
    if (!data?.id) return;
    setSavingDecision(true);
    setDecisionSuccess(false);
    try {
      const res = await verificationService.submitDecision(data.id, selectedDecision, notes);
      setData(res);
      setDecision(res.hr_decision);
      setDecisionSuccess(true);
      setTimeout(() => setDecisionSuccess(false), 3000);
    } catch (err) {
      setError('Failed to record HR decision.');
    } finally {
      setSavingDecision(false);
    }
  };

  if (loading) {
    return (
      <div className="verif-loading-wrapper">
        <div className="verif-spinner-wrap">
          <Loader2 className="verif-spinner" size={36} />
          <Sparkles className="verif-sparkle-center" size={16} />
        </div>
        <h4 className="verif-loading-title">Analyzing Digital Footprint...</h4>
        <p className="verif-loading-stage">{STAGES[stageIndex]}</p>
        <div className="verif-progress-bar-wrap">
          <div className="verif-progress-bar-fill" style={{ width: `${((stageIndex + 1) / STAGES.length) * 100}%` }} />
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="verif-error-box">
        <AlertTriangle size={24} />
        <p>{error}</p>
        <button onClick={() => fetchVerification(false)} className="verif-retry-btn">
          <RefreshCw size={14} /> Retry Verification
        </button>
      </div>
    );
  }

  return (
    <div className="verif-tab-container">
      {/* Top Header Controls */}
      <div className="verif-topbar">
        <div className="verif-topbar-left">
          <div className="verif-topbar-title-wrap">
            <ShieldCheck size={22} className="verif-topbar-icon" />
            <div>
              <h3 className="verif-topbar-heading">AI Trust & Experience Verification</h3>
              <span className="verif-topbar-sub">
                Candidate: <strong>{data?.candidate_name || `Candidate #C-${candidateId}`}</strong> • Version {data?.verification_version || 1}
              </span>
            </div>
          </div>
        </div>

        <div className="verif-topbar-actions">
          <button 
            className="verif-btn-secondary"
            onClick={() => setShowHistory(true)}
            title="View Reverification History"
          >
            <History size={14} />
            <span>History</span>
          </button>

          <button 
            className="verif-btn-primary"
            onClick={() => fetchVerification(true)}
            disabled={reverifying}
          >
            <RefreshCw size={14} className={reverifying ? 'verif-spin' : ''} />
            <span>{reverifying ? 'Re-Verifying...' : 'Re-Verify Experience'}</span>
          </button>
        </div>
      </div>

      {/* Main Trust Score Gauge Card */}
      <TrustScoreGauge 
        score={data?.trust_score || 0}
        outcome={data?.verification_outcome || 'needs_review'}
        confidenceLabel={data?.confidence_label || 'Medium'}
        breakdown={data?.trust_score_breakdown || []}
      />

      {/* AI Reasoning & Grounded Interview Suggestions */}
      <AiReasoningCard aiReasoning={data?.ai_reasoning || {}} />

      {/* Company Verification Section */}
      <CompanyVerificationCard companies={data?.company_verifications || []} />

      {/* Project & Repository Verification Table */}
      <ProjectVerificationTable projects={data?.project_verifications || []} />

      {/* Timeline Intelligence Engine */}
      <TimelineVisualization timelineData={data?.timeline_intelligence || {}} />

      {/* Evidence Graph */}
      <EvidenceGraph graphData={data?.evidence_graph || {}} />

      {/* Structured Evidence Sources Table */}
      <EvidenceSourcesTable sources={data?.evidence_sources || []} />

      {/* Resume Layout & White-text Authenticity */}
      <ResumeAuthenticityCard authenticity={data?.resume_authenticity || {}} />

      {/* HR Decision & Evaluation Panel */}
      <div className="verif-card verif-decision-panel">
        <div className="verif-card-header">
          <div className="verif-card-title-wrap">
            <UserCheck size={18} className="verif-card-icon" />
            <h3>HR Evaluation Decision & Manual Review</h3>
          </div>
          {data?.hr_decision && (
            <span className={`verif-decision-pill verif-dec-${data.hr_decision}`}>
              Current: {data.hr_decision.toUpperCase()}
            </span>
          )}
        </div>

        <p className="verif-decision-help">
          Record your conclusive human-in-the-loop review after investigating verified evidence and code repositories.
        </p>

        <div className="verif-decision-buttons">
          <button 
            className={`verif-dec-btn verif-dec-verified ${decision === 'verified' ? 'active' : ''}`}
            onClick={() => handleDecisionSubmit('verified')}
            disabled={savingDecision}
          >
            <CheckCircle2 size={16} />
            <span>Mark as Verified</span>
          </button>

          <button 
            className={`verif-dec-btn verif-dec-review ${decision === 'needs_review' ? 'active' : ''}`}
            onClick={() => handleDecisionSubmit('needs_review')}
            disabled={savingDecision}
          >
            <AlertTriangle size={16} />
            <span>Needs HR Review</span>
          </button>

          <button 
            className={`verif-dec-btn verif-dec-suspicious ${decision === 'suspicious' ? 'active' : ''}`}
            onClick={() => handleDecisionSubmit('suspicious')}
            disabled={savingDecision}
          >
            <ShieldAlert size={16} />
            <span>Mark as Suspicious</span>
          </button>
        </div>

        {/* HR Notes Textarea */}
        <div className="verif-notes-wrap">
          <label className="verif-notes-lbl">HR Audit Notes / Candidate Follow-up Notes:</label>
          <textarea
            className="verif-notes-input"
            rows="3"
            placeholder="Add internal audit notes (e.g. 'Spoke with supervisor, verified commit history on GitHub repository')..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
          <div className="verif-notes-actions">
            <button 
              className="verif-save-notes-btn"
              onClick={() => handleDecisionSubmit(decision || 'needs_review')}
              disabled={savingDecision}
            >
              <Save size={14} />
              <span>{savingDecision ? 'Saving...' : 'Save Notes'}</span>
            </button>
            {decisionSuccess && (
              <span className="verif-save-success">
                <CheckCircle2 size={14} /> Decision & notes recorded!
              </span>
            )}
          </div>
        </div>
      </div>

      {/* History Modal */}
      <VerificationHistoryModal 
        isOpen={showHistory}
        onClose={() => setShowHistory(false)}
        history={data?.history || []}
        currentVersion={data?.verification_version || 1}
        currentScore={data?.trust_score || 0}
      />
    </div>
  );
};

export default VerificationTab;
