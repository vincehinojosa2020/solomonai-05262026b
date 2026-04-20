import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, BookOpen, Clock, ExternalLink, Download, BadgeCheck } from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { safeHref } from '@/utils/sanitize';

export default function PortalPathways() {
  const [courses, setCourses] = useState([]);
  const [nextSteps, setNextSteps] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const [coursesRes, nextStepsRes] = await Promise.all([
          fetch(`${API_URL}/portal/pathways/courses`),
          fetch(`${API_URL}/portal/next-steps/status`)
        ]);

        if (coursesRes.ok) {
          const data = await coursesRes.json();
          setCourses(data.courses || []);
        }

        if (nextStepsRes.ok) {
          const statusData = await nextStepsRes.json();
          setNextSteps(statusData);
        }
      } catch (error) {
        console.error('Failed to fetch pathways courses:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchCourses();
  }, []);

  return (
    <div className="portal-pathways" data-testid="portal-pathways-page">
      <div className="portal-pathways-hero">
        <div>
          <span className="portal-tag">Abundant Pathways</span>
          <h1>Grow Through Discipleship</h1>
          <p>Assigned courses from your church leadership. Watch, reflect, and grow at your pace.</p>
        </div>
      </div>

      {nextSteps && (
        <div className="rounded-3xl border border-slate-200 bg-white p-6 md:p-8 shadow-sm mb-8" data-testid="next-steps-journey-card">
          <div className="flex flex-wrap items-start justify-between gap-5">
            <div className="space-y-2 max-w-2xl">
              <span className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700" data-testid="next-steps-track-tag">
                <BadgeCheck className="w-3.5 h-3.5" /> Membership Journey
              </span>
              <h2 className="text-xl md:text-2xl font-semibold text-slate-900" data-testid="next-steps-title">Abundant Next Steps</h2>
              <p className="text-sm md:text-base text-slate-600" data-testid="next-steps-description">
                Complete the core discipleship track, then your admin team can approve your official Abundant membership and unlock your completion certificate.
              </p>
            </div>

            <div className="flex flex-wrap gap-3" data-testid="next-steps-actions">
              <a
                href={safeHref(nextSteps.thinkific_url)}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-2 rounded-full bg-slate-900 text-white px-4 py-2 text-sm font-semibold"
                data-testid="next-steps-open-thinkific"
              >
                Open Thinkific
                <ExternalLink className="w-4 h-4" />
              </a>
              {nextSteps.certificate_available && (
                <a
                  href={`${API_URL}/portal/next-steps/certificate`}
                  className="inline-flex items-center gap-2 rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700"
                  data-testid="next-steps-download-certificate"
                >
                  Download Certificate
                  <Download className="w-4 h-4" />
                </a>
              )}
            </div>
          </div>

          <div className="mt-5 grid md:grid-cols-[1fr_auto] gap-4 items-center">
            <div>
              <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden" data-testid="next-steps-progress-bar">
                <div className="h-full bg-blue-600 transition-[width] duration-500" style={{ width: `${nextSteps.completion_percent || 0}%` }} />
              </div>
              <p className="mt-2 text-sm text-slate-600" data-testid="next-steps-progress-text">
                {nextSteps.completion_percent || 0}% complete • Status: {nextSteps.approval_status?.replaceAll('_', ' ') || 'in progress'}
              </p>
            </div>

            <div className="text-sm text-slate-600" data-testid="next-steps-course-summary">
              {(nextSteps.required_courses || []).filter((course) => course.completed).length}/
              {(nextSteps.required_courses || []).length} required courses completed
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="portal-pathways-loading" data-testid="pathways-loading">
          Loading courses...
        </div>
      ) : courses.length === 0 ? (
        <div className="portal-pathways-empty" data-testid="pathways-empty">
          <BookOpen className="w-8 h-8" />
          <h3>No courses assigned yet</h3>
          <p>Once your church assigns a pathway, it will appear here.</p>
        </div>
      ) : (
        <div className="portal-pathways-grid" data-testid="pathways-course-grid">
          {courses.map((course) => (
            <div key={course.id} className="portal-pathways-card" data-testid={`pathways-course-${course.id}`}>
              <div className="portal-pathways-card-image">
                <img src={course.cover_image_url || 'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?auto=format&fit=crop&w=900&q=80'} alt={course.title} />
              </div>
              <div className="portal-pathways-card-body">
                <h3>{course.title}</h3>
                <p>{course.description || 'Discipleship path curated by your church leadership.'}</p>
                <div className="portal-pathways-meta">
                  <span><BookOpen className="w-4 h-4" /> {course.total_lessons || 0} lessons</span>
                  <span><Clock className="w-4 h-4" /> {course.progress_percent || 0}% complete</span>
                </div>
                <div className="portal-pathways-progress">
                  <div className="portal-pathways-progress-bar">
                    <div style={{ width: `${course.progress_percent || 0}%` }} />
                  </div>
                </div>
                <button
                  className="portal-pathways-cta"
                  onClick={() => navigate(`/portal/pathways/${course.id}`)}
                  data-testid={`pathways-open-${course.id}`}
                >
                  {course.progress_percent > 0 ? 'Continue' : 'Start'}
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
