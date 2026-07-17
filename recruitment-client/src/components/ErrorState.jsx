import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

const ErrorState = ({ title = 'Connection Error', message, onRetry }) => {
  return (
    <div 
      className="hr-error-state"
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 'var(--space-10) var(--space-6)',
        backgroundColor: 'var(--color-danger-bg)',
        border: '1px solid var(--color-danger)',
        borderRadius: 'var(--radius-lg)',
        textAlign: 'center',
        width: '100%',
        maxWidth: '500px',
        margin: 'var(--space-10) auto',
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
          backgroundColor: '#FFFFFF', 
          color: 'var(--color-danger)',
          marginBottom: 'var(--space-4)',
          boxShadow: 'var(--elevation-1)'
        }}
      >
        <AlertCircle size={24} />
      </div>
      <h3 style={{ margin: '0 0 var(--space-2) 0', fontSize: 'var(--font-lg)', fontWeight: 'var(--weight-semibold)', color: 'var(--color-danger)' }}>
        {title}
      </h3>
      {message && (
        <p style={{ margin: '0 0 var(--space-5) 0', fontSize: 'var(--font-sm)', color: '#991B1B', lineHeight: 'var(--lh-normal)', maxWidth: '380px' }}>
          {message}
        </p>
      )}
      {onRetry && (
        <button 
          onClick={onRetry}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
            backgroundColor: 'var(--color-danger)',
            color: '#FFFFFF',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            padding: '10px 16px',
            fontSize: 'var(--font-sm)',
            fontWeight: 'var(--weight-semibold)',
            cursor: 'pointer',
            boxShadow: 'var(--elevation-1)',
            transition: 'background var(--transition-fast)'
          }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#991B1B'}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'var(--color-danger)'}
        >
          <RefreshCw size={14} />
          Try Again
        </button>
      )}
    </div>
  );
};

export default ErrorState;
