import React from 'react';
import { X, Mail, Phone, BookOpen, Briefcase, Award, Sparkles, AlertTriangle } from 'lucide-react';

const CandidateDrawer = ({ 
  isOpen, 
  onClose, 
  candidate, 
  detail = [], 
  loading, 
  error, 
  onStatusUpdate,
  noteDraft,
  onNoteChange
}) => {
  if (!isOpen || !candidate) return null;

  const normalizeSkills = (skills) => {
    if (!skills) return [];
    if (Array.isArray(skills)) return skills;
    if (typeof skills === 'string') return skills.split(',').map(s => s.trim()).filter(Boolean);
    return [];
  };

  const getInitials = (name) => {
    if (!name) return '??';
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  };

  const getAiBadge = (aiSource) => {
    const isGemini = (aiSource || '').toLowerCase().includes('gemini') || (aiSource || '').toLowerCase().includes('enhanced');
    const isHybrid = (aiSource || '').toLowerCase().includes('hybrid');
    
    let label = 'Local AI';
    let bg = '#F1F5F9';
    let color = 'var(--color-muted)';

    if (isHybrid) {
      label = 'Hybrid AI';
      bg = 'var(--color-accent-soft)';
      color = 'var(--color-primary)';
    } else if (isGemini) {
      label = 'Gemini AI';
      bg = '#F5F3FF';
      color = 'var(--color-secondary)';
    }

    return (
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px', padding: '3px 8px', backgroundColor: bg, color: color, fontSize: '10px', fontWeight: 'var(--weight-semibold)', borderRadius: 'var(--radius-pill)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>
        <Sparkles size={10} /> {label}
      </span>
    );
  };

  return (
    <>
      <div 
        className="hr-drawer-overlay" 
        onClick={onClose} 
        style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(15, 23, 42, 0.4)', backdropFilter: 'blur(4px)', zIndex: 'var(--z-index-overlay)' }}
      />
      <aside 
        className="hr-drawer"
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: '450px',
          maxWidth: '100%',
          backgroundColor: 'var(--color-surface)',
          borderLeft: '1px solid var(--color-border)',
          boxShadow: 'var(--elevation-4)',
          zIndex: 'var(--z-index-modal)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden'
        }}
      >
        {/* Drawer Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 'var(--space-5)', borderBottom: '1px solid var(--color-border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', backgroundColor: 'var(--color-accent-soft)', color: 'var(--color-primary)', display: 'flex', alignItems: 'center', justify: 'center', fontWeight: 'var(--weight-bold)' }}>
              {getInitials(candidate.name || candidate.fullName)}
            </div>
            <div>
              <h2 style={{ margin: 0, fontSize: 'var(--font-lg)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-text)' }}>
                {candidate.name || candidate.fullName}
              </h2>
              <span style={{ fontSize: 'var(--font-xs)', color: 'var(--color-muted)' }}>
                {candidate.email || 'No email provided'}
              </span>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--color-muted)', cursor: 'pointer', padding: 'var(--space-1)' }}>
            <X size={20} />
          </button>
        </div>

        {/* Drawer Body */}
        <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-5)', display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
          {/* Profile Details */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', fontSize: 'var(--font-sm)', color: 'var(--color-text)' }}>
              <Mail size={16} style={{ color: 'var(--color-muted)' }} />
              <span>{candidate.email || 'No email provided'}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', fontSize: 'var(--font-sm)', color: 'var(--color-text)' }}>
              <Phone size={16} style={{ color: 'var(--color-muted)' }} />
              <span>{candidate.phone || 'Not available'}</span>
            </div>
          </div>

          <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 'var(--space-4)' }}>
            <h4 style={{ margin: '0 0 var(--space-2) 0', fontSize: 'var(--font-xs)', color: 'var(--color-muted)', textTransform: 'uppercase' }}>
              Resume Profile
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2.5)' }}>
              <div style={{ fontSize: 'var(--font-sm)', display: 'flex', gap: 'var(--space-2)' }}>
                <BookOpen size={16} style={{ color: 'var(--color-muted)', flexShrink: 0, marginTop: '2px' }} />
                <span><b>Education:</b> {candidate.education || 'Not uploaded'}</span>
              </div>
              <div style={{ fontSize: 'var(--font-sm)', display: 'flex', gap: 'var(--space-2)' }}>
                <Briefcase size={16} style={{ color: 'var(--color-muted)', flexShrink: 0, marginTop: '2px' }} />
                <span><b>Experience:</b> {candidate.experience || 'Not uploaded'}</span>
              </div>
            </div>
          </div>

          {/* AI Matching Info */}
          <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 'var(--space-4)' }}>
            <h4 style={{ margin: '0 0 var(--space-3) 0', fontSize: 'var(--font-xs)', color: 'var(--color-muted)', textTransform: 'uppercase' }}>
              AI Match Details
            </h4>
            {loading && <p style={{ fontSize: 'var(--font-sm)', color: 'var(--color-muted)' }}>Loading AI analysis...</p>}
            {error && <p style={{ fontSize: 'var(--font-sm)', color: 'var(--color-danger)' }}>{error}</p>}
            
            {!loading && !error && detail.length > 0 && detail.map((match, idx) => (
              <div key={idx} style={{ backgroundColor: 'var(--color-background)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <b style={{ fontSize: 'var(--font-sm)', color: 'var(--color-text)' }}>{match.jobTitle || 'Job Match'}</b>
                  {getAiBadge(match.aiSource)}
                </div>
                
                {match.hrSummary && (
                  <div style={{ backgroundColor: '#F8FAFC', borderLeft: '3px solid var(--color-primary)', padding: '8px 12px', borderRadius: 'var(--radius-sm)' }}>
                    <div style={{ fontSize: '11px', fontWeight: 'var(--weight-semibold)', color: 'var(--color-primary)', textTransform: 'uppercase', marginBottom: '2px' }}>AI Match Summary</div>
                    <p style={{ margin: 0, fontSize: 'var(--font-xs)', color: 'var(--color-text)', lineHeight: '1.4' }}>{match.hrSummary}</p>
                  </div>
                )}

                {match.riskFlags && match.riskFlags.length > 0 && (
                  <div style={{ backgroundColor: 'var(--color-danger-bg)', borderLeft: '3px solid var(--color-danger)', padding: '8px 12px', borderRadius: 'var(--radius-sm)' }}>
                    <div style={{ fontSize: '11px', fontWeight: 'var(--weight-semibold)', color: 'var(--color-danger)', textTransform: 'uppercase', marginBottom: '2px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <AlertTriangle size={12} /> Risk Flags
                    </div>
                    <ul style={{ margin: 0, paddingLeft: '16px', fontSize: 'var(--font-xs)', color: 'var(--color-danger)' }}>
                      {match.riskFlags.map((r, i) => <li key={i}>{r}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Notes Section */}
          <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 'var(--space-4)' }}>
            <h4 style={{ margin: '0 0 var(--space-2) 0', fontSize: 'var(--font-xs)', color: 'var(--color-muted)', textTransform: 'uppercase' }}>
              Notes
            </h4>
            <textarea
              value={noteDraft}
              onChange={(e) => onNoteChange(e.target.value)}
              placeholder="Add a hiring note..."
              rows={3}
              style={{ width: '100%', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: 'var(--space-3)', fontSize: 'var(--font-sm)', outline: 'none', fontFamily: 'inherit', boxSizing: 'border-box' }}
            />
          </div>
        </div>

        {/* Drawer Footer */}
        <div style={{ display: 'flex', gap: 'var(--space-2)', padding: 'var(--space-4)', borderTop: '1px solid var(--color-border)' }}>
          <button 
            onClick={() => onStatusUpdate(candidate.id, 'Shortlisted')}
            style={{ flex: 1, backgroundColor: 'var(--color-primary)', color: '#FFFFFF', border: 'none', borderRadius: 'var(--radius-md)', padding: '10px', fontWeight: 'var(--weight-semibold)', cursor: 'pointer' }}
          >
            Shortlist
          </button>
          <button 
            onClick={() => onStatusUpdate(candidate.id, 'Rejected')}
            style={{ flex: 1, border: '1px solid var(--color-border)', color: 'var(--color-text)', borderRadius: 'var(--radius-md)', padding: '10px', fontWeight: 'var(--weight-medium)', cursor: 'pointer', background: 'none' }}
          >
            Reject
          </button>
        </div>
      </aside>
    </>
  );
};

export default CandidateDrawer;
