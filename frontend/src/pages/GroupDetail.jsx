import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Edit, UserPlus, Mail, MoreHorizontal, MapPin, Clock, Users,
  CalendarDays, LinkIcon, MessageCircle, Plus, Trash2, Send, FileText, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { API_URL, formatDate, getInitials } from '@/lib/utils';
import { toast } from 'sonner';

import { CreateEventDialog, AddResourceDialog } from './GroupDetailDialogs';

export default function GroupDetail() {
  const { groupId } = useParams();
  const navigate = useNavigate();
  
  const [group, setGroup] = useState(null);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('roster');
  const [events, setEvents] = useState([]);
  const [resources, setResources] = useState([]);
  const [messages, setMessages] = useState([]);
  const [showEventForm, setShowEventForm] = useState(false);
  const [showResourceForm, setShowResourceForm] = useState(false);
  const [newMessage, setNewMessage] = useState('');
  const [eventForm, setEventForm] = useState({ title: '', description: '', event_date: '', event_time: '', location: '' });
  const [resourceForm, setResourceForm] = useState({ title: '', description: '', resource_type: 'link', url: '' });
  const chatEndRef = useRef(null);

  const token = sessionStorage.getItem('session_token');
  const authHeaders = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  useEffect(() => {
    fetchGroupData();
    fetchEvents();
    fetchResources();
    fetchMessages();
  }, [groupId]);

  const fetchGroupData = async () => {
    setLoading(true);
    try {
      const [groupRes, membersRes] = await Promise.all([
        fetch(`${API_URL}/groups/${groupId}`),
        fetch(`${API_URL}/groups/${groupId}/members/list`),
      ]);

      const [groupData, membersData] = await Promise.all([
        groupRes.json(),
        membersRes.json(),
      ]);

      setGroup(groupData);
      // Ensure members is always an array
      setMembers(Array.isArray(membersData) ? membersData : (membersData.members || []));
    } catch (error) {
      console.error('Failed to fetch group data:', error);
      setMembers([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchEvents = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/groups/${groupId}/events`, { headers: authHeaders });
      if (res.ok) { const d = await res.json(); setEvents(d.events || []); }
    } catch (e) { console.error('Failed to fetch events:', e); }
  };

  const createEvent = async () => {
    if (!eventForm.title || !eventForm.event_date) { toast.error('Title and date required'); return; }
    try {
      const res = await fetch(`${API_URL}/admin/groups/${groupId}/events`, {
        method: 'POST', headers: authHeaders, body: JSON.stringify(eventForm)
      });
      if (res.ok) { toast.success('Event created'); setShowEventForm(false); setEventForm({ title: '', description: '', event_date: '', event_time: '', location: '' }); fetchEvents(); }
    } catch (e) { toast.error('Failed to create event'); }
  };

  const deleteEvent = async (eventId) => {
    try {
      await fetch(`${API_URL}/admin/groups/${groupId}/events/${eventId}`, { method: 'DELETE', headers: authHeaders });
      toast.success('Event deleted'); fetchEvents();
    } catch (e) { toast.error('Failed to delete event'); }
  };

  const rsvpEvent = async (eventId, personId, personName, response) => {
    try {
      await fetch(`${API_URL}/admin/groups/${groupId}/events/${eventId}/rsvp`, {
        method: 'POST', headers: authHeaders,
        body: JSON.stringify({ person_id: personId, person_name: personName, response })
      });
      toast.success(`RSVP: ${response}`); fetchEvents();
    } catch (e) { toast.error('Failed to RSVP'); }
  };

  const fetchResources = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/groups/${groupId}/resources`, { headers: authHeaders });
      if (res.ok) { const d = await res.json(); setResources(d.resources || []); }
    } catch (e) { console.error('Failed to fetch resources:', e); }
  };

  const addResource = async () => {
    if (!resourceForm.title) { toast.error('Title required'); return; }
    try {
      const res = await fetch(`${API_URL}/admin/groups/${groupId}/resources`, {
        method: 'POST', headers: authHeaders, body: JSON.stringify(resourceForm)
      });
      if (res.ok) { toast.success('Resource added'); setShowResourceForm(false); setResourceForm({ title: '', description: '', resource_type: 'link', url: '' }); fetchResources(); }
    } catch (e) { toast.error('Failed to add resource'); }
  };

  const deleteResource = async (resourceId) => {
    try {
      await fetch(`${API_URL}/admin/groups/${groupId}/resources/${resourceId}`, { method: 'DELETE', headers: authHeaders });
      toast.success('Resource removed'); fetchResources();
    } catch (e) { toast.error('Failed to delete resource'); }
  };

  const fetchMessages = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/groups/${groupId}/messages`, { headers: authHeaders });
      if (res.ok) { const d = await res.json(); setMessages(d.messages || []); }
    } catch (e) { console.error('Failed to fetch messages:', e); }
  };

  const sendMessage = async () => {
    if (!newMessage.trim()) return;
    try {
      const res = await fetch(`${API_URL}/admin/groups/${groupId}/messages`, {
        method: 'POST', headers: authHeaders, body: JSON.stringify({ content: newMessage.trim() })
      });
      if (res.ok) { setNewMessage(''); fetchMessages(); setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 200); }
    } catch (e) { toast.error('Failed to send message'); }
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-32 bg-slate-200 rounded-lg"></div>
        <div className="h-96 bg-slate-200 rounded-lg"></div>
      </div>
    );
  }

  if (!group) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">Group not found</p>
        <Button variant="link" onClick={() => navigate('/groups')}>
          Back to Groups
        </Button>
      </div>
    );
  }

  const capacityPercent = group.capacity 
    ? Math.round((group.member_count / group.capacity) * 100)
    : 0;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="group-detail-page">
      {/* Back Button */}
      <button
        onClick={() => navigate('/groups')}
        className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700"
        data-testid="back-btn"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Groups
      </button>

      {/* Group Header */}
      <div 
        className="rounded-xl p-6 text-white"
        style={{ backgroundColor: group.type_info?.color || '#4f6ef7' }}
        data-testid="group-header"
      >
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold">{group.name}</h1>
              <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-white/20">
                {group.is_open ? 'Open' : 'Closed'}
              </span>
            </div>
            {group.type_info && (
              <p className="text-white/80">{group.type_info.name}</p>
            )}
            {group.description && (
              <p className="text-white/70 mt-2 max-w-xl">{group.description}</p>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button size="sm" variant="secondary" data-testid="edit-group-btn">
              <Edit className="w-4 h-4 mr-2" />
              Edit
            </Button>
            <Button size="sm" variant="secondary" data-testid="add-member-btn">
              <UserPlus className="w-4 h-4 mr-2" />
              Add Member
            </Button>
            <Button size="sm" variant="secondary" data-testid="email-group-btn">
              <Mail className="w-4 h-4 mr-2" />
              Email All
            </Button>
          </div>
        </div>

        {/* Group Info */}
        <div className="flex items-center gap-6 mt-6 text-sm text-white/80">
          {group.leader && (
            <div className="flex items-center gap-2">
              <Avatar className="w-6 h-6">
                <AvatarImage src={group.leader.photo_url} />
                <AvatarFallback className="text-xs">
                  {getInitials(group.leader.first_name, group.leader.last_name)}
                </AvatarFallback>
              </Avatar>
              <span>Led by {group.leader.first_name} {group.leader.last_name}</span>
            </div>
          )}
          {group.location && (
            <div className="flex items-center gap-2">
              <MapPin className="w-4 h-4" />
              <span>{group.location}</span>
            </div>
          )}
          {group.meeting_day && (
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4" />
              <span>{group.meeting_day} {group.meeting_time && `at ${group.meeting_time}`}</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            <span>{group.member_count || 0} members</span>
          </div>
        </div>

        {/* Capacity Bar */}
        {group.capacity && (
          <div className="mt-6">
            <div className="flex items-center justify-between text-xs text-white/80 mb-2">
              <span>Capacity</span>
              <span>{group.member_count} / {group.capacity} ({capacityPercent}%)</span>
            </div>
            <div className="h-2 bg-white/20 rounded-full overflow-hidden">
              <div 
                className="h-full bg-white/80 rounded-full transition-all"
                style={{ width: `${capacityPercent}%` }}
              ></div>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-white border border-slate-200 p-1">
          <TabsTrigger value="roster" data-testid="tab-roster">Roster</TabsTrigger>
          <TabsTrigger value="attendance" data-testid="tab-attendance">Attendance</TabsTrigger>
          <TabsTrigger value="events" data-testid="tab-events">
            <CalendarDays className="w-4 h-4 mr-1" />Events
            {events.length > 0 && <Badge className="ml-1 text-xs px-1.5" variant="secondary">{events.length}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="resources" data-testid="tab-resources">
            <FileText className="w-4 h-4 mr-1" />Resources
          </TabsTrigger>
          <TabsTrigger value="chat" data-testid="tab-chat">
            <MessageCircle className="w-4 h-4 mr-1" />Chat
            {messages.length > 0 && <Badge className="ml-1 text-xs px-1.5" variant="secondary">{messages.length}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="about" data-testid="tab-about">About</TabsTrigger>
          <TabsTrigger value="settings" data-testid="tab-settings">Settings</TabsTrigger>
        </TabsList>

        {/* Roster Tab */}
        <TabsContent value="roster" className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-lg">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <h3 className="font-semibold text-slate-900">Group Members ({members.length})</h3>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm">Export Roster</Button>
                <Button size="sm" className="btn-primary">
                  <UserPlus className="w-4 h-4 mr-2" />
                  Add Member
                </Button>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Role</th>
                    <th>Joined</th>
                    <th>Email</th>
                    <th className="w-20">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {members.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="text-center py-8 text-slate-400">
                        No members in this group
                      </td>
                    </tr>
                  ) : (
                    members.map((member) => (
                      <tr key={member.id} className="hover:bg-slate-50">
                        <td>
                          <Link 
                            to={`/people/${member.id}`}
                            className="flex items-center gap-3 hover:text-blue-600"
                          >
                            <Avatar className="w-8 h-8">
                              <AvatarImage src={member.photo_url} />
                              <AvatarFallback className="text-xs">
                                {getInitials(member.first_name, member.last_name)}
                              </AvatarFallback>
                            </Avatar>
                            <span className="font-medium">
                              {member.first_name} {member.last_name}
                            </span>
                          </Link>
                        </td>
                        <td>
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            member.role === 'leader' 
                              ? 'bg-blue-50 text-blue-700' 
                              : 'bg-slate-100 text-slate-600'
                          }`}>
                            {member.role.charAt(0).toUpperCase() + member.role.slice(1)}
                          </span>
                        </td>
                        <td className="text-slate-600">{formatDate(member.joined_at)}</td>
                        <td className="text-slate-600">{member.email || '—'}</td>
                        <td>
                          <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                            <MoreHorizontal className="w-4 h-4" />
                          </Button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </TabsContent>

        {/* Attendance Tab */}
        <TabsContent value="attendance">
          <div className="bg-white border border-slate-200 rounded-lg p-8 text-center">
            <Clock className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <h3 className="font-semibold text-slate-900 mb-2">Group Attendance</h3>
            <p className="text-slate-400 text-sm mb-4">Track attendance for group meetings</p>
            <Button variant="outline" size="sm">Record Attendance</Button>
          </div>
        </TabsContent>

        {/* Events Tab */}
        <TabsContent value="events" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-700">Group Events</h3>
            <Button size="sm" onClick={() => setShowEventForm(true)} data-testid="create-event-btn">
              <Plus className="w-3.5 h-3.5 mr-1" /> New Event
            </Button>
          </div>
          {events.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-xl p-10 text-center" data-testid="events-empty">
              <CalendarDays className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <p className="text-sm text-slate-500">No events yet. Create your first group event.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {events.map(evt => (
                <div key={evt.id} className="bg-white border border-slate-200 rounded-xl p-4" data-testid={`event-${evt.id}`}>
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="text-sm font-semibold text-slate-800">{evt.title}</h4>
                      {evt.description && <p className="text-xs text-slate-500 mt-1">{evt.description}</p>}
                      <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                        <span className="flex items-center gap-1"><CalendarDays className="w-3.5 h-3.5" />{formatDate(evt.event_date)}</span>
                        {evt.event_time && <span className="flex items-center gap-1"><Clock className="w-3.5 h-3.5" />{evt.event_time}</span>}
                        {evt.location && <span className="flex items-center gap-1"><MapPin className="w-3.5 h-3.5" />{evt.location}</span>}
                      </div>
                      {evt.rsvp_counts && (
                        <div className="flex items-center gap-3 mt-2">
                          <Badge variant="outline" className="text-emerald-600 border-emerald-200 text-xs">{evt.rsvp_counts.attending} attending</Badge>
                          <Badge variant="outline" className="text-amber-600 border-amber-200 text-xs">{evt.rsvp_counts.maybe} maybe</Badge>
                          <Badge variant="outline" className="text-slate-500 border-slate-200 text-xs">{evt.rsvp_counts.declined} declined</Badge>
                        </div>
                      )}
                    </div>
                    <Button size="sm" variant="ghost" className="text-red-400 hover:text-red-600"
                      onClick={() => deleteEvent(evt.id)} data-testid={`delete-event-${evt.id}`}>
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Resources Tab */}
        <TabsContent value="resources" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-slate-700">Shared Resources</h3>
            <Button size="sm" onClick={() => setShowResourceForm(true)} data-testid="add-resource-btn">
              <Plus className="w-3.5 h-3.5 mr-1" /> Add Resource
            </Button>
          </div>
          {resources.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-xl p-10 text-center" data-testid="resources-empty">
              <FileText className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <p className="text-sm text-slate-500">No resources shared yet. Add study guides, links, or documents.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {resources.map(res => (
                <div key={res.id} className="bg-white border border-slate-200 rounded-xl p-4 flex items-center justify-between group" data-testid={`resource-${res.id}`}>
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center">
                      {res.resource_type === 'link' ? <LinkIcon className="w-4 h-4 text-blue-600" /> : <FileText className="w-4 h-4 text-blue-600" />}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-800">{res.title}</p>
                      {res.description && <p className="text-xs text-slate-500">{res.description}</p>}
                      <p className="text-xs text-slate-400 mt-0.5">Added by {res.created_by_name} &middot; {formatDate(res.created_at)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {res.url && (
                      <a href={safeHref(res.url)} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:text-blue-700">
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    )}
                    <button onClick={() => deleteResource(res.id)} className="text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity" data-testid={`delete-resource-${res.id}`}>
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Chat Tab */}
        <TabsContent value="chat" className="space-y-0">
          <div className="bg-white border border-slate-200 rounded-xl overflow-hidden" data-testid="group-chat">
            <div className="p-3 border-b border-slate-100 bg-slate-50">
              <p className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <MessageCircle className="w-4 h-4" /> Group Chat
              </p>
            </div>
            <div className="h-[400px] overflow-y-auto p-4 space-y-3" data-testid="chat-messages">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <p className="text-sm text-slate-400">No messages yet. Start the conversation!</p>
                </div>
              ) : messages.map(msg => (
                <div key={msg.id} className="flex items-start gap-2.5" data-testid={`message-${msg.id}`}>
                  <div className="w-8 h-8 rounded-full bg-emerald-50 flex items-center justify-center flex-shrink-0">
                    <span className="text-xs font-semibold text-emerald-600">{(msg.sender_name || 'U').charAt(0)}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-slate-700">{msg.sender_name}</span>
                      <span className="text-[10px] text-slate-400">{msg.created_at ? new Date(msg.created_at).toLocaleString() : ''}</span>
                    </div>
                    <p className="text-sm text-slate-600 mt-0.5 break-words">{msg.content}</p>
                  </div>
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>
            <div className="p-3 border-t border-slate-100 flex items-center gap-2">
              <Input placeholder="Type a message..." value={newMessage} onChange={e => setNewMessage(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }}}
                className="flex-1" data-testid="chat-input" />
              <Button size="sm" onClick={sendMessage} disabled={!newMessage.trim()} data-testid="send-message-btn">
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="about" className="space-y-4">
          <div className="bg-white border border-slate-200 rounded-lg p-5">
            <h3 className="font-semibold text-slate-900 mb-4">Group Details</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-slate-400 mb-1">Group Name</p>
                <p className="text-sm text-slate-700">{group.name}</p>
              </div>
              <div>
                <p className="text-xs text-slate-400 mb-1">Type</p>
                <p className="text-sm text-slate-700">{group.type_info?.name || '—'}</p>
              </div>
              <div>
                <p className="text-xs text-slate-400 mb-1">Location</p>
                <p className="text-sm text-slate-700">{group.location || '—'}</p>
              </div>
              <div>
                <p className="text-xs text-slate-400 mb-1">Meeting Schedule</p>
                <p className="text-sm text-slate-700">{group.meeting_schedule || '—'}</p>
              </div>
              <div>
                <p className="text-xs text-slate-400 mb-1">Capacity</p>
                <p className="text-sm text-slate-700">{group.capacity || 'Unlimited'}</p>
              </div>
              <div>
                <p className="text-xs text-slate-400 mb-1">Status</p>
                <p className="text-sm text-slate-700">{group.is_open ? 'Open for new members' : 'Closed'}</p>
              </div>
            </div>
          </div>
        </TabsContent>

        {/* Settings Tab */}
        <TabsContent value="settings">
          <div className="bg-white border border-slate-200 rounded-lg p-8 text-center">
            <h3 className="font-semibold text-slate-900 mb-2">Group Settings</h3>
            <p className="text-slate-400 text-sm mb-4">Manage group configuration and preferences</p>
            <Button variant="outline" size="sm">Edit Settings</Button>
          </div>
        </TabsContent>
      </Tabs>

      <CreateEventDialog
        open={showEventForm}
        onOpenChange={setShowEventForm}
        eventForm={eventForm}
        setEventForm={setEventForm}
        onCreate={createEvent}
      />

      <AddResourceDialog
        open={showResourceForm}
        onOpenChange={setShowResourceForm}
        resourceForm={resourceForm}
        setResourceForm={setResourceForm}
        onAdd={addResource}
      />
    </div>
  );
}
