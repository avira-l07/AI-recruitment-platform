import React from 'react';
import { History, X, ShieldCheck, Clock, Calendar } from 'lucide-react';

const VerificationHistoryModal = ({ isOpen, onClose, history = [], currentVersion = 1, currentScore = 0 }) => {
  if (!isOpen) return null;

  return (
    <div className="verif-modal-overlay" onClick={onClose}>
      <div className="verif-modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="verif-modal-header">
          <div className="verif-modal-title-wrap">
            <History size={18} />
            <h3>Verification Version History & Audit Trail</h3>
          </div>
          <button className="verif-modal-close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <div className="verif-modal-body">
          {/* Current Version */}
          <div className="verif-hist-item verif-hist-current">
            <div className="verif-hist-badge">Current (v{currentVersion})</div>
            <div className="verif-hist-main">
              <div className="verif-hist-score">Trust Score: <strong>{currentScore}</strong>/100</div>
              <span className="verif-hist-status">Active Production Snapshot</span>
            </div>
          </div>

          {/* Past History */}
          {history.length === 0 ? (
            <p className="verif-empty-text">No previous reverification snapshots stored.</p>
          ) : (
            <div className="verif-hist-list">
              {history.map((h, idx) => (
                <div key={idx} className="verif-hist-item">
                  <div className="verif-hist-header">
                    <span className="verif-hist-version">Version {h.version || (idx + 1)}</span>
                    <span className="verif-hist-date">
                      <Clock size={12} /> {h.verified_at ? new Date(h.verified_at).toLocaleDateString() : 'Previous Run'}
                    </span>
                  </div>

                  <div className="verif-hist-details">
                    <div>Trust Score: <strong>{h.trust_score || 0}</strong>/100</div>
                    <div>Outcome: <span className="verif-hist-outcome">{h.outcome || 'needs_review'}</span></div>
                    {h.hr_decision && (
                      <div>HR Decision: <strong>{h.hr_decision}</strong> {h.hr_decision_notes && `("${h.hr_decision_notes}")`}</div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VerificationHistoryModal;
