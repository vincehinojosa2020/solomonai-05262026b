import { useState, useEffect } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import {
  GraduationCap, Plus, Search, MoreHorizontal, Edit2, Users, Trash2, Eye
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger
} from '@/components/ui/dropdown-menu';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

const STATUS_BADGE = {
  draft: 'bg-amber-50 text-amber-700 border-amber-200',
  published: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  archived: 'bg-slate-100 text-slate-500 border-slate-200',
};

const CATEGORY_LABEL = {
  new_members: 'New Members',
  leadership: 'Leadership',
  discipleship: 'Discipleship',
  marriage: 'Marriage & Family',
  general: 'General',
};

export default function AdminCourseList() {
  const navigate = useNavigate();
  const { tenant } = useOutletContext();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const token = localStorage.getItem('session_token');
  const authHeaders = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  useEffect(() => { fetchCourses(); }, []);

  const fetchCourses = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/courses`, { headers: authHeaders });
      if (res.ok) {
        const data = await res.json();
        setCourses(data.courses || []);
      }
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const deleteCourse = async (id) => {
    if (!window.confirm('Delete this course and all its content? This cannot be undone.')) return;
    try {
      await fetch(`${API_URL}/admin/courses/${id}`, { method: 'DELETE', headers: authHeaders });
      toast.success('Course deleted');
      fetchCourses();
    } catch (err) { toast.error('Failed to delete'); }
  };

  const createCourse = async () => {
    try {
      const res = await fetch(`${API_URL}/admin/courses`, {
        method: 'POST', headers: authHeaders,
        body: JSON.stringify({ title: 'Untitled Course', status: 'draft' }),
      });
      if (res.ok) {
        const course = await res.json();
        navigate(`/admin/courses/${course.id}/edit`);
      }
    } catch (err) { toast.error('Failed to create course'); }
  };

  const filtered = courses.filter(c =>
    (c.title || '').toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="animate-pulse space-y-6" data-testid="courses-loading">
        <div className="h-8 bg-slate-200 rounded w-64" />
        <div className="h-64 bg-slate-200 rounded-lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="admin-courses-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Solomon Academy</h1>
          <p className="page-subtitle">Create and manage courses for your congregation</p>
        </div>
        <Button className="btn-primary" onClick={createCourse} data-testid="create-course-btn">
          <Plus className="w-4 h-4 mr-2" />
          Create Course
        </Button>
      </div>

      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <Input
          placeholder="Search courses..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
          data-testid="courses-search"
        />
      </div>

      {filtered.length === 0 ? (
        <div className="bg-white border border-slate-200 rounded-xl p-12 text-center" data-testid="courses-empty">
          <GraduationCap className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-1">
            {search ? 'No matching courses' : 'No courses yet'}
          </h3>
          <p className="text-sm text-slate-500 mb-4">
            {search ? 'Try a different search term.' : 'Create your first course to start building lessons.'}
          </p>
          {!search && (
            <Button className="btn-primary" onClick={createCourse} data-testid="courses-empty-create-btn">
              <Plus className="w-4 h-4 mr-2" />Create Course
            </Button>
          )}
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden" data-testid="courses-table">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/50">
                <th className="text-left p-4 text-xs font-semibold text-slate-500 uppercase">Course</th>
                <th className="text-left p-4 text-xs font-semibold text-slate-500 uppercase">Status</th>
                <th className="text-left p-4 text-xs font-semibold text-slate-500 uppercase hidden sm:table-cell">Lessons</th>
                <th className="text-left p-4 text-xs font-semibold text-slate-500 uppercase hidden md:table-cell">Enrolled</th>
                <th className="text-left p-4 text-xs font-semibold text-slate-500 uppercase hidden md:table-cell">Completion</th>
                <th className="text-right p-4 text-xs font-semibold text-slate-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((course) => (
                <tr key={course.id} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors" data-testid={`course-row-${course.id}`}>
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center flex-shrink-0">
                        <GraduationCap className="w-5 h-5 text-indigo-600" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-slate-900 truncate">{course.title}</p>
                        <p className="text-xs text-slate-500">{CATEGORY_LABEL[course.category] || course.category}</p>
                      </div>
                    </div>
                  </td>
                  <td className="p-4">
                    <Badge className={`${STATUS_BADGE[course.status] || STATUS_BADGE.draft} border capitalize`} data-testid={`course-status-${course.id}`}>
                      {course.status}
                    </Badge>
                  </td>
                  <td className="p-4 text-sm text-slate-600 hidden sm:table-cell">{course.lesson_count || 0}</td>
                  <td className="p-4 text-sm text-slate-600 hidden md:table-cell">{course.enrolled_count || 0}</td>
                  <td className="p-4 hidden md:table-cell">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 bg-slate-100 rounded-full max-w-[80px]">
                        <div className="h-2 bg-emerald-500 rounded-full" style={{ width: `${course.completion_rate || 0}%` }} />
                      </div>
                      <span className="text-xs text-slate-500">{course.completion_rate || 0}%</span>
                    </div>
                  </td>
                  <td className="p-4 text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm" data-testid={`course-actions-${course.id}`}>
                          <MoreHorizontal className="w-4 h-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => navigate(`/admin/courses/${course.id}/edit`)} data-testid={`course-edit-${course.id}`}>
                          <Edit2 className="w-4 h-4 mr-2" />Edit Course
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => navigate(`/admin/courses/${course.id}/members`)} data-testid={`course-members-${course.id}`}>
                          <Users className="w-4 h-4 mr-2" />View Members
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => deleteCourse(course.id)} className="text-red-600" data-testid={`course-delete-${course.id}`}>
                          <Trash2 className="w-4 h-4 mr-2" />Delete Course
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
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
