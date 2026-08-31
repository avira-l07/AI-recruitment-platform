import React, { useEffect, useRef } from 'react';
import { X, Sparkles, ShieldAlert, Award, FileQuestion, GraduationCap, CheckCircle2, TrendingUp, UserCheck, AlertTriangle, ShieldCheck } from 'lucide-react';
import './AiSummaryDrawer.css';

const normalizeSkills = (skills) => {
  if (!skills) return [];
  if (Array.isArray(skills)) return skills;
  if (typeof skills === 'string') return skills.split(',').map(s => s.trim()).filter(Boolean);
  return [];
};

const getInitials = (name) => {
  if (!name) return '??';
  if (name.startsWith('Candidate #')) return 'C#';
  return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
};

const normalizeAiSourceLabel = (aiSource) => {
  const src = (aiSource || '').toLowerCase();
  if (src === 'hybrid' || src.includes('hybrid_') || src === 'gemini') {
    return 'Hybrid AI — Local + Gemini';
  }
  if (src === 'local_fallback') {
    return 'Local Hybrid AI (Fallback)';
  }
  return 'Local Hybrid AI';
};

const AiSummaryDrawer = ({
  isOpen,
  onClose,
  candidate,
  detail = [],
  loading,
  error,
  isBlindMode = false,
  onStatusUpdate,
  onRetry
}) => {
  const closeButtonRef = useRef(null);

  // Focus management: Focus the close button when the drawer opens
  useEffect(() => {
    if (isOpen && closeButtonRef.current) {
      closeButtonRef.current.focus();
    }
  }, [isOpen]);

  // Lock body scrolling when drawer is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  // Escape key handler to close the drawer
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen || !candidate) return null;

  const activeMatch = detail.length > 0 ? detail[0] : null;

  // Extract fields safely
  const candidateName = candidate.name || candidate.fullName || candidate.candidate_name || 'Unknown Candidate';
  const isBlind = isBlindMode || candidateName.startsWith('Candidate #');
  const jobTitle = activeMatch?.jobTitle || activeMatch?.job_title || candidate.jobTitle || 'Unknown Role';
  const matchScore = activeMatch?.matchScore ?? activeMatch?.score ?? 0;
  const fitScore = activeMatch?.fitScore ?? activeMatch?.fit_score ?? matchScore;
  const fitLabel = activeMatch?.fitLabel || activeMatch?.fit_label || 'Not evaluated';
  const aiSource = activeMatch?.aiSource || activeMatch?.ai_source || 'local_ai';
  const aiMatchSummary = activeMatch?.hrSummary || activeMatch?.hr_summary || activeMatch?.explanation || '';
  
  const confidenceVal = activeMatch?.confidenceScore ?? activeMatch?.confidence_score;
  const confidenceLabel = activeMatch?.confidenceLabel || activeMatch?.confidence_label;
  const displayConfidence = confidenceVal != null ? `${confidenceVal}%` : (confidenceLabel && confidenceLabel !== 'not available' ? confidenceLabel : 'Not available');

  const matchedSkills = normalizeSkills(activeMatch?.matchedSkills || activeMatch?.matched_skills);
  const semanticMatches = activeMatch?.semanticMatches || activeMatch?.semantic_matches || [];
  const missingSkills = normalizeSkills(activeMatch?.missingSkills || activeMatch?.missing_skills);
  const recommendedSkills = normalizeSkills(activeMatch?.recommendedSkills || activeMatch?.recommended_skills || activeMatch?.recommended_skills_list);
  const strengths = activeMatch?.strengths || activeMatch?.strengths_list || [];
  const weaknesses = activeMatch?.weaknesses || activeMatch?.weaknesses_list || activeMatch?.riskFlags || [];
  const recruiterRecommendation = activeMatch?.recommendation || activeMatch?.recruiterRecommendation || '';
  const interviewQuestions = activeMatch?.interviewQuestions || activeMatch?.interview_questions || [];
  const roadmap = activeMatch?.roadmap || [];

  return (
    <>
      <div 
        className="ai-summary-overlay" 
        onClick={onClose}
        aria-hidden="true"
      />
      <aside 
        className="ai-summary-drawer"
        role="dialog"
        aria-modal="true"
        aria-labelledby="ai-drawer-title"
      >
        {/* Drawer Header */}
        <div className="ai-summary-header">
          <div className="ai-summary-header-info">
            <div className="ai-summary-avatar" style={isBlind ? { backgroundColor: '#EBFDF3', color: '#00A83B' } : {}}>
              {isBlind ? <ShieldCheck size={20} /> : getInitials(candidateName)}
            </div>
            <div className="ai-summary-title">
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h2 id="ai-drawer-title">{candidateName}</h2>
                {isBlind && (
                  <span style={{ fontSize: '11px', backgroundColor: '#EBFDF3', color: '#00A83B', border: '1px solid #A3E6BA', padding: '2px 8px', borderRadius: '12px', fontWeight: 600 }}>
                    Fair Review Mode
                  </span>
                )}
              </div>
              <span>AI Evaluation Insights</span>
            </div>
          </div>
          <button 
            ref={closeButtonRef}
            onClick={onClose} 
            className="ai-summary-close-btn"
            aria-label="Close AI Summary drawer"
            type="button"
          >
            <X size={20} />
          </button>
        </div>

        {/* Drawer Body */}
        <div className="ai-summary-body">
          {loading && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ display: 'flex', gap: '16px' }}>
                <div className="ai-skeleton-bar" style={{ height: '70px', flex: 1 }} />
                <div className="ai-skeleton-bar" style={{ height: '70px', flex: 1 }} />
              </div>
              <div className="ai-skeleton-bar" style={{ height: '120px', width: '100%' }} />
              <div className="ai-skeleton-bar" style={{ height: '80px', width: '100%' }} />
              <div className="ai-skeleton-bar" style={{ height: '80px', width: '100%' }} />
            </div>
          )}

          {error && (
            <div className="ai-drawer-error-state">
              <ShieldAlert size={40} style={{ color: '#DC2626' }} />
              <p>{error}</p>
              {onRetry && (
                <button 
                  type="button" 
                  onClick={onRetry} 
                  className="ai-drawer-error-btn"
                >
                  Retry Loading
                </button>
              )}
            </div>
          )}

          {!loading && !error && !activeMatch && (
            <div className="ai-drawer-error-state">
              <ShieldAlert size={40} style={{ color: '#74809A' }} />
              <p>No stored AI analysis found for this candidate.</p>
            </div>
          )}

          {!loading && !error && activeMatch && (
            <>
              {/* Score & Fit Section */}
              <div className="ai-summary-score-section">
                <div className="ai-score-card">
                  <span className="ai-score-label">Match Score</span>
                  <div className="ai-score-value">{matchScore}%</div>
                  <span className="hr-confidence-text">
                    Confidence: <b>{displayConfidence}</b>
                  </span>
                </div>
                <div className="ai-score-card">
                  <span className="ai-score-label">Fit Assessment</span>
                  <div className="ai-score-value fit">{fitScore}%</div>
                  <span className={`ai-fit-badge ${fitLabel.toLowerCase()}`}>
                    {fitLabel}
                  </span>
                </div>
              </div>

              {/* AI Source Tag */}
              <div className="ai-section-block">
                <h3><Sparkles size={13} style={{ color: '#3B55E6' }} /> AI Engine Details</h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="hr-source-badge" style={{ backgroundColor: '#EEF2FF', color: '#3B55E6' }}>
                    <Sparkles size={10} />
                    {normalizeAiSourceLabel(aiSource)}
                  </span>
                </div>
              </div>

              {/* Match Summary */}
              {aiMatchSummary && (
                <div className="ai-section-block">
                  <h3><TrendingUp size={13} style={{ color: '#3B55E6' }} /> AI Match Summary</h3>
                  <div className="ai-summary-text-card">
                    <p>{aiMatchSummary}</p>
                  </div>
                </div>
              )}

              {/* Recruiter Recommendation */}
              {recruiterRecommendation && (
                <div className="ai-section-block">
                  <h3><UserCheck size={13} style={{ color: '#3B55E6' }} /> Recruiter Recommendation</h3>
                  <div className="ai-summary-text-card" style={{ borderLeft: '3px solid #3B55E6' }}>
                    <p style={{ fontWeight: '500' }}>{recruiterRecommendation}</p>
                  </div>
                </div>
              )}

              {/* Matched Skills */}
              {matchedSkills.length > 0 && (
                <div className="ai-section-block">
                  <h3>Matched Skills</h3>
                  <div className="hr-skills-list">
                    {matchedSkills.map(skill => (
                      <span key={skill} className="hr-skill-badge matched">{skill}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Semantic Matches */}
              {semanticMatches.length > 0 && (
                <div className="ai-section-block">
                  <h3>Semantic Skill Matches</h3>
                  <div className="ai-semantic-matches-list">
                    {semanticMatches.map((sem, i) => {
                      let skillName = '';
                      let matchText = '';

                      if (typeof sem === 'string') {
                        skillName = sem;
                      } else if (sem && typeof sem === 'object') {
                        skillName = sem.required_skill || sem.skill || '';
                        if (Array.isArray(sem.evidence_skills) && sem.evidence_skills.length > 0) {
                          matchText = sem.evidence_skills.join(', ');
                        } else if (sem.match) {
                          matchText = sem.match;
                        }
                      }

                      return (
                        <div key={i} className="ai-semantic-match-item">
                          <CheckCircle2 size={14} className="ai-semantic-match-icon" />
                          <span className="ai-semantic-match-text">
                            <b>{skillName}</b> {matchText && `matched via ${matchText}`}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Missing Skills */}
              {missingSkills.length > 0 && (
                <div className="ai-section-block">
                  <h3>Missing Skills</h3>
                  <div className="hr-skills-list">
                    {missingSkills.map(skill => (
                      <span key={skill} className="hr-skill-badge missing">{skill}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Recommended Skills */}
              {recommendedSkills.length > 0 && (
                <div className="ai-section-block">
                  <h3>Recommended Skills</h3>
                  <div className="hr-skills-list">
                    {recommendedSkills.map(skill => (
                      <span key={skill} className="hr-skill-badge" style={{ backgroundColor: '#F8FAFC', border: '1px solid #E8E0D5', color: '#07152E' }}>
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Strengths */}
              {strengths.length > 0 && (
                <div className="ai-section-block">
                  <h3>Strengths</h3>
                  <ul className="ai-bullets-list">
                    {strengths.map((str, i) => <li key={i}>{str}</li>)}
                  </ul>
                </div>
              )}

              {/* Weaknesses */}
              {weaknesses.length > 0 && (
                <div className="ai-section-block">
                  <h3>Weaknesses & Risks</h3>
                  <ul className="ai-bullets-list weaknesses">
                    {weaknesses.map((weak, i) => (
                      <li key={i} style={{ color: '#B96900' }}>
                        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                          <AlertTriangle size={12} /> {weak}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Suggested Interview Questions */}
              {interviewQuestions.length > 0 && (
                <div className="ai-section-block">
                  <h3><FileQuestion size={13} style={{ color: '#3B55E6' }} /> Suggested Interview Questions</h3>
                  <ol className="ai-numbered-list">
                    {interviewQuestions.map((q, i) => <li key={i}>{q}</li>)}
                  </ol>
                </div>
              )}

              {/* Learning / Improvement Roadmap */}
              {roadmap.length > 0 && (
                <div className="ai-section-block">
                  <h3><GraduationCap size={13} style={{ color: '#3B55E6' }} /> Suggested Learning Roadmap</h3>
                  <ol className="ai-numbered-list">
                    {roadmap.map((step, i) => <li key={i}>{step}</li>)}
                  </ol>
                </div>
              )}
            </>
          )}
        </div>

        {/* Drawer Footer */}
        <div className="ai-drawer-footer">
          <button 
            onClick={() => onStatusUpdate(candidate.id, 'Shortlisted')}
            className="ai-footer-btn primary"
            type="button"
          >
            Shortlist
          </button>
          <button 
            onClick={() => onStatusUpdate(candidate.id, 'Rejected')}
            className="ai-footer-btn secondary"
            type="button"
          >
            Reject
          </button>
        </div>
      </aside>
    </>
  );
};

export default AiSummaryDrawer;
