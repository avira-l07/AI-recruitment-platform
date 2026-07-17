import React from 'react';
import { AlertCircle } from 'lucide-react';

const ReviewAlert = ({ title, message, type = 'warning' }) => {
  const getColors = () => {
    switch (type) {
      case 'danger':
        return {
          bg: 'var(--color-danger-bg)',
          border: 'var(--color-danger)',
          text: 'var(--color-danger)'
        };
      case 'success':
        return {
          bg: 'var(--color-success-bg)',
          border: 'var(--color-success)',
          text: 'var(--color-success)'
        };
      case 'warning':
      default:
        return {
          bg: 'var(--color-warning-bg)',
          border: 'var(--color-warning)',
          text: 'var(--color-warning)'
        };
    }
  };

  const colors = getColors();

  return (
    <div 
      className="hr-review-alert"
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 'var(--space-3)',
        backgroundColor: colors.bg,
        border: `1px solid ${colors.border}`,
        borderRadius: 'var(--radius-md)',
        padding: 'var(--space-4) var(--space-5)',
        marginBottom: 'var(--space-5)'
      }}
    >
      <AlertCircle size={20} style={{ color: colors.text, flexShrink: 0, marginTop: '2px' }} />
      <p style={{ margin: 0, fontSize: 'var(--font-sm)', color: colors.text, lineHeight: 'var(--lh-normal)' }}>
        {title && <strong style={{ marginRight: '8px' }}>{title}</strong>}
        {message}
      </p>
    </div>
  );
};

export default ReviewAlert;
