import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Users, AlertTriangle, BarChart3, Phone, Mail,
  Coffee, MessageSquare, Check, Calendar, TrendingUp, RefreshCw
} from 'lucide-react';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend
} from 'chart.js';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const OUTREACH_TYPES = [
  { id: 'call', label: 'Phone Call', icon: Phone, color: '#3b82f6' },
  { id: 'email', label: 'Email', icon: Mail, color: '#8b5cf6' },
  { id: 'coffee_code', label: 'Coffee Invite', icon: Coffee, color: '#f59e0b' },
  { id: 'sms', label: 'Text Message', icon: MessageSquare, color: '#10b981' },
];

export default function GroupLeaderDashboard() {
  const { groupId } = useParams();
  const navigate = useNavigate();
  const [group, setGroup] = useState(null);
  const [attendance, setAttendance] = useState([]);
  const [atRisk, setAtRisk] = useState([]);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [groupRes, attendRes, riskRes, membersRes] = await Promise.all([
        fetch(`${API_URL}/admin/groups`, { credentials: 'include' }),
        fetch(`${API_URL}/admin/groups/${groupId}/attendance?limit=8`, { credentials: 'include' }),
        fetch(`${API_URL}/admin/groups/${groupId}/at-risk`, { credentials: 'include' }),
        fetch(`${API_URL}/admin/groups/${groupId}/members`, { credentials: 'include' }),
      ]);

      if (groupRes.ok) {
        const data = await groupRes.json();
        const g = (data.groups || []).find(g => g.id === groupId);
        setGroup(g || null);
      }
      if (attendRes.ok) {
        const data = await attendRes.json();
        setAttendance((data.sessions || []).reverse());
      }
      if (riskRes.ok) {
        const data = await riskRes.json();
        setAtRisk(data.at_risk_members || []);
      }
      if (membersRes.ok) {
        const data = await membersRes.json();
        setMembers(data.members || []);
      }
    } catch (e) {
      console.error('Failed to load dashboard:', e);
    } finally {
      setLoading(false);
    }
  }, [groupId]);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  const handleOutreach = async (personId, type) => {
    try {
      const res = await fetch(`${API_URL}/admin/groups/${groupId}/outreach`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ person_id: personId, type, notes: `${type} outreach logged` }),
      });
      if (res.ok) {
        toast.success('Outreach logged successfully');
      } else {
        toast.error('Failed to log outreach');
      }
    } catch {
      toast.error('Network error');
    }
  };

  // Chart data
  const chartData = {
    labels: attendance.map(s => {
      const d = new Date(s.session_date);
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }),
    datasets: [{
      label: 'Attendance',
      data: attendance.map(s => (s.attendees || []).length),
      backgroundColor: '#3b82f6',
      borderRadius: 6,
      barThickness: 28,
    }],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#1e293b',
        titleFont: { size: 12, weight: '600' },
        bodyFont: { size: 12 },
        padding: 10,
        cornerRadius: 8,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: { precision: 0, font: { size: 11 }, color: '#94a3b8' },
        grid: { color: '#f1f5f9' },
      },
      x: {
        ticks: { font: { size: 11 }, color: '#94a3b8' },
        grid: { display: false },
      },
    },
  };

  const avgAttendance = attendance.length
    ? Math.round(attendance.reduce((s, a) => s + (a.attendees || []).length, 0) / attendance.length)
    : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-5 h-5 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="leader-dashboard" data-testid="group-leader-dashboard" style={{ padding: '24px', maxWidth: '1100px', margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '24px' }}>
        <button
          data-testid="leader-dash-back"
          onClick={() => navigate('/admin/groups')}
          style={{ background: '#f1f5f9', border: 'none', borderRadius: '8px', padding: '8px', cursor: 'pointer', display: 'flex' }}
        >
          <ArrowLeft className="w-5 h-5" style={{ color: '#64748b' }} />
        </button>
        <div style={{ flex: 1 }}>
          <h1 data-testid="leader-dash-title" style={{ fontSize: '20px', fontWeight: '700', margin: 0, color: '#0f172a' }}>{group?.name || 'Group'} Dashboard</h1>
          <p style={{ fontSize: '13px', color: '#64748b', margin: '2px 0 0' }}>Leader insights & attendance</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchAll} data-testid="leader-dash-refresh">
          <RefreshCw className="w-4 h-4 mr-1" /> Refresh
        </Button>
      </div>

      {/* Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        <StatCard icon={Users} label="Total Members" value={members.length} color="#3b82f6" />
        <StatCard icon={TrendingUp} label="Avg Attendance" value={avgAttendance} color="#10b981" />
        <StatCard icon={Calendar} label="Sessions Tracked" value={attendance.length} color="#8b5cf6" />
        <StatCard icon={AlertTriangle} label="At-Risk Members" value={atRisk.length} color={atRisk.length > 0 ? '#ef4444' : '#10b981'} />
      </div>

      {/* Chart + At-Risk Side by Side */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
        {/* Attendance Chart */}
        <div
          data-testid="attendance-chart"
          style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '20px' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <BarChart3 className="w-4 h-4" style={{ color: '#3b82f6' }} />
            <h3 style={{ fontSize: '14px', fontWeight: '600', margin: 0, color: '#0f172a' }}>Attendance Trend</h3>
          </div>
          {attendance.length > 0 ? (
            <div style={{ height: '220px' }}>
              <Bar data={chartData} options={chartOptions} />
            </div>
          ) : (
            <div style={{ height: '220px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8', fontSize: '13px' }}>
              No attendance recorded yet
            </div>
          )}
        </div>

        {/* At-Risk Members */}
        <div
          data-testid="at-risk-panel"
          style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '20px' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <AlertTriangle className="w-4 h-4" style={{ color: '#ef4444' }} />
            <h3 style={{ fontSize: '14px', fontWeight: '600', margin: 0, color: '#0f172a' }}>At-Risk Members</h3>
            <span style={{ marginLeft: 'auto', fontSize: '11px', background: atRisk.length ? '#fef2f2' : '#f0fdf4', color: atRisk.length ? '#ef4444' : '#22c55e', padding: '2px 8px', borderRadius: '99px', fontWeight: '600' }}>
              {atRisk.length} member{atRisk.length !== 1 ? 's' : ''}
            </span>
          </div>

          <div style={{ maxHeight: '260px', overflowY: 'auto' }}>
            {atRisk.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '30px 0', color: '#94a3b8', fontSize: '13px' }}>
                <Check className="w-6 h-6 mx-auto mb-2" style={{ color: '#22c55e' }} />
                No at-risk members — great engagement!
              </div>
            ) : (
              atRisk.map(member => (
                <div
                  key={member.person_id}
                  data-testid={`at-risk-member-${member.person_id}`}
                  style={{
                    display: 'flex', alignItems: 'center', gap: '10px',
                    padding: '10px', borderRadius: '8px', marginBottom: '8px',
                    background: '#fef2f2', border: '1px solid #fecaca',
                  }}
                >
                  <div style={{
                    width: '34px', height: '34px', borderRadius: '50%',
                    background: '#ef4444', color: '#fff', display: 'flex',
                    alignItems: 'center', justifyContent: 'center',
                    fontSize: '13px', fontWeight: '700', flexShrink: 0,
                  }}>
                    {member.name?.charAt(0) || '?'}
                  </div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: '#0f172a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {member.name}
                    </div>
                    <div style={{ fontSize: '11px', color: '#ef4444', fontWeight: '500' }}>
                      Missed {member.sessions_missed} sessions
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '4px' }}>
                    {OUTREACH_TYPES.map(t => (
                      <button
                        key={t.id}
                        data-testid={`outreach-${t.id}-${member.person_id}`}
                        onClick={() => handleOutreach(member.person_id, t.id)}
                        title={t.label}
                        style={{
                          width: '28px', height: '28px', borderRadius: '6px',
                          background: '#fff', border: '1px solid #e5e7eb',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          cursor: 'pointer', color: t.color,
                        }}
                      >
                        <t.icon className="w-3.5 h-3.5" />
                      </button>
                    ))}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Members List */}
      <div style={{ background: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0', padding: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <Users className="w-4 h-4" style={{ color: '#3b82f6' }} />
          <h3 style={{ fontSize: '14px', fontWeight: '600', margin: 0, color: '#0f172a' }}>All Members</h3>
          <span style={{ marginLeft: 'auto', fontSize: '12px', color: '#64748b' }}>{members.length} total</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '10px' }}>
          {members.map(m => (
            <div
              key={m.id}
              style={{
                display: 'flex', alignItems: 'center', gap: '10px',
                padding: '10px', borderRadius: '8px',
                background: '#f8fafc', border: '1px solid #f1f5f9',
              }}
            >
              <div style={{
                width: '32px', height: '32px', borderRadius: '50%',
                background: m.role === 'leader' ? '#f59e0b' : '#3b82f6',
                color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '12px', fontWeight: '700',
              }}>
                {m.name?.charAt(0) || '?'}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: '13px', fontWeight: '600', color: '#0f172a', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{m.name}</div>
                <div style={{ fontSize: '11px', color: '#94a3b8' }}>{m.role}</div>
              </div>
            </div>
          ))}
          {members.length === 0 && (
            <p style={{ gridColumn: '1/-1', textAlign: 'center', color: '#94a3b8', padding: '20px', fontSize: '13px' }}>No members in this group</p>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div style={{
      background: '#fff', borderRadius: '12px', border: '1px solid #e2e8f0',
      padding: '16px', display: 'flex', alignItems: 'center', gap: '12px',
    }}>
      <div style={{
        width: '40px', height: '40px', borderRadius: '10px',
        background: `${color}12`, display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <Icon className="w-5 h-5" style={{ color }} />
      </div>
      <div>
        <div style={{ fontSize: '22px', fontWeight: '700', color: '#0f172a', lineHeight: 1 }}>{value}</div>
        <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>{label}</div>
      </div>
    </div>
  );
}
