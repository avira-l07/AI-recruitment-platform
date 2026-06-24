import React from 'react';

const LoadingSpinner = ({ message }) => {
  return (
    <div className="loading-container">
      <div className="spinner"></div>
      {message && <p style={{ marginTop: '16px', color: 'var(--navy)' }}>{message}</p>}
    </div>
  );
};

export default LoadingSpinner;