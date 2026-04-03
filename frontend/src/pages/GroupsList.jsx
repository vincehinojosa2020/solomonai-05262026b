import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Search, Filter, Users, MapPin, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { API_URL } from '@/lib/utils';
import { HelpTooltip } from '@/components/HelpTooltip';

const GroupCard = ({ group }) => {
  const capacityPercent = group.capacity 
    ? Math.round((group.member_count / group.capacity) * 100)
    : 0;

  return (
    <Link
      to={`/groups/${group.id}`}
      className="bg-white border border-slate-200 rounded-lg overflow-hidden hover:border-blue-200 hover:shadow-sm transition-all"
      data-testid={`group-card-${group.id}`}
    >
      {/* Color Band */}
      <div 
        className="h-2"
        style={{ backgroundColor: group.type_color || '#4f6ef7' }}
      ></div>

      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="font-semibold text-slate-900">{group.name}</h3>
            {group.type_name && (
              <span 
                className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium mt-1"
                style={{ 
                  backgroundColor: `${group.type_color}15`,
                  color: group.type_color 
                }}
              >
                {group.type_name}
              </span>
            )}
          </div>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
            group.is_open 
              ? 'bg-emerald-50 text-emerald-700' 
              : 'bg-slate-100 text-slate-500'
          }`}>
            {group.is_open ? 'Open' : 'Closed'}
          </span>
        </div>

        {/* Leader */}
        {group.leader_name && (
          <div className="flex items-center gap-2 mb-3">
            {group.leader_photo ? (
              <img src={group.leader_photo} alt="" className="w-6 h-6 rounded-full" />
            ) : (
              <div className="w-6 h-6 rounded-full bg-slate-200 flex items-center justify-center">
                <Users className="w-3 h-3 text-slate-400" />
              </div>
            )}
            <span className="text-sm text-slate-600">{group.leader_name}</span>
          </div>
        )}

        {/* Capacity */}
        {group.capacity && (
          <div className="mb-3">
            <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
              <span>{group.member_count} / {group.capacity} members</span>
              <span>{capacityPercent}%</span>
            </div>
            <Progress value={capacityPercent} className="h-1.5" />
          </div>
        )}

        {/* Schedule */}
        {group.meeting_schedule && (
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <Clock className="w-3 h-3" />
            <span>{group.meeting_day} {group.meeting_time && `at ${group.meeting_time}`}</span>
          </div>
        )}
        
        {group.location && (
          <div className="flex items-center gap-2 text-xs text-slate-400 mt-1">
            <MapPin className="w-3 h-3" />
            <span>{group.location}</span>
          </div>
        )}
      </div>
    </Link>
  );
};

export default function GroupsList() {
  const [groups, setGroups] = useState([]);
  const [groupTypes, setGroupTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [total, setTotal] = useState(0);

  useEffect(() => {
    fetchGroups();
    fetchGroupTypes();
  }, [typeFilter]);

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchGroups();
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const fetchGroups = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (typeFilter !== 'all') params.append('group_type', typeFilter);

      const response = await fetch(`${API_URL}/groups?${params}`);
      const data = await response.json();
      setGroups(data.data);
      setTotal(data.total);
    } catch (error) {
      console.error('Failed to fetch groups:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchGroupTypes = async () => {
    try {
      const response = await fetch(`${API_URL}/group-types`);
      const data = await response.json();
      setGroupTypes(data);
    } catch (error) {
      console.error('Failed to fetch group types:', error);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="groups-list-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Groups</h1>
          <p className="page-subtitle">Manage small groups, ministry teams, and classes</p>
        </div>
        <Button className="h-9 btn-primary" data-testid="create-group-btn">
          <Plus className="w-4 h-4 mr-2" />
          Create Group
        </Button>
        <HelpTooltip featureKey="groups" />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Total Groups</p>
          <p className="text-2xl font-bold font-data text-slate-900">{total}</p>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Open Groups</p>
          <p className="text-2xl font-bold font-data text-slate-900">
            {groups.filter(g => g.is_open).length}
          </p>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Total Members</p>
          <p className="text-2xl font-bold font-data text-slate-900">
            {groups.reduce((acc, g) => acc + (g.member_count || 0), 0)}
          </p>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <p className="text-xs text-slate-400 mb-1">Group Types</p>
          <p className="text-2xl font-bold font-data text-slate-900">{groupTypes.length}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            placeholder="Search groups..."
            className="pl-9 h-9"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            data-testid="search-groups-input"
          />
        </div>
        <Select value={typeFilter} onValueChange={setTypeFilter}>
          <SelectTrigger className="w-48 h-9" data-testid="type-filter">
            <SelectValue placeholder="All Types" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {groupTypes.map((type) => (
              <SelectItem key={type.id} value={type.id}>{type.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Groups Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-48 bg-slate-100 rounded-lg animate-pulse"></div>
          ))}
        </div>
      ) : groups.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-lg p-12 text-center">
          <Users className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="font-semibold text-slate-900 mb-2">No groups found</h3>
          <p className="text-slate-400 text-sm mb-4">
            {search ? 'Try a different search term' : 'Create your first group to get started'}
          </p>
          <Button className="btn-primary">Create Group</Button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {groups.map((group) => (
            <GroupCard key={group.id} group={group} />
          ))}
        </div>
      )}
    </div>
  );
}
