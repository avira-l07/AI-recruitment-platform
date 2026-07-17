import React from 'react';

const ActionHeader = ({ title, subtitle, actions }) => {
  return (
    <div className="hr-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 'var(--space-6)' }}>
      <div>
        <h1 className="hr-title" style={{ fontSize: 'var(--font-3xl)', fontWeight: 'var(--weight-semibold)', margin: '0 0 var(--space-1) 0', color: 'var(--color-text)', letterSpacing: '-0.5px' }}>
          {title}
        </h1>
        {subtitle && <p className="hr-subtitle" style={{ color: 'var(--color-muted)', margin: 0, fontSize: 'var(--font-sm)' }}>{subtitle}</p>}
      </div>
      {actions && <div className="hr-header-actions" style={{ display: 'flex', gap: 'var(--space-2)' }}>{actions}</div>}
    </div>
  );
};

export default ActionHeader;
