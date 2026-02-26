import { useEffect, useState } from 'react';
import {
  BookOpen,
  Plus,
  Users,
  Edit,
  Trash2,
  Video,
  GraduationCap,
  UserPlus,
  X,
  Clock
} from 'lucide-react';
import { API_URL } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { toast } from 'sonner';

const defaultCourseForm = {
  title: '',
  description: '',
  cover_image_url: '',
  category: '',
  level: 'Beginner',
  is_published: true,
};

const defaultLessonForm = {
  title: '',
  description: '',
  video_url: '',
  duration_label: '',
  resource_url: '',
  sort_order: 1,
  is_published: true,
};

export default function AbundantPathwaysAdmin() {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [courseModalOpen, setCourseModalOpen] = useState(false);
  const [lessonModalOpen, setLessonModalOpen] = useState(false);
  const [assignmentModalOpen, setAssignmentModalOpen] = useState(false);
  const [courseForm, setCourseForm] = useState(defaultCourseForm);
  const [lessonForm, setLessonForm] = useState(defaultLessonForm);
  const [editingCourse, setEditingCourse] = useState(null);
  const [editingLesson, setEditingLesson] = useState(null);
  const [activeCourse, setActiveCourse] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [availableMembers, setAvailableMembers] = useState([]);
  const [saving, setSaving] = useState(false);

  const fetchCourses = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/admin/pathways/courses`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        setCourses(data.courses || []);
      }
    } catch (error) {
      console.error('Failed to fetch courses:', error);
      toast.error('Failed to load courses');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCourses();
  }, []);

  const resetCourseForm = () => {
    setCourseForm(defaultCourseForm);
    setEditingCourse(null);
  };

  const resetLessonForm = () => {
    setLessonForm(defaultLessonForm);
    setEditingLesson(null);
  };

  const openCourseModal = (course) => {
    if (course) {
      setEditingCourse(course);
      setCourseForm({
        title: course.title || '',
        description: course.description || '',
        cover_image_url: course.cover_image_url || '',
        category: course.category || '',
        level: course.level || 'Beginner',
        is_published: course.is_published ?? true,
      });
    } else {
      resetCourseForm();
    }
    setCourseModalOpen(true);
  };

  const openLessonsModal = async (course) => {
    setActiveCourse(course);
    setLessonModalOpen(true);
    resetLessonForm();
    try {
      const res = await fetch(`${API_URL}/admin/pathways/courses/${course.id}/lessons`, {
        credentials: 'include'
      });
      if (res.ok) {
        const data = await res.json();
        setLessons(data.lessons || []);
      }
    } catch (error) {
      toast.error('Failed to load lessons');
    }
  };

  const openAssignmentsModal = async (course) => {
    setActiveCourse(course);
    setAssignmentModalOpen(true);
    await refreshAssignments(course.id);
  };

  const refreshAssignments = async (courseId) => {
    try {
      const [assignmentsRes, membersRes] = await Promise.all([
        fetch(`${API_URL}/admin/pathways/courses/${courseId}/assignments`, { credentials: 'include' }),
        fetch(`${API_URL}/admin/pathways/available-members?course_id=${courseId}`, { credentials: 'include' })
      ]);
      if (assignmentsRes.ok) {
        const data = await assignmentsRes.json();
        setAssignments(data.assignments || []);
      }
      if (membersRes.ok) {
        const data = await membersRes.json();
        setAvailableMembers(data.members || []);
      }
    } catch (error) {
      toast.error('Failed to load assignments');
    }
  };

  const saveCourse = async () => {
    if (!courseForm.title.trim()) {
      toast.error('Course title is required');
      return;
    }
    setSaving(true);
    try {
      const res = await fetch(`${API_URL}/admin/pathways/courses${editingCourse ? `/${editingCourse.id}` : ''}`, {
        method: editingCourse ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(courseForm),
      });
      if (res.ok) {
        toast.success(editingCourse ? 'Course updated' : 'Course created');
        setCourseModalOpen(false);
        resetCourseForm();
        fetchCourses();
      } else {
        toast.error('Failed to save course');
      }
    } catch (error) {
      toast.error('Failed to save course');
    } finally {
      setSaving(false);
    }
  };

  const deleteCourse = async (courseId) => {
    if (!confirm('Delete this course and all lessons?')) return;
    try {
      const res = await fetch(`${API_URL}/admin/pathways/courses/${courseId}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      if (res.ok) {
        toast.success('Course deleted');
        fetchCourses();
      } else {
        toast.error('Failed to delete course');
      }
    } catch (error) {
      toast.error('Failed to delete course');
    }
  };

  const saveLesson = async () => {
    if (!lessonForm.title.trim()) {
      toast.error('Lesson title is required');
      return;
    }
    setSaving(true);
    try {
      const endpoint = editingLesson
        ? `${API_URL}/admin/pathways/lessons/${editingLesson.id}`
        : `${API_URL}/admin/pathways/courses/${activeCourse.id}/lessons`;
      const res = await fetch(endpoint, {
        method: editingLesson ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(lessonForm),
      });
      if (res.ok) {
        toast.success(editingLesson ? 'Lesson updated' : 'Lesson created');
        resetLessonForm();
        openLessonsModal(activeCourse);
      } else {
        toast.error('Failed to save lesson');
      }
    } catch (error) {
      toast.error('Failed to save lesson');
    } finally {
      setSaving(false);
    }
  };

  const editLesson = (lesson) => {
    setEditingLesson(lesson);
    setLessonForm({
      title: lesson.title || '',
      description: lesson.description || '',
      video_url: lesson.video_url || '',
      duration_label: lesson.duration_label || '',
      resource_url: lesson.resource_url || '',
      sort_order: lesson.sort_order || 1,
      is_published: lesson.is_published ?? true,
    });
  };

  const deleteLesson = async (lessonId) => {
    if (!confirm('Delete this lesson?')) return;
    try {
      const res = await fetch(`${API_URL}/admin/pathways/lessons/${lessonId}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      if (res.ok) {
        toast.success('Lesson deleted');
        openLessonsModal(activeCourse);
      } else {
        toast.error('Failed to delete lesson');
      }
    } catch (error) {
      toast.error('Failed to delete lesson');
    }
  };

  const assignMember = async (memberId) => {
    try {
      const res = await fetch(`${API_URL}/admin/pathways/courses/${activeCourse.id}/assignments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ member_id: memberId })
      });
      if (res.ok) {
        toast.success('Member assigned');
        refreshAssignments(activeCourse.id);
      } else {
        toast.error('Failed to assign member');
      }
    } catch (error) {
      toast.error('Failed to assign member');
    }
  };

  const removeMember = async (memberId) => {
    try {
      const res = await fetch(`${API_URL}/admin/pathways/courses/${activeCourse.id}/assignments/${memberId}`, {
        method: 'DELETE',
        credentials: 'include'
      });
      if (res.ok) {
        toast.success('Member removed');
        refreshAssignments(activeCourse.id);
      } else {
        toast.error('Failed to remove member');
      }
    } catch (error) {
      toast.error('Failed to remove member');
    }
  };

  return (
    <div className="pathways-admin" data-testid="pathways-admin-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Abundant Pathways</h1>
          <p className="page-subtitle">
            Build discipleship courses, assign members, and track progress.
          </p>
        </div>
        <Button
          className="pathways-add-btn"
          onClick={() => openCourseModal(null)}
          data-testid="add-course-btn"
        >
          <Plus className="w-4 h-4" />
          Create Course
        </Button>
      </div>

      {loading ? (
        <div className="pathways-loading" data-testid="pathways-loading">Loading courses...</div>
      ) : (
        <div className="pathways-grid" data-testid="pathways-course-grid">
          {courses.map((course) => (
            <div key={course.id} className="pathways-card" data-testid={`pathways-course-${course.id}`}>
              <div className="pathways-card-media">
                <img
                  src={course.cover_image_url || 'https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?auto=format&fit=crop&w=900&q=80'}
                  alt={course.title}
                />
                <div className="pathways-card-badge">
                  {course.is_published ? 'Published' : 'Draft'}
                </div>
              </div>
              <div className="pathways-card-body">
                <h3>{course.title}</h3>
                <p>{course.description || 'No description yet.'}</p>
                <div className="pathways-card-meta">
                  <span><BookOpen className="w-4 h-4" /> {course.lesson_count} lessons</span>
                  <span><Users className="w-4 h-4" /> {course.assigned_count} assigned</span>
                </div>
                <div className="pathways-card-tags">
                  <span>{course.category || 'Discipleship'}</span>
                  <span><GraduationCap className="w-4 h-4" /> {course.level || 'Beginner'}</span>
                </div>
              </div>
              <div className="pathways-card-actions">
                <Button
                  variant="outline"
                  onClick={() => openLessonsModal(course)}
                  data-testid={`manage-lessons-${course.id}`}
                >
                  <Video className="w-4 h-4" /> Lessons
                </Button>
                <Button
                  variant="outline"
                  onClick={() => openAssignmentsModal(course)}
                  data-testid={`assign-members-${course.id}`}
                >
                  <UserPlus className="w-4 h-4" /> Assign
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => openCourseModal(course)}
                  data-testid={`edit-course-${course.id}`}
                >
                  <Edit className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => deleteCourse(course.id)}
                  data-testid={`delete-course-${course.id}`}
                >
                  <Trash2 className="w-4 h-4 text-red-500" />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Dialog open={courseModalOpen} onOpenChange={setCourseModalOpen}>
        <DialogContent className="pathways-modal" data-testid="course-modal">
          <DialogHeader>
            <DialogTitle>{editingCourse ? 'Edit Course' : 'Create Course'}</DialogTitle>
            <DialogDescription>
              Build a new discipleship course for your congregation.
            </DialogDescription>
          </DialogHeader>
          <div className="pathways-form">
            <Input
              value={courseForm.title}
              onChange={(e) => setCourseForm((prev) => ({ ...prev, title: e.target.value }))}
              placeholder="Course title"
              data-testid="course-title-input"
            />
            <Textarea
              value={courseForm.description}
              onChange={(e) => setCourseForm((prev) => ({ ...prev, description: e.target.value }))}
              placeholder="Course description"
              data-testid="course-description-input"
            />
            <Input
              value={courseForm.cover_image_url}
              onChange={(e) => setCourseForm((prev) => ({ ...prev, cover_image_url: e.target.value }))}
              placeholder="Cover image URL"
              data-testid="course-cover-input"
            />
            <div className="pathways-form-row">
              <Input
                value={courseForm.category}
                onChange={(e) => setCourseForm((prev) => ({ ...prev, category: e.target.value }))}
                placeholder="Category (e.g. Discipleship)"
                data-testid="course-category-input"
              />
              <Input
                value={courseForm.level}
                onChange={(e) => setCourseForm((prev) => ({ ...prev, level: e.target.value }))}
                placeholder="Level (Beginner, Intermediate)"
                data-testid="course-level-input"
              />
            </div>
            <div className="pathways-form-actions">
              <Button onClick={saveCourse} disabled={saving} data-testid="course-save-btn">
                {saving ? 'Saving...' : 'Save Course'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={lessonModalOpen} onOpenChange={setLessonModalOpen}>
        <DialogContent className="pathways-modal" data-testid="lesson-modal">
          <DialogHeader>
            <DialogTitle>{activeCourse ? `Lessons for ${activeCourse.title}` : 'Lessons'}</DialogTitle>
            <DialogDescription>
              Add lessons and videos to build out the course structure.
            </DialogDescription>
          </DialogHeader>
          <div className="pathways-form">
            <Input
              value={lessonForm.title}
              onChange={(e) => setLessonForm((prev) => ({ ...prev, title: e.target.value }))}
              placeholder="Lesson title"
              data-testid="lesson-title-input"
            />
            <Textarea
              value={lessonForm.description}
              onChange={(e) => setLessonForm((prev) => ({ ...prev, description: e.target.value }))}
              placeholder="Lesson description"
              data-testid="lesson-description-input"
            />
            <Input
              value={lessonForm.video_url}
              onChange={(e) => setLessonForm((prev) => ({ ...prev, video_url: e.target.value }))}
              placeholder="YouTube video URL"
              data-testid="lesson-video-input"
            />
            <div className="pathways-form-row">
              <Input
                value={lessonForm.duration_label}
                onChange={(e) => setLessonForm((prev) => ({ ...prev, duration_label: e.target.value }))}
                placeholder="Duration (MM:SS)"
                data-testid="lesson-duration-input"
              />
              <Input
                value={lessonForm.resource_url}
                onChange={(e) => setLessonForm((prev) => ({ ...prev, resource_url: e.target.value }))}
                placeholder="Resource / PDF URL"
                data-testid="lesson-resource-input"
              />
            </div>
            <div className="pathways-form-actions">
              <Button onClick={saveLesson} disabled={saving} data-testid="lesson-save-btn">
                {saving ? 'Saving...' : editingLesson ? 'Update Lesson' : 'Add Lesson'}
              </Button>
              {editingLesson && (
                <Button variant="ghost" onClick={resetLessonForm} data-testid="lesson-cancel-edit">
                  <X className="w-4 h-4" /> Cancel
                </Button>
              )}
            </div>
          </div>

          <div className="pathways-lessons-list" data-testid="lessons-list">
            {lessons.map((lesson) => (
              <div key={lesson.id} className="pathways-lesson-card">
                <div>
                  <h4>{lesson.title}</h4>
                  <p>{lesson.description || 'No description'}</p>
                  <div className="pathways-lesson-meta">
                    <span><Clock className="w-3 h-3" /> {lesson.duration_label || '00:00'}</span>
                    <span>{lesson.is_published ? 'Published' : 'Draft'}</span>
                  </div>
                </div>
                <div className="pathways-lesson-actions">
                  <Button variant="ghost" onClick={() => editLesson(lesson)} data-testid={`edit-lesson-${lesson.id}`}>
                    <Edit className="w-4 h-4" />
                  </Button>
                  <Button variant="ghost" onClick={() => deleteLesson(lesson.id)} data-testid={`delete-lesson-${lesson.id}`}>
                    <Trash2 className="w-4 h-4 text-red-500" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>

      <Dialog open={assignmentModalOpen} onOpenChange={setAssignmentModalOpen}>
        <DialogContent className="pathways-modal" data-testid="assignment-modal">
          <DialogHeader>
            <DialogTitle>{activeCourse ? `Assign Members for ${activeCourse.title}` : 'Assign Members'}</DialogTitle>
            <DialogDescription>
              Assign and track progress for members in this course.
            </DialogDescription>
          </DialogHeader>
          <div className="pathways-assignment-grid">
            <div className="pathways-assignment-list">
              <h4>Assigned Members</h4>
              {assignments.length === 0 ? (
                <p className="pathways-empty">No members assigned yet.</p>
              ) : assignments.map((assignment) => (
                <div key={assignment.id} className="pathways-assignment-card">
                  <div>
                    <strong>{assignment.member?.name || 'Member'}</strong>
                    <span>{assignment.member?.email}</span>
                    <div className="pathways-progress">
                      <div className="pathways-progress-bar">
                        <div style={{ width: `${assignment.progress_percent || 0}%` }} />
                      </div>
                      <small>{assignment.progress_percent || 0}% complete</small>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    onClick={() => removeMember(assignment.member?.user_id)}
                    data-testid={`remove-member-${assignment.member?.user_id}`}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              ))}
            </div>

            <div className="pathways-assignment-list">
              <h4>Available Members</h4>
              {availableMembers.length === 0 ? (
                <p className="pathways-empty">All members are assigned.</p>
              ) : availableMembers.map((member) => (
                <div key={member.user_id} className="pathways-assignment-card">
                  <div>
                    <strong>{member.name || 'Member'}</strong>
                    <span>{member.email}</span>
                  </div>
                  <Button
                    variant="outline"
                    onClick={() => assignMember(member.user_id)}
                    data-testid={`assign-member-${member.user_id}`}
                  >
                    Assign
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
