import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  ArrowLeft, Edit, UserPlus, DollarSign, Mail, MoreHorizontal,
  Phone, MapPin, Calendar, Users, TrendingUp, CheckCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Progress } from '@/components/ui/progress';
import PermissionEditor from '@/components/PermissionEditor';
import PersonCustomFields from '@/components/PersonCustomFields';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  API_URL, formatCurrency, formatDate, getInitials, getStatusColor 
} from '@/lib/utils';

const StatusBadge = ({ status }) => (
  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(status || 'visitor')}`}>
    {(status || 'visitor').charAt(0).toUpperCase() + (status || 'visitor').slice(1)}
  </span>
);

const InfoItem = ({ icon: Icon, label, value }) => (
  <div className="flex items-start gap-3 py-3 border-b border-slate-100 last:border-0">
    <Icon className="w-4 h-4 text-slate-400 mt-0.5" />
    <div>
      <p className="text-xs text-slate-400 mb-0.5">{label}</p>
      <p className="text-sm text-slate-700">{value || '—'}</p>
    </div>
  </div>
);

export default function PersonDetail() {
  const { personId } = useParams();
  const navigate = useNavigate();
  
  const [person, setPerson] = useState(null);
  const [giving, setGiving] = useState(null);
  const [attendance, setAttendance] = useState(null);
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchPersonData();
  }, [personId]);

  const fetchPersonData = async () => {
    setLoading(true);
    try {
      const [personRes, givingRes, attendanceRes, groupsRes] = await Promise.all([
        fetch(`${API_URL}/people/${personId}`),
        fetch(`${API_URL}/people/${personId}/giving`),
        fetch(`${API_URL}/people/${personId}/attendance`),
        fetch(`${API_URL}/people/${personId}/groups`),
      ]);

      const [personData, givingData, attendanceData, groupsData] = await Promise.all([
        personRes.json(),
        givingRes.json(),
        attendanceRes.json(),
        groupsRes.json(),
      ]);

      setPerson(personData);
      setGiving(givingData);
      setAttendance(attendanceData);
      setGroups(groupsData);
    } catch (error) {
      console.error('Failed to fetch person data:', error);
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

  if (!person) {
    return (
      <div className="text-center py-12">
        <p className="text-slate-400">Person not found</p>
        <Button variant="link" onClick={() => navigate('/people')}>
          Back to Members
        </Button>
      </div>
    );
  }

  const calculateAge = (dob) => {
    if (!dob) return null;
    const birthDate = new Date(dob);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const m = today.getMonth() - birthDate.getMonth();
    if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
      age--;
    }
    return age;
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="person-detail-page">
      {/* Back Button */}
      <button
        onClick={() => navigate('/people')}
        className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-700"
        data-testid="back-btn"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Members
      </button>

      {/* Profile Hero */}
      <div className="bg-[#1a1a2e] rounded-xl p-6 text-white" data-testid="profile-hero">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-5">
            <Avatar className="w-20 h-20 ring-4 ring-[#4f6ef7]/30">
              <AvatarImage src={person.photo_url} />
              <AvatarFallback className="text-xl bg-[#4f6ef7] text-white">
                {getInitials(person.first_name, person.last_name)}
              </AvatarFallback>
            </Avatar>
            <div>
              <h1 className="text-2xl font-bold">
                {person.first_name} {person.last_name}
              </h1>
              {person.preferred_name && person.preferred_name !== person.first_name && (
                <p className="text-white/60 text-sm">Goes by "{person.preferred_name}"</p>
              )}
              <div className="flex items-center gap-3 mt-2">
                <StatusBadge status={person.membership_status} />
                {person.membership_date && (
                  <span className="text-sm text-white/60">
                    Member since {formatDate(person.membership_date)}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button size="sm" variant="secondary" data-testid="edit-btn">
              <Edit className="w-4 h-4 mr-2" />
              Edit
            </Button>
            <Button size="sm" variant="secondary" data-testid="add-to-group-btn">
              <UserPlus className="w-4 h-4 mr-2" />
              Add to Group
            </Button>
            <Button size="sm" variant="secondary" data-testid="record-donation-btn">
              <DollarSign className="w-4 h-4 mr-2" />
              Record Donation
            </Button>
            <Button size="sm" variant="secondary" data-testid="send-message-btn">
              <Mail className="w-4 h-4 mr-2" />
              Send Message
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button size="sm" variant="secondary" data-testid="more-actions-btn">
                  <MoreHorizontal className="w-4 h-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem>Log Note</DropdownMenuItem>
                <DropdownMenuItem>Print Profile</DropdownMenuItem>
                <DropdownMenuItem>Merge Record</DropdownMenuItem>
                <DropdownMenuItem className="text-red-600">Archive</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-white border border-slate-200 p-1">
          <TabsTrigger value="overview" data-testid="tab-overview">Overview</TabsTrigger>
          <TabsTrigger value="giving" data-testid="tab-giving">Giving</TabsTrigger>
          <TabsTrigger value="attendance" data-testid="tab-attendance">Attendance</TabsTrigger>
          <TabsTrigger value="groups" data-testid="tab-groups">Groups</TabsTrigger>
          <TabsTrigger value="communications" data-testid="tab-communications">Communications</TabsTrigger>
          <TabsTrigger value="permissions" data-testid="tab-permissions">Permissions</TabsTrigger>
          <TabsTrigger value="notes" data-testid="tab-notes">Notes</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Personal Information */}
            <div className="bg-white border border-slate-200 rounded-lg p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-slate-900">Personal Information</h3>
                <Button variant="ghost" size="sm">Edit</Button>
              </div>
              <div className="space-y-0">
                <InfoItem icon={Mail} label="Email" value={person.email} />
                <InfoItem icon={Phone} label="Mobile" value={person.mobile_phone} />
                <InfoItem icon={Phone} label="Work" value={person.work_phone} />
                <InfoItem 
                  icon={Calendar} 
                  label="Birthday" 
                  value={person.date_of_birth ? `${formatDate(person.date_of_birth)} (Age ${calculateAge(person.date_of_birth)})` : null} 
                />
                <InfoItem icon={Users} label="Gender" value={person.gender} />
                <InfoItem icon={Users} label="Marital Status" value={person.marital_status} />
                <InfoItem icon={MapPin} label="Campus" value={person.campus} />
              </div>
            </div>

            {/* Engagement Score */}
            <div className="space-y-6">
              <div className="bg-white border border-slate-200 rounded-lg p-5">
                <h3 className="font-semibold text-slate-900 mb-4">Engagement Score</h3>
                <div className="flex items-center gap-4 mb-4">
                  <div className="text-4xl font-bold text-slate-900 font-data">
                    {person.engagement_score}
                  </div>
                  <div className="flex-1">
                    <Progress value={person.engagement_score} className="h-3" />
                  </div>
                </div>
                <p className="text-sm text-slate-500">
                  {person.engagement_score >= 70 ? 'Highly Engaged' : 
                   person.engagement_score >= 40 ? 'Moderately Engaged' : 'At Risk'}
                </p>
              </div>

              {/* Quick Stats */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-white border border-slate-200 rounded-lg p-4">
                  <p className="text-xs text-slate-400 mb-1">YTD Giving</p>
                  <p className="text-2xl font-bold font-data text-slate-900">
                    {formatCurrency(person.ytd_giving || 0)}
                  </p>
                </div>
                <div className="bg-white border border-slate-200 rounded-lg p-4">
                  <p className="text-xs text-slate-400 mb-1">Lifetime Giving</p>
                  <p className="text-2xl font-bold font-data text-slate-900">
                    {formatCurrency(person.lifetime_giving || 0)}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Custom Fields */}
          <PersonCustomFields personId={personId} />
        </TabsContent>

        {/* Giving Tab */}
        <TabsContent value="giving" className="space-y-6">
          {/* Stats Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-1">YTD Total</p>
              <p className="text-2xl font-bold font-data text-slate-900">
                {formatCurrency(giving?.stats?.ytd_total || 0)}
              </p>
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-1">Lifetime Total</p>
              <p className="text-2xl font-bold font-data text-slate-900">
                {formatCurrency(giving?.stats?.lifetime_total || 0)}
              </p>
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-1">Total Gifts</p>
              <p className="text-2xl font-bold font-data text-slate-900">
                {giving?.stats?.total_gifts || 0}
              </p>
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-1">Avg Gift</p>
              <p className="text-2xl font-bold font-data text-slate-900">
                {formatCurrency(giving?.stats?.avg_gift || 0)}
              </p>
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-1">Last Gift</p>
              <p className="text-lg font-semibold text-slate-900">
                {giving?.stats?.last_gift ? formatDate(giving.stats.last_gift.donation_date) : '—'}
              </p>
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-1">Recurring</p>
              <p className="text-lg font-semibold text-slate-900">
                {giving?.recurring?.filter(r => r.is_active).length || 0} active
              </p>
            </div>
          </div>

          {/* Donations Table */}
          <div className="bg-white border border-slate-200 rounded-lg">
            <div className="p-4 border-b border-slate-200 flex items-center justify-between">
              <h3 className="font-semibold text-slate-900">Donation History</h3>
              <Button variant="outline" size="sm">Download Statement</Button>
            </div>
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Fund</th>
                    <th className="text-right">Amount</th>
                    <th>Method</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {!giving?.donations?.length ? (
                    <tr>
                      <td colSpan={5} className="text-center py-8 text-slate-400">
                        No donations recorded
                      </td>
                    </tr>
                  ) : (
                    giving.donations.slice(0, 20).map((donation) => (
                      <tr key={donation.id}>
                        <td>{formatDate(donation.donation_date)}</td>
                        <td>{donation.fund_name || 'General Fund'}</td>
                        <td className="text-right font-data">{formatCurrency(donation.amount)}</td>
                        <td className="capitalize">{donation.payment_method}</td>
                        <td className="text-slate-400">{donation.notes || '—'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </TabsContent>

        {/* Attendance Tab */}
        <TabsContent value="attendance" className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-1">Total Attended</p>
              <p className="text-2xl font-bold font-data text-slate-900">
                {attendance?.stats?.total_attended || 0}
              </p>
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-1">This Year</p>
              <p className="text-2xl font-bold font-data text-slate-900">
                {attendance?.stats?.ytd_attended || 0}
              </p>
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-1">Attendance Rate</p>
              <p className="text-2xl font-bold font-data text-slate-900">
                {attendance?.stats?.attendance_rate || 0}%
              </p>
            </div>
            <div className="bg-white border border-slate-200 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-1">Current Streak</p>
              <p className="text-2xl font-bold font-data text-slate-900">
                {attendance?.stats?.current_streak || 0} weeks
              </p>
            </div>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg">
            <div className="p-4 border-b border-slate-200">
              <h3 className="font-semibold text-slate-900">Attendance History</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Service</th>
                    <th>Check-in Time</th>
                  </tr>
                </thead>
                <tbody>
                  {!attendance?.records?.length ? (
                    <tr>
                      <td colSpan={3} className="text-center py-8 text-slate-400">
                        No attendance records
                      </td>
                    </tr>
                  ) : (
                    attendance.records.slice(0, 20).map((record, idx) => (
                      <tr key={idx}>
                        <td>{formatDate(record.date)}</td>
                        <td>{record.service_name || 'Sunday Service'}</td>
                        <td className="font-data text-sm">
                          {record.check_in_time ? new Date(record.check_in_time).toLocaleTimeString() : '—'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </TabsContent>

        {/* Groups Tab */}
        <TabsContent value="groups" className="space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-slate-900">Group Memberships</h3>
            <Button size="sm" data-testid="add-to-group-btn-tab">
              <UserPlus className="w-4 h-4 mr-2" />
              Add to Group
            </Button>
          </div>

          {!groups?.length ? (
            <div className="bg-white border border-slate-200 rounded-lg p-8 text-center">
              <p className="text-slate-400">Not a member of any groups</p>
              <Button variant="link" className="mt-2">Add to a group →</Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {groups.map((group) => (
                <Link
                  key={group.id}
                  to={`/groups/${group.id}`}
                  className="bg-white border border-slate-200 rounded-lg p-4 hover:border-blue-200 transition-colors"
                >
                  <div className="flex items-start gap-3">
                    <div 
                      className="w-3 h-3 rounded-full mt-1.5"
                      style={{ backgroundColor: group.type_color || '#4f6ef7' }}
                    ></div>
                    <div className="flex-1">
                      <h4 className="font-medium text-slate-900">{group.name}</h4>
                      <p className="text-sm text-slate-500">{group.type}</p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
                        <span>Role: {group.role}</span>
                        <span>Joined: {formatDate(group.joined_at)}</span>
                      </div>
                      {group.meeting_schedule && (
                        <p className="text-xs text-slate-400 mt-1">{group.meeting_schedule}</p>
                      )}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Communications Tab */}
        <TabsContent value="communications">
          <div className="bg-white border border-slate-200 rounded-lg p-8 text-center">
            <Mail className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <h3 className="font-semibold text-slate-900 mb-2">Email History</h3>
            <p className="text-slate-400 text-sm mb-4">View all emails sent to this person</p>
            <Button variant="outline" size="sm">Send Message</Button>
          </div>
        </TabsContent>

        {/* Permissions Tab */}
        <TabsContent value="permissions">
          <div className="bg-white border border-slate-200 rounded-xl p-6">
            <PermissionEditor userId={personId} userName={person?.name} />
          </div>
        </TabsContent>

        {/* Notes Tab */}
        <TabsContent value="notes">
          <div className="bg-white border border-slate-200 rounded-lg p-8 text-center">
            <CheckCircle className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <h3 className="font-semibold text-slate-900 mb-2">Staff Notes</h3>
            <p className="text-slate-400 text-sm mb-4">Add notes about this person for staff reference</p>
            <Button variant="outline" size="sm">Add Note</Button>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
