import React from 'react';

const StatisticsCard = ({ label, value, icon, helperText, trendColor, iconBgClass }) => {
  const getIconClass = () => {
    if (iconBgClass) return `hr-stat-icon ${iconBgClass}`;
    return 'hr-stat-icon hr-icon-blue';
  };

  return (
    <div className="hr-stat-card" style={{ display: 'flex', flexDirection: 'column', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-lg)', padding: 'var(--space-5)', boxShadow: 'var(--elevation-1)' }}>
      <div className="hr-stat-top" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
        <div className={getIconClass()} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '36px', height: '36px', borderRadius: 'var(--radius-md)' }}>
          {icon}
        </div>
        <span className="hr-stat-label" style={{ fontSize: 'var(--font-sm)', fontWeight: 'var(--weight-medium)', color: 'var(--color-muted)' }}>
          {label}
        </span>
      </div>
      <div className="hr-stat-value" style={{ fontSize: 'var(--font-3xl)', fontWeight: 'var(--weight-semibold)', marginBottom: 'var(--space-1)', color: 'var(--color-text)', lineHeight: 1 }}>
        {value}
      </div>
      {helperText && (
        <div className={`hr-stat-helper ${trendColor === 'green' ? 'green' : ''}`} style={{ fontSize: 'var(--font-xs)', color: trendColor === 'green' ? 'var(--color-success)' : 'var(--color-muted)', display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}>
          {helperText}
        </div>
      )}
    </div>
  );
};

export default StatisticsCard;
