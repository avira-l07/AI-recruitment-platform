import React from 'react';
import { Building2, Globe, ShieldCheck, ShieldAlert, AlertTriangle, ExternalLink, Cpu } from 'lucide-react';

const CompanyVerificationCard = ({ companies = [] }) => {
  if (!companies || companies.length === 0) {
    return (
      <div className="verif-card">
        <div className="verif-card-header">
          <div className="verif-card-title-wrap">
            <Building2 size={18} className="verif-card-icon" />
            <h3>Company Legitimacy Verification</h3>
          </div>
        </div>
        <p className="verif-empty-text">No company work experience claims identified on resume.</p>
      </div>
    );
  }

  return (
    <div className="verif-card">
      <div className="verif-card-header">
        <div className="verif-card-title-wrap">
          <Building2 size={18} className="verif-card-icon" />
          <h3>Company Legitimacy & Identity Verification</h3>
        </div>
        <span className="verif-count-pill">{companies.length} Claimed Organization{companies.length > 1 ? 's' : ''}</span>
      </div>

      <div className="verif-company-list">
        {companies.map((comp, idx) => {
          const isVerified = comp.verification_status === 'Verified';
          const isHighRisk = comp.verification_status === 'High Risk';
          
          return (
            <div key={idx} className={`verif-company-item ${isHighRisk ? 'verif-item-risk' : ''}`}>
              <div className="verif-company-top">
                <div className="verif-company-info">
                  <h4 className="verif-company-name">{comp.company_name}</h4>
                  {comp.domain && comp.domain !== 'Not Publicly Discoverable' && (
                    <span className="verif-company-domain">
                      <Globe size={13} /> {comp.domain}
                    </span>
                  )}
                </div>

                <div className="verif-company-badge-wrap">
                  {isVerified ? (
                    <span className="verif-status-tag verif-tag-verified">
                      <ShieldCheck size={14} /> Verified Entity
                    </span>
                  ) : isHighRisk ? (
                    <span className="verif-status-tag verif-tag-risk">
                      <ShieldAlert size={14} /> High Risk / Suspicious
                    </span>
                  ) : (
                    <span className="verif-status-tag verif-tag-review">
                      <AlertTriangle size={14} /> Needs HR Review
                    </span>
                  )}
                </div>
              </div>

              {/* Fraud Signals Alert */}
              {comp.fraud_signals && comp.fraud_signals.length > 0 && (
                <div className="verif-alert-box verif-alert-danger">
                  <ShieldAlert size={16} />
                  <div>
                    <strong>Risk Signals Detected:</strong>
                    <ul>
                      {comp.fraud_signals.map((sig, sIdx) => (
                        <li key={sIdx}>{sig}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              <div className="verif-company-details-grid">
                <div className="verif-detail-cell">
                  <span className="verif-detail-lbl">Web Presence</span>
                  <span className="verif-detail-val">{comp.business_presence || 'Standard'}</span>
                </div>
                <div className="verif-detail-cell">
                  <span className="verif-detail-lbl">Identity Consistency</span>
                  <span className="verif-detail-val">{comp.company_identity_consistency || 'Consistent'}</span>
                </div>
                <div className="verif-detail-cell">
                  <span className="verif-detail-lbl">Tech Stack Alignment</span>
                  <span className="verif-detail-val">{comp.technology_alignment || 'Standard Alignment'}</span>
                </div>
                <div className="verif-detail-cell">
                  <span className="verif-detail-lbl">Confidence</span>
                  <span className="verif-detail-val" style={{ color: isVerified ? '#10B981' : (isHighRisk ? '#EF4444' : '#F59E0B') }}>
                    {comp.confidence_score}%
                  </span>
                </div>
              </div>

              {/* Technologies Aligned */}
              {comp.aligned_technologies && comp.aligned_technologies.length > 0 && (
                <div className="verif-tech-row">
                  <span className="verif-tech-lbl"><Cpu size={13} /> Aligned Tech:</span>
                  <div className="verif-tech-tags">
                    {comp.aligned_technologies.map((t, tIdx) => (
                      <span key={tIdx} className="verif-tech-pill">{t}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Official Link if available */}
              {comp.official_website && (
                <div className="verif-link-action">
                  <a href={comp.official_website} target="_blank" rel="noopener noreferrer" className="verif-ext-link">
                    <span>Visit Official Website ({comp.domain})</span>
                    <ExternalLink size={13} />
                  </a>
                </div>
              )}

              {comp.notes && <p className="verif-item-notes">{comp.notes}</p>}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default CompanyVerificationCard;
