import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft, Play, CheckCircle } from 'lucide-react';
import { API_URL } from '@/lib/utils';

const parseDuration = (label) => {
  if (!label) return 0;
  const parts = label.split(':').map(Number);
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  if (parts.length === 1) return parts[0];
  return 0;
};

function LessonVideoModal({ lesson, onClose, onProgress }) {
  const [currentTime, setCurrentTime] = useState(lesson?.position_seconds || 0);

  useEffect(() => {
    if (!lesson) return undefined;
    const interval = setInterval(() => {
      setCurrentTime((prev) => {
        const next = prev + 15;
        onProgress(lesson, next);
        return next;
      });
    }, 15000);

    return () => clearInterval(interval);
  }, [lesson, onProgress]);

  if (!lesson) return null;

  const handleClose = () => {
    onProgress(lesson, currentTime);
    onClose();
  };

  return (
    <div className="pathways-modal-overlay" data-testid="lesson-video-modal" onClick={handleClose}>
      <div className="pathways-modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="pathways-modal-close" onClick={handleClose} data-testid="lesson-video-close">
          ×
        </button>
        <div className="pathways-modal-header">
          <h2>{lesson.title}</h2>
          <p>{lesson.description}</p>
        </div>
        <div className="pathways-modal-video">
          {lesson.youtube_id ? (
            <iframe
              title={lesson.title}
              src={`https://www.youtube.com/embed/${lesson.youtube_id}?autoplay=1&rel=0&modestbranding=1`}
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
            />
          ) : (
            <div className="pathways-video-placeholder">
              <p>No video provided for this lesson.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function PortalPathwaysCourse() {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [course, setCourse] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeLesson, setActiveLesson] = useState(null);

  const fetchCourse = async () => {
    try {
      const courseRes = await fetch(`${API_URL}/portal/pathways/courses`, { credentials: 'include' });
      if (courseRes.ok) {
        const data = await courseRes.json();
        const found = (data.courses || []).find((c) => c.id === courseId);
        setCourse(found || null);
      }
    } catch (error) {
      console.error('Failed to load course', error);
    }
  };

  const fetchLessons = async () => {
    try {
      const res = await fetch(`${API_URL}/portal/pathways/courses/${courseId}/lessons`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setLessons(data.lessons || []);
      }
    } catch (error) {
      console.error('Failed to fetch lessons', error);
    }
  };

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await Promise.all([fetchCourse(), fetchLessons()]);
      setLoading(false);
    };
    load();
  }, [courseId]);

  const updateProgress = async (lesson, positionSeconds) => {
    const durationSeconds = lesson.duration_seconds || parseDuration(lesson.duration_label);
    try {
      await fetch(`${API_URL}/portal/pathways/progress`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          course_id: courseId,
          lesson_id: lesson.id,
          position_seconds: Math.floor(positionSeconds),
          duration_seconds: durationSeconds || 0,
          title: lesson.title,
        })
      });
      await fetchLessons();
    } catch (error) {
      console.error('Failed to update progress', error);
    }
  };

  const markComplete = async (lesson) => {
    const durationSeconds = lesson.duration_seconds || parseDuration(lesson.duration_label) || 1;
    await updateProgress(lesson, durationSeconds);
  };

  if (loading) {
    return (
      <div className="portal-pathways-loading" data-testid="pathways-course-loading">
        Loading pathway...
      </div>
    );
  }

  if (!course) {
    return (
      <div className="portal-pathways-empty" data-testid="pathways-course-missing">
        <p>Course not found.</p>
      </div>
    );
  }

  return (
    <div className="portal-pathways-course" data-testid="portal-pathways-course">
      <button
        className="portal-pathways-back"
        onClick={() => navigate('/portal/pathways')}
        data-testid="pathways-back-btn"
      >
        <ArrowLeft className="w-4 h-4" /> Back to Pathways
      </button>

      <div className="portal-pathways-course-header">
        <div>
          <span className="portal-tag">Abundant Pathways</span>
          <h1>{course.title}</h1>
          <p>{course.description}</p>
        </div>
        <div className="portal-pathways-course-progress">
          <span>{course.progress_percent || 0}% complete</span>
          <div className="portal-pathways-progress-bar">
            <div style={{ width: `${course.progress_percent || 0}%` }} />
          </div>
        </div>
      </div>

      <div className="portal-pathways-lessons" data-testid="pathways-lessons">
        {lessons.map((lesson) => (
          <div key={lesson.id} className="portal-pathways-lesson" data-testid={`pathways-lesson-${lesson.id}`}>
            <div className="portal-pathways-lesson-info">
              <h3>{lesson.title}</h3>
              <p>{lesson.description}</p>
              <span>{lesson.duration_label || '00:00'}</span>
            </div>
            <div className="portal-pathways-lesson-actions">
              {lesson.completed ? (
                <span className="portal-pathways-complete">
                  <CheckCircle className="w-4 h-4" /> Completed
                </span>
              ) : (
                <button
                  className="portal-pathways-start"
                  onClick={() => setActiveLesson(lesson)}
                  data-testid={`pathways-play-${lesson.id}`}
                >
                  <Play className="w-4 h-4" /> {lesson.progress_percent > 0 ? 'Resume' : 'Start'}
                </button>
              )}
              {!lesson.completed && (
                <button
                  className="portal-pathways-mark"
                  onClick={() => markComplete(lesson)}
                  data-testid={`pathways-complete-${lesson.id}`}
                >
                  Mark Complete
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {activeLesson && (
        <LessonVideoModal
          lesson={activeLesson}
          onClose={() => setActiveLesson(null)}
          onProgress={updateProgress}
        />
      )}
    </div>
  );
}
