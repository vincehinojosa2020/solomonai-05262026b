import { useState, useEffect, useRef } from 'react';
import { Bell, Check, CheckCheck, X } from 'lucide-react';
import { API_URL } from '@/lib/utils';

export default function NotificationBell() {
  const [notifications, setNotifications] = useState([]);
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchNotifications = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/notifications`);
      if (res.ok) {
        const data = await res.json();
        setNotifications(data.notifications || []);
        setUnread(data.unread_count || 0);
      }
    } catch (e) {}
  };

  const markRead = async (id) => {
    await fetch(`${API_URL}/portal/notifications/${id}/read`, { method: 'PUT' });
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
    setUnread(prev => Math.max(0, prev - 1));
  };

  const markAllRead = async () => {
    await fetch(`${API_URL}/portal/notifications/read-all`, { method: 'PUT' });
    setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
    setUnread(0);
  };

  const typeIcon = (type) => {
    if (type === 'giving') return '💝';
    if (type === 'event') return '📅';
    if (type === 'announcement') return '📢';
    return '🔔';
  };

  const timeAgo = (ts) => {
    if (!ts) return '';
    const diff = Date.now() - new Date(ts).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    return `${Math.floor(hrs / 24)}d ago`;
  };

  return (
    <div className="notif-bell-wrapper" ref={ref} data-testid="notification-bell">
      <button
        className="notif-bell-btn"
        onClick={() => setOpen(!open)}
        data-testid="notification-bell-btn"
      >
        <Bell className="w-5 h-5" />
        {unread > 0 && (
          <span className="notif-badge" data-testid="notification-badge">{unread}</span>
        )}
      </button>

      {open && (
        <div className="notif-dropdown" data-testid="notification-dropdown">
          <div className="notif-dropdown-header">
            <span>Notifications</span>
            {unread > 0 && (
              <button className="notif-mark-all" onClick={markAllRead} data-testid="mark-all-read">
                <CheckCheck className="w-3.5 h-3.5" /> Mark all read
              </button>
            )}
          </div>
          <div className="notif-list">
            {notifications.length === 0 ? (
              <div className="notif-empty">No notifications</div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  className={`notif-item ${n.is_read ? 'read' : 'unread'}`}
                  onClick={() => !n.is_read && markRead(n.id)}
                  data-testid={`notif-item-${n.id}`}
                >
                  <span className="notif-icon">{typeIcon(n.type)}</span>
                  <div className="notif-content">
                    <span className="notif-title">{n.title}</span>
                    <span className="notif-body">{n.body}</span>
                    <span className="notif-time">{timeAgo(n.created_at)}</span>
                  </div>
                  {!n.is_read && <div className="notif-dot" />}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
