import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, useOutletContext } from 'react-router-dom';
import {
  ArrowLeft, Save, GraduationCap, Plus, Trash2, ChevronUp, ChevronDown,
  Video, FileText, HelpCircle, Download, Edit2, Grip
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue
} from '@/components/ui/select';
import {
  Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
} from '@/components/ui/dialog';
import { Switch } from '@/components/ui/switch';
import { API_URL } from '@/lib/utils';
import { toast } from 'sonner';

const LESSON_ICONS = { video: Video, text: FileText, quiz: HelpCircle, download: Download };
const LESSON_COLORS = { video: 'text-blue-600 bg-blue-50', text: 'text-emerald-600 bg-emerald-50', quiz: 'text-purple-600 bg-purple-50', download: 'text-amber-600 bg-amber-50' };

export default function AdminCourseEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('info');
  // lesson modal
  const [showLessonModal, setShowLessonModal] = useState(false);
  const [editingLesson, setEditingLesson] = useState(null);
  const [lessonModuleId, setLessonModuleId] = useState(null);
  const [lessonForm, setLessonForm] = useState({ title: '', type: 'text', content: {}, duration_minutes: 5, is_required: true });
  // module modal
  const [showModuleModal, setShowModuleModal] = useState(false);
  const [moduleTitle, setModuleTitle] = useState('');
  const [editingModuleId, setEditingModuleId] = useState(null);
  // quiz builder
  const [quizQuestions, setQuizQuestions] = useState([{ question: '', options: ['', '', '', ''], correct: 0 }]);
  const [passingScore, setPassingScore] = useState(70);

  const token = localStorage.getItem('session_token');
  const authHeaders = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };

  const fetchCourse = useCallback(async () => {
    try {
      const res = await fetch(`${API_URL}/admin/courses/${id}`, { headers: authHeaders });
      if (res.ok) setCourse(await res.json());
      else toast.error('Course not found');
    } catch (err) { console.error(err); }
    finally { setLoading(false); }
  }, [id]);

  useEffect(() => { fetchCourse(); }, [fetchCourse]);

  const saveCourseInfo = async () => {
    setSaving(true);
    try {
      const res = await fetch(`${API_URL}/admin/courses/${id}`, {
        method: 'PUT', headers: authHeaders,
        body: JSON.stringify({
          title: course.title, description: course.description,
          instructor_name: course.instructor_name, category: course.category,
          thumbnail_url: course.thumbnail_url, status: course.status,
          enrollment_type: course.enrollment_type,
        }),
      });
      if (res.ok) toast.success('Course saved');
    } catch (err) { toast.error('Failed to save'); }
    finally { setSaving(false); }
  };

  const addModule = async () => {
    if (!moduleTitle.trim()) { toast.error('Module title required'); return; }
    try {
      const endpoint = editingModuleId
        ? `${API_URL}/admin/courses/${id}/modules/${editingModuleId}`
        : `${API_URL}/admin/courses/${id}/modules`;
      const method = editingModuleId ? 'PUT' : 'POST';
      await fetch(endpoint, { method, headers: authHeaders, body: JSON.stringify({ title: moduleTitle }) });
      toast.success(editingModuleId ? 'Module updated' : 'Module added');
      setShowModuleModal(false);
      setModuleTitle('');
      setEditingModuleId(null);
      fetchCourse();
    } catch (err) { toast.error('Failed'); }
  };

  const deleteModule = async (moduleId) => {
    if (!window.confirm('Delete this module and all its lessons?')) return;
    await fetch(`${API_URL}/admin/courses/${id}/modules/${moduleId}`, { method: 'DELETE', headers: authHeaders });
    toast.success('Module deleted');
    fetchCourse();
  };

  const moveModule = async (moduleId, direction) => {
    await fetch(`${API_URL}/admin/courses/${id}/modules/${moduleId}/move`, {
      method: 'POST', headers: authHeaders, body: JSON.stringify({ direction }),
    });
    fetchCourse();
  };

  const openLessonModal = (moduleId, lesson = null) => {
    setLessonModuleId(moduleId);
    if (lesson) {
      setEditingLesson(lesson);
      setLessonForm({ title: lesson.title, type: lesson.type, content: lesson.content || {}, duration_minutes: lesson.duration_minutes || 5, is_required: lesson.is_required !== false });
      if (lesson.type === 'quiz' && lesson.content?.questions) {
        setQuizQuestions(lesson.content.questions);
        setPassingScore(lesson.content.passing_score || 70);
      }
    } else {
      setEditingLesson(null);
      setLessonForm({ title: '', type: 'text', content: {}, duration_minutes: 5, is_required: true });
      setQuizQuestions([{ question: '', options: ['', '', '', ''], correct: 0 }]);
      setPassingScore(70);
    }
    setShowLessonModal(true);
  };

  const saveLesson = async () => {
    if (!lessonForm.title.trim()) { toast.error('Lesson title required'); return; }
    let content = lessonForm.content;
    if (lessonForm.type === 'quiz') {
      content = { questions: quizQuestions.filter(q => q.question.trim()), passing_score: passingScore };
    }
    const payload = { ...lessonForm, content };
    try {
      if (editingLesson) {
        await fetch(`${API_URL}/admin/courses/${id}/lessons/${editingLesson.id}`, {
          method: 'PUT', headers: authHeaders, body: JSON.stringify(payload),
        });
        toast.success('Lesson updated');
      } else {
        await fetch(`${API_URL}/admin/courses/${id}/modules/${lessonModuleId}/lessons`, {
          method: 'POST', headers: authHeaders, body: JSON.stringify(payload),
        });
        toast.success('Lesson added');
      }
      setShowLessonModal(false);
      fetchCourse();
    } catch (err) { toast.error('Failed to save lesson'); }
  };

  const deleteLesson = async (lessonId) => {
    if (!window.confirm('Delete this lesson?')) return;
    await fetch(`${API_URL}/admin/courses/${id}/lessons/${lessonId}`, { method: 'DELETE', headers: authHeaders });
    toast.success('Lesson deleted');
    fetchCourse();
  };

  const moveLesson = async (lessonId, direction) => {
    await fetch(`${API_URL}/admin/courses/${id}/lessons/${lessonId}/move`, {
      method: 'POST', headers: authHeaders, body: JSON.stringify({ direction }),
    });
    fetchCourse();
  };

  const addQuizQuestion = () => {
    setQuizQuestions([...quizQuestions, { question: '', options: ['', '', '', ''], correct: 0 }]);
  };

  const updateQuestion = (idx, field, value) => {
    const updated = [...quizQuestions];
    updated[idx] = { ...updated[idx], [field]: value };
    setQuizQuestions(updated);
  };

  const updateOption = (qIdx, oIdx, value) => {
    const updated = [...quizQuestions];
    const opts = [...updated[qIdx].options];
    opts[oIdx] = value;
    updated[qIdx] = { ...updated[qIdx], options: opts };
    setQuizQuestions(updated);
  };

  const removeQuestion = (idx) => {
    setQuizQuestions(quizQuestions.filter((_, i) => i !== idx));
  };

  if (loading || !course) {
    return <div className="animate-pulse space-y-6"><div className="h-8 bg-slate-200 rounded w-64" /><div className="h-96 bg-slate-200 rounded-lg" /></div>;
  }

  return (
    <div className="space-y-6 animate-fade-in" data-testid="admin-course-editor">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="sm" onClick={() => navigate('/admin/courses')} data-testid="back-to-courses">
          <ArrowLeft className="w-4 h-4 mr-1" />Back
        </Button>
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-bold text-slate-900 truncate">{course.title}</h1>
          <p className="text-sm text-slate-500">Course Editor</p>
        </div>
        <Badge className={course.status === 'published' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'}>
          {course.status}
        </Badge>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-white border border-slate-200 p-1">
          <TabsTrigger value="info" data-testid="tab-info">Info</TabsTrigger>
          <TabsTrigger value="curriculum" data-testid="tab-curriculum">Curriculum</TabsTrigger>
          <TabsTrigger value="settings" data-testid="tab-settings">Settings</TabsTrigger>
        </TabsList>

        {/* INFO TAB */}
        <TabsContent value="info" className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <Label>Title</Label>
                <Input value={course.title || ''} onChange={(e) => setCourse({ ...course, title: e.target.value })} data-testid="course-title-input" />
              </div>
              <div>
                <Label>Instructor Name</Label>
                <Input value={course.instructor_name || ''} onChange={(e) => setCourse({ ...course, instructor_name: e.target.value })} data-testid="course-instructor-input" />
              </div>
            </div>
            <div>
              <Label>Description</Label>
              <textarea
                className="flex min-h-[120px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={course.description || ''}
                onChange={(e) => setCourse({ ...course, description: e.target.value })}
                data-testid="course-description-input"
              />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div>
                <Label>Category</Label>
                <Select value={course.category || 'general'} onValueChange={(v) => setCourse({ ...course, category: v })}>
                  <SelectTrigger data-testid="course-category-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="new_members">New Members</SelectItem>
                    <SelectItem value="leadership">Leadership</SelectItem>
                    <SelectItem value="discipleship">Discipleship</SelectItem>
                    <SelectItem value="marriage">Marriage & Family</SelectItem>
                    <SelectItem value="general">General</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Thumbnail URL</Label>
                <Input value={course.thumbnail_url || ''} onChange={(e) => setCourse({ ...course, thumbnail_url: e.target.value })} placeholder="https://..." data-testid="course-thumbnail-input" />
              </div>
            </div>
            <div>
              <Label>Status</Label>
              <Select value={course.status || 'draft'} onValueChange={(v) => setCourse({ ...course, status: v })}>
                <SelectTrigger data-testid="course-status-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="draft">Draft</SelectItem>
                  <SelectItem value="published">Published</SelectItem>
                  <SelectItem value="archived">Archived</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={saveCourseInfo} disabled={saving} data-testid="save-course-btn">
              <Save className="w-4 h-4 mr-2" />{saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </TabsContent>

        {/* CURRICULUM TAB */}
        <TabsContent value="curriculum" className="space-y-4">
          <div className="flex justify-end">
            <Button variant="outline" onClick={() => { setShowModuleModal(true); setEditingModuleId(null); setModuleTitle(''); }} data-testid="add-module-btn">
              <Plus className="w-4 h-4 mr-2" />Add Module
            </Button>
          </div>

          {(course.modules || []).length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-xl p-10 text-center" data-testid="curriculum-empty">
              <GraduationCap className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <p className="text-sm text-slate-500">No modules yet. Add a module to start building your curriculum.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {(course.modules || []).map((mod, mIdx) => (
                <div key={mod.id} className="bg-white border border-slate-200 rounded-xl overflow-hidden" data-testid={`module-${mod.id}`}>
                  <div className="flex items-center gap-3 p-4 bg-slate-50/50 border-b border-slate-100">
                    <Grip className="w-4 h-4 text-slate-300" />
                    <span className="text-sm font-semibold text-slate-900 flex-1">{mod.title}</span>
                    <div className="flex items-center gap-1">
                      <Button variant="ghost" size="sm" onClick={() => moveModule(mod.id, 'up')} disabled={mIdx === 0} data-testid={`move-module-up-${mod.id}`}>
                        <ChevronUp className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => moveModule(mod.id, 'down')} disabled={mIdx === (course.modules || []).length - 1} data-testid={`move-module-down-${mod.id}`}>
                        <ChevronDown className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => { setEditingModuleId(mod.id); setModuleTitle(mod.title); setShowModuleModal(true); }} data-testid={`edit-module-${mod.id}`}>
                        <Edit2 className="w-4 h-4" />
                      </Button>
                      <Button variant="ghost" size="sm" onClick={() => deleteModule(mod.id)} className="text-red-500 hover:text-red-700" data-testid={`delete-module-${mod.id}`}>
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  <div className="p-3 space-y-1.5">
                    {(mod.lessons || []).map((lesson, lIdx) => {
                      const Icon = LESSON_ICONS[lesson.type] || FileText;
                      const colorCls = LESSON_COLORS[lesson.type] || LESSON_COLORS.text;
                      return (
                        <div key={lesson.id} className="flex items-center gap-2.5 p-2.5 rounded-lg hover:bg-slate-50 group transition-colors" data-testid={`lesson-${lesson.id}`}>
                          <div className={`w-7 h-7 rounded-md flex items-center justify-center flex-shrink-0 ${colorCls}`}>
                            <Icon className="w-3.5 h-3.5" />
                          </div>
                          <span className="text-sm text-slate-800 flex-1 truncate">{lesson.title}</span>
                          <span className="text-xs text-slate-400">{lesson.duration_minutes}m</span>
                          <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => moveLesson(lesson.id, 'up')} disabled={lIdx === 0}>
                              <ChevronUp className="w-3.5 h-3.5" />
                            </Button>
                            <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => moveLesson(lesson.id, 'down')} disabled={lIdx === (mod.lessons || []).length - 1}>
                              <ChevronDown className="w-3.5 h-3.5" />
                            </Button>
                            <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => openLessonModal(mod.id, lesson)}>
                              <Edit2 className="w-3.5 h-3.5" />
                            </Button>
                            <Button variant="ghost" size="sm" className="h-7 w-7 p-0 text-red-500" onClick={() => deleteLesson(lesson.id)}>
                              <Trash2 className="w-3.5 h-3.5" />
                            </Button>
                          </div>
                        </div>
                      );
                    })}
                    <Button variant="ghost" size="sm" className="text-blue-600 w-full justify-start" onClick={() => openLessonModal(mod.id)} data-testid={`add-lesson-${mod.id}`}>
                      <Plus className="w-3.5 h-3.5 mr-1.5" />Add Lesson
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        {/* SETTINGS TAB */}
        <TabsContent value="settings" className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6 space-y-5">
            <div>
              <Label>Enrollment Type</Label>
              <Select value={course.enrollment_type || 'open'} onValueChange={(v) => setCourse({ ...course, enrollment_type: v })}>
                <SelectTrigger data-testid="enrollment-type-select"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="open">Open (Anyone can enroll)</SelectItem>
                  <SelectItem value="invite_only">Invite Only</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-slate-700">Certificate of Completion</p>
                  <p className="text-xs text-slate-500">Coming in V2</p>
                </div>
                <Switch disabled checked={false} />
              </div>
            </div>
            <Button onClick={saveCourseInfo} disabled={saving} data-testid="save-settings-btn">
              <Save className="w-4 h-4 mr-2" />{saving ? 'Saving...' : 'Save Settings'}
            </Button>
          </div>
        </TabsContent>
      </Tabs>

      {/* Module Modal */}
      <Dialog open={showModuleModal} onOpenChange={setShowModuleModal}>
        <DialogContent data-testid="module-modal">
          <DialogHeader><DialogTitle>{editingModuleId ? 'Edit Module' : 'Add Module'}</DialogTitle></DialogHeader>
          <div className="py-2">
            <Label>Module Title</Label>
            <Input value={moduleTitle} onChange={(e) => setModuleTitle(e.target.value)} placeholder="e.g. Chapter 1: Welcome" data-testid="module-title-input" />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowModuleModal(false)}>Cancel</Button>
            <Button onClick={addModule} data-testid="save-module-btn">{editingModuleId ? 'Update' : 'Add'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Lesson Modal */}
      <Dialog open={showLessonModal} onOpenChange={setShowLessonModal}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto" data-testid="lesson-modal">
          <DialogHeader><DialogTitle>{editingLesson ? 'Edit Lesson' : 'Add Lesson'}</DialogTitle></DialogHeader>
          <div className="space-y-4 py-2">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Title</Label>
                <Input value={lessonForm.title} onChange={(e) => setLessonForm({ ...lessonForm, title: e.target.value })} data-testid="lesson-title-input" />
              </div>
              <div>
                <Label>Type</Label>
                <Select value={lessonForm.type} onValueChange={(v) => setLessonForm({ ...lessonForm, type: v, content: {} })}>
                  <SelectTrigger data-testid="lesson-type-select"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="video">Video</SelectItem>
                    <SelectItem value="text">Text</SelectItem>
                    <SelectItem value="quiz">Quiz</SelectItem>
                    <SelectItem value="download">Download</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Duration (minutes)</Label>
                <Input type="number" value={lessonForm.duration_minutes} onChange={(e) => setLessonForm({ ...lessonForm, duration_minutes: parseInt(e.target.value) || 0 })} data-testid="lesson-duration-input" />
              </div>
              <div className="flex items-end gap-2 pb-1">
                <Switch checked={lessonForm.is_required} onCheckedChange={(v) => setLessonForm({ ...lessonForm, is_required: v })} data-testid="lesson-required-switch" />
                <Label className="text-sm">Required for completion</Label>
              </div>
            </div>

            {/* Type-specific content */}
            {lessonForm.type === 'video' && (
              <div>
                <Label>YouTube or Vimeo URL</Label>
                <Input
                  placeholder="https://www.youtube.com/watch?v=..."
                  value={lessonForm.content?.video_url || ''}
                  onChange={(e) => setLessonForm({ ...lessonForm, content: { video_url: e.target.value } })}
                  data-testid="lesson-video-url"
                />
              </div>
            )}
            {lessonForm.type === 'text' && (
              <div>
                <Label>Content (Markdown)</Label>
                <textarea
                  className="flex min-h-[200px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="# Heading&#10;&#10;Your lesson content here..."
                  value={lessonForm.content?.body || ''}
                  onChange={(e) => setLessonForm({ ...lessonForm, content: { body: e.target.value } })}
                  data-testid="lesson-text-body"
                />
              </div>
            )}
            {lessonForm.type === 'download' && (
              <div className="space-y-3">
                <div>
                  <Label>File URL</Label>
                  <Input
                    placeholder="https://drive.google.com/..."
                    value={lessonForm.content?.file_url || ''}
                    onChange={(e) => setLessonForm({ ...lessonForm, content: { ...lessonForm.content, file_url: e.target.value } })}
                    data-testid="lesson-download-url"
                  />
                </div>
                <div>
                  <Label>File Name</Label>
                  <Input
                    placeholder="worksheet.pdf"
                    value={lessonForm.content?.file_name || ''}
                    onChange={(e) => setLessonForm({ ...lessonForm, content: { ...lessonForm.content, file_name: e.target.value } })}
                    data-testid="lesson-download-name"
                  />
                </div>
              </div>
            )}
            {lessonForm.type === 'quiz' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Label>Quiz Questions</Label>
                  <div className="flex items-center gap-2">
                    <Label className="text-xs text-slate-500">Passing score:</Label>
                    <Input type="number" className="w-16 h-7 text-xs" value={passingScore} onChange={(e) => setPassingScore(parseInt(e.target.value) || 70)} data-testid="quiz-passing-score" />
                    <span className="text-xs text-slate-500">%</span>
                  </div>
                </div>
                {quizQuestions.map((q, qIdx) => (
                  <div key={qIdx} className="border border-slate-200 rounded-lg p-3 space-y-2" data-testid={`quiz-question-${qIdx}`}>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-slate-500">Q{qIdx + 1}</span>
                      <Input
                        className="flex-1"
                        placeholder="Enter question..."
                        value={q.question}
                        onChange={(e) => updateQuestion(qIdx, 'question', e.target.value)}
                        data-testid={`quiz-q-${qIdx}-text`}
                      />
                      {quizQuestions.length > 1 && (
                        <Button variant="ghost" size="sm" className="text-red-500 h-7 w-7 p-0" onClick={() => removeQuestion(qIdx)}>
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      )}
                    </div>
                    {q.options.map((opt, oIdx) => (
                      <div key={oIdx} className="flex items-center gap-2 pl-6">
                        <input
                          type="radio"
                          name={`q-${qIdx}-correct`}
                          checked={q.correct === oIdx}
                          onChange={() => updateQuestion(qIdx, 'correct', oIdx)}
                          className="w-4 h-4 accent-emerald-600"
                          data-testid={`quiz-q-${qIdx}-opt-${oIdx}-radio`}
                        />
                        <Input
                          className="flex-1 h-8 text-sm"
                          placeholder={`Option ${String.fromCharCode(65 + oIdx)}`}
                          value={opt}
                          onChange={(e) => updateOption(qIdx, oIdx, e.target.value)}
                          data-testid={`quiz-q-${qIdx}-opt-${oIdx}-text`}
                        />
                      </div>
                    ))}
                  </div>
                ))}
                <Button variant="outline" size="sm" onClick={addQuizQuestion} data-testid="add-quiz-question-btn">
                  <Plus className="w-3.5 h-3.5 mr-1" />Add Question
                </Button>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowLessonModal(false)}>Cancel</Button>
            <Button onClick={saveLesson} data-testid="save-lesson-btn">{editingLesson ? 'Update Lesson' : 'Add Lesson'}</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
