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
  Clock,
  CheckCircle2,
  ShieldCheck,
  Ban
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
import { safeImgSrc } from '@/utils/sanitize';

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

import { CourseDialog, LessonDialog, AssignmentDialog } from './PathwaysDialogs';

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
  const [nextStepsApprovals, setNextStepsApprovals] = useState([]);
  const [approvalsLoading, setApprovalsLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const fetchCourses = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/admin/pathways/courses`);
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
    fetchNextStepsApprovals();
  }, []);

  const fetchNextStepsApprovals = async () => {
    setApprovalsLoading(true);
    try {
      const res = await fetch(`${API_URL}/admin/next-steps/approvals`);
      if (res.ok) {
        const data = await res.json();
        setNextStepsApprovals(data.approvals || []);
      }
    } catch (error) {
      console.error('Failed to fetch next steps approvals:', error);
    } finally {
      setApprovalsLoading(false);
    }
  };

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
        fetch(`${API_URL}/admin/pathways/courses/${courseId}/assignments`),
        fetch(`${API_URL}/admin/pathways/available-members?course_id=${courseId}`)
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

  const decideApproval = async (userId, action) => {
    try {
      const res = await fetch(`${API_URL}/admin/next-steps/approvals/${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        
        body: JSON.stringify({ action })
      });
      if (res.ok) {
        toast.success(`Membership ${action === 'approve' ? 'approved' : 'rejected'}`);
        fetchNextStepsApprovals();
      } else {
        const data = await res.json().catch(() => ({}));
        toast.error(data.detail || 'Unable to update status');
      }
    } catch (error) {
      toast.error('Failed to update membership status');
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

      <section className="rounded-3xl border border-slate-200 bg-white p-5 mb-8" data-testid="next-steps-approval-queue">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div>
            <p className="text-xs uppercase tracking-wide font-semibold text-blue-700">Membership Approvals</p>
            <h2 className="text-xl font-semibold text-slate-900 mt-1">Abundant Next Steps Queue</h2>
            <p className="text-sm text-slate-600 mt-1">Manual approval ensures completed members are formally recognized.</p>
          </div>
          <Button variant="outline" onClick={fetchNextStepsApprovals} data-testid="refresh-next-steps-approvals-btn">
            Refresh Queue
          </Button>
        </div>

        {approvalsLoading ? (
          <div className="text-sm text-slate-500" data-testid="next-steps-approvals-loading">Loading approval queue...</div>
        ) : nextStepsApprovals.length === 0 ? (
          <div className="text-sm text-slate-500" data-testid="next-steps-approvals-empty">No memberships in queue right now.</div>
        ) : (
          <div className="space-y-3" data-testid="next-steps-approvals-list">
            {nextStepsApprovals.map((item) => (
              <div
                key={item.id}
                className="rounded-2xl border border-slate-200 p-4 flex flex-wrap items-center justify-between gap-3"
                data-testid={`next-steps-approval-${item.user_id}`}
              >
                <div>
                  <p className="font-semibold text-slate-900" data-testid={`next-steps-approval-name-${item.user_id}`}>{item.member?.name || 'Unknown Member'}</p>
                  <p className="text-xs text-slate-500" data-testid={`next-steps-approval-email-${item.user_id}`}>{item.member?.email || ''}</p>
                  <p className="text-sm text-slate-600 mt-1" data-testid={`next-steps-approval-progress-${item.user_id}`}>
                    {item.completion_percent || 0}% complete • {item.approval_status?.replaceAll('_', ' ') || 'in progress'}
                  </p>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    className="border-green-200 text-green-700"
                    onClick={() => decideApproval(item.user_id, 'approve')}
                    disabled={!item.eligible || item.approval_status === 'approved'}
                    data-testid={`approve-next-steps-${item.user_id}`}
                  >
                    <CheckCircle2 className="w-4 h-4" /> Approve
                  </Button>
                  <Button
                    variant="outline"
                    className="border-rose-200 text-rose-700"
                    onClick={() => decideApproval(item.user_id, 'reject')}
                    disabled={item.approval_status === 'rejected'}
                    data-testid={`reject-next-steps-${item.user_id}`}
                  >
                    <Ban className="w-4 h-4" /> Reject
                  </Button>
                  {item.approval_status === 'approved' && (
                    <span className="inline-flex items-center gap-1 text-xs rounded-full bg-emerald-50 text-emerald-700 px-3 py-1" data-testid={`next-steps-approved-badge-${item.user_id}`}>
                      <ShieldCheck className="w-3.5 h-3.5" /> Approved
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {loading ? (
        <div className="pathways-loading" data-testid="pathways-loading">Loading courses...</div>
      ) : (
        <div className="pathways-grid" data-testid="pathways-course-grid">
          {courses.map((course) => (
            <div key={course.id} className="pathways-card" data-testid={`pathways-course-${course.id}`}>
              <div className="pathways-card-media">
                <img
                  src={safeImgSrc(course.cover_image_url, 'https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?auto=format&fit=crop&w=900&q=80')}
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

      <CourseDialog
        open={courseModalOpen}
        onOpenChange={setCourseModalOpen}
        editingCourse={editingCourse}
        courseForm={courseForm}
        setCourseForm={setCourseForm}
        onSave={saveCourse}
        saving={saving}
      />

      <LessonDialog
        open={lessonModalOpen}
        onOpenChange={setLessonModalOpen}
        activeCourse={activeCourse}
        lessons={lessons}
        lessonForm={lessonForm}
        setLessonForm={setLessonForm}
        editingLesson={editingLesson}
        onSave={saveLesson}
        onEdit={editLesson}
        onDelete={deleteLesson}
        onCancelEdit={resetLessonForm}
        saving={saving}
      />

      <AssignmentDialog
        open={assignmentModalOpen}
        onOpenChange={setAssignmentModalOpen}
        activeCourse={activeCourse}
        assignments={assignments}
        availableMembers={availableMembers}
        onAssign={assignMember}
        onRemove={removeMember}
      />
    </div>
  );
}
