import React from 'react';
import ScoreBadge from './ScoreBadge';
import { getStatusColor } from '../utils/formatScore';

const CandidateCard = ({ candidate }) => {
  const { name, email, skills, score, status } = candidate;

  return (
    <div className="card candidate-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h3>{name}</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '12px' }}>{email}</p>
        </div>
        <ScoreBadge score={score} />
      </div>
      <div style={{ marginBottom: '12px' }}>
        {skills.slice(0, 3).map((skill, index) => (
          <span key={index} className="skill-tag">{skill}</span>
        ))}
        {skills.length > 3 && <span className="skill-tag">+{skills.length - 3}</span>}
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--border)' }}>
        <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Status</span>
        <span style={{ color: getStatusColor(status), fontWeight: '600' }}>{status}</span>
      </div>
    </div>
  );
};

export default CandidateCard;