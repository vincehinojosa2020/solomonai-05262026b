import { useState, useEffect } from 'react';
import { useParams, useNavigate, useOutletContext } from 'react-router-dom';
import { ArrowLeft, Users, GraduationCap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { API_URL } from '@/lib/utils';

export default function AdminCourseMembers() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [enrollments, setEnrollments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [courseName, setCourseName] = useState('');

  const token = localStorage.getItem('session_token');
  const authHeaders = { 'Authorization': `Bearer ${token}` };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [enrollRes, courseRes] = await Promise.all([
          fetch(`${API_URL}/admin/courses/${id}/enrollments`, { headers: authHeaders }),
          fetch(`${API_URL}/admin/courses/${id}`, { headers: authHeaders }),
        ]);
        if (enrollRes.ok) {
          const data = await enrollRes.json();
          setEnrollments(data.enrollments || []);
        }
        if (courseRes.ok) {
          const c = await courseRes.json();
          setCourseName(c.title || '');
        }
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    };
    fetchData();
  }, [id]);

  const getInitials = (name) => {
    if (!name) return '?';
    return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
  };

  if (loading) {
    return <div className="animate-pulse space-y-6"><div className="h-8 bg-slate-200 rounded w-64" /><div className="h-64 bg-slate-200 rounded-lg" /></div>;
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="admin-course-members">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/admin/courses')} data-testid="back-to-courses">
          <ArrowLeft className="w-4 h-4 mr-1" />Back
        </Button>
        <div>
          <h1 className="text-xl font-bold text-slate-900">{courseName}</h1>
          <p className="text-sm text-slate-500">Enrolled Members</p>
        </div>
      </div>

      <Badge variant="secondary">
        <Users className="w-3.5 h-3.5 mr-1" />
        {enrollments.length} enrolled
      </Badge>

      {enrollments.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center" data-testid="members-empty">
          <GraduationCap className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-1">No enrollments yet</h3>
          <p className="text-sm text-slate-500">Members will appear here when they enroll in this course.</p>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden" data-testid="members-table">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/50">
                <th className="text-left p-4 text-xs font-semibold text-slate-500 uppercase">Member</th>
                <th className="text-left p-4 text-xs font-semibold text-slate-500 uppercase">Enrolled</th>
                <th className="text-left p-4 text-xs font-semibold text-slate-500 uppercase">Progress</th>
                <th className="text-left p-4 text-xs font-semibold text-slate-500 uppercase">Completed</th>
              </tr>
            </thead>
            <tbody>
              {enrollments.map((e, idx) => (
                <tr key={e.id || idx} className="border-b border-slate-50" data-testid={`member-row-${idx}`}>
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <Avatar className="w-8 h-8">
                        <AvatarFallback className="bg-indigo-100 text-indigo-700 text-xs font-semibold">
                          {getInitials(e.user?.name)}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="text-sm font-medium text-slate-900">{e.user?.name || 'Unknown'}</p>
                        <p className="text-xs text-slate-500">{e.user?.email || ''}</p>
                      </div>
                    </div>
                  </td>
                  <td className="p-4 text-sm text-slate-600">
                    {e.enrolled_at ? new Date(e.enrolled_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '-'}
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 bg-slate-100 rounded-full max-w-[100px]">
                        <div className="h-2 bg-indigo-500 rounded-full transition-all" style={{ width: `${e.progress || 0}%` }} />
                      </div>
                      <span className="text-xs font-medium text-slate-600">{e.progress || 0}%</span>
                    </div>
                  </td>
                  <td className="p-4">
                    {e.completed_at ? (
                      <Badge className="bg-emerald-50 text-emerald-700">
                        {new Date(e.completed_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                      </Badge>
                    ) : (
                      <span className="text-xs text-slate-400">In progress</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
