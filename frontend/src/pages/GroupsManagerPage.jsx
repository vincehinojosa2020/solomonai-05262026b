import { useState, useEffect } from 'react';
import { 
  Users, Plus, Search, Edit, Trash2, UserPlus, MapPin, Clock,
  Calendar, ChevronRight, MoreVertical, CheckCircle, XCircle,
  Loader2, X
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
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

  useEffect(() => {
    fetchGroups();
  }, [searchQuery, filterType]);

  const fetchGroups = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('search', searchQuery);
      if (filterType && filterType !== 'all') params.append('group_type', filterType);
      
      const res = await fetch(`${API_URL}/admin/groups?${params}`, { credentials: 'include' });
      
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

  const handleDeleteGroup = async (groupId) => {
    if (!confirm('Are you sure you want to delete this group?')) return;
    
    try {
      const res = await fetch(`${API_URL}/admin/groups/${groupId}`, {
        method: 'DELETE',
        credentials: 'include'
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
        credentials: 'include',
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
  const typeInfo = GROUP_TYPES.find(t => t.name === group.group_type) || GROUP_TYPES[0];
  
  return (
    <div className={`group-card ${!group.is_open ? 'closed' : ''}`} data-testid={`group-card-${group.id}`}>
      <div className="group-card-header">
        <span className="group-type-badge">{typeInfo.icon} {group.group_type || 'Small Group'}</span>
        <span className={`group-status-badge ${group.is_open ? 'open' : 'closed'}`}>
          {group.is_open ? 'Open' : 'Closed'}
        </span>
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
        credentials: 'include',
        body: JSON.stringify({
          name,
          description,
          group_type: groupType,
          meeting_day: meetingDay || null,
          meeting_time: meetingTime || null,
          location: location || null,
          capacity: capacity ? parseInt(capacity) : null,
          is_open: isOpen
        })
      });

      if (res.ok) {
        toast.success('Group created!');
        onSuccess();
        // Reset form
        setName('');
        setDescription('');
        setGroupType('Small Group');
        setMeetingDay('');
        setMeetingTime('');
        setLocation('');
        setCapacity('');
        setIsOpen(true);
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
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/admin/groups/${group.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          name,
          description,
          group_type: groupType,
          meeting_day: meetingDay || null,
          meeting_time: meetingTime || null,
          location: location || null,
          capacity: capacity ? parseInt(capacity) : null
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

  useEffect(() => {
    if (open) {
      fetchMembers();
    }
  }, [open, group.id]);

  const fetchMembers = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/groups/${group.id}/members`, { credentials: 'include' });
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

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="view-members-modal">
        <DialogHeader>
          <DialogTitle>{group.name} - Members</DialogTitle>
          <DialogDescription>{members.length} member{members.length !== 1 ? 's' : ''}</DialogDescription>
        </DialogHeader>

        <div className="members-list">
          {loading ? (
            <div className="members-loading">Loading...</div>
          ) : members.length === 0 ? (
            <div className="members-empty">No members yet</div>
          ) : (
            members.map(member => (
              <div key={member.id} className="member-row">
                <div className="member-avatar">{member.name?.charAt(0) || '?'}</div>
                <div className="member-info">
                  <div className="member-name">{member.name}</div>
                  <div className="member-email">{member.email}</div>
                </div>
                <span className="member-role">{member.role}</span>
              </div>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
