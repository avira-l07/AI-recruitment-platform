import React from 'react';

const PipelineStage = ({ label, count, isAlert }) => {
  const getStageStyle = () => {
    if (isAlert) {
      return {
        border: '1.5px solid var(--color-danger)',
        backgroundColor: 'var(--color-danger-bg)',
        color: 'var(--color-danger)'
      };
    }
    return {
      border: '1px solid var(--color-border)',
      backgroundColor: 'var(--color-surface)',
      color: 'var(--color-text)'
    };
  };

  return (
    <div 
      className="hr-pipeline-stage" 
      style={{
        flex: 1,
        borderRadius: 'var(--radius-lg)',
        padding: 'var(--space-4) var(--space-5)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-1)',
        minWidth: '120px',
        boxShadow: 'var(--elevation-1)',
        transition: 'transform var(--transition-fast)',
        ...getStageStyle()
      }}
      onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-1px)'}
      onMouseLeave={(e) => e.currentTarget.style.transform = 'none'}
    >
      <span style={{ fontSize: 'var(--font-xs)', fontWeight: 'var(--weight-medium)', textTransform: 'uppercase', letterSpacing: '0.05em', opacity: 0.8 }}>
        {label}
      </span>
      <span style={{ fontSize: 'var(--font-2xl)', fontWeight: 'var(--weight-bold)' }}>
        {count}
      </span>
    </div>
  );
};

export default PipelineStage;
