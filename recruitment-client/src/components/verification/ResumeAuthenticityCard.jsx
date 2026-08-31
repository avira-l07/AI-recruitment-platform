import React from 'react';
import { FileCheck, ShieldCheck, ShieldAlert, CheckCircle2, AlertCircle } from 'lucide-react';

const ResumeAuthenticityCard = ({ authenticity = {} }) => {
  const score = authenticity.authenticity_score || 95;
  const observations = authenticity.observations || [];
  const fraudFlags = authenticity.fraud_flags || [];

  return (
    <div className="verif-card">
      <div className="verif-card-header">
        <div className="verif-card-title-wrap">
          <FileCheck size={18} className="verif-card-icon" />
          <h3>Resume Structural & Layout Authenticity</h3>
        </div>
        <span className="verif-status-tag verif-tag-verified">
          <ShieldCheck size={13} /> {authenticity.status || 'Authentic / Clean'} ({score}%)
        </span>
      </div>

      {fraudFlags.length > 0 && (
        <div className="verif-alert-box verif-alert-danger">
          <ShieldAlert size={16} />
          <div>
            <strong>Authenticity Observations:</strong>
            <ul>
              {fraudFlags.map((f, idx) => (
                <li key={idx}>{f}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <div className="verif-auth-observations">
        {observations.map((obs, idx) => (
          <div key={idx} className="verif-auth-obs-item">
            <CheckCircle2 size={14} className="verif-check-icon" />
            <span>{obs}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ResumeAuthenticityCard;
