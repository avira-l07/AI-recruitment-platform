import React from 'react';
import { AlertTriangle } from 'lucide-react';

const EmptyState = ({ message = 'No data available.', subMessage, icon }) => {
  return (
    <div 
      className="hr-empty-state"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--space-12) var(--space-6)',
        backgroundColor: 'var(--color-surface)',
        border: '1px dashed var(--color-border)',
        borderRadius: 'var(--radius-lg)',
        textAlign: 'center',
        width: '100%',
        boxSizing: 'border-box'
      }}
    >
      <div 
        style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          width: '48px', 
          height: '48px', 
          borderRadius: '50%', 
          backgroundColor: 'var(--color-background)', 
          color: 'var(--color-muted)',
          marginBottom: 'var(--space-4)'
        }}
      >
        {icon || <AlertTriangle size={20} />}
      </div>
      <h4 style={{ margin: '0 0 var(--space-1) 0', fontSize: 'var(--font-base)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-text)' }}>
        {message}
      </h4>
      {subMessage && (
        <p style={{ margin: 0, fontSize: 'var(--font-sm)', color: 'var(--color-muted)', maxWidth: '360px', lineHeight: 'var(--lh-normal)' }}>
          {subMessage}
        </p>
      )}
    </div>
  );
};

export default EmptyState;
