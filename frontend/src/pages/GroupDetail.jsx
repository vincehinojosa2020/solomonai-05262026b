import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { ArrowLeft, Edit, UserPlus, Mail, MoreHorizontal, MapPin, Clock, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Progress } from '@/components/ui/progress';
import { API_URL, formatDate, getInitials } from '@/lib/utils';

export default function GroupDetail() {
  const { groupId } = useParams();
  const navigate = useNavigate();
  
  const [group, setGroup] = useState(null);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('roster');

  useEffect(() => {
    fetchGroupData();
  }, [groupId]);

  const fetchGroupData = async () => {
    setLoading(true);
    try {
      const [groupRes, membersRes] = await Promise.all([
        fetch(`${API_URL}/groups/${groupId}`),
        fetch(`${API_URL}/groups/${groupId}/members`),
      ]);

      const [groupData, membersData] = await Promise.all([
        groupRes.json(),
        membersRes.json(),
      ]);

      setGroup(groupData);
      setMembers(membersData);
    } catch (error) {
      console.error('Failed to fetch group data:', error);
    } finally {
      setLoading(false);
    }
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

        {/* About Tab */}
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
    </div>
  );
}
