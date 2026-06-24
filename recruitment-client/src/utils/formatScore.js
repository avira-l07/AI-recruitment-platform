export const formatScore = (score) => `${Math.round(score)}%`;

export const getScoreColor = (score) => {
  if (score >= 70) return 'var(--green)';
  if (score >= 40) return 'var(--orange)';
  return 'var(--red)';
};

export const getScoreLabel = (score) => {
  if (score >= 70) return 'Strong Match';
  if (score >= 40) return 'Moderate Match';
  return 'Weak Match';
};

export const getStatusColor = (status) => {
  switch (status.toLowerCase()) {
    case 'shortlisted': return 'var(--green)';
    case 'rejected': return 'var(--red)';
    default: return 'var(--orange)';
  }
};