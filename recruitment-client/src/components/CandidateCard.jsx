import React from 'react';
import { Sparkles, User } from 'lucide-react';

const CandidateCard = ({ 
  name, 
  role, 
  score, 
  aiSource, 
  matchedSkills = [], 
  missingSkills = [], 
  confidence = 'High', 
  status,
  onAiSummary, 
  onReview, 
  onShortlist 
}) => {
  const getAiSourceBadge = () => {
    const source = (aiSource || '').toLowerCase();
    let label = 'LOCAL AI';

    if (source === 'hybrid') {
      label = 'HYBRID';
    } else if (source === 'gemini') {
      label = 'GEMINI';
    } else if (source === 'local_fallback') {
      label = 'LOCAL FALLBACK';
    } else if (source === 'local_ai' || source === 'local') {
      label = 'LOCAL AI';
    } else {
      label = source.toUpperCase() || 'LOCAL AI';
    }

    return (
      <span className="hr-source-badge">
        <Sparkles size={10} />
        {label}
      </span>
    );
  };

  const getScoreColorClass = () => {
    if (score >= 75) return 'high';
    if (score >= 50) return 'mid';
    return 'low';
  };

  const displayConfidence = confidence && confidence !== 'not available' ? confidence : 'Not available';

  return (
    <div className="hr-candidate-card">
      <div className="hr-candidate-header-row">
        <div className="hr-candidate-avatar-container">
          <User size={20} />
        </div>
        <div className="hr-candidate-meta">
          <div className="hr-candidate-name-row">
            <h4 className="hr-candidate-name">{name}</h4>
            <span className={`hr-candidate-score ${getScoreColorClass()}`}>
              {score}%
            </span>
          </div>
          <span className="hr-candidate-role">{role}</span>
        </div>
      </div>

      <div className="hr-candidate-status-row">
        {getAiSourceBadge()}
        <span className="hr-confidence-text">
          Confidence: <b className="hr-confidence-val">{displayConfidence}</b>
        </span>
        {status && (
          <span className="hr-candidate-status-label">
            {status}
          </span>
        )}
      </div>

      <div className="hr-skills-container">
        {matchedSkills.length > 0 && (
          <div className="hr-skills-block">
            <h4>Matched Skills</h4>
            <div className="hr-skills-list">
              {matchedSkills.map(s => (
                <span key={s} className="hr-skill-badge matched">{s}</span>
              ))}
            </div>
          </div>
        )}

        {missingSkills.length > 0 && (
          <div className="hr-skills-block">
            <h4>Missing Skills</h4>
            <div className="hr-skills-list">
              {missingSkills.map(s => (
                <span key={s} className="hr-skill-badge missing">{s}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="hr-candidate-actions">
        <button 
          onClick={onAiSummary} 
          className="hr-card-btn secondary"
          type="button"
        >
          AI summary
        </button>
        <button 
          onClick={onReview} 
          className="hr-card-btn secondary"
          type="button"
        >
          Review
        </button>
        <button 
          onClick={onShortlist} 
          className="hr-card-btn primary"
          type="button"
        >
          Shortlist
        </button>
      </div>
    </div>
  );
};

export default CandidateCard;

