import React, { useState } from 'react';
import { Bell } from 'lucide-react';

const NotificationBell = ({ notifications = [], onMarkAllRead }) => {
  const [isOpen, setIsOpen] = useState(false);
  const unreadCount = notifications.filter(n => !n.read).length;

  return (
    <div style={{ position: 'relative' }}>
      <button 
        onClick={() => setIsOpen(!isOpen)}
        style={{ 
          background: 'none', 
          border: 'none', 
          cursor: 'pointer', 
          color: 'var(--color-muted)',
          position: 'relative',
          padding: 'var(--space-2)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: 'var(--radius-pill)',
          transition: 'background var(--transition-fast)'
        }}
        onMouseEnter={(e) => e.currentTarget.style.background = 'var(--color-background)'}
        onMouseLeave={(e) => e.currentTarget.style.background = 'none'}
      >
        <Bell size={20} />
        {unreadCount > 0 && (
          <span 
            style={{ 
              position: 'absolute', 
              top: '4px', 
              right: '4px', 
              backgroundColor: 'var(--color-danger)', 
              color: '#fff', 
              fontSize: '10px', 
              fontWeight: 'var(--weight-bold)',
              borderRadius: 'var(--radius-pill)', 
              padding: '2px 5px',
              lineHeight: 1
            }}
          >
            {unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div 
          style={{ 
            position: 'absolute', 
            top: '100%', 
            right: 0, 
            marginTop: '8px', 
            width: '320px', 
            backgroundColor: 'var(--color-surface)', 
            border: '1px solid var(--color-border)', 
            borderRadius: 'var(--radius-lg)', 
            boxShadow: 'var(--elevation-3)', 
            zIndex: 'var(--z-index-dropdown)',
            overflow: 'hidden'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px', borderBottom: '1px solid var(--color-border)' }}>
            <span style={{ fontWeight: 'var(--weight-semibold)', color: 'var(--color-text)' }}>Notifications</span>
            {unreadCount > 0 && onMarkAllRead && (
              <button 
                onClick={onMarkAllRead} 
                style={{ background: 'none', border: 'none', color: 'var(--color-primary)', fontSize: '0.8rem', cursor: 'pointer', fontWeight: 'var(--weight-medium)' }}
              >
                Mark all read
              </button>
            )}
          </div>
          <div style={{ maxHeight: '240px', overflowY: 'auto' }}>
            {notifications.length > 0 ? (
              notifications.map((n) => (
                <div key={n.id} style={{ padding: '12px 16px', borderBottom: '1px solid var(--color-border)', backgroundColor: n.read ? 'transparent' : 'rgba(79, 70, 229, 0.02)' }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: n.read ? 'var(--weight-normal)' : 'var(--weight-medium)', color: 'var(--color-text)' }}>{n.title}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-muted)', marginTop: '4px' }}>{n.time}</div>
                </div>
              ))
            ) : (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--color-muted)', fontSize: '0.85rem' }}>
                No notifications
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
