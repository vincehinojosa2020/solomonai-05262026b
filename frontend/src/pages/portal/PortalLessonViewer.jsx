import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, useOutletContext } from 'react-router-dom';
import {
  ArrowLeft, ArrowRight, CheckCircle2, Video, FileText, HelpCircle, Download
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';
import ReactMarkdown from 'react-markdown';

function extractEmbedUrl(url) {
  if (!url) return null;
  // YouTube
  const ytMatch = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]+)/);
  if (ytMatch) return `https://www.youtube.com/embed/${ytMatch[1]}`;
  // Vimeo
  const vimeoMatch = url.match(/vimeo\.com\/(\d+)/);
  if (vimeoMatch) return `https://player.vimeo.com/video/${vimeoMatch[1]}`;
  return url;
}

function VideoLesson({ lesson }) {
  const embedUrl = extractEmbedUrl(lesson.content?.video_url);
  return (
    <div data-testid="lesson-video-content">
      {embedUrl ? (
        <div className="aspect-video bg-black rounded-xl overflow-hidden mb-6">
          <iframe
            src={embedUrl}
            className="w-full h-full"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            title={lesson.title}
          />
        </div>
      ) : (
        <div className="aspect-video bg-slate-100 rounded-xl flex items-center justify-center mb-6">
          <Video className="w-12 h-12 text-slate-300" />
        </div>
      )}
      <h2 className="text-xl font-bold text-slate-900 mb-2">{lesson.title}</h2>
    </div>
  );
}

function TextLesson({ lesson }) {
  return (
    <div data-testid="lesson-text-content">
      <div className="prose prose-slate max-w-none bg-white rounded-xl border border-slate-100 p-6 sm:p-8">
        <ReactMarkdown>{lesson.content?.body || ''}</ReactMarkdown>
      </div>
    </div>
  );
}

function DownloadLesson({ lesson }) {
  return (
    <div className="bg-white rounded-xl border border-slate-100 p-8 text-center" data-testid="lesson-download-content">
      <Download className="w-12 h-12 text-amber-500 mx-auto mb-4" />
      <h2 className="text-xl font-bold text-slate-900 mb-2">{lesson.title}</h2>
      {lesson.content?.file_name && (
        <p className="text-sm text-slate-500 mb-4">{lesson.content.file_name}</p>
      )}
      {lesson.content?.file_url ? (
        <a href={lesson.content.file_url} target="_blank" rel="noopener noreferrer">
          <Button data-testid="download-file-btn">
            <Download className="w-4 h-4 mr-2" />Download File
          </Button>
        </a>
      ) : (
        <p className="text-sm text-slate-400">No file available</p>
      )}
    </div>
  );
}

function QuizLesson({ lesson, courseId, onComplete }) {
  const questions = lesson.content?.questions || [];
  const [currentQ, setCurrentQ] = useState(0);
  const [answers, setAnswers] = useState(new Array(questions.length).fill(-1));
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const token = sessionStorage.getItem('session_token');

  // If already passed, show result
  useEffect(() => {
    if (lesson.quiz_passed !== undefined) {
      setSubmitted(true);
      setResult({ score: lesson.quiz_score, passed: lesson.quiz_passed, correct: 0, total: questions.length, passing_score: lesson.content?.passing_score || 70 });
    }
  }, [lesson.quiz_passed]);

  const selectAnswer = (idx) => {
    const updated = [...answers];
    updated[currentQ] = idx;
    setAnswers(updated);
  };

  const submitQuiz = async () => {
    setSubmitting(true);
    try {
      const res = await fetch(`${API_URL}/portal/courses/${courseId}/lessons/${lesson.id}/quiz`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers }),
      });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
        setSubmitted(true);
        if (data.passed) {
          toast.success(`Passed with ${data.score}%!`);
          onComplete?.();
        } else {
          toast.error(`Score: ${data.score}%. Need ${data.passing_score}% to pass.`);
        }
      }
    } catch (err) { toast.error('Failed to submit quiz'); }
    finally { setSubmitting(false); }
  };

  const retake = () => {
    setAnswers(new Array(questions.length).fill(-1));
    setCurrentQ(0);
    setSubmitted(false);
    setResult(null);
  };

  if (submitted && result) {
    return (
      <div className="bg-white rounded-xl border border-slate-100 p-8 text-center" data-testid="quiz-result">
        <div className={`w-16 h-16 rounded-full mx-auto mb-4 flex items-center justify-center ${result.passed ? 'bg-emerald-100' : 'bg-red-100'}`}>
          {result.passed ? (
            <CheckCircle2 className="w-8 h-8 text-emerald-600" />
          ) : (
            <HelpCircle className="w-8 h-8 text-red-500" />
          )}
        </div>
        <h2 className="text-xl font-bold text-slate-900 mb-1">{result.passed ? 'Congratulations!' : 'Not quite'}</h2>
        <p className="text-3xl font-extrabold mb-2" style={{ color: result.passed ? '#10b981' : '#ef4444' }}>
          {result.score}%
        </p>
        <p className="text-sm text-slate-500 mb-4">
          {result.correct}/{result.total} correct ({result.passing_score}% needed to pass)
        </p>
        {!result.passed && (
          <Button onClick={retake} variant="outline" data-testid="quiz-retake-btn">Try Again</Button>
        )}
      </div>
    );
  }

  if (questions.length === 0) {
    return <div className="text-center py-12"><p className="text-slate-500">No questions in this quiz.</p></div>;
  }

  const q = questions[currentQ];
  const allAnswered = answers.every(a => a >= 0);

  return (
    <div className="bg-white rounded-xl border border-slate-100 p-6 sm:p-8" data-testid="quiz-content">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-bold text-slate-900">{lesson.title}</h2>
        <Badge variant="secondary">Question {currentQ + 1} of {questions.length}</Badge>
      </div>

      <p className="text-base font-medium text-slate-800 mb-5" data-testid="quiz-question-text">{q.question}</p>

      <div className="space-y-2.5 mb-6">
        {q.options.map((opt, oIdx) => (
          <button
            key={oIdx}
            className={`w-full text-left p-3.5 rounded-xl border-2 transition-all text-sm ${
              answers[currentQ] === oIdx
                ? 'border-indigo-500 bg-indigo-50 text-indigo-900'
                : 'border-slate-200 hover:border-slate-300 text-slate-700'
            }`}
            onClick={() => selectAnswer(oIdx)}
            data-testid={`quiz-option-${oIdx}`}
          >
            <span className="font-semibold mr-2">{String.fromCharCode(65 + oIdx)}.</span>
            {opt}
          </button>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <Button variant="ghost" disabled={currentQ === 0} onClick={() => setCurrentQ(currentQ - 1)} data-testid="quiz-prev">
          Previous
        </Button>
        <div className="flex items-center gap-1.5">
          {questions.map((_, i) => (
            <button
              key={i}
              className={`w-2.5 h-2.5 rounded-full transition-colors ${
                i === currentQ ? 'bg-indigo-500' : answers[i] >= 0 ? 'bg-indigo-200' : 'bg-slate-200'
              }`}
              onClick={() => setCurrentQ(i)}
            />
          ))}
        </div>
        {currentQ < questions.length - 1 ? (
          <Button onClick={() => setCurrentQ(currentQ + 1)} disabled={answers[currentQ] < 0} data-testid="quiz-next">
            Next
          </Button>
        ) : (
          <Button onClick={submitQuiz} disabled={!allAnswered || submitting} data-testid="quiz-submit">
            {submitting ? 'Submitting...' : 'Submit Quiz'}
          </Button>
        )}
      </div>
    </div>
  );
}

export default function PortalLessonViewer() {
  const { id: courseId, lessonId } = useParams();
  const navigate = useNavigate();
  const [lesson, setLesson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);

  const token = sessionStorage.getItem('session_token');

  useEffect(() => { fetchLesson(); }, [courseId, lessonId]);

  const fetchLesson = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/portal/courses/${courseId}/lessons/${lessonId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) setLesson(await res.json());
      else toast.error('Could not load lesson');
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  };

  const markComplete = async () => {
    setCompleting(true);
    try {
      const res = await fetch(`${API_URL}/portal/courses/${courseId}/lessons/${lessonId}/complete`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        toast.success(data.course_completed ? 'Course completed!' : 'Lesson complete!');
        setLesson(prev => ({ ...prev, completed: true }));
      }
    } catch (err) { toast.error('Failed to mark complete'); }
    finally { setCompleting(false); }
  };

  if (loading) {
    return <div className="animate-pulse space-y-6 py-6"><div className="h-64 bg-slate-200 rounded-2xl" /><div className="h-8 bg-slate-200 rounded w-64" /></div>;
  }

  if (!lesson) {
    return <div className="text-center py-12"><p className="text-slate-500">Lesson not found</p></div>;
  }

  return (
    <div className="space-y-6 pb-8" data-testid="portal-lesson-viewer">
      {/* Back nav */}
      <Button variant="ghost" size="sm" onClick={() => navigate(`/portal/courses/${courseId}`)} data-testid="back-to-course">
        <ArrowLeft className="w-4 h-4 mr-1" />Back to Course
      </Button>

      {/* Lesson content */}
      {lesson.type === 'video' && <VideoLesson lesson={lesson} />}
      {lesson.type === 'text' && <TextLesson lesson={lesson} />}
      {lesson.type === 'download' && <DownloadLesson lesson={lesson} />}
      {lesson.type === 'quiz' && <QuizLesson lesson={lesson} courseId={courseId} onComplete={fetchLesson} />}

      {/* Navigation */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-100">
        <div>
          {lesson.prev_lesson_id && (
            <Button
              variant="outline"
              onClick={() => navigate(`/portal/courses/${courseId}/lessons/${lesson.prev_lesson_id}`)}
              data-testid="prev-lesson-btn"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />Previous
            </Button>
          )}
        </div>

        {/* Mark Complete (not for quiz — quiz auto-marks) */}
        {lesson.type !== 'quiz' && (
          <Button
            onClick={markComplete}
            disabled={lesson.completed || completing}
            variant={lesson.completed ? 'outline' : 'default'}
            data-testid="mark-complete-btn"
          >
            <CheckCircle2 className="w-4 h-4 mr-2" />
            {lesson.completed ? 'Completed' : completing ? 'Saving...' : 'Mark Complete'}
          </Button>
        )}

        <div>
          {lesson.next_lesson_id && (
            <Button
              onClick={() => navigate(`/portal/courses/${courseId}/lessons/${lesson.next_lesson_id}`)}
              data-testid="next-lesson-btn"
            >
              Next<ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
