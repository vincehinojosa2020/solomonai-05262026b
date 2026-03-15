import { useState, useEffect, useRef, useCallback } from 'react';
import { Send, ArrowLeft, Trash2 } from 'lucide-react';
import { API_URL } from '@/lib/utils';

export default function GroupChat({ groupId, groupName, currentUser, onBack }) {
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [sending, setSending] = useState(false);
  const endRef = useRef(null);
  const pollRef = useRef(null);

  const fetchMessages = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/groups/${groupId}/messages?limit=100`);
      if (res.ok) {
        const data = await res.json();
        setMessages(data.messages || []);
      }
    } catch (e) { console.error(e); }
  }, [groupId]);

  useEffect(() => {
    fetchMessages();
    pollRef.current = setInterval(fetchMessages, 5000);
    return () => clearInterval(pollRef.current);
  }, [fetchMessages]);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!text.trim() || sending) return;
    setSending(true);
    try {
      const res = await fetch(`${API_URL}/groups/${groupId}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({ text: text.trim() }),
      });
      if (res.ok) {
        setText('');
        fetchMessages();
      }
    } catch (e) { console.error(e); }
    finally { setSending(false); }
  };

  const handleDelete = async (msgId) => {
    try {
      await fetch(`${API_URL}/groups/${groupId}/messages/${msgId}`, {
        method: 'DELETE', 
      });
      fetchMessages();
    } catch (e) { console.error(e); }
  };

  const userId = currentUser?.user_id || currentUser?.id || '';
  const isAdmin = currentUser?.role === 'church_admin' || currentUser?.role === 'platform_admin';

  const formatTime = (ts) => {
    const d = new Date(ts);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDateSep = (ts) => {
    const d = new Date(ts);
    const today = new Date();
    if (d.toDateString() === today.toDateString()) return 'Today';
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    if (d.toDateString() === yesterday.toDateString()) return 'Yesterday';
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  // Group messages by date
  let lastDate = '';

  return (
    <div data-testid="group-chat" style={{ display: 'flex', flexDirection: 'column', height: '100%', maxHeight: '70vh', background: '#f8fafc', borderRadius: '12px', overflow: 'hidden', border: '1px solid #e2e8f0' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '12px 16px', background: '#0f172a', color: '#fff', flexShrink: 0 }}>
        {onBack && (
          <button onClick={onBack} data-testid="chat-back" style={{ background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: '8px', padding: '6px', cursor: 'pointer', display: 'flex', color: '#fff' }}>
            <ArrowLeft className="w-4 h-4" />
          </button>
        )}
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: '14px', fontWeight: '600' }}>{groupName || 'Group Chat'}</div>
          <div style={{ fontSize: '11px', color: '#94a3b8' }}>{messages.length} messages</div>
        </div>
      </div>

      {/* Messages */}
      <div data-testid="chat-messages" style={{ flex: 1, overflowY: 'auto', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {messages.length === 0 && (
          <div style={{ textAlign: 'center', color: '#94a3b8', fontSize: '13px', padding: '40px 0' }}>
            No messages yet. Start the conversation!
          </div>
        )}
        {messages.map((msg) => {
          const isMine = msg.sender_id === userId;
          const dateStr = formatDateSep(msg.created_at);
          let showDateSep = false;
          if (dateStr !== lastDate) {
            lastDate = dateStr;
            showDateSep = true;
          }

          return (
            <div key={msg.id}>
              {showDateSep && (
                <div style={{ textAlign: 'center', fontSize: '11px', color: '#94a3b8', fontWeight: '600', padding: '8px 0 4px' }}>
                  {dateStr}
                </div>
              )}
              <div
                data-testid={`msg-${msg.id}`}
                style={{
                  display: 'flex',
                  justifyContent: isMine ? 'flex-end' : 'flex-start',
                  marginBottom: '2px',
                }}
              >
                <div style={{
                  maxWidth: '75%',
                  padding: '8px 12px',
                  borderRadius: isMine ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                  background: isMine ? '#3b82f6' : '#fff',
                  color: isMine ? '#fff' : '#1e293b',
                  border: isMine ? 'none' : '1px solid #e2e8f0',
                  position: 'relative',
                  group: 'msg',
                }}>
                  {!isMine && (
                    <div style={{ fontSize: '11px', fontWeight: '600', color: msg.sender_role?.includes('admin') ? '#f59e0b' : '#3b82f6', marginBottom: '2px' }}>
                      {msg.sender_name}
                      {msg.sender_role?.includes('admin') && (
                        <span style={{ fontSize: '9px', background: '#fef3c7', color: '#d97706', padding: '1px 5px', borderRadius: '4px', marginLeft: '4px' }}>Admin</span>
                      )}
                    </div>
                  )}
                  <div style={{ fontSize: '13px', lineHeight: 1.5, wordBreak: 'break-word' }}>{msg.text}</div>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: isMine ? 'flex-end' : 'flex-start', gap: '6px', marginTop: '2px' }}>
                    <span style={{ fontSize: '10px', color: isMine ? 'rgba(255,255,255,0.6)' : '#94a3b8' }}>{formatTime(msg.created_at)}</span>
                    {(isMine || isAdmin) && (
                      <button
                        data-testid={`delete-msg-${msg.id}`}
                        onClick={() => handleDelete(msg.id)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px', opacity: 0.4, color: isMine ? '#fff' : '#94a3b8' }}
                        title="Delete"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div style={{ display: 'flex', gap: '8px', padding: '12px 16px', background: '#fff', borderTop: '1px solid #e2e8f0', flexShrink: 0 }}>
        <input
          data-testid="chat-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
          placeholder="Type a message..."
          style={{ flex: 1, padding: '10px 14px', border: '1px solid #e2e8f0', borderRadius: '10px', fontSize: '13px', outline: 'none' }}
        />
        <button
          data-testid="chat-send"
          onClick={handleSend}
          disabled={!text.trim() || sending}
          style={{
            width: '40px', height: '40px', borderRadius: '10px',
            background: text.trim() ? '#3b82f6' : '#e5e7eb',
            border: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: text.trim() ? 'pointer' : 'not-allowed',
            color: text.trim() ? '#fff' : '#94a3b8',
            transition: 'background 0.2s',
          }}
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
