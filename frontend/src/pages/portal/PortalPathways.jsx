import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, BookOpen, Clock } from 'lucide-react';
import { API_URL } from '@/lib/utils';

export default function PortalPathways() {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchCourses = async () => {
      try {
        const res = await fetch(`${API_URL}/portal/pathways/courses`, { credentials: 'include' });
        if (res.ok) {
          const data = await res.json();
          setCourses(data.courses || []);
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
