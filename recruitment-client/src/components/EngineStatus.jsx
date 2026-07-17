import React from 'react';
import { CheckCircle2, Loader2, Clock, XCircle } from 'lucide-react';

const EngineStatus = ({ title, status, capabilities = [] }) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 size={16} style={{ color: 'var(--color-success)' }} />;
      case 'running':
        return (
          <Loader2 
            size={16} 
            style={{ 
              color: 'var(--color-primary)', 
              animation: 'spin 1s linear infinite' 
            }} 
          />
        );
      case 'failed':
        return <XCircle size={16} style={{ color: 'var(--color-danger)' }} />;
      case 'waiting':
      default:
        return <Clock size={16} style={{ color: 'var(--color-muted)' }} />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'completed': return 'var(--color-success)';
      case 'running': return 'var(--color-primary)';
      case 'failed': return 'var(--color-danger)';
      case 'waiting':
      default: return 'var(--color-muted)';
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'completed': return 'Active';
      case 'running': return 'Running';
      case 'failed': return 'Failed';
      case 'waiting':
      default: return 'Waiting';
    }
  };

  return (
    <div 
      className="hr-engine-status-card" 
      style={{ 
        flex: 1, 
        backgroundColor: 'rgba(255, 255, 255, 0.03)', 
        border: '1px solid rgba(255, 255, 255, 0.08)', 
        borderRadius: 'var(--radius-lg)', 
        padding: 'var(--space-4)',
        minWidth: '200px'
      }}
    >
      <div 
        style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          marginBottom: 'var(--space-3)', 
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)', 
          paddingBottom: 'var(--space-2)' 
        }}
      >
        <h4 style={{ margin: 0, fontSize: 'var(--font-sm)', fontWeight: 'var(--weight-semibold)', color: '#FFFFFF' }}>
          {title}
        </h4>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}>
          {getStatusIcon()}
          <span style={{ fontSize: 'var(--font-xs)', color: getStatusColor(), fontWeight: 'var(--weight-medium)' }}>
            {getStatusText()}
          </span>
        </div>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
        {capabilities.map((cap) => (
          <div key={cap} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <span style={{ display: 'inline-block', width: '5px', height: '5px', backgroundColor: 'var(--color-primary)', borderRadius: '50%' }} />
            <span style={{ fontSize: 'var(--font-xs)', color: '#CBD5E1' }}>{cap}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default EngineStatus;
