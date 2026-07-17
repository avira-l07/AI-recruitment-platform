import React, { useEffect, useRef, useState } from 'react';
import { Bell, CheckCheck } from 'lucide-react';

const NotificationBell = ({ notifications = [], unreadCount = 0, onMarkRead, onMarkAllRead }) => {
  const [isOpen, setIsOpen] = useState(false);
  const rootRef = useRef(null);

  useEffect(() => {
    const close = (event) => {
      if (rootRef.current && !rootRef.current.contains(event.target)) setIsOpen(false);
    };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  return (
    <div ref={rootRef} className="hr-notification-root">
      <button
        type="button"
        className="hr-icon-button"
        onClick={() => setIsOpen((value) => !value)}
        aria-label={`Notifications${unreadCount ? `, ${unreadCount} unread` : ''}`}
        aria-expanded={isOpen}
      >
        <Bell size={19} />
        {unreadCount > 0 && <span className="hr-notification-count">{Math.min(unreadCount, 99)}</span>}
      </button>

      {isOpen && (
        <div className="hr-notification-menu" role="dialog" aria-label="Notifications">
          <div className="hr-notification-header">
            <strong>Notifications</strong>
            {unreadCount > 0 && (
              <button type="button" onClick={onMarkAllRead} className="hr-text-button">
                <CheckCheck size={14} /> Mark all read
              </button>
            )}
          </div>
          <div className="hr-notification-list">
            {notifications.length === 0 ? (
              <p className="hr-empty-inline">No notifications yet.</p>
            ) : notifications.map((item) => (
              <button
                type="button"
                key={item.id}
                className={`hr-notification-item ${item.is_read ? '' : 'unread'}`}
                onClick={() => onMarkRead?.(item)}
              >
                <span className="hr-notification-title">{item.title}</span>
                <span className="hr-notification-message">{item.message}</span>
                <span className="hr-notification-time">
                  {item.created_at ? new Date(item.created_at).toLocaleString() : ''}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell;
