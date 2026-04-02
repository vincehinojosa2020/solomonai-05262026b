/**
 * Pathways course/lesson/assignment dialog components — extracted from AbundantPathwaysAdmin.
 */
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Clock, Edit, Trash2, X } from 'lucide-react';

export const CourseDialog = ({ open, onOpenChange, editingCourse, courseForm, setCourseForm, onSave, saving }) => (
  <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent className="pathways-modal" data-testid="course-modal">
      <DialogHeader>
        <DialogTitle>{editingCourse ? 'Edit Course' : 'Create Course'}</DialogTitle>
        <DialogDescription>Build a new discipleship course for your congregation.</DialogDescription>
      </DialogHeader>
      <div className="pathways-form">
        <Input value={courseForm.title} onChange={(e) => setCourseForm((prev) => ({ ...prev, title: e.target.value }))} placeholder="Course title" data-testid="course-title-input" />
        <Textarea value={courseForm.description} onChange={(e) => setCourseForm((prev) => ({ ...prev, description: e.target.value }))} placeholder="Course description" data-testid="course-description-input" />
        <Input value={courseForm.cover_image_url} onChange={(e) => setCourseForm((prev) => ({ ...prev, cover_image_url: e.target.value }))} placeholder="Cover image URL" data-testid="course-cover-input" />
        <div className="pathways-form-row">
          <Input value={courseForm.category} onChange={(e) => setCourseForm((prev) => ({ ...prev, category: e.target.value }))} placeholder="Category (e.g. Discipleship)" data-testid="course-category-input" />
          <Input value={courseForm.level} onChange={(e) => setCourseForm((prev) => ({ ...prev, level: e.target.value }))} placeholder="Level (Beginner, Intermediate)" data-testid="course-level-input" />
        </div>
        <div className="pathways-form-actions">
          <Button onClick={onSave} disabled={saving} data-testid="course-save-btn">{saving ? 'Saving...' : 'Save Course'}</Button>
        </div>
      </div>
    </DialogContent>
  </Dialog>
);

export const LessonDialog = ({ open, onOpenChange, activeCourse, lessons, lessonForm, setLessonForm, editingLesson, onSave, onEdit, onDelete, onCancelEdit, saving }) => (
  <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent className="pathways-modal" data-testid="lesson-modal">
      <DialogHeader>
        <DialogTitle>{activeCourse ? `Lessons for ${activeCourse.title}` : 'Lessons'}</DialogTitle>
        <DialogDescription>Add lessons and videos to build out the course structure.</DialogDescription>
      </DialogHeader>
      <div className="pathways-form">
        <Input value={lessonForm.title} onChange={(e) => setLessonForm((prev) => ({ ...prev, title: e.target.value }))} placeholder="Lesson title" data-testid="lesson-title-input" />
        <Textarea value={lessonForm.description} onChange={(e) => setLessonForm((prev) => ({ ...prev, description: e.target.value }))} placeholder="Lesson description" data-testid="lesson-description-input" />
        <Input value={lessonForm.video_url} onChange={(e) => setLessonForm((prev) => ({ ...prev, video_url: e.target.value }))} placeholder="YouTube video URL" data-testid="lesson-video-input" />
        <div className="pathways-form-row">
          <Input value={lessonForm.duration_label} onChange={(e) => setLessonForm((prev) => ({ ...prev, duration_label: e.target.value }))} placeholder="Duration (MM:SS)" data-testid="lesson-duration-input" />
          <Input value={lessonForm.resource_url} onChange={(e) => setLessonForm((prev) => ({ ...prev, resource_url: e.target.value }))} placeholder="Resource / PDF URL" data-testid="lesson-resource-input" />
        </div>
        <div className="pathways-form-actions">
          <Button onClick={onSave} disabled={saving} data-testid="lesson-save-btn">{saving ? 'Saving...' : editingLesson ? 'Update Lesson' : 'Add Lesson'}</Button>
          {editingLesson && (
            <Button variant="ghost" onClick={onCancelEdit} data-testid="lesson-cancel-edit"><X className="w-4 h-4" /> Cancel</Button>
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
              <Button variant="ghost" onClick={() => onEdit(lesson)} data-testid={`edit-lesson-${lesson.id}`}><Edit className="w-4 h-4" /></Button>
              <Button variant="ghost" onClick={() => onDelete(lesson.id)} data-testid={`delete-lesson-${lesson.id}`}><Trash2 className="w-4 h-4 text-red-500" /></Button>
            </div>
          </div>
        ))}
      </div>
    </DialogContent>
  </Dialog>
);

export const AssignmentDialog = ({ open, onOpenChange, activeCourse, assignments, availableMembers, onAssign, onRemove }) => (
  <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent className="pathways-modal" data-testid="assignment-modal">
      <DialogHeader>
        <DialogTitle>{activeCourse ? `Assign Members for ${activeCourse.title}` : 'Assign Members'}</DialogTitle>
        <DialogDescription>Assign and track progress for members in this course.</DialogDescription>
      </DialogHeader>
      <div className="pathways-assignment-grid">
        <div className="pathways-assignment-list">
          <h4>Assigned Members</h4>
          {assignments.length === 0 ? (
            <p className="pathways-empty">No members assigned yet.</p>
          ) : assignments.map((assignment) => {
            const memberId = assignment.member?.user_id || assignment.user_id;
            return (
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
                <Button variant="ghost" onClick={() => onRemove(memberId)} data-testid={`remove-member-${memberId}`}>
                  <X className="w-4 h-4" />
                </Button>
              </div>
            );
          })}
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
              <Button variant="outline" onClick={() => onAssign(member.user_id)} data-testid={`assign-member-${member.user_id}`}>Assign</Button>
            </div>
          ))}
        </div>
      </div>
    </DialogContent>
  </Dialog>
);
