import { useState, useEffect } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  HandHeart, Plus, Users, Calendar, Shield, Search,
  ChevronDown, ChevronUp, UserPlus, Trash2, CalendarOff
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
} from '@/components/ui/dialog';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

export default function VolunteerPage() {
  const { tenant } = useOutletContext();
  const [activeTab, setActiveTab] = useState('teams');
  const [teams, setTeams] = useState([]);
  const [schedule, setSchedule] = useState([]);
  const [scheduleRoles, setScheduleRoles] = useState([]);
  const [blockouts, setBlockouts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedTeam, setExpandedTeam] = useState(null);
  const [showCreateTeam, setShowCreateTeam] = useState(false);
  const [showCreateSchedule, setShowCreateSchedule] = useState(false);
  const [showCreateBlockout, setShowCreateBlockout] = useState(false);
  const [teamForm, setTeamForm] = useState({ team_name: '', ministry: '', description: '' });
  const [scheduleForm, setScheduleForm] = useState({ date: '', role: '', user_name: '', user_id: '' });
  const [blockoutForm, setBlockoutForm] = useState({ user_name: '', start_date: '', end_date: '', reason: '' });

  const token = sessionStorage.getItem('session_token');
  const authHeaders = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  useEffect(() => { fetchTeams(); fetchSchedule(); fetchBlockouts(); }, []);

  const fetchTeams = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/volunteers`, { headers: authHeaders });
      if (res.ok) {
        const data = await res.json();
        setTeams(data.teams || []);
      }
    } catch (err) { console.error('Failed to fetch teams:', err); }
    finally { setLoading(false); }
  };

  const fetchSchedule = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/volunteers/schedule`, { headers: authHeaders });
      if (res.ok) {
        const data = await res.json();
        setSchedule(data.schedule || []);
        setScheduleRoles(data.roles || []);
      }
    } catch (err) { console.error('Failed to fetch schedule:', err); }
  };

  const createTeam = async () => {
    if (!teamForm.team_name) { toast.error('Team name is required'); return; }
    try {
      const res = await fetch(`${API_URL}/admin/volunteers/teams`, {
        method: 'POST', headers: authHeaders,
        body: JSON.stringify(teamForm),
      });
      if (res.ok) {
        toast.success('Team created');
        setShowCreateTeam(false);
        setTeamForm({ team_name: '', ministry: '', description: '' });
        fetchTeams();
      }
    } catch (err) { toast.error('Failed to create team'); }
  };

  const createScheduleEntry = async () => {
    if (!scheduleForm.date || !scheduleForm.role) { toast.error('Date and role are required'); return; }
    try {
      const res = await fetch(`${API_URL}/admin/volunteers/schedule`, {
        method: 'POST', headers: authHeaders,
        body: JSON.stringify(scheduleForm),
      });
      if (res.ok) {
        toast.success('Schedule entry created');
        setShowCreateSchedule(false);
        setScheduleForm({ date: '', role: '', user_name: '', user_id: '' });
        fetchSchedule();
      }
    } catch (err) { toast.error('Failed to create schedule entry'); }
  };

  const fetchBlockouts = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/volunteers/blockout-dates`, { headers: authHeaders });
      if (res.ok) {
        const data = await res.json();
        setBlockouts(data.blockout_dates || []);
      }
    } catch (err) { console.error('Failed to fetch blockouts:', err); }
  };

  const createBlockout = async () => {
    if (!blockoutForm.start_date || !blockoutForm.user_name) { toast.error('Volunteer name and start date are required'); return; }
    try {
      const res = await fetch(`${API_URL}/admin/volunteers/blockout-dates`, {
        method: 'POST', headers: authHeaders,
        body: JSON.stringify(blockoutForm),
      });
      if (res.ok) {
        toast.success('Blockout date added');
        setShowCreateBlockout(false);
        setBlockoutForm({ user_name: '', start_date: '', end_date: '', reason: '' });
        fetchBlockouts();
      }
    } catch (err) { toast.error('Failed to add blockout date'); }
  };

  const deleteBlockout = async (blockoutId) => {
    try {
      await fetch(`${API_URL}/admin/volunteers/blockout-dates/${blockoutId}`, {
        method: 'DELETE', headers: authHeaders
      });
      toast.success('Blockout date removed');
      fetchBlockouts();
    } catch (err) { toast.error('Failed to remove blockout date'); }
  };

  const getInitials = (name) => {
    if (!name) return '?';
    return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
  };

  const formatDate = (d) => {
    if (!d) return '';
    return new Date(d + 'T00:00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-6" data-testid="volunteers-loading">
        <div className="h-8 bg-slate-200 rounded w-64" />
        <div className="h-64 bg-slate-200 rounded-lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="volunteers-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Volunteers</h1>
          <p className="page-subtitle">Manage volunteer teams and scheduling for services and events</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-white border border-slate-200 p-1">
          <TabsTrigger value="teams" data-testid="tab-teams">
            <Users className="w-4 h-4 mr-2" />
            Teams
          </TabsTrigger>
          <TabsTrigger value="schedule" data-testid="tab-schedule">
            <Calendar className="w-4 h-4 mr-2" />
            Schedule
          </TabsTrigger>
          <TabsTrigger value="blockouts" data-testid="tab-blockouts">
            <CalendarOff className="w-4 h-4 mr-2" />
            Blockout Dates
          </TabsTrigger>
        </TabsList>

        {/* Teams Tab */}
        <TabsContent value="teams" className="space-y-4">
          <div className="flex items-center justify-end">
            <Button className="btn-primary" onClick={() => setShowCreateTeam(true)} data-testid="create-team-btn">
              <Plus className="w-4 h-4 mr-2" />
              New Team
            </Button>
          </div>

          {teams.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-xl p-12 text-center" data-testid="teams-empty">
              <HandHeart className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 mb-1">No volunteer teams yet</h3>
              <p className="text-sm text-slate-500 mb-4">Create teams like Worship, Greeters, Kids Ministry, and more.</p>
              <Button className="btn-primary" onClick={() => setShowCreateTeam(true)} data-testid="teams-empty-create-btn">
                <Plus className="w-4 h-4 mr-2" />Create Team
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {teams.map((team) => {
                const isExpanded = expandedTeam === team.id;
                const memberCount = (team.members || []).length;
                return (
                  <div
                    key={team.id}
                    className="bg-white border border-slate-200 rounded-xl overflow-hidden hover:shadow-sm transition-shadow"
                    data-testid={`team-card-${team.id}`}
                  >
                    <button
                      className="w-full flex items-center justify-between p-4 text-left"
                      onClick={() => setExpandedTeam(isExpanded ? null : team.id)}
                      data-testid={`team-toggle-${team.id}`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
                          <HandHeart className="w-5 h-5 text-purple-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-slate-900">{team.team_name}</h3>
                          <div className="flex items-center gap-3 text-sm text-slate-500 mt-0.5">
                            {team.ministry && <span>{team.ministry}</span>}
                            <span className="flex items-center gap-1">
                              <Users className="w-3.5 h-3.5" />{memberCount} volunteer{memberCount !== 1 ? 's' : ''}
                            </span>
                          </div>
                        </div>
                      </div>
                      {isExpanded ? <ChevronUp className="w-5 h-5 text-slate-400" /> : <ChevronDown className="w-5 h-5 text-slate-400" />}
                    </button>

                    {isExpanded && (
                      <div className="border-t border-slate-100 p-4 space-y-3" data-testid={`team-details-${team.id}`}>
                        {team.description && (
                          <p className="text-sm text-slate-600">{team.description}</p>
                        )}
                        <div>
                          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Team Members</p>
                          {memberCount === 0 ? (
                            <p className="text-sm text-slate-400">No volunteers assigned yet.</p>
                          ) : (
                            <div className="space-y-2">
                              {(team.members || []).map((m, idx) => (
                                <div key={m.id || idx} className="flex items-center gap-2 p-2 bg-slate-50 rounded-lg" data-testid={`team-member-${m.id || idx}`}>
                                  <Avatar className="w-7 h-7">
                                    <AvatarImage src={m.user?.picture} />
                                    <AvatarFallback className="bg-purple-100 text-purple-700 text-xs">
                                      {getInitials(m.user?.name)}
                                    </AvatarFallback>
                                  </Avatar>
                                  <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium text-slate-700 truncate">{m.user?.name || m.user_id}</p>
                                    <p className="text-xs text-slate-400">{m.role_title || 'Volunteer'}</p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </TabsContent>

        {/* Schedule Tab */}
        <TabsContent value="schedule" className="space-y-4">
          <div className="flex items-center justify-end">
            <Button className="btn-primary" onClick={() => setShowCreateSchedule(true)} data-testid="create-schedule-btn">
              <Plus className="w-4 h-4 mr-2" />
              Add Schedule Entry
            </Button>
          </div>

          {schedule.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-xl p-12 text-center" data-testid="schedule-empty">
              <Calendar className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 mb-1">No schedule entries</h3>
              <p className="text-sm text-slate-500 mb-4">Add volunteer assignments for upcoming services.</p>
              <Button className="btn-primary" onClick={() => setShowCreateSchedule(true)} data-testid="schedule-empty-create-btn">
                <Plus className="w-4 h-4 mr-2" />Add Entry
              </Button>
            </div>
          ) : (
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
              <table className="data-table w-full" data-testid="schedule-table">
                <thead>
                  <tr>
                    <th className="text-left p-3 text-xs font-semibold text-slate-500 uppercase">Date</th>
                    <th className="text-left p-3 text-xs font-semibold text-slate-500 uppercase">Role</th>
                    <th className="text-left p-3 text-xs font-semibold text-slate-500 uppercase">Volunteer</th>
                    <th className="text-left p-3 text-xs font-semibold text-slate-500 uppercase">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {schedule.map((entry, idx) => (
                    <tr key={entry.id || idx} className="border-t border-slate-100" data-testid={`schedule-row-${idx}`}>
                      <td className="p-3 text-sm text-slate-700">{formatDate(entry.date)}</td>
                      <td className="p-3 text-sm text-slate-700">{entry.role}</td>
                      <td className="p-3 text-sm text-slate-700">{entry.user_name || entry.user_id || '-'}</td>
                      <td className="p-3">
                        <Badge className={entry.status === 'confirmed' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'}>
                          {entry.status || 'pending'}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </TabsContent>

        {/* Blockout Dates Tab */}
        <TabsContent value="blockouts" className="space-y-4">
          <div className="flex items-center justify-end">
            <Button className="btn-primary" onClick={() => setShowCreateBlockout(true)} data-testid="create-blockout-btn">
              <Plus className="w-4 h-4 mr-2" />
              Add Blockout Date
            </Button>
          </div>

          {blockouts.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-xl p-12 text-center" data-testid="blockouts-empty">
              <CalendarOff className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 mb-1">No blockout dates</h3>
              <p className="text-sm text-slate-500 mb-4">Add dates when volunteers are unavailable to prevent scheduling conflicts.</p>
              <Button className="btn-primary" onClick={() => setShowCreateBlockout(true)} data-testid="blockouts-empty-create-btn">
                <Plus className="w-4 h-4 mr-2" />Add Blockout Date
              </Button>
            </div>
          ) : (
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
              <table className="data-table w-full" data-testid="blockouts-table">
                <thead>
                  <tr>
                    <th className="text-left p-3 text-xs font-semibold text-slate-500 uppercase">Volunteer</th>
                    <th className="text-left p-3 text-xs font-semibold text-slate-500 uppercase">Start Date</th>
                    <th className="text-left p-3 text-xs font-semibold text-slate-500 uppercase">End Date</th>
                    <th className="text-left p-3 text-xs font-semibold text-slate-500 uppercase">Reason</th>
                    <th className="text-right p-3 text-xs font-semibold text-slate-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {blockouts.map((b, idx) => (
                    <tr key={b.id || idx} className="border-t border-slate-100" data-testid={`blockout-row-${idx}`}>
                      <td className="p-3 text-sm font-medium text-slate-700">{b.user_name || '-'}</td>
                      <td className="p-3 text-sm text-slate-700">{formatDate(b.start_date)}</td>
                      <td className="p-3 text-sm text-slate-700">{formatDate(b.end_date)}</td>
                      <td className="p-3 text-sm text-slate-500">{b.reason || '-'}</td>
                      <td className="p-3 text-right">
                        <Button size="sm" variant="outline" className="text-red-500 hover:text-red-700"
                          onClick={() => deleteBlockout(b.id)} data-testid={`delete-blockout-${idx}`}>
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Create Team Dialog */}
      <Dialog open={showCreateTeam} onOpenChange={setShowCreateTeam}>
        <DialogContent data-testid="create-team-dialog">
          <DialogHeader><DialogTitle>New Volunteer Team</DialogTitle></DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label>Team Name</Label>
              <Input
                placeholder="e.g. Worship Team"
                value={teamForm.team_name}
                onChange={(e) => setTeamForm({ ...teamForm, team_name: e.target.value })}
                data-testid="team-name-input"
              />
            </div>
            <div>
              <Label>Ministry</Label>
              <Input
                placeholder="e.g. Worship, Kids, Hospitality"
                value={teamForm.ministry}
                onChange={(e) => setTeamForm({ ...teamForm, ministry: e.target.value })}
                data-testid="team-ministry-input"
              />
            </div>
            <div>
              <Label>Description</Label>
              <Input
                placeholder="Brief description of the team"
                value={teamForm.description}
                onChange={(e) => setTeamForm({ ...teamForm, description: e.target.value })}
                data-testid="team-description-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateTeam(false)}>Cancel</Button>
            <Button onClick={createTeam} data-testid="save-team-btn">Create Team</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Schedule Entry Dialog */}
      <Dialog open={showCreateSchedule} onOpenChange={setShowCreateSchedule}>
        <DialogContent data-testid="create-schedule-dialog">
          <DialogHeader><DialogTitle>Add Schedule Entry</DialogTitle></DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label>Date</Label>
              <Input
                type="date"
                value={scheduleForm.date}
                onChange={(e) => setScheduleForm({ ...scheduleForm, date: e.target.value })}
                data-testid="schedule-date-input"
              />
            </div>
            <div>
              <Label>Role</Label>
              <Input
                placeholder="e.g. Sound Tech, Greeter, Usher"
                value={scheduleForm.role}
                onChange={(e) => setScheduleForm({ ...scheduleForm, role: e.target.value })}
                data-testid="schedule-role-input"
              />
            </div>
            <div>
              <Label>Volunteer Name</Label>
              <Input
                placeholder="Name of the volunteer"
                value={scheduleForm.user_name}
                onChange={(e) => setScheduleForm({ ...scheduleForm, user_name: e.target.value })}
                data-testid="schedule-volunteer-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateSchedule(false)}>Cancel</Button>
            <Button onClick={createScheduleEntry} data-testid="save-schedule-btn">Add Entry</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Blockout Date Dialog */}
      <Dialog open={showCreateBlockout} onOpenChange={setShowCreateBlockout}>
        <DialogContent data-testid="create-blockout-dialog">
          <DialogHeader><DialogTitle>Add Blockout Date</DialogTitle></DialogHeader>
          <div className="space-y-4 py-2">
            <div>
              <Label>Volunteer Name</Label>
              <Input
                placeholder="Name of the volunteer"
                value={blockoutForm.user_name}
                onChange={(e) => setBlockoutForm({ ...blockoutForm, user_name: e.target.value })}
                data-testid="blockout-name-input"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label>Start Date</Label>
                <Input
                  type="date"
                  value={blockoutForm.start_date}
                  onChange={(e) => setBlockoutForm({ ...blockoutForm, start_date: e.target.value })}
                  data-testid="blockout-start-input"
                />
              </div>
              <div>
                <Label>End Date</Label>
                <Input
                  type="date"
                  value={blockoutForm.end_date}
                  onChange={(e) => setBlockoutForm({ ...blockoutForm, end_date: e.target.value })}
                  data-testid="blockout-end-input"
                />
              </div>
            </div>
            <div>
              <Label>Reason (optional)</Label>
              <Input
                placeholder="e.g. Vacation, Family event"
                value={blockoutForm.reason}
                onChange={(e) => setBlockoutForm({ ...blockoutForm, reason: e.target.value })}
                data-testid="blockout-reason-input"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateBlockout(false)}>Cancel</Button>
            <Button onClick={createBlockout} data-testid="save-blockout-btn">Add Blockout</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
