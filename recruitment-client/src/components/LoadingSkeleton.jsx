import React from 'react';

const LoadingSkeleton = ({ type = 'list', count = 3 }) => {
  const renderCardSkeleton = () => (
    <div 
      className="animate-pulse" 
      style={{ 
        backgroundColor: 'var(--color-surface)', 
        border: '1px solid var(--color-border)', 
        borderRadius: 'var(--radius-lg)', 
        padding: 'var(--space-5)', 
        display: 'flex', 
        flexDirection: 'column', 
        gap: 'var(--space-3)',
        animation: 'pulse 2s infinite ease-in-out'
      }}
    >
      <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center' }}>
        <div style={{ width: '40px', height: '40px', borderRadius: '50%', backgroundColor: '#E2E8F0' }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', flex: 1 }}>
          <div style={{ height: '14px', backgroundColor: '#E2E8F0', borderRadius: '4px', width: '50%' }} />
          <div style={{ height: '10px', backgroundColor: '#E2E8F0', borderRadius: '4px', width: '30%' }} />
        </div>
      </div>
      <div style={{ height: '32px', backgroundColor: '#E2E8F0', borderRadius: 'var(--radius-md)' }} />
      <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
        <div style={{ height: '24px', backgroundColor: '#E2E8F0', borderRadius: '4px', flex: 1 }} />
        <div style={{ height: '24px', backgroundColor: '#E2E8F0', borderRadius: '4px', flex: 1 }} />
      </div>
    </div>
  );

  const renderRowSkeleton = () => (
    <tr 
      className="animate-pulse" 
      style={{ 
        borderBottom: '1px solid var(--color-border)',
        animation: 'pulse 2s infinite ease-in-out'
      }}
    >
      <td style={{ padding: 'var(--space-4) var(--space-5)' }}>
        <div style={{ width: '16px', height: '16px', backgroundColor: '#E2E8F0', borderRadius: '3px' }} />
      </td>
      <td style={{ padding: 'var(--space-4) var(--space-5)' }}>
        <div style={{ width: '24px', height: '14px', backgroundColor: '#E2E8F0', borderRadius: '3px' }} />
      </td>
      <td style={{ padding: 'var(--space-4) var(--space-5)' }}>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '50%', backgroundColor: '#E2E8F0' }} />
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div style={{ width: '120px', height: '12px', backgroundColor: '#E2E8F0', borderRadius: '3px' }} />
            <div style={{ width: '80px', height: '8px', backgroundColor: '#E2E8F0', borderRadius: '3px' }} />
          </div>
        </div>
      </td>
      <td style={{ padding: 'var(--space-4) var(--space-5)' }}>
        <div style={{ width: '140px', height: '10px', backgroundColor: '#E2E8F0', borderRadius: '3px' }} />
      </td>
      <td style={{ padding: 'var(--space-4) var(--space-5)' }}>
        <div style={{ width: '100px', height: '16px', backgroundColor: '#E2E8F0', borderRadius: '8px' }} />
      </td>
      <td style={{ padding: 'var(--space-4) var(--space-5)' }}>
        <div style={{ width: '48px', height: '14px', backgroundColor: '#E2E8F0', borderRadius: '3px' }} />
      </td>
      <td style={{ padding: 'var(--space-4) var(--space-5)' }}>
        <div style={{ width: '80px', height: '16px', backgroundColor: '#E2E8F0', borderRadius: '8px' }} />
      </td>
      <td style={{ padding: 'var(--space-4) var(--space-5)' }}>
        <div style={{ width: '70px', height: '20px', backgroundColor: '#E2E8F0', borderRadius: '10px' }} />
      </td>
      <td style={{ padding: 'var(--space-4) var(--space-5)' }}>
        <div style={{ width: '120px', height: '24px', backgroundColor: '#E2E8F0', borderRadius: '4px' }} />
      </td>
    </tr>
  );

  return (
    <>
      {type === 'grid' ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 'var(--space-4)', width: '100%' }}>
          {Array.from({ length: count }).map((_, i) => (
            <React.Fragment key={i}>{renderCardSkeleton()}</React.Fragment>
          ))}
        </div>
      ) : (
        <>
          {Array.from({ length: count }).map((_, i) => (
            <React.Fragment key={i}>{renderRowSkeleton()}</React.Fragment>
          ))}
        </>
      )}
    </>
  );
};

export default LoadingSkeleton;
