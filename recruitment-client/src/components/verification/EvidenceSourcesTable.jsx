import React from 'react';
import { Database, ExternalLink, ShieldCheck, ShieldAlert, Award } from 'lucide-react';

const getTierBadge = (tier = '') => {
  if (tier.includes('Tier 1')) {
    return <span className="verif-tier-pill verif-tier-1">Tier 1 — Official Organization</span>;
  } else if (tier.includes('Tier 2')) {
    return <span className="verif-tier-pill verif-tier-2">Tier 2 — Verified Independent</span>;
  } else if (tier.includes('Tier 3')) {
    return <span className="verif-tier-pill verif-tier-3">Tier 3 — Candidate-Controlled</span>;
  } else {
    return <span className="verif-tier-pill verif-tier-4">Tier 4 — Low Confidence / Web</span>;
  }
};

const EvidenceSourcesTable = ({ sources = [] }) => {
  if (!sources || sources.length === 0) {
    return (
      <div className="verif-card">
        <div className="verif-card-header">
          <div className="verif-card-title-wrap">
            <Database size={18} className="verif-card-icon" />
            <h3>Discovered Digital Evidence Sources</h3>
          </div>
        </div>
        <p className="verif-empty-text">No digital sources extracted for this profile.</p>
      </div>
    );
  }

  return (
    <div className="verif-card">
      <div className="verif-card-header">
        <div className="verif-card-title-wrap">
          <Database size={18} className="verif-card-icon" />
          <h3>Discovered Digital Evidence Sources & Reliability Tiers</h3>
        </div>
        <span className="verif-count-pill">{sources.length} Evidence Source{sources.length > 1 ? 's' : ''}</span>
      </div>

      <div className="verif-table-wrapper">
        <table className="verif-sources-table">
          <thead>
            <tr>
              <th>Source / Title</th>
              <th>Reliability Tier</th>
              <th>Signal</th>
              <th>Reliability</th>
              <th>Reason Used</th>
              <th>Link</th>
            </tr>
          </thead>
          <tbody>
            {sources.map((s, idx) => (
              <tr key={idx}>
                <td>
                  <strong>{s.title || 'Evidence Record'}</strong>
                  <span className="verif-table-cat">{s.category || 'Web Source'}</span>
                </td>
                <td>{getTierBadge(s.tier)}</td>
                <td>
                  {s.contradiction ? (
                    <span className="verif-status-tag verif-tag-risk">
                      <ShieldAlert size={12} /> Contradiction
                    </span>
                  ) : (
                    <span className="verif-status-tag verif-tag-verified">
                      <ShieldCheck size={12} /> Supports Claim
                    </span>
                  )}
                </td>
                <td>
                  <span className="verif-rel-score">{s.reliability_score || 80}%</span>
                </td>
                <td className="verif-reason-cell">
                  <p className="verif-reason-text">{s.reason_used || 'Referenced in digital background verification.'}</p>
                </td>
                <td>
                  {s.url ? (
                    <a href={s.url} target="_blank" rel="noopener noreferrer" className="verif-source-link">
                      <span>Open</span>
                      <ExternalLink size={12} />
                    </a>
                  ) : (
                    <span className="verif-na-text">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default EvidenceSourcesTable;
