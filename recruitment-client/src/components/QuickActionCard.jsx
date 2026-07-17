import React from 'react';

const QuickActionCard = ({ title, description, icon, actionLabel, onClick }) => {
  return (
    <div 
      className="hr-shortcut-card" 
      style={{ 
        display: 'flex', 
        alignItems: 'flex-start', 
        gap: 'var(--space-4)', 
        backgroundColor: 'var(--color-surface)', 
        border: '1px solid var(--color-border)', 
        borderRadius: 'var(--radius-lg)', 
        padding: 'var(--space-5)', 
        boxShadow: 'var(--elevation-1)', 
        transition: 'transform var(--transition-fast), box-shadow var(--transition-fast)'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = 'var(--elevation-2)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'none';
        e.currentTarget.style.boxShadow = 'var(--elevation-1)';
      }}
    >
      <div 
        className="hr-shortcut-icon" 
        style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          width: '40px', 
          height: '40px', 
          borderRadius: 'var(--radius-md)', 
          backgroundColor: 'var(--color-accent-soft)', 
          color: 'var(--color-primary)', 
          flexShrink: 0 
        }}
      >
        {icon}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
        <h3 style={{ margin: 0, fontSize: 'var(--font-sm)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-text)' }}>
          {title}
        </h3>
        <p style={{ margin: 0, fontSize: 'var(--font-xs)', color: 'var(--color-muted)', lineHeight: 'var(--lh-normal)' }}>
          {description}
        </p>
        <button 
          onClick={onClick} 
          style={{ 
            background: 'none', 
            border: 'none', 
            padding: 0, 
            color: 'var(--color-primary)', 
            fontSize: 'var(--font-xs)', 
            fontWeight: 'var(--weight-medium)', 
            cursor: 'pointer',
            textAlign: 'left',
            marginTop: 'var(--space-2)'
          }}
        >
          {actionLabel} &rarr;
        </button>
      </div>
    </div>
  );
};

export default QuickActionCard;
