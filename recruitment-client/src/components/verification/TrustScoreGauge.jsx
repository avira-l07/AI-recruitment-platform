import React from 'react';
import { ShieldCheck, ShieldAlert, AlertTriangle, HelpCircle, CheckCircle2, ChevronDown, ChevronUp } from 'lucide-react';

const getOutcomeDetails = (outcome) => {
  switch (outcome) {
    case 'strong_evidence':
      return {
        label: 'STRONG EVIDENCE',
        badgeClass: 'verif-badge-strong',
        color: '#10B981',
        icon: <ShieldCheck size={18} className="verif-icon-strong" />,
        desc: 'Verified by independent organizational domains and accessible repositories.'
      };
    case 'suspicious':
      return {
        label: 'CONTRADICTORY / SUSPICIOUS',
        badgeClass: 'verif-badge-suspicious',
        color: '#EF4444',
        icon: <ShieldAlert size={18} className="verif-icon-suspicious" />,
        desc: 'Potential contradictions, unreachable domains, or risky patterns detected.'
      };
    case 'insufficient_evidence':
      return {
        label: 'INSUFFICIENT EVIDENCE',
        badgeClass: 'verif-badge-insufficient',
        color: '#94A3B8',
        icon: <HelpCircle size={18} className="verif-icon-insufficient" />,
        desc: 'No public digital footprint discoverable for claimed private entities.'
      };
    case 'needs_review':
    default:
      return {
        label: 'NEEDS HR REVIEW',
        badgeClass: 'verif-badge-review',
        color: '#F59E0B',
        icon: <AlertTriangle size={18} className="verif-icon-review" />,
        desc: 'Standard HR verification required (e.g. check offer letter or code demo).'
      };
  }
};

const TrustScoreGauge = ({ score = 0, outcome = 'needs_review', confidenceLabel = 'Medium', breakdown = [] }) => {
  const [showBreakdown, setShowBreakdown] = React.useState(false);
  const outcomeInfo = getOutcomeDetails(outcome);
  const normalizedScore = Math.min(100, Math.max(0, Math.round(score)));

  // SVG Gauge calculations
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (normalizedScore / 100) * circumference;

  return (
    <div className="verif-score-card">
      <div className="verif-score-main">
        {/* Circular Gauge */}
        <div className="verif-gauge-wrapper">
          <svg className="verif-gauge-svg" width="130" height="130" viewBox="0 0 130 130">
            <circle
              className="verif-gauge-bg"
              cx="65"
              cy="65"
              r={radius}
              strokeWidth="10"
            />
            <circle
              className="verif-gauge-fill"
              cx="65"
              cy="65"
              r={radius}
              strokeWidth="10"
              stroke={outcomeInfo.color}
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              strokeLinecap="round"
              transform="rotate(-90 65 65)"
            />
          </svg>
          <div className="verif-gauge-text">
            <span className="verif-gauge-val" style={{ color: outcomeInfo.color }}>{normalizedScore}</span>
            <span className="verif-gauge-label">TRUST SCORE</span>
          </div>
        </div>

        {/* Outcome Banner */}
        <div className="verif-outcome-content">
          <div className="verif-outcome-header">
            <span className={`verif-outcome-badge ${outcomeInfo.badgeClass}`}>
              {outcomeInfo.icon}
              <span>{outcomeInfo.label}</span>
            </span>
            <span className="verif-conf-tag">
              Confidence: <strong>{confidenceLabel}</strong>
            </span>
          </div>
          <p className="verif-outcome-desc">{outcomeInfo.desc}</p>
          
          <button 
            className="verif-breakdown-toggle"
            onClick={() => setShowBreakdown(!showBreakdown)}
            aria-expanded={showBreakdown}
          >
            <span>Score Point Breakdown ({breakdown.length} components)</span>
            {showBreakdown ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </div>

      {/* Itemized Points Breakdown Accordion */}
      {showBreakdown && breakdown.length > 0 && (
        <div className="verif-breakdown-panel">
          <h4 className="verif-breakdown-title">Point Contribution Breakdown (0 - 100)</h4>
          <div className="verif-breakdown-grid">
            {breakdown.map((item, idx) => (
              <div key={idx} className="verif-breakdown-item">
                <div className="verif-breakdown-row">
                  <span className="verif-breakdown-comp">{item.component}</span>
                  <span className="verif-breakdown-pts" style={{ color: item.points_earned < 0 ? '#EF4444' : '#10B981' }}>
                    {item.points_earned > 0 ? `+${item.points_earned}` : item.points_earned} / {item.max_points} pts
                  </span>
                </div>
                <p className="verif-breakdown-sub">{item.explanation}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default TrustScoreGauge;
