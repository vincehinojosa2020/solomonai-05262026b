/**
 * GroupDetail dialog components — extracted for maintainability.
 */
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

export const CreateEventDialog = ({ open, onOpenChange, eventForm, setEventForm, onCreate }) => (
  <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent data-testid="create-event-dialog">
      <DialogHeader><DialogTitle>New Group Event</DialogTitle></DialogHeader>
      <div className="space-y-3 py-2">
        <div>
          <Label>Title</Label>
          <Input placeholder="e.g. Bible Study Night" value={eventForm.title}
            onChange={e => setEventForm({ ...eventForm, title: e.target.value })} data-testid="event-title-input" />
        </div>
        <div>
          <Label>Description</Label>
          <Input placeholder="What's this event about?" value={eventForm.description}
            onChange={e => setEventForm({ ...eventForm, description: e.target.value })} data-testid="event-desc-input" />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label>Date</Label>
            <Input type="date" value={eventForm.event_date}
              onChange={e => setEventForm({ ...eventForm, event_date: e.target.value })} data-testid="event-date-input" />
          </div>
          <div>
            <Label>Time</Label>
            <Input type="time" value={eventForm.event_time}
              onChange={e => setEventForm({ ...eventForm, event_time: e.target.value })} data-testid="event-time-input" />
          </div>
        </div>
        <div>
          <Label>Location</Label>
          <Input placeholder="Where?" value={eventForm.location}
            onChange={e => setEventForm({ ...eventForm, location: e.target.value })} data-testid="event-location-input" />
        </div>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
        <Button onClick={onCreate} data-testid="save-event-btn">Create Event</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
);

export const AddResourceDialog = ({ open, onOpenChange, resourceForm, setResourceForm, onAdd }) => (
  <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent data-testid="add-resource-dialog">
      <DialogHeader><DialogTitle>Add Resource</DialogTitle></DialogHeader>
      <div className="space-y-3 py-2">
        <div>
          <Label>Title</Label>
          <Input placeholder="e.g. Week 1 Study Guide" value={resourceForm.title}
            onChange={e => setResourceForm({ ...resourceForm, title: e.target.value })} data-testid="resource-title-input" />
        </div>
        <div>
          <Label>Description</Label>
          <Input placeholder="Brief description" value={resourceForm.description}
            onChange={e => setResourceForm({ ...resourceForm, description: e.target.value })} data-testid="resource-desc-input" />
        </div>
        <div>
          <Label>Type</Label>
          <select className="w-full rounded-md border border-slate-200 p-2 text-sm" value={resourceForm.resource_type}
            onChange={e => setResourceForm({ ...resourceForm, resource_type: e.target.value })} data-testid="resource-type-select">
            <option value="link">Link / URL</option>
            <option value="document">Document</option>
            <option value="video">Video</option>
            <option value="audio">Audio</option>
          </select>
        </div>
        <div>
          <Label>URL</Label>
          <Input placeholder="https://..." value={resourceForm.url}
            onChange={e => setResourceForm({ ...resourceForm, url: e.target.value })} data-testid="resource-url-input" />
        </div>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
        <Button onClick={onAdd} data-testid="save-resource-btn">Add Resource</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
);
