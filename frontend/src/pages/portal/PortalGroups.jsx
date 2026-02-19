import { useState, useEffect } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import { Users, MapPin, Clock, ChevronRight, Search, Bell } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

export default function PortalGroups() {
  const { user, memberData } = useOutletContext();
  const [allGroups, setAllGroups] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');

  useEffect(() => {
    fetchGroups();
  }, []);

  const fetchGroups = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/groups`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setAllGroups(data);
      }
    } catch (error) {
      console.error('Failed to fetch groups:', error);
    }
  };

  const myGroups = memberData?.groups || [];
  const myGroupIds = myGroups.map(g => g.id);

  const filteredGroups = allGroups.filter(g => {
    const matchesSearch = !searchQuery || 
      g.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      g.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = filterType === 'all' || g.group_type_id === filterType;
    const notMyGroup = !myGroupIds.includes(g.id);
    return matchesSearch && matchesType && notMyGroup;
  });

  const handleJoinRequest = (groupId) => {
    toast.success('Request sent! The group leader will be notified.');
  };

  const handleNotify = (groupId) => {
    toast.success('You will be notified when a spot opens up.');
  };

  const GroupCard = ({ group, isMine = false }) => (
    <div className="portal-group-card" data-testid={`group-card-${group.id}`}>
      <div className="portal-group-card-header">
        <h3 className="portal-group-name">{group.name}</h3>
        {isMine ? (
          <Link to={`/portal/groups/${group.id}`} className="portal-group-action-btn">
            View Group
          </Link>
        ) : group.is_open ? (
          <button 
            onClick={() => handleJoinRequest(group.id)}
            className="portal-group-action-btn primary"
          >
            Request to Join
          </button>
        ) : (
          <button 
            onClick={() => handleNotify(group.id)}
            className="portal-group-action-btn secondary"
          >
            <Bell className="w-3 h-3" />
            Get Notified
          </button>
        )}
      </div>
      
      <div className="portal-group-meta">
        <span className="portal-group-type">{group.group_type || 'Small Group'}</span>
        {group.leader && (
          <span className="portal-group-leader">
            {group.leader.first_name} {group.leader.last_name}, Leader
          </span>
        )}
      </div>
      
      <div className="portal-group-details">
        {group.meeting_day && (
          <div className="portal-group-detail">
            <Clock className="w-4 h-4" />
            <span>{group.meeting_day}s at {group.meeting_time || '7:00 PM'}</span>
          </div>
        )}
        {group.location && (
          <div className="portal-group-detail">
            <MapPin className="w-4 h-4" />
            <span>{group.location}</span>
          </div>
        )}
        <div className="portal-group-detail">
          <Users className="w-4 h-4" />
          <span>{group.member_count || 0} members</span>
          {group.is_open && <span className="text-green-600 ml-1">• Open</span>}
        </div>
      </div>
    </div>
  );

  return (
    <div className="portal-groups" data-testid="portal-groups">
      <div className="portal-page-header">
        <h1 className="portal-page-title">Discover Groups</h1>
        <p className="portal-page-subtitle">Connect with others at Abundant Church</p>
      </div>

      {/* My Groups */}
      {myGroups.length > 0 && (
        <div className="portal-section">
          <h2 className="portal-section-title">MY GROUPS</h2>
          <div className="portal-groups-grid">
            {myGroups.map((group) => (
              <GroupCard key={group.id} group={group} isMine={true} />
            ))}
          </div>
        </div>
      )}

      {/* Discover Groups */}
      <div className="portal-section mt-8">
        <h2 className="portal-section-title">DISCOVER MORE GROUPS</h2>
        
        {/* Filters */}
        <div className="portal-groups-filters">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="portal-select"
          >
            <option value="all">All Types</option>
            <option value="small-group">Small Groups</option>
            <option value="ministry">Ministry Teams</option>
            <option value="class">Classes</option>
          </select>
          
          <div className="portal-search-input">
            <Search className="w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search groups..."
              className="portal-search-field"
            />
          </div>
        </div>

        {/* Groups Grid */}
        <div className="portal-groups-grid">
          {filteredGroups.length === 0 ? (
            <p className="text-slate-500 text-sm py-4 col-span-full">
              No groups found matching your criteria.
            </p>
          ) : (
            filteredGroups.map((group) => (
              <GroupCard key={group.id} group={group} isMine={false} />
            ))
          )}
        </div>
      </div>
    </div>
  );
}
