import React from 'react';
import { Sparkles, CheckCircle2, User } from 'lucide-react';

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
    let label = 'Local AI';
    let bg = '#F1F5F9';
    let text = 'var(--color-muted)';

    if (source.includes('gemini_text_enhanced') || source === 'gemini') {
      label = 'Gemini AI';
      bg = '#F5F3FF';
      text = 'var(--color-secondary)';
    } else if (source.includes('hybrid')) {
      label = 'Hybrid AI';
      bg = 'var(--color-accent-soft)';
      text = 'var(--color-primary)';
    }

    return (
      <span 
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          padding: '4px 10px',
          backgroundColor: bg,
          color: text,
          fontSize: '11px',
          fontWeight: 'var(--weight-semibold)',
          borderRadius: 'var(--radius-pill)',
          textTransform: 'uppercase',
          letterSpacing: '0.02em',
          fontFamily: 'var(--font-mono)'
        }}
      >
        <Sparkles size={10} />
        {label}
      </span>
    );
  };

  const getScoreColor = () => {
    if (score >= 75) return 'var(--color-success)';
    if (score >= 50) return 'var(--color-warning)';
    return 'var(--color-danger)';
  };

  return (
    <div 
      className="hr-candidate-detail-card"
      style={{
        backgroundColor: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-5)',
        boxShadow: 'var(--elevation-1)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-4)',
        transition: 'transform var(--transition-fast), box-shadow var(--transition-fast)'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = 'var(--elevation-2)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'none';
        e.currentTarget.style.boxShadow = 'var(--elevation-1)';
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', justify: 'center', width: '40px', height: '40px', borderRadius: '50%', backgroundColor: 'var(--color-accent-soft)', color: 'var(--color-primary)' }}>
            <User size={18} />
          </div>
          <div>
            <h4 style={{ margin: 0, fontSize: 'var(--font-base)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-text)' }}>{name}</h4>
            <span style={{ fontSize: 'var(--font-xs)', color: 'var(--color-muted)' }}>{role}</span>
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '4px' }}>
          <span style={{ fontSize: 'var(--font-2xl)', fontWeight: 'var(--weight-bold)', color: getScoreColor(), lineHeight: 1 }}>
            {score}%
          </span>
          <span style={{ fontSize: '10px', color: 'var(--color-muted)', textTransform: 'uppercase', fontWeight: 'var(--weight-medium)' }}>
            Match Score
          </span>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--color-border)', borderBottom: '1px solid var(--color-border)', padding: 'var(--space-2) 0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
          {getAiSourceBadge()}
          <span style={{ fontSize: 'var(--font-xs)', color: 'var(--color-muted)' }}>
            Confidence: <b>{confidence}</b>
          </span>
        </div>
        {status && (
          <span style={{ fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-primary)' }}>
            {status}
          </span>
        )}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        {matchedSkills.length > 0 && (
          <div>
            <div style={{ fontSize: '11px', color: 'var(--color-muted)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.02em' }}>Matched Skills</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1.5)' }}>
              {matchedSkills.map(s => (
                <span key={s} style={{ backgroundColor: 'var(--color-success-bg)', color: 'var(--color-success)', fontSize: 'var(--font-xs)', padding: '2px 8px', borderRadius: 'var(--radius-sm)', fontWeight: 'var(--weight-medium)' }}>{s}</span>
              ))}
            </div>
          </div>
        )}

        {missingSkills.length > 0 && (
          <div>
            <div style={{ fontSize: '11px', color: 'var(--color-muted)', marginBottom: '4px', textTransform: 'uppercase', letterSpacing: '0.02em' }}>Missing Skills</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1.5)' }}>
              {missingSkills.map(s => (
                <span key={s} style={{ backgroundColor: 'var(--color-danger-bg)', color: 'var(--color-danger)', fontSize: 'var(--font-xs)', padding: '2px 8px', borderRadius: 'var(--radius-sm)', fontWeight: 'var(--weight-medium)' }}>{s}</span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'auto', paddingTop: 'var(--space-2)' }}>
        <button 
          onClick={onAiSummary} 
          style={{ flex: 1, border: '1px solid var(--color-border)', background: 'none', borderRadius: 'var(--radius-md)', padding: '8px', fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-medium)', color: 'var(--color-text)', cursor: 'pointer' }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#F8FAFC'}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
        >
          AI Summary
        </button>
        <button 
          onClick={onReview} 
          style={{ flex: 1, border: '1px solid var(--color-border)', background: 'none', borderRadius: 'var(--radius-md)', padding: '8px', fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-medium)', color: 'var(--color-text)', cursor: 'pointer' }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#F8FAFC'}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
        >
          Review
        </button>
        <button 
          onClick={onShortlist} 
          style={{ flex: 1, border: 'none', backgroundColor: 'var(--color-primary)', color: '#FFFFFF', borderRadius: 'var(--radius-md)', padding: '8px', fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-medium)', cursor: 'pointer' }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2c46c2'}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'var(--color-primary)'}
        >
          Shortlist
        </button>
      </div>
    </div>
  );
};

export default CandidateCard;
