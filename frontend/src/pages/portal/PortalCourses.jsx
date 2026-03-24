import { useState, useEffect } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import { GraduationCap, Clock, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { API_URL } from '@/lib/utils';

const CATEGORY_LABEL = {
  new_members: 'New Members',
  leadership: 'Leadership',
  discipleship: 'Discipleship',
  marriage: 'Marriage & Family',
  general: 'General',
};

export default function PortalCourses() {
  const navigate = useNavigate();
  const { user, tenant } = useOutletContext();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('all');

  const token = localStorage.getItem('session_token');

  useEffect(() => { fetchCourses(); }, []);

  const fetchCourses = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/courses`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setCourses(data.courses || []);
      }
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const filtered = courses.filter(c => {
    if (tab === 'my') return c.enrolled && !c.completed_at;
    if (tab === 'completed') return c.completed_at;
    return true;
  });

  if (loading) {
    return (
      <div className="space-y-4 py-6" data-testid="portal-courses-loading">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="animate-pulse bg-white rounded-2xl h-48 border border-slate-100" />
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-5" data-testid="portal-courses-page">
      <div>
        <h1 className="text-2xl font-bold text-slate-900" data-testid="courses-title">Solomon Academy</h1>
        <p className="text-sm text-slate-500 mt-1">Grow in your faith with courses from {tenant?.name || 'your church'}</p>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="bg-white border border-slate-200 p-1">
          <TabsTrigger value="all" data-testid="tab-all">All Courses</TabsTrigger>
          <TabsTrigger value="my" data-testid="tab-my">My Courses</TabsTrigger>
          <TabsTrigger value="completed" data-testid="tab-completed">Completed</TabsTrigger>
        </TabsList>

        <TabsContent value={tab} className="mt-4">
          {filtered.length === 0 ? (
            <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center" data-testid="courses-empty-state">
              <GraduationCap className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 mb-1">
                {tab === 'my' ? 'No courses in progress' : tab === 'completed' ? 'No completed courses' : 'No courses available'}
              </h3>
              <p className="text-sm text-slate-500">
                {tab === 'my' ? 'Enroll in a course to get started!' : tab === 'completed' ? 'Complete a course to see it here.' : 'Check back soon for new courses.'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {filtered.map((course) => (
                <div
                  key={course.id}
                  className="bg-white rounded-2xl border border-slate-100 overflow-hidden hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => navigate(`/portal/courses/${course.id}`)}
                  data-testid={`course-card-${course.id}`}
                >
                  {/* Thumbnail */}
                  <div className="h-36 bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center relative">
                    {course.thumbnail_url ? (
                      <img src={course.thumbnail_url} alt={course.title} className="w-full h-full object-cover" />
                    ) : (
                      <GraduationCap className="w-12 h-12 text-white/50" />
                    )}
                    {course.completed_at && (
                      <div className="absolute top-2 right-2">
                        <Badge className="bg-emerald-500 text-white border-none">Completed</Badge>
                      </div>
                    )}
                  </div>

                  {/* Info */}
                  <div className="p-4">
                    <Badge variant="secondary" className="text-xs mb-2">{CATEGORY_LABEL[course.category] || course.category}</Badge>
                    <h3 className="font-semibold text-slate-900 text-sm mb-1 line-clamp-2" data-testid={`course-title-${course.id}`}>{course.title}</h3>
                    <div className="flex items-center gap-3 text-xs text-slate-500 mb-3">
                      <span className="flex items-center gap-1"><BookOpen className="w-3 h-3" />{course.lesson_count} lessons</span>
                      {course.total_duration_minutes > 0 && (
                        <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{course.total_duration_minutes}m</span>
                      )}
                    </div>

                    {/* Progress bar */}
                    {course.enrolled && (
                      <div className="mb-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-medium text-slate-600">{course.progress}% complete</span>
                        </div>
                        <div className="h-2 bg-slate-100 rounded-full">
                          <div
                            className="h-2 rounded-full transition-all"
                            style={{ width: `${course.progress}%`, background: course.progress === 100 ? '#10b981' : '#6366f1' }}
                          />
                        </div>
                      </div>
                    )}

                    <Button
                      className="w-full text-sm"
                      variant={course.enrolled ? 'default' : 'outline'}
                      data-testid={`course-action-${course.id}`}
                    >
                      {course.completed_at ? 'Review' : course.enrolled ? 'Continue' : 'Enroll'}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
