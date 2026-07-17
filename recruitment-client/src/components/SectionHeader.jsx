import React from 'react';

const SectionHeader = ({ title, style }) => {
  return (
    <h3 
      className="hr-section-header" 
      style={{ 
        fontSize: 'var(--font-lg)', 
        fontWeight: 'var(--weight-semibold)', 
        color: 'var(--color-text)', 
        margin: '0 0 var(--space-4) 0',
        letterSpacing: '-0.3px',
        ...style 
      }}
    >
      {title}
    </h3>
  );
};

export default SectionHeader;
