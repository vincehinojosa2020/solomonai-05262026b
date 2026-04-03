import { useState, useEffect, useCallback } from 'react';
import { useOutletContext } from 'react-router-dom';
import { usePolling } from '@/hooks/usePolling';
import { Users, MapPin, Clock, ChevronRight, Search, Bell, LogOut, MessageCircle, ArrowLeft, Calendar, X, Send } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import GroupChat from '@/components/GroupChat';

export default function PortalGroups() {
  const { user, memberData, tenant } = useOutletContext();
  const [allGroups, setAllGroups] = useState([]);
  const [myGroups, setMyGroups] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [loadingGroups, setLoadingGroups] = useState(true);
  const [chatGroup, setChatGroup] = useState(null);
  const [detailGroup, setDetailGroup] = useState(null);
  const [detailData, setDetailData] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [newQuestion, setNewQuestion] = useState('');

  useEffect(() => { fetchGroups(); fetchMyGroups(); }, []);
  const pollGroups = useCallback(() => { fetchGroups(); fetchMyGroups(); }, []);
  usePolling(pollGroups, 30000);

  const fetchGroups = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/groups`);
      if (res.ok) setAllGroups(await res.json());
    } catch (e) { console.error('Failed to fetch groups:', e); }
    finally { setLoadingGroups(false); }
  };

  const fetchMyGroups = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/my-groups`);
      if (res.ok) { const d = await res.json(); setMyGroups(d.groups || []); }
    } catch (e) { console.error('Failed to fetch my groups:', e); }
  };

  const myGroupIds = myGroups.map(g => g.id);

  const filteredGroups = allGroups.filter(g => {
    const matchesSearch = !searchQuery || g.name.toLowerCase().includes(searchQuery.toLowerCase()) || g.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = filterType === 'all' || g.group_type_id === filterType;
    return matchesSearch && matchesType && !myGroupIds.includes(g.id);
  });

  const handleJoinRequest = async (groupId) => {
    try {
      const res = await fetch(`${API_URL}/portal/groups/${groupId}/join`, { method: 'POST' });
      if (res.ok) { const d = await res.json(); toast.success(d.message || 'You have joined the group!'); fetchGroups(); fetchMyGroups(); }
      else { const err = await res.json(); toast.error(err.detail || 'Failed to join group'); }
    } catch { toast.error('Failed to join group'); }
  };

  const handleLeaveGroup = async (groupId) => {
    if (!confirm('Are you sure you want to leave this group?')) return;
    try {
      const res = await fetch(`${API_URL}/portal/groups/${groupId}/leave`, { method: 'DELETE' });
      if (res.ok) { toast.success('You have left the group'); fetchGroups(); fetchMyGroups(); }
      else { const err = await res.json(); toast.error(err.detail || 'Failed to leave group'); }
    } catch { toast.error('Failed to leave group'); }
  };

  const handleNotify = async (groupId) => {
    try {
      const res = await fetch(`${API_URL}/portal/groups/${groupId}/notify`, { method: 'POST' });
      if (res.ok) { const d = await res.json(); toast.success(d.message || 'You will be notified when a spot opens up.'); }
      else { const err = await res.json(); toast.info(err.detail || 'Already on the notification list'); }
    } catch { toast.error('Failed to subscribe'); }
  };

  const openGroupDetail = async (group) => {
    setDetailGroup(group);
    setDetailData(null);
    setQuestions([]);
    setNewQuestion('');
    try {
      const [detailRes, qaRes] = await Promise.all([
        fetch(`${API_URL}/portal/groups/${group.id}/detail`),
        fetch(`${API_URL}/portal/groups/${group.id}/questions`),
      ]);
      if (detailRes.ok) setDetailData(await detailRes.json());
      if (qaRes.ok) { const d = await qaRes.json(); setQuestions(d.questions || []); }
    } catch (e) { console.error(e); }
  };

  const submitQuestion = async () => {
    if (!newQuestion.trim() || !detailGroup) return;
    try {
      const res = await fetch(`${API_URL}/portal/groups/${detailGroup.id}/questions`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: newQuestion }),
      });
      if (res.ok) {
        toast.success('Question submitted!');
        setNewQuestion('');
        const qaRes = await fetch(`${API_URL}/portal/groups/${detailGroup.id}/questions`);
        if (qaRes.ok) { const d = await qaRes.json(); setQuestions(d.questions || []); }
      }
    } catch { toast.error('Failed to submit question'); }
  };

  const GroupCard = ({ group, isMine = false }) => (
    <div className="portal-group-card" data-testid={`group-card-${group.id}`}>
      <div className="portal-group-card-header">
        <h3 className="portal-group-name">{group.name}</h3>
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          {isMine && (
            <button onClick={() => setChatGroup(group)} className="portal-group-action-btn primary" data-testid={`group-chat-btn-${group.id}`} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <MessageCircle className="w-3.5 h-3.5" /> Chat
            </button>
          )}
          {isMine ? (
            <button onClick={() => handleLeaveGroup(group.id)} className="portal-group-action-btn secondary" style={{ color: '#dc2626' }}>
              <LogOut className="w-3 h-3" /> Leave
            </button>
          ) : group.is_open ? (
            <button onClick={() => handleJoinRequest(group.id)} className="portal-group-action-btn primary">Request to Join</button>
          ) : (
            <button onClick={() => handleNotify(group.id)} className="portal-group-action-btn secondary" data-testid={`group-notify-btn-${group.id}`}>
              <Bell className="w-3 h-3" /> Get Notified
            </button>
          )}
        </div>
      </div>
      <div className="portal-group-meta">
        <span className="portal-group-type">{group.group_type || 'Small Group'}</span>
        {group.leader && <span className="portal-group-leader">{group.leader.first_name} {group.leader.last_name}, Leader</span>}
        {isMine && group.role && (
          <span style={{ background: group.role === 'leader' ? '#dcfce7' : '#e0f2fe', color: group.role === 'leader' ? '#16a34a' : '#0369a1', padding: '2px 8px', borderRadius: '10px', fontSize: '11px' }}>{group.role}</span>
        )}
      </div>
      <div className="portal-group-details">
        {group.meeting_day && <div className="portal-group-detail"><Clock className="w-4 h-4" /><span>{group.meeting_day}s at {group.meeting_time || '7:00 PM'}</span></div>}
        {group.location && <div className="portal-group-detail"><MapPin className="w-4 h-4" /><span>{group.location}</span></div>}
        <div className="portal-group-detail"><Users className="w-4 h-4" /><span>{group.member_count || 0}{group.capacity ? ` / ${group.capacity}` : ''} members</span>{group.is_open && !isMine && <span className="text-green-600 ml-1">Open</span>}</div>
        {(group.start_date || group.end_date) && <div className="portal-group-detail"><Calendar className="w-4 h-4" /><span>{group.start_date || ''}{group.end_date ? ` — ${group.end_date}` : ''}</span></div>}
      </div>
      <button onClick={() => openGroupDetail(group)} className="text-xs text-blue-600 font-medium mt-2 hover:underline" data-testid={`group-detail-btn-${group.id}`}>View Details & Q&A</button>
    </div>
  );

  /* ---- Detail / Q&A Overlay ---- */
  const DetailOverlay = () => {
    if (!detailGroup) return null;
    const d = detailData || detailGroup;
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm" data-testid="group-detail-overlay">
        <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 max-h-[85vh] overflow-y-auto" style={{ animation: 'fadeInUp .2s ease' }}>
          {/* Header */}
          <div className="flex items-center justify-between p-5 border-b border-slate-100">
            <h2 className="text-lg font-bold text-slate-900">{d.name}</h2>
            <button onClick={() => setDetailGroup(null)} className="p-1 rounded-full hover:bg-slate-100" data-testid="close-group-detail"><X className="w-5 h-5 text-slate-400" /></button>
          </div>

          {/* Info */}
          <div className="p-5 space-y-3 text-sm text-slate-700">
            {d.description && <p className="text-slate-600">{d.description}</p>}
            <div className="grid grid-cols-2 gap-3">
              {(d.leader_name || d.leader) && (
                <div className="flex items-center gap-2"><Users className="w-4 h-4 text-slate-400" /><span className="font-medium">Leader:</span> {d.leader_name || `${d.leader?.first_name || ''} ${d.leader?.last_name || ''}`}</div>
              )}
              {(d.address || d.location) && <div className="flex items-center gap-2"><MapPin className="w-4 h-4 text-slate-400" />{d.address || d.location}</div>}
              {d.meeting_day && <div className="flex items-center gap-2"><Clock className="w-4 h-4 text-slate-400" />{d.meeting_day}s at {d.meeting_time || '7:00 PM'}</div>}
              {d.capacity && <div className="flex items-center gap-2"><Users className="w-4 h-4 text-slate-400" />{d.member_count ?? '?'} / {d.capacity} members {d.spots_available != null && <span className="text-xs text-green-600">({d.spots_available} spots left)</span>}</div>}
            </div>
            {d.start_date && <div className="flex items-center gap-2"><Calendar className="w-4 h-4 text-slate-400" />{d.start_date}{d.end_date ? ` — ${d.end_date}` : ''}</div>}
          </div>

          {/* Q&A Section */}
          <div className="border-t border-slate-100 p-5">
            <h3 className="font-semibold text-sm text-slate-800 mb-3">Questions & Answers</h3>
            {questions.length === 0 ? (
              <p className="text-slate-400 text-xs mb-3">No questions yet. Be the first to ask!</p>
            ) : (
              <div className="space-y-3 mb-4 max-h-48 overflow-y-auto">
                {questions.map(q => (
                  <div key={q.id} className="bg-slate-50 rounded-lg p-3" data-testid={`question-${q.id}`}>
                    <p className="text-sm font-medium text-slate-700">{q.question}</p>
                    <p className="text-xs text-slate-400 mt-1">— {q.person_name} · {new Date(q.created_at).toLocaleDateString()}</p>
                    {q.answer && (
                      <div className="mt-2 pl-3 border-l-2 border-teal-400">
                        <p className="text-sm text-teal-800">{q.answer}</p>
                        <p className="text-xs text-slate-400 mt-1">— {q.answered_by}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
            <div className="flex gap-2">
              <input
                type="text"
                value={newQuestion}
                onChange={e => setNewQuestion(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && submitQuestion()}
                placeholder="Ask a question..."
                className="flex-1 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-300"
                data-testid="group-question-input"
              />
              <button onClick={submitQuestion} disabled={!newQuestion.trim()} className="bg-slate-900 text-white rounded-lg px-3 py-2 text-sm disabled:opacity-40 hover:bg-slate-800 transition-colors" data-testid="group-question-submit">
                <Send className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="portal-groups" data-testid="portal-groups">
      <DetailOverlay />

      {chatGroup ? (
        <div data-testid="portal-group-chat-view" style={{ maxWidth: '700px', margin: '0 auto' }}>
          <GroupChat groupId={chatGroup.id} groupName={chatGroup.name} currentUser={user} onBack={() => setChatGroup(null)} />
        </div>
      ) : (
        <>
          <div className="portal-page-header">
            <h1 className="portal-page-title">Discover Groups</h1>
            <p className="portal-page-subtitle">Connect with others at {tenant?.name || 'our church'}</p>
          </div>

          {myGroups.length > 0 && (
            <div className="portal-section">
              <h2 className="portal-section-title">MY GROUPS</h2>
              <div className="portal-groups-grid">
                {myGroups.map(group => <GroupCard key={group.id} group={group} isMine={true} />)}
              </div>
            </div>
          )}

          <div className="portal-section mt-8">
            <h2 className="portal-section-title">DISCOVER MORE GROUPS</h2>
            <div className="portal-groups-filters">
              <select value={filterType} onChange={e => setFilterType(e.target.value)} className="portal-select">
                <option value="all">All Types</option>
                <option value="small-group">Small Groups</option>
                <option value="ministry">Ministry Teams</option>
                <option value="class">Classes</option>
              </select>
              <div className="portal-search-input">
                <Search className="w-4 h-4 text-slate-400" />
                <input type="text" value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Search groups..." className="portal-search-field" />
              </div>
            </div>
            <div className="portal-groups-grid">
              {filteredGroups.length === 0 ? (
                <p className="text-slate-500 text-sm py-4 col-span-full">No groups found matching your criteria.</p>
              ) : filteredGroups.map(group => <GroupCard key={group.id} group={group} isMine={false} />)}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
