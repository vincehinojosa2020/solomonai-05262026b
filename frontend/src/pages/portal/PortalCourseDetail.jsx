import { useState, useEffect } from 'react';
import { useParams, useNavigate, useOutletContext } from 'react-router-dom';
import {
  ArrowLeft, GraduationCap, Clock, BookOpen, CheckCircle2, Circle,
  Video, FileText, HelpCircle, Download, Lock, User
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

const LESSON_ICONS = { video: Video, text: FileText, quiz: HelpCircle, download: Download };
const LESSON_COLORS = { video: 'text-blue-600', text: 'text-emerald-600', quiz: 'text-purple-600', download: 'text-amber-600' };

export default function PortalCourseDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useOutletContext();
  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [enrolling, setEnrolling] = useState(false);

  const token = localStorage.getItem('session_token');

  useEffect(() => { fetchCourse(); }, [id]);

  const fetchCourse = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/courses/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) setCourse(await res.json());
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const enroll = async () => {
    setEnrolling(true);
    try {
      const res = await fetch(`${API_URL}/portal/courses/${id}/enroll`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        toast.success('Enrolled successfully!');
        fetchCourse();
      }
    } catch (err) { toast.error('Failed to enroll'); }
    finally { setEnrolling(false); }
  };

  const goToLesson = (lessonId) => {
    if (!course.enrolled) {
      toast.error('Please enroll first to access lessons');
      return;
    }
    navigate(`/portal/courses/${id}/lessons/${lessonId}`);
  };

  if (loading) {
    return (
      <div className="animate-pulse space-y-6 py-6">
        <div className="h-48 bg-slate-200 rounded-2xl" />
        <div className="h-8 bg-slate-200 rounded w-64" />
        <div className="space-y-3">{[...Array(5)].map((_, i) => <div key={i} className="h-12 bg-slate-100 rounded-lg" />)}</div>
      </div>
    );
  }

  if (!course) {
    return <div className="text-center py-12"><p className="text-slate-500">Course not found</p></div>;
  }

  return (
    <div className="space-y-6" data-testid="portal-course-detail">
      <Button variant="ghost" size="sm" onClick={() => navigate('/portal/courses')} data-testid="back-to-catalog">
        <ArrowLeft className="w-4 h-4 mr-1" />Back to Courses
      </Button>

      {/* Hero */}
      <div className="bg-gradient-to-br from-indigo-600 to-purple-700 rounded-2xl overflow-hidden" data-testid="course-hero">
        <div className="p-6 sm:p-8 text-white">
          <Badge className="bg-white/20 text-white border-none mb-3">{course.category?.replace('_', ' ')}</Badge>
          <h1 className="text-2xl sm:text-3xl font-bold mb-2" data-testid="course-detail-title">{course.title}</h1>
          {course.instructor_name && (
            <p className="flex items-center gap-1.5 text-white/80 text-sm mb-4">
              <User className="w-4 h-4" />{course.instructor_name}
            </p>
          )}
          <div className="flex items-center gap-4 text-sm text-white/70 mb-5">
            <span className="flex items-center gap-1"><BookOpen className="w-4 h-4" />{course.lesson_count} lessons</span>
            {course.total_duration_minutes > 0 && (
              <span className="flex items-center gap-1"><Clock className="w-4 h-4" />{course.total_duration_minutes} min</span>
            )}
          </div>

          {/* Progress or Enroll */}
          {course.enrolled ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-white/80">{course.progress}% complete ({course.completed_lessons}/{course.lesson_count} lessons)</span>
                {course.completed_at && <Badge className="bg-emerald-400 text-white border-none">Completed</Badge>}
              </div>
              <div className="h-2.5 bg-white/20 rounded-full">
                <div className="h-2.5 bg-white rounded-full transition-all" style={{ width: `${course.progress}%` }} />
              </div>
            </div>
          ) : (
            <Button
              className="bg-white text-indigo-700 hover:bg-white/90 font-semibold px-8"
              onClick={enroll}
              disabled={enrolling}
              data-testid="enroll-btn"
            >
              {enrolling ? 'Enrolling...' : 'Enroll Now'}
            </Button>
          )}
        </div>
      </div>

      {/* Description */}
      {course.description && (
        <div className="bg-white rounded-2xl border border-slate-100 p-5" data-testid="course-description">
          <h2 className="text-sm font-semibold text-slate-900 mb-2">About This Course</h2>
          <p className="text-sm text-slate-600 whitespace-pre-line leading-relaxed">{course.description}</p>
        </div>
      )}

      {/* Curriculum */}
      <div data-testid="course-curriculum">
        <h2 className="text-sm font-semibold text-slate-900 mb-3">Curriculum</h2>
        <div className="space-y-3">
          {(course.modules || []).map((mod) => (
            <div key={mod.id} className="bg-white rounded-xl border border-slate-100 overflow-hidden" data-testid={`curriculum-module-${mod.id}`}>
              <div className="px-4 py-3 bg-slate-50/50 border-b border-slate-100">
                <h3 className="text-sm font-semibold text-slate-800">{mod.title}</h3>
              </div>
              <div className="divide-y divide-slate-50">
                {(mod.lessons || []).map((lesson) => {
                  const Icon = LESSON_ICONS[lesson.type] || FileText;
                  const color = LESSON_COLORS[lesson.type] || LESSON_COLORS.text;
                  return (
                    <button
                      key={lesson.id}
                      className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-slate-50/50 transition-colors disabled:opacity-50"
                      onClick={() => goToLesson(lesson.id)}
                      disabled={!course.enrolled}
                      data-testid={`lesson-link-${lesson.id}`}
                    >
                      {lesson.completed ? (
                        <CheckCircle2 className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                      ) : course.enrolled ? (
                        <Circle className="w-5 h-5 text-slate-300 flex-shrink-0" />
                      ) : (
                        <Lock className="w-5 h-5 text-slate-300 flex-shrink-0" />
                      )}
                      <Icon className={`w-4 h-4 ${color} flex-shrink-0`} />
                      <span className="text-sm text-slate-800 flex-1 truncate">{lesson.title}</span>
                      {lesson.duration_minutes > 0 && (
                        <span className="text-xs text-slate-400">{lesson.duration_minutes}m</span>
                      )}
                      {lesson.type === 'quiz' && lesson.quiz_passed !== undefined && (
                        <Badge className={lesson.quiz_passed ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'}>
                          {lesson.quiz_score}%
                        </Badge>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
