import React from 'react';
import { formatScore, getScoreColor } from '../utils/formatScore';

const ScoreBadge = ({ score }) => {
  const bgColor = getScoreColor(score);
  return (
    <span 
      className="badge" 
      style={{ backgroundColor: bgColor, color: 'white', padding: '4px 12px', borderRadius: '12px', fontWeight: 'bold' }}
    >
      {formatScore(score)}
    </span>
  );
};

export default ScoreBadge;