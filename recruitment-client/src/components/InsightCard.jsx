import React from 'react';

const InsightCard = ({ title, value, description, icon, alertType }) => {
  const getBorderColor = () => {
    if (alertType === 'warning') return 'var(--color-warning)';
    if (alertType === 'danger') return 'var(--color-danger)';
    if (alertType === 'success') return 'var(--color-success)';
    return 'var(--color-border)';
  };

  return (
    <div 
      className="hr-insight-card" 
      style={{
        backgroundColor: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderLeft: `4px solid ${getBorderColor()}`,
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-4)',
        boxShadow: 'var(--elevation-1)',
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-4)',
        transition: 'transform var(--transition-fast)'
      }}
      onMouseEnter={(e) => e.currentTarget.style.transform = 'translateX(2px)'}
      onMouseLeave={(e) => e.currentTarget.style.transform = 'none'}
    >
      {icon && (
        <div style={{ color: getBorderColor(), display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          {icon}
        </div>
      )}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-05)' }}>
        <h4 style={{ margin: 0, fontSize: 'var(--font-sm)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-text)' }}>
          {title}
        </h4>
        {value && (
          <span style={{ fontSize: 'var(--font-lg)', fontWeight: 'var(--weight-bold)', color: 'var(--color-text)' }}>
            {value}
          </span>
        )}
        <p style={{ margin: 0, fontSize: 'var(--font-xs)', color: 'var(--color-muted)', lineHeight: 'var(--lh-normal)' }}>
          {description}
        </p>
      </div>
    </div>
  );
};

export default InsightCard;
