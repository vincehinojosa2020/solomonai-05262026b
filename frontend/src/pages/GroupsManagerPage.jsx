import { useState, useEffect, useCallback } from 'react';
import { usePolling } from '@/hooks/usePolling';
import { useNavigate } from 'react-router-dom';
import { 
  Users, Plus, Search, Edit, Trash2, UserPlus, MapPin, Clock,
  Calendar, ChevronRight, MoreVertical, CheckCircle, XCircle,
  Loader2, X, BarChart3, Inbox, Check, Ban
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';

const GROUP_TYPES = [
  { id: 'small-group', name: 'Small Group', icon: '👥' },
  { id: 'bible-study', name: 'Bible Study', icon: '📖' },
  { id: 'prayer-group', name: 'Prayer Group', icon: '🙏' },
  { id: 'youth-group', name: 'Youth Group', icon: '🎯' },
  { id: 'mens-group', name: "Men's Group", icon: '👨' },
  { id: 'womens-group', name: "Women's Group", icon: '👩' },
  { id: 'couples-group', name: 'Couples Group', icon: '💑' },
  { id: 'ministry-team', name: 'Ministry Team', icon: '⛪' },
];

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

export default function GroupsManagerPage() {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingGroup, setEditingGroup] = useState(null);
  const [viewingGroup, setViewingGroup] = useState(null);
  const [stats, setStats] = useState({ total: 0, open: 0, members: 0 });
  const [activeTab, setActiveTab] = useState('groups');
  const [joinRequests, setJoinRequests] = useState([]);

  const token = sessionStorage.getItem('session_token');
  const authHeaders = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  useEffect(() => {
    fetchGroups();
    fetchJoinRequests();
  }, [searchQuery, filterType]);

  // Real-time polling every 30 seconds
  usePolling(useCallback(() => fetchGroups(), [searchQuery, filterType]), 30000);

  const fetchGroups = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('search', searchQuery);
      if (filterType && filterType !== 'all') params.append('group_type', filterType);
      
      const res = await fetch(`${API_URL}/admin/groups?${params}`);
      
      if (res.ok) {
        const data = await res.json();
        setGroups(data.groups || []);
        
        const openCount = (data.groups || []).filter(g => g.is_open).length;
        const totalMembers = (data.groups || []).reduce((sum, g) => sum + (g.member_count || 0), 0);
        setStats({
          total: data.total || 0,
          open: openCount,
          members: totalMembers
        });
      }
    } catch (error) {
      console.error('Error fetching groups:', error);
      toast.error('Failed to load groups');
    } finally {
      setLoading(false);
    }
  };

  const fetchJoinRequests = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/groups/join-requests/all`, { headers: authHeaders });
      if (res.ok) {
        const data = await res.json();
        setJoinRequests(data.requests || []);
      }
    } catch (err) { console.error('Failed to fetch join requests:', err); }
  };

  const handleJoinRequest = async (groupId, requestId, action) => {
    try {
      const res = await fetch(`${API_URL}/admin/groups/${groupId}/join-requests/${requestId}`, {
        method: 'PUT', headers: authHeaders,
        body: JSON.stringify({ action }),
      });
      if (res.ok) {
        toast.success(action === 'approve' ? 'Request approved' : 'Request rejected');
        fetchJoinRequests();
        fetchGroups();
      }
    } catch (err) { toast.error('Failed to process request'); }
  };

  const handleDeleteGroup = async (groupId) => {
    if (!confirm('Are you sure you want to delete this group?')) return;
    
    try {
      const res = await fetch(`${API_URL}/admin/groups/${groupId}`, {
        method: 'DELETE',
        
      });
      
      if (res.ok) {
        toast.success('Group deleted');
        fetchGroups();
      } else {
        toast.error('Failed to delete group');
      }
    } catch (error) {
      toast.error('Failed to delete group');
    }
  };

  const handleToggleOpen = async (group) => {
    try {
      const res = await fetch(`${API_URL}/admin/groups/${group.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({ is_open: !group.is_open })
      });
      
      if (res.ok) {
        toast.success(group.is_open ? 'Group closed' : 'Group opened for registration');
        fetchGroups();
      }
    } catch (error) {
      toast.error('Failed to update group');
    }
  };

  return (
    <div className="groups-manager" data-testid="groups-manager">
      {/* Header */}
      <div className="groups-manager-header">
        <div className="groups-manager-title-row">
          <div>
            <h1 className="groups-manager-title">
              <Users className="w-7 h-7 text-emerald-600" />
              Groups & Bible Studies
            </h1>
            <p className="groups-manager-subtitle">
              Manage small groups that members can discover and join
            </p>
          </div>
          
          <Button 
            onClick={() => setShowAddModal(true)}
            className="groups-add-btn"
            data-testid="add-group-btn"
          >
            <Plus className="w-4 h-4" />
            Create Group
          </Button>
        </div>

        {/* Stats */}
        <div className="groups-stats-row">
          <div className="groups-stat">
            <span className="groups-stat-value">{stats.total}</span>
            <span className="groups-stat-label">Total Groups</span>
          </div>
          <div className="groups-stat">
            <span className="groups-stat-value text-emerald-600">{stats.open}</span>
            <span className="groups-stat-label">Open for Joining</span>
          </div>
          <div className="groups-stat">
            <span className="groups-stat-value text-blue-600">{stats.members}</span>
            <span className="groups-stat-label">Total Members</span>
          </div>
        </div>
      </div>

      {/* Tabs: Groups + Join Requests */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-4">
        <TabsList className="bg-white border border-slate-200 p-1">
          <TabsTrigger value="groups" data-testid="tab-groups">
            <Users className="w-4 h-4 mr-2" />
            Groups
          </TabsTrigger>
          <TabsTrigger value="requests" data-testid="tab-join-requests">
            <Inbox className="w-4 h-4 mr-2" />
            Join Requests
            {joinRequests.length > 0 && (
              <Badge className="ml-1.5 bg-amber-100 text-amber-700 border-amber-200 text-xs px-1.5">{joinRequests.length}</Badge>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="groups" className="mt-4">
          {/* Filters */}
          <div className="groups-filters-bar">
            <div className="groups-search">
              <Search className="w-4 h-4 text-slate-400" />
              <Input
                type="text"
                placeholder="Search groups..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="groups-search-input"
              />
            </div>

            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="groups-type-select"
            >
              <option value="all">All Types</option>
              {GROUP_TYPES.map(type => (
                <option key={type.id} value={type.name}>{type.icon} {type.name}</option>
              ))}
            </select>
          </div>

          {/* Groups List */}
          {loading ? (
            <div className="groups-loading">
              <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
              <p>Loading groups...</p>
            </div>
          ) : groups.length === 0 ? (
            <div className="groups-empty-state">
              <Users className="w-16 h-16 text-slate-300" />
              <h2>No groups yet</h2>
              <p>Create groups for members to discover and join.</p>
              <Button onClick={() => setShowAddModal(true)} className="groups-add-btn">
                <Plus className="w-4 h-4" />
                Create Your First Group
              </Button>
            </div>
          ) : (
            <div className="groups-grid" data-testid="groups-grid">
              {groups.map(group => (
                <GroupCard 
                  key={group.id} 
                  group={group}
                  onEdit={() => setEditingGroup(group)}
                  onDelete={() => handleDeleteGroup(group.id)}
                  onToggleOpen={() => handleToggleOpen(group)}
                  onViewMembers={() => setViewingGroup(group)}
                />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="requests" className="mt-4">
          {joinRequests.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-xl p-12 text-center" data-testid="requests-empty">
              <Inbox className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 mb-1">No pending requests</h3>
              <p className="text-sm text-slate-500">When members request to join groups with approval required, they'll appear here.</p>
            </div>
          ) : (
            <div className="space-y-3" data-testid="join-requests-list">
              {joinRequests.map((req) => (
                <div key={req.id} className="bg-white border border-slate-200 rounded-xl p-4 flex items-center justify-between" data-testid={`join-request-${req.id}`}>
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-amber-50 flex items-center justify-center">
                      <UserPlus className="w-5 h-5 text-amber-600" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-slate-800">{req.person_name || 'Unknown'}</p>
                      <p className="text-xs text-slate-500">
                        Wants to join <span className="font-medium text-slate-700">{req.group_name || 'Unknown Group'}</span>
                        {req.person_email && <span className="ml-2 text-slate-400">{req.person_email}</span>}
                      </p>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Requested {req.requested_at ? new Date(req.requested_at).toLocaleDateString() : 'Recently'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" variant="outline" className="text-red-600 border-red-200 hover:bg-red-50"
                      onClick={() => handleJoinRequest(req.group_id, req.id, 'reject')} data-testid={`reject-request-${req.id}`}>
                      <Ban className="w-3.5 h-3.5 mr-1" /> Reject
                    </Button>
                    <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700 text-white"
                      onClick={() => handleJoinRequest(req.group_id, req.id, 'approve')} data-testid={`approve-request-${req.id}`}>
                      <Check className="w-3.5 h-3.5 mr-1" /> Approve
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Add Group Modal */}
      <AddGroupModal 
        open={showAddModal} 
        onClose={() => setShowAddModal(false)}
        onSuccess={() => {
          setShowAddModal(false);
          fetchGroups();
        }}
      />

      {/* Edit Group Modal */}
      {editingGroup && (
        <EditGroupModal 
          group={editingGroup}
          open={!!editingGroup} 
          onClose={() => setEditingGroup(null)}
          onSuccess={() => {
            setEditingGroup(null);
            fetchGroups();
          }}
        />
      )}

      {/* View Members Modal */}
      {viewingGroup && (
        <ViewMembersModal
          group={viewingGroup}
          open={!!viewingGroup}
          onClose={() => setViewingGroup(null)}
        />
      )}
    </div>
  );
}

function GroupCard({ group, onEdit, onDelete, onToggleOpen, onViewMembers }) {
  const navigate = useNavigate();
  const typeInfo = GROUP_TYPES.find(t => t.name === group.group_type) || GROUP_TYPES[0];
  
  return (
    <div className={`group-card ${!group.is_open ? 'closed' : ''}`} data-testid={`group-card-${group.id}`}>
      <div className="group-card-header">
        <span className="group-type-badge">{typeInfo.icon} {group.group_type || 'Small Group'}</span>
        <div className="flex items-center gap-1.5">
          {group.enrollment_type === 'request_to_join' && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-semibold bg-amber-50 text-amber-700 rounded-full border border-amber-200">Approval Required</span>
          )}
          <span className={`group-status-badge ${group.is_open ? 'open' : 'closed'}`}>
            {group.enrollment_type === 'closed' ? 'Invite Only' : group.is_open ? 'Open' : 'Closed'}
          </span>
        </div>
      </div>
      
      <h3 className="group-card-title">{group.name}</h3>
      
      {group.description && (
        <p className="group-card-desc">{group.description}</p>
      )}
      
      <div className="group-card-meta">
        {group.meeting_day && (
          <div className="group-meta-item">
            <Calendar className="w-4 h-4" />
            <span>{group.meeting_day}{group.meeting_time && ` at ${group.meeting_time}`}</span>
          </div>
        )}
        {group.location && (
          <div className="group-meta-item">
            <MapPin className="w-4 h-4" />
            <span>{group.location}</span>
          </div>
        )}
        <div className="group-meta-item">
          <Users className="w-4 h-4" />
          <span>{group.member_count || 0} members{group.capacity && ` / ${group.capacity} max`}</span>
        </div>
      </div>

      <div className="group-card-actions">
        <button onClick={() => navigate(`/admin/groups/${group.id}/dashboard`)} className="action-btn" title="Leader Dashboard" data-testid={`group-dashboard-${group.id}`}>
          <BarChart3 className="w-4 h-4" />
        </button>
        <button onClick={onViewMembers} className="action-btn" title="View Members">
          <Users className="w-4 h-4" />
        </button>
        <button onClick={onToggleOpen} className={`action-btn ${group.is_open ? 'active' : ''}`} title={group.is_open ? 'Close Group' : 'Open Group'}>
          {group.is_open ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
        </button>
        <button onClick={onEdit} className="action-btn" title="Edit">
          <Edit className="w-4 h-4" />
        </button>
        <button onClick={onDelete} className="action-btn danger" title="Delete">
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

function AddGroupModal({ open, onClose, onSuccess }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [groupType, setGroupType] = useState('Small Group');
  const [meetingDay, setMeetingDay] = useState('');
  const [meetingTime, setMeetingTime] = useState('');
  const [location, setLocation] = useState('');
  const [capacity, setCapacity] = useState('');
  const [isOpen, setIsOpen] = useState(true);
  const [enrollmentType, setEnrollmentType] = useState('open');
  const [category, setCategory] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name) {
      toast.error('Please enter a group name');
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/admin/groups`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({
          name,
          description,
          group_type: groupType,
          meeting_day: meetingDay || null,
          meeting_time: meetingTime || null,
          location: location || null,
          capacity: capacity ? parseInt(capacity) : null,
          is_open: enrollmentType !== 'closed',
          enrollment_type: enrollmentType,
          category: category || null,
        })
      });

      if (res.ok) {
        toast.success('Group created!');
        onSuccess();
        setName(''); setDescription(''); setGroupType('Small Group');
        setMeetingDay(''); setMeetingTime(''); setLocation('');
        setCapacity(''); setIsOpen(true); setEnrollmentType('open'); setCategory('');
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Failed to create group');
      }
    } catch (error) {
      toast.error('Failed to create group');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="add-group-modal">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Users className="w-5 h-5 text-emerald-600" />
            Create New Group
          </DialogTitle>
          <DialogDescription>
            Add a new group for members to discover and join
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="add-group-form">
          <div className="form-group">
            <label>Group Name *</label>
            <Input
              type="text"
              placeholder="e.g., Young Adults Bible Study"
              value={name}
              onChange={(e) => setName(e.target.value)}
              data-testid="group-name-input"
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Group Type</label>
              <select
                value={groupType}
                onChange={(e) => setGroupType(e.target.value)}
                className="form-select"
              >
                {GROUP_TYPES.map(type => (
                  <option key={type.id} value={type.name}>{type.icon} {type.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Capacity (optional)</label>
              <Input
                type="number"
                placeholder="Max members"
                value={capacity}
                onChange={(e) => setCapacity(e.target.value)}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Meeting Day</label>
              <select
                value={meetingDay}
                onChange={(e) => setMeetingDay(e.target.value)}
                className="form-select"
              >
                <option value="">Select day...</option>
                {DAYS.map(day => (
                  <option key={day} value={day}>{day}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Meeting Time</label>
              <Input
                type="time"
                value={meetingTime}
                onChange={(e) => setMeetingTime(e.target.value)}
              />
            </div>
          </div>

          <div className="form-group">
            <label>Location</label>
            <Input
              type="text"
              placeholder="e.g., Room 205 or Johnson Home"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label>Description (optional)</label>
            <textarea
              placeholder="Brief description of the group..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="form-textarea"
              rows={2}
            />
          </div>

          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={isOpen}
              onChange={(e) => setIsOpen(e.target.checked)}
            />
            <UserPlus className="w-4 h-4 text-emerald-500" />
            Open for new members to join
          </label>

          <div className="form-row">
            <div className="form-group">
              <label>Enrollment Type</label>
              <select
                value={enrollmentType}
                onChange={(e) => setEnrollmentType(e.target.value)}
                className="form-select"
                data-testid="enrollment-type-select"
              >
                <option value="open">Open — Anyone can join</option>
                <option value="request_to_join">Request to Join — Requires approval</option>
                <option value="closed">Closed — Invite only</option>
              </select>
            </div>
            <div className="form-group">
              <label>Category (optional)</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="form-select"
                data-testid="category-select"
              >
                <option value="">No category</option>
                <option value="discipleship">Discipleship</option>
                <option value="fellowship">Fellowship</option>
                <option value="outreach">Outreach</option>
                <option value="prayer">Prayer</option>
                <option value="study">Bible Study</option>
                <option value="youth">Youth</option>
                <option value="women">Women's Ministry</option>
                <option value="men">Men's Ministry</option>
                <option value="recovery">Recovery</option>
                <option value="serving">Serving Teams</option>
              </select>
            </div>
          </div>

          <div className="modal-actions">
            <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={loading || !name}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
              Create Group
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function EditGroupModal({ group, open, onClose, onSuccess }) {
  const [name, setName] = useState(group.name || '');
  const [description, setDescription] = useState(group.description || '');
  const [groupType, setGroupType] = useState(group.group_type || 'Small Group');
  const [meetingDay, setMeetingDay] = useState(group.meeting_day || '');
  const [meetingTime, setMeetingTime] = useState(group.meeting_time || '');
  const [location, setLocation] = useState(group.location || '');
  const [capacity, setCapacity] = useState(group.capacity?.toString() || '');
  const [enrollmentType, setEnrollmentType] = useState(group.enrollment_type || 'open');
  const [category, setCategory] = useState(group.category || '');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/admin/groups/${group.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({
          name,
          description,
          group_type: groupType,
          meeting_day: meetingDay || null,
          meeting_time: meetingTime || null,
          location: location || null,
          capacity: capacity ? parseInt(capacity) : null,
          enrollment_type: enrollmentType,
          category: category || null,
          is_open: enrollmentType !== 'closed',
        })
      });

      if (res.ok) {
        toast.success('Group updated!');
        onSuccess();
      } else {
        toast.error('Failed to update group');
      }
    } catch (error) {
      toast.error('Failed to update group');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="edit-group-modal">
        <DialogHeader>
          <DialogTitle>Edit Group</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="edit-group-form">
          <div className="form-group">
            <label>Group Name</label>
            <Input value={name} onChange={(e) => setName(e.target.value)} />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Type</label>
              <select value={groupType} onChange={(e) => setGroupType(e.target.value)} className="form-select">
                {GROUP_TYPES.map(type => (
                  <option key={type.id} value={type.name}>{type.icon} {type.name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Capacity</label>
              <Input type="number" value={capacity} onChange={(e) => setCapacity(e.target.value)} />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Day</label>
              <select value={meetingDay} onChange={(e) => setMeetingDay(e.target.value)} className="form-select">
                <option value="">None</option>
                {DAYS.map(day => <option key={day} value={day}>{day}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>Time</label>
              <Input type="time" value={meetingTime} onChange={(e) => setMeetingTime(e.target.value)} />
            </div>
          </div>

          <div className="form-group">
            <label>Location</label>
            <Input value={location} onChange={(e) => setLocation(e.target.value)} />
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} className="form-textarea" rows={2} />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Enrollment Type</label>
              <select value={enrollmentType} onChange={(e) => setEnrollmentType(e.target.value)} className="form-select" data-testid="edit-enrollment-type">
                <option value="open">Open</option>
                <option value="request_to_join">Request to Join</option>
                <option value="closed">Closed / Invite Only</option>
              </select>
            </div>
            <div className="form-group">
              <label>Category</label>
              <select value={category} onChange={(e) => setCategory(e.target.value)} className="form-select" data-testid="edit-category">
                <option value="">No category</option>
                <option value="discipleship">Discipleship</option>
                <option value="fellowship">Fellowship</option>
                <option value="outreach">Outreach</option>
                <option value="prayer">Prayer</option>
                <option value="study">Bible Study</option>
                <option value="youth">Youth</option>
                <option value="women">Women's Ministry</option>
                <option value="men">Men's Ministry</option>
                <option value="recovery">Recovery</option>
                <option value="serving">Serving Teams</option>
              </select>
            </div>
          </div>

          <div className="modal-actions">
            <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={loading}>
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save Changes'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function ViewMembersModal({ group, open, onClose }) {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddMember, setShowAddMember] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [availablePeople, setAvailablePeople] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);

  useEffect(() => {
    if (open) {
      fetchMembers();
    }
  }, [open, group.id]);

  const fetchMembers = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/groups/${group.id}/members`);
      if (res.ok) {
        const data = await res.json();
        setMembers(data.members || []);
      }
    } catch (error) {
      console.error('Failed to fetch members:', error);
    } finally {
      setLoading(false);
    }
  };

  const searchPeople = async (query) => {
    if (!query || query.length < 2) {
      setAvailablePeople([]);
      return;
    }
    
    setSearchLoading(true);
    try {
      const res = await fetch(
        `${API_URL}/admin/groups/${group.id}/available-members?search=${encodeURIComponent(query)}`,
        { }
      );
      if (res.ok) {
        const data = await res.json();
        setAvailablePeople(data.people || []);
      }
    } catch (error) {
      console.error('Failed to search people:', error);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleAddMember = async (personId) => {
    try {
      const res = await fetch(`${API_URL}/admin/groups/${group.id}/members`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({ person_id: personId })
      });
      
      if (res.ok) {
        toast.success('Member added to group');
        fetchMembers();
        setSearchQuery('');
        setAvailablePeople([]);
        setShowAddMember(false);
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Failed to add member');
      }
    } catch (error) {
      toast.error('Failed to add member');
    }
  };

  const handleRemoveMember = async (personId) => {
    if (!confirm('Remove this member from the group?')) return;
    
    try {
      const res = await fetch(`${API_URL}/admin/groups/${group.id}/members/${personId}`, {
        method: 'DELETE',
        
      });
      
      if (res.ok) {
        toast.success('Member removed');
        fetchMembers();
      } else {
        toast.error('Failed to remove member');
      }
    } catch (error) {
      toast.error('Failed to remove member');
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="view-members-modal" style={{ maxWidth: '500px' }}>
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>{group.name} - Members</span>
            <Button 
              size="sm" 
              variant="outline"
              onClick={() => setShowAddMember(!showAddMember)}
            >
              <UserPlus className="w-4 h-4 mr-1" />
              Add Member
            </Button>
          </DialogTitle>
          <DialogDescription>{members.length} member{members.length !== 1 ? 's' : ''}</DialogDescription>
        </DialogHeader>

        {/* Add Member Section */}
        {showAddMember && (
          <div className="add-member-section" style={{ 
            padding: '12px', 
            background: '#f8fafc', 
            borderRadius: '8px',
            marginBottom: '12px' 
          }}>
            <div style={{ position: 'relative' }}>
              <Search className="w-4 h-4" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
              <Input
                type="text"
                placeholder="Search by name or email..."
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  searchPeople(e.target.value);
                }}
                style={{ paddingLeft: '36px' }}
              />
            </div>
            
            {searchLoading && (
              <div style={{ padding: '8px', textAlign: 'center', color: '#64748b' }}>
                <Loader2 className="w-4 h-4 animate-spin inline" /> Searching...
              </div>
            )}
            
            {availablePeople.length > 0 && (
              <div style={{ marginTop: '8px', maxHeight: '150px', overflowY: 'auto' }}>
                {availablePeople.map(person => (
                  <div 
                    key={person.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '8px',
                      borderRadius: '6px',
                      cursor: 'pointer',
                      background: 'white',
                      marginBottom: '4px'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: '500', fontSize: '14px' }}>
                        {person.first_name} {person.last_name}
                      </div>
                      <div style={{ fontSize: '12px', color: '#64748b' }}>{person.email}</div>
                    </div>
                    <Button size="sm" onClick={() => handleAddMember(person.id)}>
                      <Plus className="w-3 h-3" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
            
            {searchQuery.length >= 2 && !searchLoading && availablePeople.length === 0 && (
              <div style={{ padding: '8px', textAlign: 'center', color: '#94a3b8', fontSize: '13px' }}>
                No available members found
              </div>
            )}
          </div>
        )}

        <div className="members-list" style={{ maxHeight: '300px', overflowY: 'auto' }}>
          {loading ? (
            <div className="members-loading" style={{ textAlign: 'center', padding: '20px' }}>
              <Loader2 className="w-5 h-5 animate-spin inline" /> Loading members...
            </div>
          ) : members.length === 0 ? (
            <div className="members-empty" style={{ textAlign: 'center', padding: '30px', color: '#94a3b8' }}>
              <Users className="w-10 h-10 mx-auto mb-2 opacity-40" />
              <p>No members yet</p>
              <p style={{ fontSize: '12px' }}>Add members using the button above</p>
            </div>
          ) : (
            members.map(member => (
              <div key={member.id} className="member-row" style={{
                display: 'flex',
                alignItems: 'center',
                padding: '10px',
                borderBottom: '1px solid #f1f5f9',
                gap: '12px'
              }}>
                <div className="member-avatar" style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '50%',
                  background: '#3b82f6',
                  color: 'white',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: '600',
                  fontSize: '14px'
                }}>
                  {member.name?.charAt(0) || '?'}
                </div>
                <div className="member-info" style={{ flex: 1 }}>
                  <div className="member-name" style={{ fontWeight: '500', fontSize: '14px' }}>{member.name}</div>
                  <div className="member-email" style={{ fontSize: '12px', color: '#64748b' }}>{member.email}</div>
                </div>
                <span className="member-role" style={{
                  fontSize: '11px',
                  padding: '2px 8px',
                  background: member.role === 'leader' ? '#dcfce7' : '#f1f5f9',
                  color: member.role === 'leader' ? '#16a34a' : '#64748b',
                  borderRadius: '20px',
                  textTransform: 'capitalize'
                }}>
                  {member.role}
                </span>
                <button 
                  onClick={() => handleRemoveMember(member.person_id)}
                  style={{
                    padding: '4px',
                    background: 'transparent',
                    border: 'none',
                    cursor: 'pointer',
                    color: '#94a3b8',
                    borderRadius: '4px'
                  }}
                  title="Remove from group"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
